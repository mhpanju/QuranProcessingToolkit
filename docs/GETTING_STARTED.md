# Getting started

This guide takes a new user from installation to useful morphology and text queries.
All examples use only ASCII in Python source unless Arabic output is requested.

## Install code and data

Python 3.10 or newer is required.

```bash
python -m pip install "quran-processing-toolkit[data]"
```

The optional `fast` extra installs `orjson`, which can reduce the time needed to read
the local derived cache:

```bash
python -m pip install "quran-processing-toolkit[data,fast]"
```

The code and data packages are separate for licensing reasons. Installing only
`quran-processing-toolkit` is valid, but `load_quran()` will explain that its data
provider is missing until `quran-processing-toolkit-qac-data` is installed or a
supported `data_dir` is supplied.

## Load the corpus

```python
from quran_processing_toolkit import load_quran

quran = load_quran()
```

The first load in a process verifies source data and builds the object graph. A local
derived-record cache makes later processes faster, and later calls in the same process
normally return the same corpus instance.

```python
assert load_quran() is quran
```

Use `load_quran(cache=False)` when object identity must be fresh. Use
`load_quran(disk_cache=False)` to force deterministic source parsing instead of using
the cross-process derived cache.

## Look up known addresses

Quranic addresses are 1-based:

```python
chapter = quran.chapters[1]
verse = quran.verses[2, 255]
word = quran.words[2, 255, 1]
token = quran.tokens[2, 255, 1, 1]
juz = quran.juzs[1]
```

Equivalent named methods are useful when an address is stored in separate variables:

```python
verse = quran.get_verse(2, 255)
word = quran.get_word(2, 255, 1)
token = quran.get_token(2, 255, 1, 1)
```

Nested collections are also 1-based:

```python
first_verse = quran.chapters[1].verses[1]
first_word = first_verse.words[1]
first_part = first_word.tokens[1]
```

Filtered results are different: a `QuerySet` is a result sequence, so `results[0]`
means its first result. See [Data model and indexing](DATA_MODEL.md).

## Display text

```python
verse = quran.verse(2, 255)

print(verse.get_arabic())
print(verse.get_transliteration())
```

`get_transliteration()` returns Buckwalter assembled from the QAC morphology tokens.
A collection can print a compact address-and-text listing:

```python
quran.chapters[1].verses.show("arabic")
quran.chapters[1].verses.show("buckwalter")
```

Translations are user-installed and optional. See [Translations](TRANSLATIONS.md).

## Search text

The simplest entry point searches complete verses:

```python
moses_verses = quran.search("muwsaY")
```

ASCII input means Buckwalter. Arabic input means Arabic:

```python
moses_verses_arabic = quran.search("مُوسَى")
```

Search words instead of verses with `level="word"`:

```python
words = quran.search("muwsaY", level="word")
```

For prefix, suffix, exact-text, and letter queries, start from any text-bearing
collection:

```python
quran.verses.starts_with("AlH")
quran.verses.ends_with("n", strip_diacritics=True)
quran.words.equals("bisomi")
quran.words.contains_any_letter("mn")
quran.words.without_letters("mn")
```

Normalization never happens unless requested. Common options are:

- `strip_diacritics=True`
- `strip_quranic_marks=True`
- `normalize_alif=True`
- `normalize_ya=True`
- `remove_spaces=True`

## Query morphology without lambdas

The most frequently needed subsets are ready-made:

```python
quran.verbs
quran.nouns
```

Named filters compose and always return another immutable `QuerySet`:

```python
passive_present = (
    quran.verbs
    .with_tense("present")
    .with_voice("passive")
)

first_plural = quran.verbs.with_person(1).with_number("plural")
accusative_nouns = quran.nouns.with_case("acc")
form_four = quran.verbs.with_form("IV")
```

Scope any addressed result to a location:

```python
medina_example = quran.verbs.in_chapter(2).with_form("IV")
verse_tokens = quran.tokens.in_verse(2, 255)
word_tokens = quran.tokens.in_word(2, 255, 1)
```

## Summarize results

```python
present = quran.verbs.with_tense("present")

print(len(present))
print(present.first())
print(present.most_common_forms(limit=10))
print(present.roots())
print(present.lemmas())
```

General projections and summaries are available when no named helper fits:

```python
present.count_by("voice")
present.most_common("root", limit=10)
present.group_by("chapter")
present.select("address")
present.sorted_by("address")
```

`where()` performs exact attribute matching and understands multi-valued word fields:

```python
quran.words.where(root="ktb", part_of_speech="V")
quran.tokens.where(TAG="V")  # raw uppercase fields remain available
```

Prefer the lowercase named API for ordinary code; uppercase access exists to expose
the complete derived record and support research that needs less common fields.

## Continue learning

- [Query cookbook](QUERY_COOKBOOK.md) solves complete analysis questions.
- [API reference](API_REFERENCE.md) lists every main public operation.
- [Morphology reference](MORPHOLOGY.md) explains annotations and derived fields.
- [Architecture](ARCHITECTURE.md) explains verification, transformations, and caches.
