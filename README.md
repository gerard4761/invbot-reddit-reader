# invbot-reddit-reader

A small, **read-only** Reddit reader for a personal research project.

Once a day it reads the newest public posts of a short, fixed list of consumer-product subreddits and counts how many posts mention each brand or product name. The goal is personal, non-commercial research: understanding whether genuine consumer interest discussed on Reddit (product launches, shortages, brands people recommend) shows up before companies report their sales.

## What it does

- Reads the newest public posts (title and body) of the subreddits in [`subreddits.txt`](subreddits.txt), 2 pages of 100 posts each, once a day.
- Counts, per subreddit and day, how many posts mention each term in [`terms.txt`](terms.txt).
- Writes only those daily counts to a JSON file.

## What it does not do

- It never posts, comments, votes, sends messages, moderates or creates any content.
- It stores no post text, no usernames and no personal data: the text is processed in memory and discarded.
- The data is not resold, redistributed or published, and it is not used to train AI models.
- It uses application-only OAuth (client credentials): it does not log in as, or act for, any user.

## Limits

- At most one request per second, and at most 100 requests per daily run (well under 1,000 a day and under the free-tier limit of 100 queries per minute).
- A descriptive User-Agent: `script:invbot-reddit-reader:v0.1 (by /u/<username>)`.

## Running it

```bash
pip install -r requirements.txt
export REDDIT_CLIENT_ID=...  REDDIT_CLIENT_SECRET=...  REDDIT_USERNAME=...
python reader.py        # writes counts/YYYY-MM-DD.json
python -m pytest        # tests (no network)
```

Credentials come from the environment and are never committed.

## Privacy

See [PRIVACY.md](PRIVACY.md).
