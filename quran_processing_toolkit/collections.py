"""Composable collection helpers for corpus objects."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Generic, TypeVar, overload

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
        return self._items

    def first(self, default: T | None = None) -> T | None:
        return self._items[0] if self._items else default

    def last(self, default: T | None = None) -> T | None:
        return self._items[-1] if self._items else default

    def filter(self, predicate: Callable[[T], bool]) -> QuerySet[T]:
        return QuerySet(item for item in self if predicate(item))

    def exclude(self, predicate: Callable[[T], bool]) -> QuerySet[T]:
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
        select = _selector(field_or_callable)
        return tuple(select(item) for item in self)

    def unique(self, field_or_callable: str | Callable[[T], R]) -> tuple[R, ...]:
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
        select = _selector(field_or_callable)
        groups: defaultdict[K, list[T]] = defaultdict(list)
        for item in self:
            groups[select(item)].append(item)
        return {key: QuerySet(values) for key, values in groups.items()}

    def count_by(self, field_or_callable: str | Callable[[T], K]) -> dict[K, int]:
        return {key: len(values) for key, values in self.group_by(field_or_callable).items()}

    def sorted_by(
        self,
        field_or_callable: str | Callable[[T], Any],
        *,
        reverse: bool = False,
    ) -> QuerySet[T]:
        return QuerySet(sorted(self, key=_selector(field_or_callable), reverse=reverse))

    def starts_with(
        self, prefix: str, *, representation: str = "arabic", **normalization: Any
    ) -> QuerySet[T]:
        return self.filter(
            lambda item: item.starts_with(  # type: ignore[attr-defined]
                prefix, representation=representation, **normalization
            )
        )

    def ends_with(
        self, suffix: str, *, representation: str = "arabic", **normalization: Any
    ) -> QuerySet[T]:
        return self.filter(
            lambda item: item.ends_with(  # type: ignore[attr-defined]
                suffix, representation=representation, **normalization
            )
        )

    def contains(
        self, fragment: str, *, representation: str = "arabic", **normalization: Any
    ) -> QuerySet[T]:
        return self.filter(
            lambda item: item.contains(  # type: ignore[attr-defined]
                fragment, representation=representation, **normalization
            )
        )

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
        return tuple(self._index)

    def values(self) -> tuple[T, ...]:
        return self._items

    def items(self) -> tuple[tuple[K, T], ...]:
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
        return tuple(range(1, len(self._items) + 1))

    def values(self) -> tuple[T, ...]:
        return self._items

    def items(self) -> tuple[tuple[int, T], ...]:
        return tuple(enumerate(self._items, 1))
