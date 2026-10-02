"""Unicode-aware normalization, representation selection, and text predicates.

The toolkit never normalizes stored text in place. Each comparison starts from the
preserved Arabic or Buckwalter form and applies only options explicitly requested by
the caller. With ``representation='auto'``, wholly ASCII input means Buckwalter and
non-ASCII input means Arabic.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from typing import Any

QURANIC_PAUSE_MARKS = frozenset("ۛۖۗۚۙۘ۩ۜ")
QURANIC_PAUSE_TRANSLATION = str.maketrans("", "", "".join(QURANIC_PAUSE_MARKS))
# Extended Buckwalter vowel and recitation marks. Long-vowel letters A, w, and Y/y
# are deliberately not included.
BUCKWALTER_DIACRITICS = frozenset("aiuoFNK~`^#@")
_ARABIC_DIACRITIC_RE = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")


class TranslationNotAvailableError(ValueError):
    """Raised when English output is requested without a translation for an item."""


def normalize_arabic(
    text: str,
    *,
    strip_diacritics: bool = False,
    strip_quranic_marks: bool = False,
    normalize_alif: bool = False,
    normalize_ya: bool = False,
    remove_spaces: bool = False,
) -> str:
    """Return NFC Arabic text with only the requested optional transformations.

    The conservative defaults are intentional: alif variants, alif maqsura, Quranic
    marks, and vowel marks can all be linguistically significant for a particular
    analysis. Callers choose which distinctions to collapse.
    """
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


def normalize_buckwalter(
    text: str,
    *,
    strip_diacritics: bool = False,
    normalize_alif: bool = False,
    normalize_ya: bool = False,
    remove_spaces: bool = False,
    **_: Any,
) -> str:
    """Normalize Buckwalter with options parallel to Arabic normalization."""
    result = text
    if strip_diacritics:
        result = "".join(
            character for character in result if character not in BUCKWALTER_DIACRITICS
        )
    if normalize_alif:
        result = result.translate(str.maketrans("><|{", "AAAA"))
    if normalize_ya:
        result = result.replace("Y", "y")
    if remove_spaces:
        result = "".join(result.split())
    return result


def canonical_representation(representation: str) -> str:
    """Accept concise names for the three user-facing text representations."""
    aliases = {
        "arabic": "arabic",
        "transliteration": "transliteration",
        "buckwalter": "transliteration",
        "translation": "translation",
        "english": "translation",
    }
    try:
        return aliases[representation.lower()]
    except KeyError as error:
        raise ValueError(
            f"Unknown representation {representation!r}; choose Arabic, "
            "transliteration/Buckwalter, or translation/English"
        ) from error


def infer_representation(text: str, representation: str = "auto") -> str:
    """Treat ASCII input as Buckwalter and non-ASCII input as Arabic."""
    if representation == "auto":
        return "transliteration" if text.isascii() else "arabic"
    return canonical_representation(representation)


class TextMixin:
    """Display and comparison operations shared by tokens, words, and verses."""

    def get_text(self, representation: str = "arabic") -> str:
        """Return Arabic, Buckwalter, or supplied translation text."""
        representation = canonical_representation(representation)
        candidates = {
            "arabic": "arabic_text",
            "translation": "translation_text",
            "transliteration": "transliteration",
        }
        attribute = candidates[representation]
        value = getattr(self, attribute, None)
        if value is None:
            if representation == "translation":
                raise TranslationNotAvailableError(
                    f"{type(self).__name__} has no translation representation; "
                    "pass translation=... to load_quran()"
                )
            raise ValueError(f"{type(self).__name__} has no {representation} representation")
        return value

    def normalized_text(self, representation: str = "arabic", **options: Any) -> str:
        """Return one representation after applying explicit normalization options."""
        representation = canonical_representation(representation)
        text = self.get_text(representation)
        if representation == "arabic":
            return normalize_arabic(text, **options)
        if representation == "transliteration":
            return normalize_buckwalter(text, **options)
        return text

    def display(self, representation: str = "arabic") -> str:
        """Return Arabic, English translation, or Buckwalter for display."""
        return self.get_text(representation)

    def get_arabic(self) -> str:
        """Return preserved Arabic surface text."""
        return self.get_text("arabic")

    def get_transliteration(self) -> str:
        """Return Buckwalter transliteration assembled from morphology tokens."""
        return self.get_text("transliteration")

    def get_translation(self) -> str:
        """Return user-supplied translation text or raise a clear error."""
        return self.get_text("translation")

    @staticmethod
    def _normalize_input(text: str, representation: str, options: dict[str, Any]) -> str:
        if representation == "arabic":
            return normalize_arabic(text, **options)
        if representation == "transliteration":
            return normalize_buckwalter(text, **options)
        return text

    def starts_with(
        self, prefix: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Test a normalized prefix; ASCII input automatically means Buckwalter."""
        representation = infer_representation(prefix, representation)
        text = self.normalized_text(representation, **normalization)
        expected = self._normalize_input(prefix, representation, normalization)
        return text.startswith(expected)

    def ends_with(self, suffix: str, *, representation: str = "auto", **normalization: Any) -> bool:
        """Test a normalized suffix; ASCII input automatically means Buckwalter."""
        representation = infer_representation(suffix, representation)
        text = self.normalized_text(representation, **normalization)
        expected = self._normalize_input(suffix, representation, normalization)
        return text.endswith(expected)

    def contains(
        self, fragment: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Test a normalized substring; ASCII input automatically means Buckwalter."""
        representation = infer_representation(fragment, representation)
        text = self.normalized_text(representation, **normalization)
        expected = self._normalize_input(fragment, representation, normalization)
        return expected in text

    def equals(
        self, expected_text: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Test normalized whole-text equality."""
        representation = infer_representation(expected_text, representation)
        text = self.normalized_text(representation, **normalization)
        expected = self._normalize_input(expected_text, representation, normalization)
        return text == expected

    def contains_letter(
        self, letter: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Return whether a letter occurs; ASCII letters mean Buckwalter."""
        if len(letter) != 1:
            raise ValueError("contains_letter() expects exactly one character")
        return self.contains(letter, representation=representation, **normalization)

    def contains_any_letter(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Return whether at least one requested character occurs."""
        return any(
            self.contains_letter(letter, representation=representation, **normalization)
            for letter in letters
        )

    def contains_all_letters(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Return whether every requested character occurs at least once."""
        return all(
            self.contains_letter(letter, representation=representation, **normalization)
            for letter in letters
        )

    def contains_no_letters(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> bool:
        """Return whether none of the requested characters occur."""
        return not self.contains_any_letter(letters, representation=representation, **normalization)

    def count_characters(
        self,
        characters: str | Collection[str],
        *,
        representation: str = "auto",
        **normalization: Any,
    ) -> int:
        """Count occurrences belonging to a set of requested characters."""
        sample = characters if isinstance(characters, str) else "".join(characters)
        representation = infer_representation(sample, representation)
        wanted = set(self._normalize_input(sample, representation, normalization))
        return sum(
            character in wanted
            for character in self.normalized_text(representation, **normalization)
        )

    def letter_count(self, *, representation: str = "arabic", **normalization: Any) -> int:
        """Count alphabetic characters after optional normalization."""
        text = self.normalized_text(representation, **normalization)
        return sum(character.isalpha() for character in text)
