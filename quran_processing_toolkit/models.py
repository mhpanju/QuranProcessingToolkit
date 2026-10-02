"""Typed objects representing addresses, tokens, words, verses, chapters, and juzs.

The hierarchy follows the corpus rather than Python list positions: chapters, verses,
words, and token parts are all addressed from one. A ``Word`` may contain several
``Token`` objects because QAC stores prefixes, stems, and suffixes as separate
morphological segments. Convenience properties on a word normally aggregate only its
stem tokens so that prefixes do not unexpectedly supply a root or part of speech.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .collections import OneBasedCollection, QuerySet
from .text import TextMixin


@dataclass(frozen=True, slots=True, order=True)
class VerseAddress:
    """Immutable ``chapter:verse`` address using Quranic 1-based numbers."""

    chapter: int
    verse: int

    def __iter__(self):
        yield self.chapter
        yield self.verse

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}"


@dataclass(frozen=True, slots=True, order=True)
class WordAddress:
    """Immutable ``chapter:verse:word`` address using 1-based numbers."""

    chapter: int
    verse: int
    word: int

    def __iter__(self):
        yield self.chapter
        yield self.verse
        yield self.word

    def as_tuple(self) -> tuple[int, int, int]:
        """Return the address in the form used by keyed collection lookups."""
        return self.chapter, self.verse, self.word

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}:{self.word}"


@dataclass(frozen=True, slots=True, order=True)
class TokenAddress:
    """Immutable ``chapter:verse:word:part`` address using 1-based numbers."""

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
        """Return the address in the form used by keyed collection lookups."""
        return self.chapter, self.verse, self.word, self.part

    def __str__(self) -> str:
        return f"{self.chapter}:{self.verse}:{self.word}:{self.part}"


class Token(TextMixin):
    """One QAC morphological segment with source and convenience annotations.

    Unknown attributes are looked up against the retained uppercase record keys for
    backwards compatibility. New code should prefer the documented lowercase
    properties such as :attr:`root`, :attr:`aspect`, and :attr:`case`.
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def address(self) -> TokenAddress:
        """Return this segment's complete semantic address."""
        return TokenAddress(
            self._data["CHAPTER"],
            self._data["VERSE"],
            self._data["WORD"],
            self._data["WORD_PART"],
        )

    @property
    def address_tuple(self) -> tuple[int, int, int, int]:
        """Return ``(chapter, verse, word, part)`` without allocating an address."""
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
        """Read an uppercase derived-record field without raising when absent."""
        return self._data.get(field, default)

    @property
    def data(self) -> dict[str, Any]:
        """Return a shallow copy of all retained and derived record fields."""
        return self._data.copy()

    @property
    def chapter(self) -> int:
        """Return the 1-based chapter number."""
        return self._data["CHAPTER"]

    @property
    def verse(self) -> int:
        """Return the 1-based verse number within the chapter."""
        return self._data["VERSE"]

    @property
    def word(self) -> int:
        """Return the 1-based word number within the verse."""
        return self._data["WORD"]

    @property
    def part(self) -> int:
        """Return the 1-based morphological part number within the word."""
        return self._data["WORD_PART"]

    @property
    def form(self) -> str:
        """Return the source Buckwalter surface form for this segment."""
        return self._data["FORM"]

    def get_form(self) -> str:
        """Return this segment's Buckwalter surface form."""
        return self.form

    @property
    def tag(self) -> str:
        """Return the source QAC tag, such as ``V``, ``N``, or ``P``."""
        return self._data["TAG"]

    @property
    def role(self) -> str:
        """Return ``PREFIX``, ``STEM``, or ``SUFFIX``."""
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
        """Return the QAC ``POS`` code when the segment supplies one."""
        return self._data.get("POS")

    @property
    def root(self) -> str | None:
        """Return the Buckwalter root annotation when present."""
        return self._data.get("ROOT")

    @property
    def lemma(self) -> str | None:
        """Return the Buckwalter lemma annotation when present."""
        return self._data.get("LEM")

    @property
    def transliteration(self) -> str:
        """Return the segment's Buckwalter surface form."""
        return self.form

    @property
    def verb_form(self) -> str | None:
        """Return the derived verb-form/baab code, such as ``I`` or ``IV``."""
        return self._data.get("VERB_FORM")

    @property
    def baab(self) -> str | None:
        """Alias for :attr:`verb_form`."""
        return self.verb_form

    @property
    def aspect(self) -> str | None:
        """Return ``PERFECT``, ``IMPERFECT``, or ``IMPERATIVE`` when present."""
        return self._data.get("ASPECT")

    @property
    def tense(self) -> str | None:
        """Return the toolkit's derived tense label when present."""
        return self._data.get("TENSE")

    @property
    def voice(self) -> str | None:
        """Return ``ACTIVE`` or ``PASSIVE`` for finite verbs."""
        return self._data.get("VOICE")

    @property
    def case(self) -> str | None:
        """Return the derived case/state annotation when present."""
        return self._data.get("CASE")

    @property
    def mood(self) -> str | None:
        """Return the untouched keyed QAC mood annotation when present."""
        return self._data.get("MOOD")

    @property
    def gender(self) -> str | None:
        """Return the derived ``MASC`` or ``FEM`` annotation when present."""
        return self._data.get("GENDER")

    @property
    def definiteness(self) -> str | None:
        """Return the derived definiteness annotation when present."""
        return self._data.get("DEFINITENESS")

    @property
    def derived_noun(self) -> str | None:
        """Return participle or verbal-noun classification when present."""
        return self._data.get("DERIVED_NOUN")

    @property
    def conjugation(self) -> int | None:
        """Return the legacy 1-through-14 conjugation identifier when present."""
        return self._data.get("CONJUGATE")

    @property
    def person(self) -> int | None:
        """Return grammatical person derived from the conjugation annotation."""
        if self.conjugation is None:
            return None
        return int(_CONJUGATION_LABELS[self.conjugation][0])

    @property
    def grammatical_number(self) -> str | None:
        """Return ``SINGULAR``, ``DUAL``, or ``PLURAL`` when annotated."""
        if self.conjugation is not None:
            suffix = _CONJUGATION_LABELS[self.conjugation][-1]
            return {"S": "SINGULAR", "D": "DUAL", "P": "PLURAL"}[suffix]
        return self._data.get("COUNT")

    def has_source_feature(self, feature: str) -> bool:
        """Return whether the exact non-keyed feature occurs in the source column."""
        return feature in self.source_features


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
    """One orthographic Quran word assembled from one or more QAC tokens."""

    __slots__ = ("address", "tokens", "_stem_tokens", "arabic_text")

    def __init__(self, address: WordAddress, tokens: list[Token], arabic_text: str) -> None:
        self.address = address
        self.tokens = OneBasedCollection(tokens)
        self._stem_tokens = tuple(token for token in tokens if token.role == "STEM")
        self.arabic_text = arabic_text

    @property
    def stem_tokens(self) -> QuerySet[Token]:
        """Return only morphological segments classified as stems."""
        return QuerySet(self._stem_tokens)

    def __repr__(self) -> str:
        return f"Word({self.address}, {self.arabic_text!r})"

    @property
    def chapter(self) -> int:
        """Return the 1-based chapter number."""
        return self.address.chapter

    @property
    def verse(self) -> int:
        """Return the 1-based verse number within the chapter."""
        return self.address.verse

    @property
    def word(self) -> int:
        """Return the 1-based word number within the verse."""
        return self.address.word

    @property
    def transliteration(self) -> str:
        """Join all token forms into the word's complete Buckwalter spelling."""
        return "".join(token.form for token in self.tokens)

    def values(self, field: str, *, stems_only: bool = True) -> tuple[Any, ...]:
        """Return distinct values of an uppercase token field in source order.

        Stem-only aggregation is the default because affixes can have their own part
        of speech and other annotations. Pass ``stems_only=False`` when explicitly
        inspecting a complete segmented word.
        """
        tokens = self._stem_tokens if stems_only else self.tokens
        result: list[Any] = []
        for token in tokens:
            value = token.get(field)
            if value is not None and value not in result:
                result.append(value)
        return tuple(result)

    def value(self, field: str, *, stems_only: bool = True) -> Any:
        """Return ``None``, one field value, or a tuple for a multi-valued word."""
        values = self.values(field, stems_only=stems_only)
        if not values:
            return None
        return values[0] if len(values) == 1 else values

    @property
    def roots(self) -> tuple[str, ...]:
        """Return every distinct stem root in source order."""
        return self.values("ROOT")

    @property
    def root(self) -> str | tuple[str, ...] | None:
        """Return the sole root, multiple roots, or ``None``."""
        return self.value("ROOT")

    @property
    def lemmas(self) -> tuple[str, ...]:
        """Return every distinct stem lemma in source order."""
        return self.values("LEM")

    @property
    def lemma(self) -> str | tuple[str, ...] | None:
        """Return the sole lemma, multiple lemmas, or ``None``."""
        return self.value("LEM")

    @property
    def parts_of_speech(self) -> tuple[str, ...]:
        """Return every distinct stem part-of-speech code."""
        return self.values("POS")

    @property
    def part_of_speech(self) -> str | tuple[str, ...] | None:
        """Return one part of speech, several, or ``None``."""
        return self.value("POS")

    @property
    def is_multi_stem(self) -> bool:
        """Return whether QAC represents the word with more than one stem."""
        return len(self._stem_tokens) > 1

    def has_part_of_speech(self, value: str) -> bool:
        """Return whether any stem has the exact QAC part-of-speech code."""
        return value in self.parts_of_speech

    def is_verb(self) -> bool:
        """Return whether any stem is tagged as a verb."""
        return self.has_part_of_speech("V")

    def is_noun(self) -> bool:
        """Return whether any stem is tagged as a noun."""
        return self.has_part_of_speech("N")

    @property
    def verb_form(self) -> str | tuple[str, ...] | None:
        """Return one or more Roman-numeral verb-form codes."""
        return self.value("VERB_FORM")

    @property
    def baab(self) -> str | tuple[str, ...] | None:
        """Convenience alias for :attr:`verb_form`."""
        return self.verb_form

    @property
    def baab_name(self) -> str | tuple[str, ...] | None:
        """Return familiar transliterated names for the word's verb forms."""
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
        """Compatibility method returning :attr:`root`."""
        return self.root

    def get_lemma(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`lemma`."""
        return self.lemma

    @property
    def tense(self) -> str | tuple[str, ...] | None:
        """Return derived convenience tense values from all stems."""
        return self.value("TENSE")

    def get_tense(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`tense`."""
        return self.tense

    @property
    def aspect(self) -> str | tuple[str, ...] | None:
        """Return grammatical aspect values from all stems."""
        return self.value("ASPECT")

    def get_aspect(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`aspect`."""
        return self.aspect

    @property
    def voice(self) -> str | tuple[str, ...] | None:
        """Return finite verb voice values from all stems."""
        return self.value("VOICE")

    def get_voice(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`voice`."""
        return self.voice

    @property
    def conjugation(self) -> int | tuple[int, ...] | None:
        """Return legacy numeric conjugation identifiers from all stems."""
        return self.value("CONJUGATE")

    @property
    def conjugation_labels(self) -> tuple[str, ...]:
        """Return compact person/gender/number labels such as ``3MS``."""
        return tuple(
            _CONJUGATION_LABELS[number]
            for number in self.values("CONJUGATE")
            if number in _CONJUGATION_LABELS
        )

    @property
    def person(self) -> int | tuple[int, ...] | None:
        """Return one or more grammatical persons derived from conjugation."""
        values = tuple(dict.fromkeys(int(label[0]) for label in self.conjugation_labels))
        return values[0] if len(values) == 1 else values or None

    def get_person(self) -> int | tuple[int, ...] | None:
        """Compatibility method returning :attr:`person`."""
        return self.person

    @property
    def grammatical_number(self) -> str | tuple[str, ...] | None:
        """Return singular, dual, or plural from conjugation or nominal count."""
        mapping = {"S": "SINGULAR", "D": "DUAL", "P": "PLURAL"}
        values = tuple(dict.fromkeys(mapping[label[-1]] for label in self.conjugation_labels))
        if values:
            return values[0] if len(values) == 1 else values
        # Nominals carry COUNT directly rather than through a finite-verb
        # conjugation label. Falling back here makes with_number() useful for both.
        return self.value("COUNT")

    def get_number(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`grammatical_number`."""
        return self.grammatical_number

    @property
    def gender(self) -> str | tuple[str, ...] | None:
        """Return masculine/feminine values from all stems."""
        return self.value("GENDER")

    def get_gender(self) -> str | tuple[str, ...] | None:
        """Compatibility method returning :attr:`gender`."""
        return self.gender

    @property
    def case(self) -> str | tuple[str, ...] | None:
        """Return the word's derived case/state annotation."""
        return self.value("CASE")

    @property
    def mood(self) -> str | tuple[str, ...] | None:
        """Return the word's untouched keyed QAC mood annotation."""
        return self.value("MOOD")

    @property
    def definiteness(self) -> str | tuple[str, ...] | None:
        """Return the word's derived definiteness annotation."""
        return self.value("DEFINITENESS")

    @property
    def derived_noun(self) -> str | tuple[str, ...] | None:
        """Return verbal-noun or participle classification when present."""
        return self.value("DERIVED_NOUN")


class Verse(TextMixin):
    """A Quran verse with words, Uthmani text, and an optional translation."""

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
        """Return the 1-based chapter number."""
        return self.address.chapter

    @property
    def verse(self) -> int:
        """Return the 1-based verse number within the chapter."""
        return self.address.verse

    @property
    def transliteration(self) -> str:
        """Join word transliterations with spaces in Quranic order."""
        return " ".join(word.transliteration for word in self.words)

    @property
    def has_translation(self) -> bool:
        """Return whether a user-supplied translation covers this verse."""
        return self.translation_text is not None


class Chapter:
    """A 1-based chapter containing a 1-based verse collection."""

    __slots__ = ("number", "verses")

    def __init__(self, number: int, verses: list[Verse]) -> None:
        self.number = number
        self.verses = OneBasedCollection(verses)

    @property
    def chapter(self) -> int:
        """Alias for the chapter's numeric address."""
        return self.number

    def __repr__(self) -> str:
        return f"Chapter({self.number}, {len(self.verses)} verses)"


@dataclass(frozen=True, slots=True)
class Juz:
    """One of thirty sequential juz divisions and its ordered verses."""

    number: int
    start: VerseAddress
    verses: QuerySet[Verse]

    def __len__(self) -> int:
        return len(self.verses)
