# API reference

This is a hand-written reference for the stable, user-facing surface. Python
docstrings provide the same semantics at the point of use with `help()`.

## Top-level imports

The following are exported from `quran_processing_toolkit`:

- loading: `load_quran`, `QuranCorpus`, `clear_memory_cache`
- models: `Chapter`, `Verse`, `Word`, `Token`, `Juz`
- addresses: `VerseAddress`, `WordAddress`, `TokenAddress`
- collections: `QuerySet`, `IndexedCollection`, `OneBasedCollection`
- text: `normalize_arabic`, `normalize_buckwalter`,
  `canonical_representation`, `infer_representation`
- errors: `CorpusError`, `CorpusAlignmentError`, `DataError`,
  `DataIntegrityError`, `DataPackageNotInstalledError`,
  `TranslationNotAvailableError`
- constants: `VERB_FORM_NAMES`, `BUCKWALTER_DIACRITICS`,
  `QURANIC_PAUSE_MARKS`

## Loading

### `load_quran(...)`

```python
load_quran(
    data_dir=None,
    *,
    translation=None,
    cache=True,
    disk_cache=True,
    cache_dir=None,
) -> QuranCorpus
```

- `data_dir`: supported source-data directory; normally omitted.
- `translation`: optional numbered user translation file.
- `cache`: reuse the equivalent complete corpus object in this process.
- `disk_cache`: use the verified derived-record cache between processes.
- `cache_dir`: per-call override for that disk cache location.

Environment equivalents are `QURAN_PROCESSING_TOOLKIT_DATA`,
`QURAN_PROCESSING_TOOLKIT_TRANSLATION`, and `QURAN_PROCESSING_TOOLKIT_CACHE`.

### `clear_memory_cache()`

Forgets process-local `QuranCorpus` instances. It does not delete files or clear the
derived disk cache.

## `QuranCorpus`

### Collections

- `chapters`: 114 `Chapter` objects, keyed 1 through 114.
- `verses`: 6,236 `Verse` objects, keyed by `(chapter, verse)`.
- `words`: 77,429 `Word` objects, keyed by `(chapter, verse, word)`.
- `tokens`: 128,219 `Token` objects, keyed by
  `(chapter, verse, word, part)`.
- `juzs`: 30 `Juz` objects, keyed 1 through 30.
- `verbs`: lazily selected words with a verb stem.
- `nouns`: lazily selected words with a noun stem.

### Address lookup

```python
quran.chapter(number)
quran.verse(chapter, verse)
quran.word(chapter, verse, word)
quran.token(chapter, verse, word, part)
```

`get_chapter`, `get_verse`, `get_word`, and `get_token` are aliases.

### Search and analysis

```python
quran.search(text, level="verse", representation="auto", **normalization)
quran.find_words(**criteria)
quran.index_words(field)
quran.longest_word_sequence(predicate, cross_verse_boundaries=False)
quran.longest_word_sequence_without_letters(
    letters,
    representation="auto",
    cross_verse_boundaries=False,
    **normalization,
)
```

`search()` accepts `verse`/`verses` or `word`/`words`. `find_words()` is intended for
exact morphology/property lookup and uses a lazy inverted index.

### Metadata

```python
quran.stats()       # dict[str, int]
quran.provenance()  # deep-copied installed manifest
quran.licenses()    # summarized source/license records
```

## `QuerySet`

Every operation returns a new `QuerySet` unless the documented return type is a tuple,
set, dictionary, scalar, or printed output.

### Sequence and conversion

```python
len(results)
bool(results)
results[index]       # zero-based result position
results[start:stop]  # another QuerySet
results.all()        # tuple
results.first(default=None)
results.last(default=None)
results.take(count)
```

### General filtering

```python
results.filter(predicate)
results.exclude(predicate)
results.where(**criteria)
```

`where()` accepts dotted attribute names and callable expected values. When the actual
attribute is a tuple/list/set, exact criteria use membership semantics.

```python
quran.words.where(root="ktb")
quran.verbs.where(**{"address.chapter": 2})
```

Dotted paths use a dictionary expansion because dots are not valid in Python keyword
syntax. Prefer `in_chapter(2)` over that form for ordinary location scoping.

### Scope helpers

