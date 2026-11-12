# Query cookbook

These complete examples favor named methods, ASCII source code, and intermediate
variables that make the linguistic question visible. Unless stated otherwise, each
snippet begins with:

```python
from quran_processing_toolkit import load_quran

quran = load_quran()
```

## Match all six verb criteria and export JSON

```python
matches = (
    quran.verbs()
    .with_root("Aty")
    .with_tense("present")
    .with_form("I")
    .with_conjugation(1)
    .with_voice("active")
    .with_nun_of_emphasis()
)

for verb in matches:
    verse = quran.verse(verb.chapter, verb.verse)
    print(str(verse.address), verb.word, verse.get_arabic())
```

This returns five occurrences in the supported corpus. For absence, use
`.without_nun_of_emphasis()` or `.with_nun_of_emphasis(False)`. All conditions
apply to the same verb token; `verb.word` is the 1-based word position, not the
token-part position. Keep separate hits when a verse contains multiple matches.

The complete [export script](../examples/export_verb_index.py) builds a JSON index
of all 19,356 verb occurrences. It stores Arabic verses once and nests references
under root, tense, form, conjugation, voice, and nun presence. Its `find_verbs()`
helper joins matching references back to Arabic text without reloading the corpus.

```bash
python examples/export_verb_index.py verbs.json
```

Roots remain case-sensitive Buckwalter. Forms use `verb_form` (not token `form`),
and conjugation numbers become string keys in JSON. These helpers are included in
0.4.0, the first production PyPI release.

## Compare two verse endings

How many verses end in nun, compared with fathah tanween followed by alif?

```python
ending_in_nun = quran.verses.ends_with("n", strip_diacritics=True)
ending_in_tanween_alif = quran.verses.ends_with("FA")

print("nun:", len(ending_in_nun))
print("fathah tanween plus alif:", len(ending_in_tanween_alif))

ending_in_nun.show("arabic", limit=5)
ending_in_tanween_alif.show("buckwalter", limit=5)
```

`strip_diacritics=True` makes nun the last significant Buckwalter letter. It is not
used for `FA`, where `F` itself is the fathah-tanween mark being tested.

## Rank forms among present-tense verbs

```python
present_verbs = quran.verb_words.with_tense("present")

for form, count in present_verbs.most_common_forms():
    print(form, count)
```

Use `.with_aspect("imperfect")` if the analysis should explicitly use aspect rather
than the package's convenience tense terminology.

## First-person plural but not singular roots

```python
first_plural = quran.verb_words.with_person(1).with_number("plural")
first_singular = quran.verb_words.with_person(1).with_number("singular")

plural_only_roots = first_plural.roots() - first_singular.roots()
occurrences = first_plural.with_any_root(plural_only_roots)

print(sorted(plural_only_roots))
occurrences.show("buckwalter", limit=20)
```

This compares roots, not surface forms. Replace `.roots()` with `.lemmas()` when lemma
identity is the desired unit.

## Three-letter noun roots with two weak letters

```python
weak_nouns = quran.noun_words.with_root_length(3).with_minimum_root_letter_count("Awy", 2)

print("occurrences:", len(weak_nouns))
print("roots:", sorted(weak_nouns.roots()))
weak_nouns.show("arabic", limit=20)
```

The letters are Buckwalter: `A` is alif, `w` is waw, and `y` is ya.

## Longest run without mim or nun

By default, a run cannot cross a verse boundary:

```python
longest = quran.longest_word_sequence_without_letters(
    "mn",
    strip_diacritics=True,
)

print(len(longest))
longest.show("arabic", include_address=False)
```

To treat the entire Quran as one continuous word stream:

```python
longest_across_verses = quran.longest_word_sequence_without_letters(
    "mn",
    strip_diacritics=True,
    cross_verse_boundaries=True,
)
```

## Find all occurrences of a root

```python
writing_words = quran.find_words(root="ktb")
writing_words.show("arabic", limit=20)
```

