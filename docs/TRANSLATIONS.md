# User-supplied translations

No translation is distributed with the project. Translation copyright and reuse terms
vary independently of Quran text and morphology, so users install only a translation
they are entitled to use.

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
- malformed or non-integer addresses are rejected with the source line number.

The file may be partial. A verse absent from the file simply has no translation.

## Loading

Pass the path explicitly:

```python
from quran_processing_toolkit import load_quran

quran = load_quran(translation="/path/to/translation.txt")
```

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
nanosecond modification time. Saving a changed file normally causes the next
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
