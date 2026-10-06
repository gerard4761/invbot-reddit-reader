"""invbot-reddit-reader: a small, read-only Reddit reader for personal research.

Once a day it reads the newest public posts of a fixed list of consumer-product
subreddits and counts how many posts mention each brand or product name. Only
the daily counts are written to disk; post text, usernames and any other
personal data are never stored.

Read-only by design: it never posts, comments, votes, sends messages or
moderates. It uses Reddit's application-only OAuth (client credentials), so it
does not act as any user.

Configuration (environment variables):
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET   the app's credentials
    REDDIT_USERNAME                          used only in the User-Agent
    OUTPUT_DIR                               where daily counts go (default ./counts)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx

SUBREDDITS_FILE = Path(__file__).with_name("subreddits.txt")
TERMS_FILE = Path(__file__).with_name("terms.txt")

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"

PAGES_PER_SUBREDDIT = 2  # 2 x 100 newest posts per subreddit and day
PAUSE_SECONDS = 1.0  # at most one request per second (limit: 100 per minute)
MAX_REQUESTS_PER_RUN = 100  # hard cap per daily run (declared: under 1,000 a day)


def read_list(path: Path) -> list[str]:
    """Non-empty, non-comment lines of a text file."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def count_mentions(texts: list[str], terms: list[str]) -> Counter:
    """How many texts mention each term (whole words, case-insensitive). Each
    text counts at most once per term."""
    patterns = {t: re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE) for t in terms}
    counts: Counter = Counter()
    for text in texts:
        for term, pattern in patterns.items():
            if pattern.search(text):
                counts[term] += 1
    return counts


class Reader:
    def __init__(self, client_id: str, client_secret: str, username: str) -> None:
        self.user_agent = f"script:invbot-reddit-reader:v0.1 (by /u/{username})"
        self.client = httpx.Client(timeout=30, headers={"User-Agent": self.user_agent})
        self.requests = 0
        response = self.client.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self.client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"

    def _get(self, path: str, params: dict) -> dict:
        if self.requests >= MAX_REQUESTS_PER_RUN:
            raise RuntimeError("Request cap for this run reached.")
        time.sleep(PAUSE_SECONDS)
        self.requests += 1
        response = self.client.get(f"{API}{path}", params=params)
        response.raise_for_status()
        return response.json()

    def newest_texts(self, subreddit: str) -> list[str]:
        """Title and body of the newest public posts. Kept in memory only."""
        texts, after = [], None
        for _ in range(PAGES_PER_SUBREDDIT):
            data = self._get(f"/r/{subreddit}/new", {"limit": 100, "after": after, "raw_json": 1})["data"]
            texts += [f"{p['data'].get('title', '')}\n{p['data'].get('selftext', '')}" for p in data["children"]]
            after = data.get("after")
            if not after:
                break
        return texts


def main() -> int:
    reader = Reader(
        os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"], os.environ["REDDIT_USERNAME"]
    )
    terms = read_list(TERMS_FILE)
    day = datetime.now(UTC).date().isoformat()
    result = {"date": day, "subreddits": {}}
    for subreddit in read_list(SUBREDDITS_FILE):
        texts = reader.newest_texts(subreddit)
        result["subreddits"][subreddit] = {"posts_read": len(texts), "mentions": dict(count_mentions(texts, terms))}
        del texts  # the text itself is never written anywhere
    out = Path(os.environ.get("OUTPUT_DIR", "counts"))
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{day}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"{day}: {len(result['subreddits'])} subreddits, {reader.requests} requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
