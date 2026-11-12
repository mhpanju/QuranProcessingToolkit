# Quran Processing Toolkit

Typed Python access to Quranic text, morphology, and composable research queries.
Search in Arabic or ASCII Buckwalter, inspect every original annotation, and address
chapters, verses, words, and tokens using Quranic 1-based indexes.

Requires **Python 3.10+**. Version **0.4.0** is the first production PyPI release;
the API is early-stage and future minor releases may introduce documented changes.

## Install and run

```bash
python -m pip install "quran-processing-toolkit[data]"
```

```python
from quran_processing_toolkit import load_quran

quran = load_quran()
assert len(quran.chapters) == 114
assert len(quran.verses) == 6236

print(quran.chapter(2).name)  # al-Baqarah
print(quran.verse(2, 255).get_arabic())

# ASCII search input is Buckwalter, so an Arabic keyboard is optional.
quran.search("muwsaY").show("arabic", limit=3)

# These are verb tokens: all filters apply to the same morphological stem.
present = quran.verbs().with_tense("present")
print(present.most_common_forms(limit=5))

quran.verses.ends_with("n", strip_diacritics=True).show("arabic", limit=3)
```

Loading is offline and verifies the installed source data. Nothing is downloaded
implicitly. The core has no mandatory third-party Python dependencies. Code and data
are separate distributions because their licenses differ; the `data` extra installs
the matching source-data package. For optional faster cache decoding, install
`"quran-processing-toolkit[data,fast]"`.

## What you can do

