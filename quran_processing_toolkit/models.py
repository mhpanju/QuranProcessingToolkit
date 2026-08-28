"""Typed object model for the Quran corpus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .collections import OneBasedCollection, QuerySet
from .text import TextMixin


@dataclass(frozen=True, slots=True, order=True)
class VerseAddress:
    chapter: int
    verse: int

    def __iter__(self):
        yield self.chapter
        yield self.verse

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}"


@dataclass(frozen=True, slots=True, order=True)
class WordAddress:
    chapter: int
    verse: int
    word: int

    def __iter__(self):
        yield self.chapter
        yield self.verse
        yield self.word

    def as_tuple(self) -> tuple[int, int, int]:
        return self.chapter, self.verse, self.word

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}:{self.word}"


@dataclass(frozen=True, slots=True, order=True)
class TokenAddress:
    chapter: int
    verse: int
    word: int
    part: int

    def __iter__(self):
        yield self.chapter
        yield self.verse
        yield self.word
        yield self.part

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.chapter, self.verse, self.word, self.part

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}:{self.word}:{self.part}"


class Token(TextMixin):
    """One morphological segment, retaining every processed-corpus field."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def address(self) -> TokenAddress:
        return TokenAddress(
            self._data["CHAPTER"],
            self._data["VERSE"],
            self._data["WORD"],
            self._data["WORD_PART"],
        )

    @property
    def address_tuple(self) -> tuple[int, int, int, int]:
        return (
            self._data["CHAPTER"],
            self._data["VERSE"],
            self._data["WORD"],
            self._data["WORD_PART"],
        )

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __repr__(self) -> str:
        return f"Token({self.address}, {self.form!r}, tag={self.tag!r})"

    def get(self, field: str, default: Any = None) -> Any:
        return self._data.get(field, default)

    @property
    def data(self) -> dict[str, Any]:
        return self._data.copy()

    @property
    def form(self) -> str:
        return self._data["FORM"]

    def get_form(self) -> str:
        """Return this segment's Buckwalter surface form."""
        return self.form

    @property
    def tag(self) -> str:
        return self._data["TAG"]

    @property
    def role(self) -> str:
        return self._data["TOKEN_ROLE"]

    @property
    def source_features(self) -> tuple[str, ...]:
        """Return the untouched non-keyed QAC features for this segment."""
        return tuple(
            feature for feature in self.source_feature_text.split("|") if ":" not in feature
        )

    @property
    def source_feature_text(self) -> str:
        """Return the complete original QAC feature column."""
        return self._data["FEATURES"]

    @property
    def part_of_speech(self) -> str | None:
        return self._data.get("POS")

    @property
    def root(self) -> str | None:
        return self._data.get("ROOT")

    @property
    def lemma(self) -> str | None:
        return self._data.get("LEM")

    @property
    def transliteration(self) -> str:
        return self.form


_CONJUGATION_LABELS = {
    1: "3MS",
    2: "3MD",
    3: "3MP",
    4: "3FS",
    5: "3FD",
    6: "3FP",
    7: "2MS",
    8: "2MD",
    9: "2MP",
    10: "2FS",
    11: "2FD",
    12: "2FP",
    13: "1S",
    14: "1P",
}

VERB_FORM_NAMES = {
    "I": "Thulathy Mujarrad",
    "II": "Taf'eel",
    "III": "Mufaa'alah",
    "IV": "If'aal",
    "V": "Tafa'ul",
    "VI": "Tafaa'ul",
    "VII": "Infi'aal",
    "VIII": "Ifti'aal",
    "IX": "If'ilaal",
    "X": "Istif'aal",
    "XI": "If'eelaal",
    "XII": "Other",
    "rI": "Ruba'iy Mujarrad",
    "rIV": "If'illaal",
}


