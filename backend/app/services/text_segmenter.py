from dataclasses import dataclass


@dataclass(frozen=True)
class TextSegment:
    index: int
    text: str
    start: int
    end: int
    is_sentence_end: bool


class TextSegmenter:
    """Sentence-level segmenter for child-facing safe replies."""

    def __init__(
        self,
        *,
        min_chars: int = 12,
        preferred_max_chars: int = 80,
        hard_max_chars: int = 600,
    ) -> None:
        self._min_chars = min_chars
        self._preferred_max_chars = preferred_max_chars
        self._hard_max_chars = hard_max_chars

    def segment(self, text: str, *, hard_max_chars: int | None = None) -> list[TextSegment]:
        stripped_text = text.strip()
        if not stripped_text:
            return []

        max_chars = hard_max_chars or self._hard_max_chars
        raw_sentences = self._split_sentences(stripped_text)
        split_sentences: list[str] = []
        for sentence in raw_sentences:
            split_sentences.extend(self._split_long_sentence(sentence, max_chars=max_chars))

        merged = self._merge_short_segments(split_sentences, max_chars=max_chars)
        return self._with_ranges(stripped_text, merged)

    def _split_sentences(self, text: str) -> list[str]:
        sentences: list[str] = []
        start = 0
        index = 0
        while index < len(text):
            char = text[index]
            if self._is_sentence_boundary(text, index):
                end = self._consume_boundary(text, index)
                sentence = text[start:end].strip()
                if sentence:
                    sentences.append(sentence)
                start = end
                index = end
                continue
            char_consumed = 2 if char == "\r" and text[index:index + 2] == "\r\n" else 1
            index += char_consumed

        tail = text[start:].strip()
        if tail:
            sentences.append(tail)
        return sentences

    def _is_sentence_boundary(self, text: str, index: int) -> bool:
        char = text[index]
        if char in {"。", "！", "？", "!", "?", "；", ";"}:
            return True
        if char == "…":
            return True
        if char == "\n":
            return True
        if char == ".":
            next_char = text[index + 1] if index + 1 < len(text) else ""
            return not next_char or next_char.isspace()
        return False

    def _consume_boundary(self, text: str, index: int) -> int:
        char = text[index]
        if char == "…":
            end = index + 1
            while end < len(text) and text[end] == "…":
                end += 1
            return end
        if char == "\n":
            return index + 1
        return index + 1

    def _split_long_sentence(self, sentence: str, *, max_chars: int) -> list[str]:
        if len(sentence) <= max_chars:
            return [sentence]

        chunks: list[str] = []
        remaining = sentence
        while len(remaining) > max_chars:
            split_at = self._last_soft_boundary(remaining[:max_chars])
            if split_at <= 0:
                split_at = max_chars
            chunk = remaining[:split_at].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_at:].strip()
        if remaining:
            chunks.append(remaining)
        return chunks

    def _last_soft_boundary(self, text: str) -> int:
        soft_boundaries = ("，", ",", "；", ";", "：", ":", "、", " ")
        positions = [text.rfind(boundary) for boundary in soft_boundaries]
        best = max(positions)
        return best + 1 if best >= self._min_chars else -1

    def _merge_short_segments(self, segments: list[str], *, max_chars: int) -> list[str]:
        merged: list[str] = []
        segment_limit = min(max_chars, self._preferred_max_chars)
        for segment in segments:
            if not segment:
                continue
            if (
                merged
                and len(merged[-1]) + len(segment) <= segment_limit
                and len(merged[-1]) < self._min_chars
            ):
                merged[-1] += segment
                continue
            merged.append(segment)
        return merged

    def _with_ranges(self, text: str, segments: list[str]) -> list[TextSegment]:
        output: list[TextSegment] = []
        cursor = 0
        for index, segment in enumerate(segments):
            start = text.find(segment, cursor)
            if start < 0:
                start = cursor
            end = start + len(segment)
            output.append(
                TextSegment(
                    index=index,
                    text=segment,
                    start=start,
                    end=end,
                    is_sentence_end=self._ends_sentence(segment),
                )
            )
            cursor = end
        return output

    def _ends_sentence(self, text: str) -> bool:
        return text.endswith(("。", "！", "？", "!", "?", ".", "…", "；", ";"))
