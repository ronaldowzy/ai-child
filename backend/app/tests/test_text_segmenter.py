from app.services.text_segmenter import TextSegmenter


def test_text_segmenter_splits_chinese_and_english_sentence_boundaries() -> None:
    segments = TextSegmenter().segment(
        "我们先看题目。What did you notice? 再说第一步！"
    )

    assert [segment.text for segment in segments] == [
        "我们先看题目。What did you notice?",
        "再说第一步！",
    ]
    assert segments[0].start == 0
    assert segments[0].end == len("我们先看题目。What did you notice?")
    assert segments[1].is_sentence_end is True


def test_text_segmenter_merges_short_neighboring_segments() -> None:
    segments = TextSegmenter(min_chars=8, preferred_max_chars=40).segment(
        "好。我们慢慢来。先说题目问什么？"
    )

    assert [segment.text for segment in segments] == [
        "好。我们慢慢来。",
        "先说题目问什么？",
    ]


def test_text_segmenter_treats_semicolon_as_sentence_boundary() -> None:
    segments = TextSegmenter(min_chars=4, preferred_max_chars=80).segment(
        "先看看题目问什么；再找已经知道的条件;最后试第一步。"
    )

    assert [segment.text for segment in segments] == [
        "先看看题目问什么；",
        "再找已经知道的条件;",
        "最后试第一步。",
    ]
    assert all(segment.is_sentence_end for segment in segments)


def test_text_segmenter_splits_long_sentence_under_hard_limit() -> None:
    text = "我们先把题目里已经知道的条件圈出来，然后看看它到底想问什么，再决定第一步怎么做。"

    segments = TextSegmenter(min_chars=8, preferred_max_chars=30).segment(
        text,
        hard_max_chars=24,
    )

    assert len(segments) > 1
    assert all(len(segment.text) <= 24 for segment in segments)
    assert "".join(segment.text for segment in segments) == text


def test_text_segmenter_splits_long_sentence_by_preferred_max_for_streaming() -> None:
    text = "我看到这张图片里有一个蓝色的小盒子，上面还有一些字，看起来像是你刚刚想让我一起看的新东西。"

    segments = TextSegmenter(min_chars=8, preferred_max_chars=32).segment(
        text,
        hard_max_chars=600,
    )

    assert len(segments) > 1
    assert all(len(segment.text) <= 32 for segment in segments)
    assert "".join(segment.text for segment in segments) == text


def test_text_segmenter_ignores_blank_text() -> None:
    assert TextSegmenter().segment("   ") == []
