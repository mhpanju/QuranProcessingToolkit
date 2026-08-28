"""Backward-compatible imports for the original single-file prototype.

New code should import from :mod:`quran_processing_toolkit` instead.
"""

from __future__ import annotations

from quran_processing_toolkit import (  # noqa: F401
    Chapter,
    Juz,
    QuerySet,
    QuranCorpus,
    Token,
    Verse,
    Word,
    load_quran,
    normalize_arabic,
)


def loc_str_to_coords(location: str) -> tuple[int, int, int, int]:
    """Parse ``(chapter:verse:word:part)`` into a validated coordinate tuple."""
    components = location.strip().strip("()").split(":")
    if len(components) != 4:
        raise ValueError("location must have the form (chapter:verse:word:part)")
    coordinates = tuple(map(int, components))
    if any(coordinate < 1 for coordinate in coordinates):
        raise ValueError("Quranic coordinates are 1-based positive integers")
    return coordinates  # type: ignore[return-value]


if __name__ == "__main__":
    corpus = load_quran()
    print(
        f"Loaded {len(corpus.chapters)} chapters, {len(corpus.verses)} verses, "
        f"{len(corpus.words)} words, and {len(corpus.tokens)} morphological segments."
    )
