"""Pairwise surface-word comparison; corpus-wide research searches live in client scripts."""

from __future__ import annotations

from dataclasses import dataclass

from .collections import QuerySet
from .models import Verse


@dataclass(frozen=True, slots=True)
class VerseMatch:
    """One verse pair and a deterministic one-word edit explanation.

    Positions refer to the 1-based surface-word sequence, NOT QAC word addresses.
    For addition A is shorter and position_a/word_a are None. Substitution uses
    earlier-addressed A. Shift is oriented so A's word moves later in B; among
    ambiguous explanations, earliest A, B, and positions win. Identical texts do
    not match, even at different addresses. Original Verse objects are retained.
    """

    kind: str
    verse_a: Verse
    verse_b: Verse
    position_a: int | None
    position_b: int
    word_a: str | None
    word_b: str

    @property
    def verses(self) -> tuple[Verse, Verse]:
        """Return the original (verse A, verse B) objects."""
        return self.verse_a, self.verse_b


def _address(verse: Verse) -> tuple[int, int]:
    return verse.chapter, verse.verse


def compare_verses(
    verse_a: Verse,
    verse_b: Verse,
    *,
    ignore_pause_marks: bool = False,
) -> QuerySet[VerseMatch]:
    """Explain a one-word insertion, substitution, or later movement between two verses.

    Only these two inputs are compared; this is not a corpus-wide search. Original
    display text is preserved. Addition puts the shorter verse first; substitution
    uses address order; shifts choose the earliest valid A/B addresses and positions.
    """
    if _address(verse_a) == _address(verse_b):
        return QuerySet()
    first, second = sorted((verse_a, verse_b), key=_address)
    a = first.surface_words(ignore_pause_marks=ignore_pause_marks)
    b = second.surface_words(ignore_pause_marks=ignore_pause_marks)
    if a == b:
        return QuerySet()
    if abs(len(a) - len(b)) == 1:
        shorter, longer, short_text, long_text = (
            (first, second, a, b) if len(a) < len(b) else (second, first, b, a)
        )
        for pos, word in enumerate(long_text):
            if long_text[:pos] + long_text[pos + 1 :] == short_text:
                return QuerySet(
                    (VerseMatch("addition", shorter, longer, None, pos + 1, None, word),)
                )
        return QuerySet()
    if len(a) != len(b):
        return QuerySet()
    changed = [pos for pos, (left, right) in enumerate(zip(a, b, strict=True)) if left != right]
    if len(changed) == 1:
        pos = changed[0]
        return QuerySet(
            (VerseMatch("substitution", first, second, pos + 1, pos + 1, a[pos], b[pos]),)
        )
    candidates = []
    for source, target, left, right in ((first, second, a, b), (second, first, b, a)):
        for start, word in enumerate(left):
            remainder = left[:start] + left[start + 1 :]
            for end in range(start + 1, len(right)):
                if right[end] == word and right[:end] + right[end + 1 :] == remainder:
                    candidates.append(
                        VerseMatch("shift", source, target, start + 1, end + 1, word, word)
                    )
    if not candidates:
        return QuerySet()
    chosen = min(
        candidates,
        key=lambda m: (
            _address(m.verse_a),
            _address(m.verse_b),
            m.position_a or 0,
            m.position_b,
            m.word_b,
        ),
    )
    return QuerySet((chosen,))
