# User-installed translations

No translation is distributed with the project. Translation copyright and reuse terms
vary independently of Quran text and morphology, so users install only a translation
they are entitled to use.

## One-line opt-in download

```python
from quran_processing_toolkit import download_translation, load_quran

quran = load_quran(translation=download_translation("en.qarai"))
print(quran.verse(1, 1).get_translation())
```

This explicitly downloads Ali Quli Qarai's English translation from
[Tanzil](https://tanzil.net/trans/en.qarai) on first use. Nothing downloads when the
package is imported or when `load_quran()` is called without a translation. There
are no mandatory third-party dependencies. The curated catalog currently contains
`en.qarai` (alias `qarai`); `translation_sources()` returns its immutable source
descriptor, author, language, URL, content pin, and terms.

**Licensing:** Tanzil provides translations for non-commercial purposes only;
other use requires permission from the translator or publisher. The downloader
emits a non-blocking usage-terms warning before fetching and retains the terms URL
in metadata. Downloading is not a grant of commercial or redistribution rights.
See [Tanzil's current terms](https://tanzil.net/trans/).

### Reproducibility, cache, and offline use

The downloader verifies the entire file against this reviewed SHA-256:

```text
1207b98ee7ae47891b4dd01b608416da2278820acf54cdaf3943d0a6f9823fdf
```

It also validates all 6,236 canonical addresses, rejects duplicate/empty records,
and refuses unreviewed upstream changes. The downloaded file's footer identifies
its last update as April 11, 2022. The hash identifies that exact artifact; it does
not certify the linguistic accuracy of the translation.

Verbatim downloaded bytes and a provenance/terms sidecar live under the toolkit
user cache's `translations/` directory, never inside either installed distribution
or the morphology cache file. Writes are atomic. Cache filenames contain the ID
and full content hash; corrupt bytes are rejected, not silently accepted.

```python
translation = download_translation("en.qarai", offline=True)
quran = load_quran(translation=translation)

# Override only the translation cache location.
translation = download_translation("en.qarai", cache_dir="/my/cache/translations")

# Deliberately fetch the SAME pinned source again, e.g. to repair a corrupt cache.
translation = download_translation("en.qarai", refresh=True)
```

Ordinary repeated calls reuse a verified cached file without networking.
`offline=True` forbids networking and errors if the pinned file is missing.
`offline=True, refresh=True` is invalid. Requests use HTTPS, a finite default
timeout, an 8 MiB size limit, and reject non-HTTPS redirects. Download failures do
not write unverified content. An upstream content change requires a reviewed
catalog update, not `refresh=True` or disabling verification.

## Provenance and coverage

```python
metadata = quran.translation_metadata()  # copied dict; None if no translation
print(metadata["translator"])
print(metadata["source_url"])
print(metadata["sha256"])

coverage = quran.translation_coverage()
print(coverage.translated, coverage.total, coverage.fraction, coverage.complete)
print(coverage.missing)  # sorted tuple of (chapter, verse) addresses
quran.require_translation()  # raises if any verse lacks text

# Only require coverage for the actual output, not unrelated verses.
verses = quran.verses.in_chapter(2)
quran.require_translation(verses)
```

`quran.translation` is a `Translation` object (or `None`); `translation_path`
remains available. `Translation.texts` and `.metadata` are read-only mappings.
`.coverage(addresses=None)` and `.require_complete(addresses=None)` operate on
address tuples rather than Verse objects. A complete empty requested subset has
fraction 1.0. Its fingerprint identifies text plus attribution for corpus caching.

The earlier third-party GitHub JSON mirror was missing `94:7` and `94:8`. The
curated direct Tanzil source covers both. We do not repair that mirror or substitute
text from another translator.

## File format

Use UTF-8 plain text with one record per line:

```text
chapter|verse|translation text
```

Example:

```text
# My translation or private research notes
1|1|Translation of verse 1:1
1|2|Translation of verse 1:2
2|255|Translation of verse 2:255
```

Rules:

- chapter and verse are decimal Quranic 1-based numbers;
- the first two `|` characters delimit fields;
- additional `|` characters are retained inside the translation text;
- blank lines and lines beginning with `#` are ignored;
- duplicate addresses are rejected; and
- malformed lines identify their line number; non-integer or invalid canonical
  addresses are rejected.

The file may be partial. A verse absent from the file simply has no translation.

## Loading

Pass the path explicitly:

```python
from quran_processing_toolkit import load_quran

quran = load_quran(translation="/path/to/translation.txt")
```

Structured JSON of the form `{"surahs": [{"number": 1, "verses": [{"number": 1,
"text": "..."}]}]}` is also accepted when the filename ends in `.json`. Embedded
newlines and literal `|` characters in translation text are preserved.

Attach your own descriptive metadata without making a network request:

```python
from quran_processing_toolkit import load_translation

translation = load_translation(
    "/path/to/translation.txt",
    name="My translation layer",
    translator="Author supplied by the caller",
    language="English",
)
quran = load_quran(translation=translation)
```

Metadata supplied for a local file is descriptive, not independently verified.
Its raw-byte SHA-256 is always recorded. Invalid canonical verse addresses, empty
texts, and duplicate addresses are rejected. Local files may still be partial.

Or configure the process environment:

```bash
export QURAN_PROCESSING_TOOLKIT_TRANSLATION=/path/to/translation.txt
```

An explicit argument takes precedence over the environment variable. A configured
path that is not a file raises `CorpusError` immediately.

## Access and output

```python
verse = quran.verse(1, 1)

if verse.has_translation:
    print(verse.get_translation())

quran.verses.show("translation", limit=3)
quran.verses.show("english", limit=3)  # alias
```

`translation` and `english` are representation aliases; the package does not assert
that a supplied file is English. They exist for compatibility and convenience.

Requesting translation output for an untranslated verse raises
`TranslationNotAvailableError`. This is intentional: returning an empty string could
silently corrupt counts or exported results.

Filter a partial translation first when printing all available records:

```python
translated = quran.verses.filter(lambda verse: verse.has_translation)
translated.show("english")
```

## Translation search

Use an explicit representation so ASCII is not interpreted as Buckwalter:

```python
mercy = quran.verses.contains("mercy", representation="translation")
```

Translation comparisons are literal. Arabic-specific and Buckwalter-specific
normalization options do not change translation strings. Apply language-specific case
folding, tokenization, or stemming in user code because those policies depend on the
language and research task.

Collection text predicates skip verses absent from a partial translation. Directly
asking an absent verse for translation still raises, so missing data cannot be mistaken
for an empty translation.

## Reloading after editing a file

The in-process cache key includes the translation's resolved path, size, and
nanosecond modification time. For a `Translation` object it also includes the
fingerprint of the immutable text and attribution, so differently labeled layers
cannot accidentally reuse one another. Saving a changed file normally causes the next
`load_quran()` call to build a new corpus automatically.

To force this behavior regardless of filesystem timestamp resolution:

```python
from quran_processing_toolkit import clear_memory_cache, load_quran

clear_memory_cache()
quran = load_quran(translation="translation.txt")
```

The derived morphology disk cache does not contain translation text and does not need
to be cleared.

## Licensing responsibility

Supplying a local translation does not copy it into either Python distribution or the
derived morphology cache. The caller remains responsible for that file's acquisition,
use, attribution, and redistribution terms.
