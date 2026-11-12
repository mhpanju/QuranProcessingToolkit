"""Natural, 1-based access to Quranic text and morphology."""

from .chapter_names import chapter_name
from .collections import IndexedCollection, OneBasedCollection, QuerySet
from .corpus import (
    CorpusAlignmentError,
    CorpusError,
    QuranCorpus,
    clear_memory_cache,
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
from .similarity import VerseMatch, compare_verses
from .source_data import (
    DataError,
    DataIntegrityError,
    DataPackageNotInstalledError,
)
from .text import (
    BUCKWALTER_DIACRITICS,
    QURANIC_PAUSE_MARKS,
    TranslationNotAvailableError,
    canonical_representation,
    infer_representation,
    normalize_arabic,
    normalize_buckwalter,
    split_surface_words,
)
from .translations import (
    Translation,
    TranslationCoverage,
    TranslationDownloadError,
    TranslationIntegrityError,
    TranslationLicenseWarning,
    TranslationSource,
    download_translation,
    load_translation,
    translation_sources,
)

__all__ = [
    "Chapter",
    "BUCKWALTER_DIACRITICS",
    "CorpusAlignmentError",
    "CorpusError",
    "DataError",
    "DataIntegrityError",
    "DataPackageNotInstalledError",
    "IndexedCollection",
    "Juz",
    "OneBasedCollection",
    "QuranCorpus",
    "QURANIC_PAUSE_MARKS",
    "QuerySet",
    "Token",
    "TokenAddress",
    "TranslationNotAvailableError",
    "Verse",
    "VerseAddress",
    "VERB_FORM_NAMES",
    "Word",
    "WordAddress",
    "clear_memory_cache",
    "default_data_directory",
    "canonical_representation",
    "infer_representation",
    "load_quran",
    "normalize_arabic",
    "normalize_buckwalter",
    "chapter_name",
    "split_surface_words",
    "VerseMatch",
    "compare_verses",
    "Translation",
    "TranslationCoverage",
    "TranslationDownloadError",
    "TranslationIntegrityError",
    "TranslationLicenseWarning",
    "TranslationSource",
    "download_translation",
    "load_translation",
    "translation_sources",
]

__version__ = "0.4.0"
