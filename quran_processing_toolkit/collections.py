"""Immutable query collections used throughout the public API.

``QuerySet`` deliberately provides two layers:

* small, general operations such as :meth:`where`, :meth:`group_by`, and
  :meth:`sorted_by`; and
* readable domain helpers such as :meth:`with_root`, :meth:`with_aspect`, and
  :meth:`in_verse` for programs that should not need lambdas or a query language.

Semantic corpus collections (chapters, verses, words, and tokens) add keyed lookup
through ``IndexedCollection`` or ``OneBasedCollection``. A filtered result is an
ordinary ``QuerySet`` and therefore uses normal Python zero-based result positions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Generic, TypeVar, overload

from .text import TranslationNotAvailableError

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R")


def resolve_value(item: Any, field: str) -> Any:
    """Resolve a dotted attribute name on an object or mapping."""
    value = item
    for component in field.split("."):
        value = value[component] if isinstance(value, dict) else getattr(value, component)
    return value


def _selector(field_or_callable: str | Callable[[T], R]) -> Callable[[T], R]:
    if callable(field_or_callable):
        return field_or_callable
    return lambda item: resolve_value(item, field_or_callable)


def _values(item: Any, field: str) -> tuple[Any, ...]:
    method = getattr(item, "values", None)
    return method(field) if method else ()


def _morphology_values(item: Any, plural: str, singular: str) -> tuple[Any, ...]:
    """Read a possibly multi-valued morphology attribute from words or tokens."""
    values = getattr(item, plural, None)
    if values is not None:
        return tuple(values)
    value = getattr(item, singular, None)
    if value is None:
        return ()
    return value if isinstance(value, tuple) else (value,)


def _text_matches(item: Any, method: str, *args: Any, **kwargs: Any) -> bool:
    """Run a text predicate, skipping only absent verse translation layers."""
    try:
        return bool(getattr(item, method)(*args, **kwargs))
    except TranslationNotAvailableError:
        # A partial translation is a supported sparse layer. Collection searches
        # omit untranslated verses, while asking a single object for unavailable
        # translation text continues to raise. Non-verse objects still surface the
        # representation error rather than looking like a legitimate empty result.
        if hasattr(item, "translation_text"):
            return False
        raise


class QuerySet(Generic[T]):
    """An immutable, reusable result set with composable query operations."""

    __slots__ = ("_items",)

    def __init__(self, items: Iterable[T] = ()) -> None:
        self._items = tuple(items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> QuerySet[T]: ...

    def __getitem__(self, index: int | slice) -> T | QuerySet[T]:
        if isinstance(index, slice):
            return QuerySet(self._items[index])
        return self._items[index]

    def __bool__(self) -> bool:
        return bool(self._items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({len(self)} items)"

    def all(self) -> tuple[T, ...]:
        """Return all results as an immutable tuple."""
        return self._items

    def first(self, default: T | None = None) -> T | None:
        """Return the first result, or ``default`` when the set is empty."""
        return self._items[0] if self._items else default

    def last(self, default: T | None = None) -> T | None:
        """Return the last result, or ``default`` when the set is empty."""
        return self._items[-1] if self._items else default

    def take(self, count: int) -> QuerySet[T]:
        """Return at most the first ``count`` results without converting to a tuple."""
        if count < 0:
            raise ValueError("take() count cannot be negative")
        return QuerySet(self._items[:count])

    def filter(self, predicate: Callable[[T], bool]) -> QuerySet[T]:
        """Return items for which ``predicate(item)`` is true."""
        return QuerySet(item for item in self if predicate(item))

    def exclude(self, predicate: Callable[[T], bool]) -> QuerySet[T]:
        """Return items for which ``predicate(item)`` is false."""
        return QuerySet(item for item in self if not predicate(item))

    def where(self, **criteria: Any) -> QuerySet[T]:
        """Filter by attributes; callable expected values act as predicates."""

        def matches(item: T) -> bool:
            for field, expected in criteria.items():
                actual = resolve_value(item, field)
                if callable(expected):
                    if not expected(actual):
                        return False
                elif isinstance(actual, (tuple, list, set, frozenset)):
                    if expected not in actual:
                        return False
                elif actual != expected:
                    return False
            return True

        return self.filter(matches)

    def select(self, field_or_callable: str | Callable[[T], R]) -> tuple[R, ...]:
        """Project each item to a dotted attribute or callable result."""
        select = _selector(field_or_callable)
        return tuple(select(item) for item in self)

    def unique(self, field_or_callable: str | Callable[[T], R]) -> tuple[R, ...]:
        """Return distinct projected values in their first-seen order."""
        select = _selector(field_or_callable)
        seen: set[Any] = set()
        result: list[R] = []
        for item in self:
            value = select(item)
            if value not in seen:
                seen.add(value)
                result.append(value)
        return tuple(result)

    def group_by(self, field_or_callable: str | Callable[[T], K]) -> dict[K, QuerySet[T]]:
        """Group results by a dotted attribute or callable result."""
        select = _selector(field_or_callable)
        groups: defaultdict[K, list[T]] = defaultdict(list)
        for item in self:
            groups[select(item)].append(item)
        return {key: QuerySet(values) for key, values in groups.items()}

    def count_by(self, field_or_callable: str | Callable[[T], K]) -> dict[K, int]:
        """Count projected values without materializing a ``QuerySet`` per group."""
        select = _selector(field_or_callable)
        return dict(Counter(select(item) for item in self))

    def most_common(
        self,
        field: str,
        *,
        limit: int | None = None,
        include_none: bool = False,
    ) -> tuple[tuple[Any, int], ...]:
        """Count and rank values without requiring ``group_by`` knowledge."""
        counts: dict[Any, int] = self.count_by(field)
        ranked = sorted(
            (
                (value, count)
                for value, count in counts.items()
                if include_none or value is not None
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        return tuple(ranked[:limit])

    # Friendly morphology filters. They intentionally delegate to the generic query
    # engine so specific and advanced programs compose identically.
    def with_root(self, root: str) -> QuerySet[T]:
        """Keep tokens or words annotated with the exact Buckwalter ``root``."""
        return self.where(root=root)

    def with_any_root(self, roots: Iterable[str]) -> QuerySet[T]:
        """Keep tokens or words having any root in ``roots``."""
        wanted = set(roots)
        return self.filter(
            lambda item: bool(wanted.intersection(_morphology_values(item, "roots", "root")))
        )

    def with_root_length(self, length: int) -> QuerySet[T]:
        """Keep items having at least one root of exactly ``length`` letters."""
        return self.filter(
            lambda item: any(
                len(root) == length for root in _morphology_values(item, "roots", "root")
            )
        )

    def with_minimum_root_letter_count(self, letters: str, count: int) -> QuerySet[T]:
        """Keep items whose root contains ``count`` selected Buckwalter letters."""
        wanted = set(letters)
        return self.filter(
            lambda item: any(
                sum(character in wanted for character in root) >= count
                for root in _morphology_values(item, "roots", "root")
            )
        )

    def with_lemma(self, lemma: str) -> QuerySet[T]:
        """Keep tokens or words annotated with the exact Buckwalter ``lemma``."""
        return self.where(lemma=lemma)

    def with_form(self, form: str) -> QuerySet[T]:
        """Keep verbs with a form/baab code such as ``I`` or ``IV``."""
        return self.where(verb_form=form)

    def with_tense(self, tense: str) -> QuerySet[T]:
        """Keep items with derived ``PAST``, ``PRESENT``, or ``IMPERATIVE`` tense."""
        aliases = {"PRES": "PRESENT", "IMPV": "IMPERATIVE"}
        value = tense.upper()
        return self.where(tense=aliases.get(value, value))

    def with_aspect(self, aspect: str) -> QuerySet[T]:
        """Keep items with perfect, imperfect, or imperative source aspect."""
        aliases = {"PERF": "PERFECT", "IMPF": "IMPERFECT", "IMPV": "IMPERATIVE"}
        value = aspect.upper()
        return self.where(aspect=aliases.get(value, value))

    def with_voice(self, voice: str) -> QuerySet[T]:
        """Keep finite verbs with active or passive voice."""
        aliases = {"ACT": "ACTIVE", "PASS": "PASSIVE"}
        value = voice.upper()
        return self.where(voice=aliases.get(value, value))

    def with_person(self, person: int) -> QuerySet[T]:
        """Keep inflected items with grammatical person 1, 2, or 3."""
        return self.where(person=person)

    def with_number(self, number: str) -> QuerySet[T]:
        """Keep items whose number is singular, dual, or plural."""
        aliases = {"S": "SINGULAR", "SG": "SINGULAR", "D": "DUAL", "P": "PLURAL", "PL": "PLURAL"}
        value = number.upper()
        return self.where(grammatical_number=aliases.get(value, value))

    def with_gender(self, gender: str) -> QuerySet[T]:
        """Keep masculine or feminine items; ``M`` and ``F`` are accepted."""
        aliases = {"M": "MASC", "MASCULINE": "MASC", "F": "FEM", "FEMININE": "FEM"}
        value = gender.upper()
        return self.where(gender=aliases.get(value, value))

    def with_part_of_speech(self, part_of_speech: str) -> QuerySet[T]:
        """Keep items with an exact QAC part-of-speech code such as ``V`` or ``N``."""
        return self.where(part_of_speech=part_of_speech.upper())

    def with_case(self, case: str) -> QuerySet[T]:
        """Keep items with a derived case/state such as ``NOM``, ``ACC``, or ``GEN``."""
        return self.where(case=case.upper())

    def with_mood(self, mood: str) -> QuerySet[T]:
        """Keep items with an exact QAC mood code such as ``SUBJ`` or ``JUS``."""
        return self.where(mood=mood.upper())

    def with_definiteness(self, definiteness: str) -> QuerySet[T]:
        """Keep items with the requested derived definiteness value."""
        return self.where(definiteness=definiteness.upper())

    def with_derived_noun(self, kind: str) -> QuerySet[T]:
        """Keep verbal nouns or active/passive participles by derived noun kind."""
        return self.where(derived_noun=kind.upper())

    def with_conjugation(self, conjugation: int) -> QuerySet[T]:
        """Keep items with a legacy numeric conjugation identifier (1 through 14)."""
        return self.where(conjugation=conjugation)

    def with_tag(self, tag: str) -> QuerySet[T]:
        """Keep morphology tokens with an exact QAC tag."""
        return self.where(tag=tag.upper())

    def with_role(self, role: str) -> QuerySet[T]:
        """Keep tokens whose structural role is ``PREFIX``, ``STEM``, or ``SUFFIX``."""
        return self.where(role=role.upper())

    def with_source_feature(self, feature: str) -> QuerySet[T]:
        """Keep tokens containing an exact non-keyed source feature."""
        return self.filter(lambda item: feature in getattr(item, "source_features", ()))

    def in_chapter(self, chapter: int) -> QuerySet[T]:
        """Keep addressed objects belonging to ``chapter``."""
        return self.where(chapter=chapter)

    def in_verse(self, chapter: int, verse: int) -> QuerySet[T]:
        """Keep addressed objects belonging to one verse."""
        return self.where(chapter=chapter, verse=verse)

    def in_word(self, chapter: int, verse: int, word: int) -> QuerySet[T]:
        """Keep addressed objects belonging to one morphology word."""
        return self.where(chapter=chapter, verse=verse, word=word)

    def roots(self) -> frozenset[str]:
        """Return all distinct Buckwalter roots represented in the result."""
        return frozenset(
            root for item in self for root in _morphology_values(item, "roots", "root")
        )

    def lemmas(self) -> frozenset[str]:
        """Return all distinct Buckwalter lemmas represented in the result."""
        return frozenset(
            lemma for item in self for lemma in _morphology_values(item, "lemmas", "lemma")
        )

    def forms(self) -> frozenset[str]:
        """Return all distinct verb-form/baab codes represented in the result."""
        return frozenset(
            form
            for item in self
            for form in (
                _values(item, "VERB_FORM") or _morphology_values(item, "forms", "verb_form")
            )
        )

    def most_common_forms(self, limit: int | None = None) -> tuple[tuple[str, int], ...]:
        """Rank individual verb-form codes, including words with multiple stems."""
        counts = Counter(form for item in self for form in _values(item, "VERB_FORM"))
        return tuple(counts.most_common(limit))

    def sorted_by(
        self,
        field_or_callable: str | Callable[[T], Any],
        *,
        reverse: bool = False,
    ) -> QuerySet[T]:
        """Return results sorted by a dotted attribute or callable."""
        return QuerySet(sorted(self, key=_selector(field_or_callable), reverse=reverse))

    def starts_with(
        self, prefix: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep text-bearing objects whose normalized text starts with ``prefix``."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "starts_with",
                prefix,
                representation=representation,
                **normalization,
            )
        )

    def ends_with(
        self, suffix: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep text-bearing objects whose normalized text ends with ``suffix``."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "ends_with",
                suffix,
                representation=representation,
                **normalization,
            )
        )

    def contains(
        self, fragment: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep text-bearing objects containing a normalized substring."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "contains",
                fragment,
                representation=representation,
                **normalization,
            )
        )

    def equals(
        self, expected_text: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep objects whose complete normalized text equals ``expected_text``."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "equals",
                expected_text,
                representation=representation,
                **normalization,
            )
        )

    def contains_letter(
        self, letter: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep text-bearing objects containing exactly one requested character."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "contains_letter",
                letter,
                representation=representation,
                **normalization,
            )
        )

    def contains_any_letter(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep objects containing at least one requested character."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "contains_any_letter",
                letters,
                representation=representation,
                **normalization,
            )
        )

    def contains_all_letters(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep objects containing every requested character at least once."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "contains_all_letters",
                letters,
                representation=representation,
                **normalization,
            )
        )

    def without_letters(
        self, letters: str, *, representation: str = "auto", **normalization: Any
    ) -> QuerySet[T]:
        """Keep objects containing none of the requested characters."""
        return self.filter(
            lambda item: _text_matches(
                item,
                "contains_no_letters",
                letters,
                representation=representation,
                **normalization,
            )
        )

    def with_letter_count(
        self,
        count: int,
        *,
        representation: str = "arabic",
        **normalization: Any,
    ) -> QuerySet[T]:
        """Keep objects with exactly ``count`` alphabetic characters."""
        return self.filter(
            lambda item: (
                item.letter_count(  # type: ignore[attr-defined]
                    representation=representation, **normalization
                )
                == count
            )
        )

    def with_minimum_character_count(
        self,
        characters: str,
        count: int,
        *,
        representation: str = "auto",
        **normalization: Any,
    ) -> QuerySet[T]:
        """Keep objects containing selected characters at least ``count`` times."""
        return self.filter(
            lambda item: (
                item.count_characters(  # type: ignore[attr-defined]
                    characters, representation=representation, **normalization
                )
                >= count
            )
        )

    def texts(self, representation: str = "arabic") -> tuple[str, ...]:
        """Return display text for every item in the requested representation."""
        return tuple(
            item.get_text(representation)  # type: ignore[attr-defined]
            for item in self
        )

    def show(
        self,
        representation: str = "arabic",
        *,
        limit: int | None = None,
        include_address: bool = True,
    ) -> None:
        """Print a result set in Arabic, Buckwalter, or English translation."""
        items = self._items if limit is None else self._items[:limit]
        for item in items:
            text = item.get_text(representation)  # type: ignore[attr-defined]
            address = getattr(item, "address", None)
            print(f"{address}\t{text}" if include_address and address else text)

    def longest_run(self, predicate: Callable[[T], bool]) -> QuerySet[T]:
        """Return the longest contiguous run satisfying ``predicate``."""
        best: list[T] = []
        current: list[T] = []
        for item in self:
            if predicate(item):
                current.append(item)
                if len(current) > len(best):
                    best = current.copy()
            else:
                current.clear()
        return QuerySet(best)


class IndexedCollection(QuerySet[T], Generic[K, T]):
    """A queryable collection addressed by semantic, usually 1-based, keys."""

    __slots__ = ("_index",)

    def __init__(self, items: Iterable[T], key: Callable[[T], K]) -> None:
        super().__init__(items)
        self._index = {key(item): item for item in self._items}
        if len(self._index) != len(self._items):
            raise ValueError("Collection keys must be unique")

    def __getitem__(self, key: K) -> T:  # type: ignore[override]
        return self._index[key]

    def __contains__(self, key: object) -> bool:
        return key in self._index

    def keys(self) -> tuple[K, ...]:
        """Return semantic keys in collection order."""
        return tuple(self._index)

    def values(self) -> tuple[T, ...]:
        """Return indexed objects in collection order."""
        return self._items

    def items(self) -> tuple[tuple[K, T], ...]:
        """Return semantic key/object pairs in collection order."""
        return tuple(self._index.items())


class OneBasedCollection(QuerySet[T]):
    """A compact 1-based collection for naturally consecutive Quranic numbers."""

    __slots__ = ()

    def __getitem__(self, number: int) -> T:  # type: ignore[override]
        if not isinstance(number, int):
            raise TypeError("One-based collections require an integer key")
        if number < 1 or number > len(self._items):
            raise KeyError(number)
        return self._items[number - 1]

    def __contains__(self, number: object) -> bool:
        return isinstance(number, int) and 1 <= number <= len(self._items)

    def keys(self) -> tuple[int, ...]:
        """Return consecutive 1-based keys."""
        return tuple(range(1, len(self._items) + 1))

    def values(self) -> tuple[T, ...]:
        """Return objects in semantic order."""
        return self._items

    def items(self) -> tuple[tuple[int, T], ...]:
        """Return consecutive 1-based key/object pairs."""
        return tuple(enumerate(self._items, 1))
