"""Natural, 1-based access to Quranic text and morphology."""

from .collections import IndexedCollection, OneBasedCollection, QuerySet
from .corpus import (
    CorpusAlignmentError,
    CorpusError,
    QuranCorpus,
    default_data_directory,
    load_quran,
)
from .models import (
    VERB_FORM_NAMES,
    Chapter,
    Juz,
    Token,
    TokenAddress,
    Verse,
    VerseAddress,
    Word,
    WordAddress,
)
from .text import (
    BUCKWALTER_DIACRITICS,
    QURANIC_PAUSE_MARKS,
    canonical_representation,
    infer_representation,
    normalize_arabic,
    normalize_buckwalter,
)

__all__ = [
    "Chapter",
    "BUCKWALTER_DIACRITICS",
    "CorpusAlignmentError",
    "CorpusError",
    "IndexedCollection",
    "Juz",
    "OneBasedCollection",
    "QuranCorpus",
    "QURANIC_PAUSE_MARKS",
    "QuerySet",
    "Token",
    "TokenAddress",
    "Verse",
    "VerseAddress",
    "VERB_FORM_NAMES",
    "Word",
    "WordAddress",
    "default_data_directory",
    "canonical_representation",
    "infer_representation",
    "load_quran",
    "normalize_arabic",
    "normalize_buckwalter",
]

__version__ = "0.2.0"