```python
results.in_chapter(chapter)
results.in_verse(chapter, verse)
results.in_word(chapter, verse, word)
```

The objects must expose the relevant address properties. For example,
`quran.tokens.in_word(...)` is valid while `quran.chapters.in_verse(...)` is not.

### Morphology helpers

```python
with_root(root)
with_any_root(roots)
with_root_length(length)
with_minimum_root_letter_count(letters, count)
with_lemma(lemma)
with_form(form)
with_tense(tense)
with_aspect(aspect)
with_voice(voice)
with_person(person)
with_number(number)
with_gender(gender)
with_part_of_speech(code)
with_case(case)
with_mood(mood)
with_definiteness(value)
with_derived_noun(kind)
with_conjugation(number)
with_tag(tag)
with_role(role)
with_source_feature(feature)
```

Not every helper applies to every model type. `with_tag()`, `with_role()`, and
`with_source_feature()` are token operations; root/lemma/form helpers work on tokens
or words; aggregate person/number/gender/case helpers work on compatible words and
tokens.

### Text helpers

```python
starts_with(text, representation="auto", **normalization)
ends_with(text, representation="auto", **normalization)
contains(text, representation="auto", **normalization)
equals(text, representation="auto", **normalization)
contains_letter(letter, representation="auto", **normalization)
contains_any_letter(letters, representation="auto", **normalization)
contains_all_letters(letters, representation="auto", **normalization)
without_letters(letters, representation="auto", **normalization)
with_letter_count(count, representation="arabic", **normalization)
with_minimum_character_count(characters, count, representation="auto", **normalization)
```

`representation="auto"` maps ASCII input to Buckwalter and non-ASCII input to Arabic.
Text methods require objects that support the requested representation.

### Projection and summary

```python
results.select(field_or_callable)       # tuple
results.unique(field_or_callable)       # ordered tuple
results.group_by(field_or_callable)     # dict[value, QuerySet]
results.count_by(field_or_callable)     # dict[value, int]
results.most_common(field, limit=None, include_none=False)
results.sorted_by(field_or_callable, reverse=False)
results.roots()                         # frozenset
results.lemmas()                        # frozenset
results.forms()                         # frozenset
results.most_common_forms(limit=None)   # tuple[(form, count), ...]
```

### Output and runs

```python
results.texts(representation="arabic")
results.show(representation="arabic", limit=None, include_address=True)
results.longest_run(predicate)
```

`show()` prints and returns `None`. Use `texts()` when output must be captured or
formatted by the calling program.

## Text-bearing models

`Token`, `Word`, and `Verse` provide:

```python
item.get_text(representation="arabic")
item.normalized_text(representation="arabic", **options)
item.display(representation="arabic")
item.get_arabic()
item.get_transliteration()
item.get_translation()
item.starts_with(...)
item.ends_with(...)
item.contains(...)
item.equals(...)
item.contains_letter(...)
item.contains_any_letter(...)
item.contains_all_letters(...)
item.contains_no_letters(...)
item.count_characters(...)
item.letter_count(...)
```

See [Data model](DATA_MODEL.md) for which representation each object supplies.

## Normalization functions

### `normalize_arabic(text, ...)`

Options:

- `strip_diacritics`
- `strip_quranic_marks`
- `normalize_alif`
- `normalize_ya`
- `remove_spaces`

The function always applies Unicode NFC first.

### `normalize_buckwalter(text, ...)`

Options:

- `strip_diacritics`
- `normalize_alif` (`>`, `<`, `|`, `{` become `A`)
- `normalize_ya` (`Y` becomes `y`)
- `remove_spaces`

Unknown options are ignored so the same normalization dictionary can be passed after
automatic representation selection.

## Errors

- `DataPackageNotInstalledError`: core installed without a discoverable data package.
- `DataIntegrityError`: unsupported or modified source/manifest/cache derivation.
- `CorpusAlignmentError`: source morphology and Quran text word boundaries disagree.
- `TranslationNotAvailableError`: translation output requested for an untranslated
  item.
- `KeyError`: valid collection type but nonexistent semantic address.
- `ValueError`: invalid representation, search level, or helper argument.

All data-related errors inherit from `DataError`; `CorpusError` is a compatibility
alias for `DataError`.
