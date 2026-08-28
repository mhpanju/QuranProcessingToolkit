# Quran Processing Toolkit

An opinionated, queryable Python edition of the Quranic Arabic Corpus. The toolkit
preserves Quranic addresses as 1-based values, attaches Uthmani text and an English
translation to the morphology, and makes linguistic and text-processing questions
natural to express in Python.

The project is currently an early research release. The normalized morphology is a
modified annotation corpus; see [Data provenance](docs/DATA_PROVENANCE.md) and
[Proposed corpus changes](docs/PROPOSED_CORPUS_CHANGES.md) before treating its labels
as upstream Quranic Arabic Corpus labels.

## Install and load

```bash
python -m pip install -e .
```

The core package has no third-party dependencies. Install `.[fast]` to use `orjson`
when available. Repeated `load_quran()` calls in one process reuse the loaded corpus.

```python
from quran_processing_toolkit import load_quran

quran = load_quran()

fatihah = quran.chapters[1]
ayat_al_kursi = quran.verses[2, 255]
first_word = quran.words[1, 1, 1]
first_segment = quran.tokens[1, 1, 1, 1]
```

All semantic indexes are genuinely 1-based. There are no dummy chapter 0, chapter
115, or juz 31 records. Iterating a collection yields its real objects.

## General queries

Collections support `filter`, `exclude`, `where`, `group_by`, `count_by`, `select`,
`unique`, `sorted_by`, `starts_with`, `ends_with`, `contains`, and `longest_run`.
Text predicates accept Arabic, transliteration, or translation representations and
explicit Unicode-normalization options.

```python
# Verses ending in nun, ignoring diacritics and Quranic pause marks.
ending_in_nun = quran.verses.ends_with(
    "ن", strip_diacritics=True, strip_quranic_marks=True
)

# Fathah tanween followed by alif, while retaining diacritics.
ending_in_tanween_alif = quran.verses.ends_with(
    "ًا", strip_quranic_marks=True
)

# Current normalized-corpus tense names are exposed without reinterpretation.
present_tagged_verbs = quran.verbs.where(tense="PRES")
forms_by_frequency = present_tagged_verbs.count_by("baab")

# First-person plural verbs and roots absent from first-person singular verbs.
first_plural = quran.verbs.where(person=1, grammatical_number="PLURAL")
first_singular = quran.verbs.where(person=1, grammatical_number="SINGULAR")
plural_only_roots = set(first_plural.select("root")) - set(first_singular.select("root"))

# Three-letter nouns containing at least two selected weak letters.
weak_letters = {"ا", "و", "ي", "ى", "ی"}
weak_nouns = quran.nouns.filter(
    lambda word: word.letter_count(strip_diacritics=True) == 3
    and word.count_characters(weak_letters, strip_diacritics=True) >= 2
)

# Longest within-verse sequence containing neither mim nor nun.
longest = quran.longest_word_sequence(
    lambda word: not word.contains("م") and not word.contains("ن")
)
```

Use `find_words()` for repeated equality queries; it lazily builds an inverted index:

```python
from_root_ktb = quran.find_words(root="ktb")
form_iv_verbs = quran.find_words(baab="IV").filter(lambda word: word.is_verb())
```

Raw processed fields remain available on tokens using their original uppercase names:

```python
token = quran.tokens[2, 255, 1, 1]
print(token.FORM, token.TAG, token.get("CASE"))
```

## Commands

```bash
quran-toolkit stats
quran-toolkit word 2:255:1
quran-toolkit validate
quran-rebuild --check
python verses_per_juzz.py
```

`quran-rebuild --check` reconstructs all 128,219 processed records from
`quran-morphologies_base.json` and compares them with the checked-in normalized
corpus. The resulting JSON is byte-for-byte identical. Writing requires an explicit
`--output` path, so validation cannot overwrite the corpus accidentally.

## Development

```bash
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

The historical `from tools import QuranCorpus` import continues to work, but new code
should import `quran_processing_toolkit`.

## License

The Python code is released under Apache-2.0. Bundled source texts, translations, and
linguistic annotations retain their own upstream terms; the top-level Apache license
does not relicense them. See [Data provenance](docs/DATA_PROVENANCE.md).