class Word(TextMixin):
    __slots__ = ("address", "tokens", "_stem_tokens", "arabic_text")

    def __init__(self, address: WordAddress, tokens: list[Token], arabic_text: str) -> None:
        self.address = address
        self.tokens = OneBasedCollection(tokens)
        self._stem_tokens = tuple(token for token in tokens if token.role == "STEM")
        self.arabic_text = arabic_text

    @property
    def stem_tokens(self) -> QuerySet[Token]:
        return QuerySet(self._stem_tokens)

    def __repr__(self) -> str:
        return f"Word({self.address}, {self.arabic_text!r})"

    @property
    def chapter(self) -> int:
        return self.address.chapter

    @property
    def verse(self) -> int:
        return self.address.verse

    @property
    def word(self) -> int:
        return self.address.word

    @property
    def transliteration(self) -> str:
        return "".join(token.form for token in self.tokens)

    def values(self, field: str, *, stems_only: bool = True) -> tuple[Any, ...]:
        tokens = self._stem_tokens if stems_only else self.tokens
        result: list[Any] = []
        for token in tokens:
            value = token.get(field)
            if value is not None and value not in result:
                result.append(value)
        return tuple(result)

    def value(self, field: str, *, stems_only: bool = True) -> Any:
        values = self.values(field, stems_only=stems_only)
        if not values:
            return None
        return values[0] if len(values) == 1 else values

    @property
    def roots(self) -> tuple[str, ...]:
        return self.values("ROOT")

    @property
    def root(self) -> str | tuple[str, ...] | None:
        return self.value("ROOT")

    @property
    def lemmas(self) -> tuple[str, ...]:
        return self.values("LEM")

    @property
    def lemma(self) -> str | tuple[str, ...] | None:
        return self.value("LEM")

    @property
    def parts_of_speech(self) -> tuple[str, ...]:
        return self.values("POS")

    @property
    def part_of_speech(self) -> str | tuple[str, ...] | None:
        return self.value("POS")

    @property
    def is_multi_stem(self) -> bool:
        return len(self._stem_tokens) > 1

    def has_part_of_speech(self, value: str) -> bool:
        return value in self.parts_of_speech

    def is_verb(self) -> bool:
        return self.has_part_of_speech("V")

    def is_noun(self) -> bool:
        return self.has_part_of_speech("N")

    @property
    def verb_form(self) -> str | tuple[str, ...] | None:
        return self.value("VERB_FORM")

    @property
    def baab(self) -> str | tuple[str, ...] | None:
        return self.verb_form

    @property
    def baab_name(self) -> str | tuple[str, ...] | None:
        forms = self.values("VERB_FORM")
        names = tuple(VERB_FORM_NAMES.get(form, form) for form in forms)
        return names[0] if len(names) == 1 else names or None

    def get_baab(self) -> str | tuple[str, ...] | None:
        """Compatibility alias for the prototype's named-baab method."""
        return self.baab_name

    def get_form(self) -> str | tuple[str, ...] | None:
        """Return the verb form/baab code, such as ``I`` or ``IV``."""
        return self.verb_form

    def get_root(self) -> str | tuple[str, ...] | None:
        return self.root

    def get_lemma(self) -> str | tuple[str, ...] | None:
        return self.lemma

    @property
    def tense(self) -> str | tuple[str, ...] | None:
        return self.value("TENSE")

    def get_tense(self) -> str | tuple[str, ...] | None:
        return self.tense

    @property
    def aspect(self) -> str | tuple[str, ...] | None:
        return self.value("ASPECT")

    def get_aspect(self) -> str | tuple[str, ...] | None:
        return self.aspect

    @property
    def voice(self) -> str | tuple[str, ...] | None:
        return self.value("VOICE")

    def get_voice(self) -> str | tuple[str, ...] | None:
        return self.voice

    @property
    def conjugation(self) -> int | tuple[int, ...] | None:
        return self.value("CONJUGATE")

    @property
    def conjugation_labels(self) -> tuple[str, ...]:
        return tuple(
            _CONJUGATION_LABELS[number]
            for number in self.values("CONJUGATE")
            if number in _CONJUGATION_LABELS
        )

    @property
    def person(self) -> int | tuple[int, ...] | None:
        values = tuple(dict.fromkeys(int(label[0]) for label in self.conjugation_labels))
        return values[0] if len(values) == 1 else values or None

    def get_person(self) -> int | tuple[int, ...] | None:
        return self.person

    @property
    def grammatical_number(self) -> str | tuple[str, ...] | None:
        mapping = {"S": "SINGULAR", "D": "DUAL", "P": "PLURAL"}
        values = tuple(dict.fromkeys(mapping[label[-1]] for label in self.conjugation_labels))
        return values[0] if len(values) == 1 else values or None

    def get_number(self) -> str | tuple[str, ...] | None:
        return self.grammatical_number

    @property
    def gender(self) -> str | tuple[str, ...] | None:
        return self.value("GENDER")

    def get_gender(self) -> str | tuple[str, ...] | None:
        return self.gender


class Verse(TextMixin):
    __slots__ = ("address", "words", "arabic_text", "translation_text")

    def __init__(
        self,
        address: VerseAddress,
        words: list[Word],
        arabic_text: str,
        translation_text: str | None,
    ) -> None:
        self.address = address
        self.words = OneBasedCollection(words)
        self.arabic_text = arabic_text
        self.translation_text = translation_text

    def __repr__(self) -> str:
        return f"Verse({self.address}, {len(self.words)} words)"

    @property
    def chapter(self) -> int:
        return self.address.chapter

    @property
    def verse(self) -> int:
        return self.address.verse

    @property
    def transliteration(self) -> str:
        return " ".join(word.transliteration for word in self.words)

    @property
    def has_translation(self) -> bool:
        return self.translation_text is not None


class Chapter:
    __slots__ = ("number", "verses")

    def __init__(self, number: int, verses: list[Verse]) -> None:
        self.number = number
        self.verses = OneBasedCollection(verses)

    @property
    def chapter(self) -> int:
        return self.number

    def __repr__(self) -> str:
        return f"Chapter({self.number}, {len(self.verses)} verses)"


@dataclass(frozen=True, slots=True)
class Juz:
    number: int
    start: VerseAddress
    verses: QuerySet[Verse]

    def __len__(self) -> int:
        return len(self.verses)
