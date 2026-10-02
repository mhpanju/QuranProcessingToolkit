# Quran Processing Toolkit

Natural, typed Python access to Quranic text and morphology—with an ASCII-first query
interface and Quranic 1-based addresses.

```python
from quran_processing_toolkit import load_quran

quran = load_quran()

# ASCII input is Buckwalter, so an Arabic keyboard is optional.
present = quran.verbs.with_tense("present")
print(present.most_common_forms(limit=5))

ending_in_nun = quran.verses.ends_with("n", strip_diacritics=True)
ending_in_nun.show("arabic", limit=3)
```

The toolkit combines the verbatim Quranic Arabic Corpus (QAC) morphology source with
verbatim Tanzil Uthmani text at load time. It verifies both sources, builds a friendly
object model, and preserves every original annotation. No translation is bundled.

## What this package is for

It is designed for exploratory questions that should read like ordinary Python:

```python
# Which verb form is most common in present-tense verbs?
quran.verbs.with_tense("present").most_common_forms()

# Which roots occur in first-person plural verbs but not first-person singular verbs?
plural = quran.verbs.with_person(1).with_number("plural")
singular = quran.verbs.with_person(1).with_number("singular")
plural_only_roots = plural.roots() - singular.roots()

# Which three-letter noun roots contain at least two weak letters?
weak = quran.nouns.with_root_length(3).with_minimum_root_letter_count("Awy", 2)

# What is the longest within-verse run containing neither mim nor nun?
longest = quran.longest_word_sequence_without_letters("mn", strip_diacritics=True)
```

Named methods cover common work, while `where()`, `filter()`, `group_by()`, and
`count_by()` remain available for advanced analysis. SQL is never required.

## Installation

Code and data are deliberately separate distributions because their licenses differ:

```bash
python -m pip install "quran-processing-toolkit[data]"
```

That convenience extra installs:

- `quran-processing-toolkit`: Apache-2.0 Python code; and
- `quran-processing-toolkit-qac-data`: separately licensed, verbatim source data.

For a faster derived-cache decode, install the optional `fast` extra too:

```bash
python -m pip install "quran-processing-toolkit[data,fast]"
```

The two distributions can also be installed independently. See
[Data provenance](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
before redistributing either artifact.

## The object model

```python
fatihah = quran.chapters[1]
first_verse = quran.verses[1, 1]
first_word = quran.words[1, 1, 1]
first_part = quran.tokens[1, 1, 1, 1]
first_juz = quran.juzs[1]
```

These are semantic Quranic indexes—not padded Python lists. Chapter 1 is
`quran.chapters[1]`; there is no dummy chapter 0. A filtered `QuerySet`, by contrast,
uses ordinary Python result positions: `results[0]` is its first result.

The hierarchy is:

```text
QuranCorpus
├── Chapter → Verse → Word → Token
├── verses[(chapter, verse)]
├── words[(chapter, verse, word)]
├── tokens[(chapter, verse, word, part)]
└── Juz → Verse
```

A token is one morphological segment. Prefixes, stems, and suffixes can therefore be
separate tokens inside one orthographic word. Word-level morphology aggregates stem
tokens and retains multiple values rather than silently choosing one.

See [Data model and indexing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_MODEL.md)
for the precise semantics.

## Text and ASCII-first search

All words and verses provide `starts_with()`, `ends_with()`, `contains()`, `equals()`,
letter tests, and character counts. The same operations work on collections:

```python
quran.search("muwsaY")
quran.search("مُوسَى")

quran.words.starts_with("Al")
quran.verses.contains_any_letter("mn")
quran.verses.without_letters("mn")
```

With `representation="auto"`, ASCII input is interpreted as Buckwalter and non-ASCII
input as Arabic. Normalization is opt-in:

```python
matches = quran.verses.ends_with(
    "n",
    strip_diacritics=True,
    strip_quranic_marks=True,
)
```

Available outputs are Arabic, Buckwalter, and a user-supplied translation:

```python
verse = quran.verse(2, 255)
print(verse.get_arabic())
print(verse.get_transliteration())

matches.show("arabic", limit=10)
matches.show("buckwalter", limit=10)
```

## Morphology

Word- and token-level helpers include:

```python
quran.verbs.with_form("IV")
quran.verbs.with_aspect("imperfect")
quran.verbs.with_voice("passive")
quran.verbs.with_person(1).with_number("plural")
quran.nouns.with_gender("f").with_case("acc")
quran.tokens.with_role("prefix")
quran.tokens.with_tag("V")
quran.tokens.with_source_feature("IMPF")
```

Source aliases such as `PERF`, `IMPF`, `ACT`, and `PASS` are accepted by the relevant
helpers. Original QAC content remains inspectable:

```python
token = quran.token(2, 255, 1, 1)
print(token.source_feature_text)
print(token.source_features)
print(token.data)
```

See [Morphology reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/MORPHOLOGY.md)
for fields, derived values, aliases,
multi-stem behavior, and the distinction between aspect and tense.

## User-supplied translations

Pass a UTF-8 `chapter|verse|text` file:

```text
1|1|Translation of verse 1:1
1|2|Translation of verse 1:2
```

```python
translated = load_quran(translation="/path/to/translation.txt")
print(translated.verse(1, 1).get_translation())
translated.verses.show("english", limit=3)
```

The environment variable `QURAN_PROCESSING_TOOLKIT_TRANSLATION` is equivalent. See
[Translations](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/TRANSLATIONS.md)
for validation and partial-file behavior.

## Verification and caching

Every load verifies source filenames, byte sizes, and SHA-256 digests. Derived
morphology has its own canonical digest. The first process load may create a local
derived JSON cache; installed source files are never changed.

```python
quran = load_quran()                       # in-process and disk caching
fresh = load_quran(cache=False)            # new object graph
uncached = load_quran(disk_cache=False)    # rederive source records
```

Use `QURAN_PROCESSING_TOOLKIT_CACHE` or `cache_dir=...` to relocate the disk cache.
Read-only environments fall back safely to uncached loading. See
[Architecture and performance](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/ARCHITECTURE.md).

## Command line

```bash
quran-toolkit stats
quran-toolkit search muwsaY --level verse --limit 5
quran-toolkit word 2:255:1
quran-toolkit sources
quran-toolkit validate
quran-rebuild --check
```

See the [CLI reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/CLI.md)
for every option.

## Documentation

- [Getting started](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/GETTING_STARTED.md)
- [Query cookbook](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/QUERY_COOKBOOK.md)
- [API reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/API_REFERENCE.md)
- [Data model and indexing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_MODEL.md)
- [Morphology reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/MORPHOLOGY.md)
- [Translations](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/TRANSLATIONS.md)
- [Architecture and performance](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/ARCHITECTURE.md)
- [Design review and roadmap](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/ROADMAP.md)
- [Data provenance and licensing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
- [Source-preserving interpretation decisions](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/PROPOSED_CORPUS_CHANGES.md)
- [Command-line reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/CLI.md)
- [Release process](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/RELEASING.md)
- [Contributing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/CONTRIBUTING.md)

Runnable programs for the motivating questions are in
[`examples/`](https://github.com/mhpanju/QuranProcessingToolkit/tree/master/examples).

## Development

```bash
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy quran_processing_toolkit packages/quran_processing_toolkit_qac_data/src
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

The historical `from tools import QuranCorpus` import remains available for old local
scripts. New code should import from `quran_processing_toolkit`.

## License

The core Python distribution is Apache-2.0. The separate data distribution has mixed
upstream terms and complete notices. No English translation is included. See
[Data provenance](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
for the exact file-level boundary.