`find_words()` lazily builds an inverted index, making later exact queries for the same
field inexpensive:

```python
quran.find_words(root="qwl")
quran.find_words(root="Elm")
```

## Restrict an analysis to one location

```python
chapter_two_verbs = quran.verb_words.in_chapter(2)
ayat_al_kursi_words = quran.words.in_verse(2, 255)
first_word_parts = quran.tokens.in_word(2, 255, 1)
```

Scopes compose with morphology and text filters:

```python
chapter_two_passives = quran.verb_words.in_chapter(2).with_voice("passive")
```

## Find passive present verbs

```python
passive_present = quran.verb_words.with_tense("present").with_voice("passive")

print("occurrences:", len(passive_present))
print("common forms:", passive_present.most_common_forms(limit=10))
passive_present.show("arabic", limit=20)
```

## Compare singular, dual, and plural nouns

```python
singular = quran.noun_words.with_number("singular")
dual = quran.noun_words.with_number("dual")
plural = quran.noun_words.with_number("plural")

print(len(singular), len(dual), len(plural))
```

Nominal number comes from the source `COUNT` annotation; finite-verb number is derived
from conjugation. `with_number()` handles both representations.

## Find verbal nouns and participles

```python
verbal_nouns = quran.noun_words.with_derived_noun("verbal_noun")
active_participles = quran.noun_words.with_derived_noun("verb_subject")
passive_participles = quran.noun_words.with_derived_noun("verb_object")
```

The convenience labels are documented in [Morphology](MORPHOLOGY.md); original `VN`
and `PCPL` features remain accessible on tokens.

## Search by Arabic or Buckwalter

```python
ascii_results = quran.search("muwsaY")
arabic_results = quran.search("مُوسَى")

assert ascii_results.all() == arabic_results.all()
```

The assertion depends on exact spellings and normalization choices. When broader
matching is intended:

```python
results = quran.search(
    "muwsaY",
    strip_diacritics=True,
    normalize_alif=True,
    normalize_ya=True,
)
```

## Count roots or lemmas by occurrence

```python
common_roots = quran.verb_words.most_common("root", limit=20)
common_lemmas = quran.verb_words.most_common("lemma", limit=20)
```

`most_common()` counts the word-level property as one value. For the rare multi-stem
word, that property may be a tuple. To count every individual root independently:

```python
from collections import Counter

root_counts = Counter(root for word in quran.verb_words for root in word.roots)
print(root_counts.most_common(20))
```

## Group without SQL

```python
verbs_by_chapter = quran.verb_words.group_by("chapter")

for chapter_number, verbs in verbs_by_chapter.items():
    print(chapter_number, len(verbs))
```

For counts only, `count_by()` avoids materializing grouped result sets:

```python
counts = quran.verb_words.count_by("chapter")
```

## Inspect an unusual annotation

Start at the source token rather than guessing from a word summary:

```python
word = quran.word(2, 90, 1)

print(word.is_multi_stem)
for token in word.tokens:
    print(token.address, token.form, token.tag, token.source_feature_text)
```

The complete derived record is available as a copy:

```python
record = word.tokens[1].data
print(sorted(record))
```

## Supply and query a translation

```python
quran = load_quran(translation="translation.txt")

translated = quran.verses.filter(lambda verse: verse.has_translation)
translated.show("english", limit=10)
```

Text predicates can explicitly search translation text:

```python
mercy = quran.verses.contains("mercy", representation="translation")
```

Translation matching is literal and does not case-fold or perform English stemming.
Those policies belong in user code because translations and research needs differ.

## Write a custom condition only when needed

Named methods intentionally cover common tasks, but the underlying API remains normal
Python:

```python
long_words = quran.words.filter(lambda word: word.letter_count(strip_diacritics=True) >= 10)
```

If a custom condition becomes common across several analyses, it is a good candidate
for a new general named method. See [Contributing](../CONTRIBUTING.md).