| Task | API | Guide |
|---|---|---|
| Look up an address | `quran.verse(2, 255)` | [Getting started](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/GETTING_STARTED.md) |
| Search Arabic or Buckwalter | `quran.search("muwsaY")` | [Query cookbook](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/QUERY_COOKBOOK.md) |
| Filter stems by root, form, tense, voice, person, or number | `quran.verbs().with_root("qwl")` | [Morphology](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/MORPHOLOGY.md) |
| Select nouns, pronouns, particles, and other parts of speech | `quran.nouns()`, `quran.pronouns()` | [API reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/API_REFERENCE.md) |
| Count, group, and export results | `results.count_by("root")`, `results.select("address")` | [Cookbook](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/QUERY_COOKBOOK.md) |
| Compare two verses for one-word edits | `compare_verses(a, b)` | [Comparison API](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/API_REFERENCE.md#chapter-names-and-surface-word-comparison) |
| Add a local translation or explicitly download one | `load_translation()`, `download_translation()` | [Translations](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/TRANSLATIONS.md) |
| Inspect sources and validate the corpus | `quran.provenance()`, `quran-toolkit validate` | [Data provenance](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md) |

SQL and a database server are not required. Named helpers cover ordinary queries;
`where()`, `filter()`, `group_by()`, and `count_by()` support custom analyses.

## Addresses, words, and tokens

```python
chapter = quran.chapters[1]
verse = quran.verses[2, 255]
word = quran.words[2, 255, 1]
token = quran.tokens[2, 255, 1, 1]
juz = quran.juzs[1]

results = quran.verbs().in_chapter(2)
first_result = results[0]  # filtered results use ordinary zero-based positions
```

A **word** is a QAC-aligned orthographic word. A **token** is one morphological
segment: prefixes, stems, and suffixes can be separate tokens inside a word.
`quran.verbs()` and `quran.nouns()` return tokens; `quran.verb_words` and
`quran.noun_words` return whole words. Chained word filters aggregate stem values,
so use token queries when all conditions must match a single stem.

On a token, `form` is its surface spelling and `verb_form` is its Roman-numeral
morphological form. The query `with_form("IV")` selects the morphological form.
Roots and lemmas use case-sensitive Buckwalter; categorical aliases such as
`"present"`, `"IMPF"`, `"passive"`, and `"PASS"` are accepted by the relevant helpers.

See [Data model and indexing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_MODEL.md)
for multi-stem behavior and the full hierarchy.

## Compose research queries

```python
# Roots found in first-person plural verbs but never first-person singular verbs.
plural = quran.verbs().with_person(1).with_number("plural")
singular = quran.verbs().with_person(1).with_number("singular")
plural_only_roots = plural.roots() - singular.roots()

# Three-letter noun roots with at least two weak letters.
weak_roots = quran.nouns().with_root_length(3).with_minimum_root_letter_count("Awy", 2)

# Explicit nun-of-emphasis annotations associated with their verb stem.
emphatic = quran.verbs().with_nun_of_emphasis()
assert len(emphatic) == 243

# The longest within-verse word run containing neither mim nor nun.
longest = quran.longest_word_sequence_without_letters("mn", strip_diacritics=True)

# Preserve access to every original annotation.
token = quran.token(2, 38, 6, 1)
print(token.source_feature_text)
print(token.source_features)
```

Text matching is literal by default. ASCII input selects Buckwalter; non-ASCII
input selects Arabic. Pass normalization options explicitly, for example
`strip_diacritics=True`, `strip_quranic_marks=True`, or `normalize_alif=True`.
Use `representation="translation"` for translation search so English input is
not interpreted as Buckwalter.

## Translations and verse comparison

Translations are optional. Load your own UTF-8 `chapter|verse|text` file or supported
JSON file:

```python
translated = load_quran(translation="/path/to/translation.txt")
print(translated.verse(1, 1).get_translation())
```

An explicit, hash-verified downloader is also available:

```python
from quran_processing_toolkit import compare_verses, download_translation

# This call opts into a network download on first use.
translated = load_quran(translation=download_translation("en.qarai"))
translated.require_translation()  # require coverage of all 6,236 verses

changes = compare_verses(
    quran.verse(27, 68),
    quran.verse(23, 83),
    ignore_pause_marks=True,
)
for change in changes:
    print(change.kind, change.verse_a.address, change.verse_b.address)
```

The catalog currently contains Ali Quli Qarai's English translation from Tanzil.
Its terms specify non-commercial use unless permission is obtained from the
translator or publisher. Downloads are cached outside the package and support
`offline=True`. Missing translation output raises `TranslationNotAvailableError`.
See [Translations](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/TRANSLATIONS.md)
for terms, formats, coverage checks, and provenance.

`compare_verses()` explains a single-word addition, substitution, or shift between
two verses. It returns zero or one match, rather than a general similarity score.
Its space-delimited surface positions differ from QAC word addresses; it performs
no spelling or vowel normalization.

## Command line

```bash
quran-toolkit stats
quran-toolkit search muwsaY --level verse --limit 5
quran-toolkit word 2:255:1
quran-toolkit sources
quran-toolkit validate
quran-rebuild --check
```

The [CLI reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/CLI.md)
explains all commands, options, and exit behavior.

## Integrity and caching

Every newly constructed corpus verifies source filenames, sizes, and SHA-256 hashes,
plus the canonical derived morphology digest. Later equivalent `load_quran()` calls
reuse the same in-process object. A local derived JSON cache speeds up new processes;
installed source files are never changed.

```python
fresh = load_quran(cache=False)  # a new object graph
uncached = load_quran(cache=False, disk_cache=False)  # rederive from source
```

Set `QURAN_PROCESSING_TOOLKIT_CACHE` or pass `cache_dir=...` to relocate the derived
cache. Read-only cache locations fall back to uncached loading. See
[Architecture](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/ARCHITECTURE.md).

## Documentation for people and AI assistants

Start at the [documentation index](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/README.md).
The [AI usage guide](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/AI_GUIDE.md)
provides a compact, executable introduction, task-to-API mapping, and common mistakes.
[`llms.txt`](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/llms.txt)
links to the authoritative Markdown references.

- [Getting started](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/GETTING_STARTED.md)
- [Query cookbook](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/QUERY_COOKBOOK.md)
- [API reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/API_REFERENCE.md)
- [Morphology reference](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/MORPHOLOGY.md)
- [Release notes and preview migration](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/CHANGELOG.md)
- [Runnable examples](https://github.com/mhpanju/QuranProcessingToolkit/tree/master/examples), including a [complete verb JSON exporter](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/examples/export_verb_index.py)
- [Known limits and roadmap](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/ROADMAP.md)
- [Contributing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/CONTRIBUTING.md)

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy quran_processing_toolkit packages/quran_processing_toolkit_qac_data/src
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

The historical `from tools import QuranCorpus` import is available in source
checkouts. Installed applications should import `quran_processing_toolkit`.

## License and attribution

The Python code is Apache-2.0. The core also includes separately attributed Tanzil
chapter-label metadata, whose upstream declaration is CC-BY without a version;
see [Third-party notices](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/THIRD_PARTY_NOTICES.md).
The data package preserves the QAC and Tanzil sources verbatim under their respective
upstream terms, with full notices. No translation is bundled. Read
[Data provenance and licensing](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
before redistributing data or derived artifacts.
