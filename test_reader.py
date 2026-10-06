from reader import count_mentions, read_list


def test_counts_each_post_once_per_term_whole_words_only():
    texts = ["Costco Costco costco run", "I love my Stanley cup", "Stanleyville is not it", "nothing here"]
    counts = count_mentions(texts, ["Costco", "Stanley"])
    assert counts == {"Costco": 1, "Stanley": 1}


def test_the_lists_skip_comments_and_blank_lines(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("# comment\nCostco\n\n  Sneakers  \n", encoding="utf-8")
    assert read_list(f) == ["Costco", "Sneakers"]
