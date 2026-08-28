"""Unicode-aware text helpers used by words, verses, and queries."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from typing import Any

QURANIC_PAUSE_MARKS = frozenset("ۛۖۗۚۙۘ۩ۜ")
QURANIC_PAUSE_TRANSLATION = str.maketrans("", "", "".join(QURANIC_PAUSE_MARKS))
_ARABIC_DIACRITIC_RE = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")


def normalize_arabic(
    text: str,
    *,
    strip_diacritics: bool = False,
    strip_quranic_marks: bool = False,
    normalize_alif: bool = False,
    normalize_ya: bool = False,
    remove_spaces: bool = False,
) -> str:
    """Normalize Arabic text using only explicitly requested operations."""
    result = unicodedata.normalize("NFC", text)
    if strip_quranic_marks:
        result = "".join(character for character in result if character not in QURANIC_PAUSE_MARKS)
    if strip_diacritics:
        result = _ARABIC_DIACRITIC_RE.sub("", result)
    if normalize_alif:
        result = result.translate(str.maketrans("أإآٱ", "اااا"))
    if normalize_ya:
        result = result.translate(str.maketrans("ىی", "يي"))
    if remove_spaces:
        result = "".join(result.split())
    return result


class TextMixin:
    """General text predicates shared by Quranic model objects."""

    def get_text(self, representation: str = "arabic") -> str:
        candidates = {
            "arabic": "arabic_text",
            "translation": "translation_text",
            "transliteration": "transliteration",
            "form": "form",
        }
        try:
            attribute = candidates[representation]
        except KeyError as error:
            raise ValueError(
                f"Unknown representation {representation!r}; choose from {tuple(candidates)}"
            ) from error
        value = getattr(self, attribute, None)
        if value is None:
            raise ValueError(f"{type(self).__name__} has no {representation} representation")
        return value

    def normalized_text(self, representation: str = "arabic", **options: Any) -> str:
        text = self.get_text(representation)
        return normalize_arabic(text, **options) if representation == "arabic" else text

    def starts_with(
        self, prefix: str, *, representation: str = "arabic", **normalization: Any
    ) -> bool:
        text = self.normalized_text(representation, **normalization)
        expected = (
            normalize_arabic(prefix, **normalization) if representation == "arabic" else prefix
        )
        return text.startswith(expected)

    def ends_with(
        self, suffix: str, *, representation: str = "arabic", **normalization: Any
    ) -> bool:
        text = self.normalized_text(representation, **normalization)
        expected = (
            normalize_arabic(suffix, **normalization) if representation == "arabic" else suffix
        )
        return text.endswith(expected)

    def contains(
        self, fragment: str, *, representation: str = "arabic", **normalization: Any
    ) -> bool:
        text = self.normalized_text(representation, **normalization)
        expected = (
            normalize_arabic(fragment, **normalization) if representation == "arabic" else fragment
        )
        return expected in text

    def count_characters(
        self,
        characters: str | Collection[str],
        *,
        representation: str = "arabic",
        **normalization: Any,
    ) -> int:
        wanted = set(characters)
        return sum(
            character in wanted
            for character in self.normalized_text(representation, **normalization)
        )

    def letter_count(self, *, representation: str = "arabic", **normalization: Any) -> int:
        text = self.normalized_text(representation, **normalization)
        return sum(character.isalpha() for character in text)
