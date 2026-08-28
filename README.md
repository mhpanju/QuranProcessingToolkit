# Quran Processing Toolkit

An ASCII-friendly, queryable Python interface to Quranic text and morphology. The
toolkit preserves Quranic addresses as 1-based values and makes linguistic and
text-processing questions natural to express in Python.

The project is an early research release. It retains the original Quranic Arabic
Corpus annotations and constructs a documented convenience model at runtime; it does
not redistribute a modified corpus.

## Install

The Apache-2.0 toolkit and the separately licensed source data are separate Python
distributions:

```bash
python -m pip install quran-processing-toolkit
python -m pip install quran-processing-toolkit-qac-data
```

The equivalent convenience command is:

```bash
python -m pip install "quran-processing-toolkit[data]"
```

The data package contains verbatim Quranic Arabic Corpus v0.4 morphology and Tanzil
Uthmani text with their complete notices. It does not contain an English translation.

```python
from quran_processing_toolkit import load_quran

quran = load_quran()

fatihah = quran.chapters[1]
ayat_al_kursi = quran.verses[2, 255]
first_word = quran.words[1, 1, 1]
first_segment = quran.tokens[1, 1, 1, 1]
```

All semantic indexes are genuinely 1-based. There are no dummy chapter 0, chapter
115, or juz 31 records.

## ASCII-first queries

ASCII text supplied to text predicates is automatically interpreted as Buckwalter.
Arabic input is also accepted, but an entire program can be written without an Arabic
keyboard.

```python
# Verses ending in nun after removing short-vowel marks.
ending_in_nun = quran.verses.ends_with("n", strip_diacritics=True)

# Fathah tanween followed by alif, retaining diacritics.
ending_in_tanween_alif = quran.verses.ends_with("FA")

# Present-tense verbs are source IMPF / derived IMPERFECT records.
present_verbs = quran.verbs.with_tense("PRESENT")
forms_by_frequency = present_verbs.most_common_forms()

# First-person plural roots absent from first-person singular verbs.
first_plural = quran.verbs.with_person(1).with_number("PLURAL")
first_singular = quran.verbs.with_person(1).with_number("SINGULAR")
plural_only_roots = first_plural.roots() - first_singular.roots()
plural_only_verbs = first_plural.with_any_root(plural_only_roots)

# Nouns with a three-letter root containing at least two weak letters.
weak_nouns = quran.nouns.with_root_length(3).with_minimum_root_letter_count("Awy", 2)

# Longest within-verse sequence containing neither mim nor nun.
longest = quran.longest_word_sequence_without_letters("mn", strip_diacritics=True)
```

Results can be returned or printed in Arabic or Buckwalter:

```python
verse = quran.get_verse(2, 255)
print(verse.get_arabic())
print(verse.get_transliteration())

ending_in_nun.show("arabic", limit=3)
ending_in_nun.show("buckwalter", limit=3)
```

See the runnable programs in the
[`examples` directory](https://github.com/mhpanju/QuranProcessingToolkit/tree/master/examples).

## User-supplied translations

No translation is bundled because translation rights differ from those of the code
and morphology. Supply a numbered UTF-8 file when you have the right to use it:

```text
1|1|Translation of verse 1:1
1|2|Translation of verse 1:2
```

```python
quran = load_quran(translation="/path/to/my-translation.txt")
print(quran.verses[1, 1].get_translation())
quran.verses.show("english", limit=3)
```

The `QURAN_PROCESSING_TOOLKIT_TRANSLATION` environment variable provides the same
configuration. Missing verses simply have no translation; requesting one raises a
clear error.

## Source annotations and derived fields

The original QAC feature column remains available on every token:

```python
token = quran.tokens[2, 255, 1, 1]
print(token.source_feature_text)
print(token.source_features)
```

Convenience fields are derived without modifying the source file:

```python
perfect = quran.verbs.with_aspect("PERFECT")
imperfect = quran.verbs.with_aspect("IMPERFECT")
passive = quran.verbs.with_voice("PASSIVE")
```

Short source aliases such as `PERF`, `IMPF`, `ACT`, and `PASS` are also accepted by
the named methods.

## Provenance, verification, and caching

Every source file is checked against the data distribution's byte size and SHA-256
before use. The transformation has its own version and expected complete-output
digest.

```python
print(quran.provenance())
print(quran.licenses())
```

The first load in a new environment parses the verbatim source and writes derived JSON
to the user's cache directory. The cache key includes the transformation version and
source hash. The source package is never changed, and read-only environments fall back
to uncached loading. Set `QURAN_PROCESSING_TOOLKIT_CACHE` to choose another cache
directory or call `load_quran(disk_cache=False)` to disable it.

## Commands

```bash
quran-toolkit stats
quran-toolkit sources
quran-toolkit word 2:255:1
quran-toolkit validate
quran-rebuild --check
```

`quran-rebuild --check` verifies the verbatim source hash, derives all 128,219 records,
and compares their canonical digest. `--output /some/path.json` may be used to write a
local derived representation; it never overwrites source data.

## Development

```bash
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

The historical `from tools import QuranCorpus` import continues to work, but new code
should import `quran_processing_toolkit`.

## Licensing

The core Python distribution is Apache-2.0. The separate source-data distribution is
not Apache-2.0 and includes complete upstream notices. See
[`DATA_PROVENANCE.md`](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
for the file-level breakdown.
