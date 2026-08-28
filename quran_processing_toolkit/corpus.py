"""Portable, validated loading and querying of the bundled Quran corpus."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Any

from .collections import IndexedCollection, OneBasedCollection, QuerySet, resolve_value
from .models import (
    Chapter,
    Juz,
    Token,
    Verse,
    VerseAddress,
    Word,
    WordAddress,
)
from .text import QURANIC_PAUSE_TRANSLATION

_CACHE: dict[Path, QuranCorpus] = {}
_CACHE_LOCK = Lock()


class CorpusError(RuntimeError):
    pass


class CorpusAlignmentError(CorpusError):
    pass


def default_data_directory() -> Path:
    """Find corpus data in an override, installed package, or source checkout."""
    override = os.environ.get("QURAN_PROCESSING_TOOLKIT_DATA")
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_dir():
            raise CorpusError(f"Configured corpus directory does not exist: {path}")
        return path

    try:
        from importlib.resources import files

        installed = Path(str(files("quran_processing_toolkit.data")))
        if (installed / "quran-morphologies.json").is_file():
            return installed
    except (ImportError, ModuleNotFoundError, TypeError):
        pass

    source = Path(__file__).resolve().parents[1] / "corpus"
    if source.is_dir():
        return source
    raise CorpusError(
        "Could not locate corpus data. Set QURAN_PROCESSING_TOOLKIT_DATA or "
        "pass data_dir=... to QuranCorpus."
    )


def _load_json(path: Path) -> list[dict[str, Any]]:
    """Use orjson when available, with a dependency-free fallback."""
    try:
        import orjson  # type: ignore[import-not-found]
    except ImportError:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    return orjson.loads(path.read_bytes())


def _read_numbered_text(path: Path, delimiter: str = "|") -> dict[VerseAddress, str]:
    result: dict[VerseAddress, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split(delimiter, 2)
            if len(parts) != 3:
                raise CorpusError(f"Malformed line {line_number} in {path}")
            try:
                address = VerseAddress(int(parts[0]), int(parts[1]))
            except ValueError as error:
                raise CorpusError(f"Malformed address on line {line_number} in {path}") from error
            if address in result:
                raise CorpusError(f"Duplicate verse {address} in {path}")
            result[address] = parts[2]
    return result


_BASMALA_FORMS = (
    "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ ",
    "بِّسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ ",
)


def _without_non_verse_basmala(address: VerseAddress, text: str) -> str:
    if address.chapter == 1 or address.verse != 1:
        return text
    for basmala in _BASMALA_FORMS:
        if text.startswith(basmala):
            return text[len(basmala) :]
    return text


def _arabic_words(address: VerseAddress, text: str) -> list[str]:
    # These are orthographic contractions represented as one corpus word.
    text = text.replace("بَعْدَ مَا", "بَعْد###مَا")
    text = text.replace("إِلْ يَاسِينَ", "إِلْ###يَاسِينَ")
    text = text.translate(QURANIC_PAUSE_TRANSLATION)
    return [word.replace("###", " ") for word in text.strip().split()]


class QuranCorpus:
    """The complete corpus, with 1-based semantic indexes at every level."""

    __slots__ = (
        "data_dir",
        "chapters",
        "verses",
        "words",
        "tokens",
        "juzs",
        "_word_indexes",
        "_verbs",
        "_nouns",
    )

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        self.data_dir = (
            Path(data_dir).expanduser().resolve() if data_dir else default_data_directory()
        )
        self._word_indexes: dict[str, dict[Any, tuple[Word, ...]]] = {}
        self._verbs: QuerySet[Word] | None = None
        self._nouns: QuerySet[Word] | None = None
        self._build()

    @classmethod
    def load(
        cls,
        data_dir: str | os.PathLike[str] | None = None,
        *,
        cache: bool = True,
    ) -> QuranCorpus:
        """Load a corpus, reusing the in-process instance by default."""
        path = Path(data_dir).expanduser().resolve() if data_dir else default_data_directory()
        if not cache:
            return cls(path)
        with _CACHE_LOCK:
            corpus = _CACHE.get(path)
            if corpus is None:
                corpus = cls(path)
                _CACHE[path] = corpus
            return corpus

    def _build(self) -> None:
        morphology_path = self.data_dir / "quran-morphologies.json"
        arabic = _read_numbered_text(self.data_dir / "uthmani-numbered.txt")
        translations = _read_numbered_text(self.data_dir / "translation_qarai.txt")
        records = _load_json(morphology_path)

        token_groups: defaultdict[tuple[int, int, int], list[Token]] = defaultdict(list)
        verse_addresses: defaultdict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(
            list
        )
        all_tokens: list[Token] = []
        last_address: tuple[int, int, int, int] | None = None
        for record in records:
            address = (record["CHAPTER"], record["VERSE"], record["WORD"], record["WORD_PART"])
            if last_address is not None and address <= last_address:
                raise CorpusError(f"Morphology records are not strictly ordered at {address}")
            last_address = address
            token = Token(record)
            word_address = address[:3]
            if word_address not in token_groups:
                verse_addresses[word_address[:2]].append(word_address)
            token_groups[word_address].append(token)
            all_tokens.append(token)

        verse_word_groups: defaultdict[VerseAddress, list[Word]] = defaultdict(list)
        all_words: list[Word] = []
        for verse_key in sorted(verse_addresses):
            verse_address = VerseAddress(*verse_key)
            word_addresses = verse_addresses[verse_key]
            if verse_address not in arabic:
                raise CorpusAlignmentError(f"Missing Arabic text for verse {verse_address}")
            verse_arabic = _without_non_verse_basmala(verse_address, arabic[verse_address])
            surface_words = _arabic_words(verse_address, verse_arabic)
            if len(surface_words) != len(word_addresses):
                raise CorpusAlignmentError(
                    f"Verse {verse_address} has {len(surface_words)} Arabic words but "
                    f"{len(word_addresses)} morphology words"
                )
            for address, surface in zip(word_addresses, surface_words, strict=True):
                word = Word(WordAddress(*address), token_groups[address], surface)
                verse_word_groups[verse_address].append(word)
                all_words.append(word)

        chapter_verse_groups: defaultdict[int, list[Verse]] = defaultdict(list)
        all_verses: list[Verse] = []
        for address in sorted(verse_word_groups):
            verse_arabic = _without_non_verse_basmala(address, arabic[address])
            verse = Verse(
                address,
                verse_word_groups[address],
                verse_arabic,
                translations.get(address),
            )
            chapter_verse_groups[address.chapter].append(verse)
            all_verses.append(verse)

        all_chapters = [
            Chapter(number, chapter_verse_groups[number]) for number in sorted(chapter_verse_groups)
        ]
        self.chapters = OneBasedCollection(all_chapters)
        self.verses = IndexedCollection(
            all_verses,
            key=lambda verse: (verse.address.chapter, verse.address.verse),
        )
        self.words = IndexedCollection(all_words, key=lambda word: word.address.as_tuple())
        self.tokens = IndexedCollection(all_tokens, key=lambda token: token.address_tuple)
        self.juzs = self._build_juzs()

    def _build_juzs(self) -> OneBasedCollection[Juz]:
        starts: list[VerseAddress] = []
        with (self.data_dir / "juzz-breakdown.tsv").open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 3 or int(parts[0]) != line_number:
                    raise CorpusError(f"Malformed juz boundary on line {line_number}")
                starts.append(VerseAddress(int(parts[1]), int(parts[2])))
        verse_positions = {verse.address: index for index, verse in enumerate(self.verses)}
        juzs: list[Juz] = []
        for index, start in enumerate(starts):
            start_position = verse_positions[start]
            end_position = (
                verse_positions[starts[index + 1]] if index + 1 < len(starts) else len(self.verses)
            )
            juzs.append(
                Juz(index + 1, start, QuerySet(self.verses.values()[start_position:end_position]))
            )
        return OneBasedCollection(juzs)

    @property
    def verbs(self) -> QuerySet[Word]:
        if self._verbs is None:
            self._verbs = self.words.filter(Word.is_verb)
        return self._verbs

    @property
    def nouns(self) -> QuerySet[Word]:
        if self._nouns is None:
            self._nouns = self.words.filter(Word.is_noun)
        return self._nouns

    def chapter(self, number: int) -> Chapter:
        return self.chapters[number]

    def verse(self, chapter: int, verse: int) -> Verse:
        return self.verses[chapter, verse]

    def word(self, chapter: int, verse: int, word: int) -> Word:
        return self.words[chapter, verse, word]

    def token(self, chapter: int, verse: int, word: int, part: int) -> Token:
        return self.tokens[chapter, verse, word, part]

    def index_words(self, field: str) -> dict[Any, tuple[Word, ...]]:
        """Build and cache an inverted word index for a field or property."""
        if field not in self._word_indexes:
            index: defaultdict[Any, list[Word]] = defaultdict(list)
            for word in self.words:
                value = resolve_value(word, field)
                values = value if isinstance(value, tuple) else (value,)
                for member in values:
                    index[member].append(word)
            self._word_indexes[field] = {key: tuple(words) for key, words in index.items()}
        return self._word_indexes[field]

    def find_words(self, **criteria: Any) -> QuerySet[Word]:
        """Find words, using a lazy inverted index for equality criteria."""
        if not criteria:
            return QuerySet(self.words)
        field, expected = next(iter(criteria.items()))
        if callable(expected):
            return self.words.where(**criteria)
        candidates = QuerySet(self.index_words(field).get(expected, ()))
        return candidates.where(**criteria)

    def longest_word_sequence(
        self,
        predicate: Callable[[Word], bool],
        *,
        cross_verse_boundaries: bool = False,
    ) -> QuerySet[Word]:
        """Find the longest contiguous sequence of words matching a predicate."""
        if cross_verse_boundaries:
            return QuerySet(self.words).longest_run(predicate)
        best = QuerySet[Word]()
        for verse in self.verses:
            candidate = QuerySet(verse.words).longest_run(predicate)
            if len(candidate) > len(best):
                best = candidate
        return best


def load_quran(
    data_dir: str | os.PathLike[str] | None = None, *, cache: bool = True
) -> QuranCorpus:
    return QuranCorpus.load(data_dir, cache=cache)
