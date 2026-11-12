# API reference

This is a hand-written reference for the stable, user-facing surface. Python
docstrings provide the same semantics at the point of use with `help()`.

## Top-level imports

The following are exported from `quran_processing_toolkit`:

- loading: `load_quran`, `QuranCorpus`, `clear_memory_cache`, `default_data_directory`
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
- chapter names: `chapter_name`
- surface comparison: `split_surface_words`, `compare_verses`, `VerseMatch`
- translations: `download_translation`, `load_translation`, `translation_sources`,
  `Translation`, `TranslationSource`, `TranslationCoverage`, `TranslationDownloadError`,
  `TranslationIntegrityError`, `TranslationLicenseWarning`

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
- `translation`: optional numbered TXT/structured JSON user file, or a `Translation`
  returned by `load_translation()` / `download_translation()`. A translation name
  string is not a magic filename or an implicit network request.
- `cache`: reuse the equivalent complete corpus object in this process.
- `disk_cache`: use the verified derived-record cache between processes.
- `cache_dir`: per-call override for that disk cache location.

Environment equivalents are `QURAN_PROCESSING_TOOLKIT_DATA`,
`QURAN_PROCESSING_TOOLKIT_TRANSLATION`, and `QURAN_PROCESSING_TOOLKIT_CACHE`.

### `default_data_directory()`

Return the resolved source-data directory from `QURAN_PROCESSING_TOOLKIT_DATA`,
the installed data provider, or a source checkout, in that order. Raises
`DataPackageNotInstalledError` when no provider is discoverable. This performs
discovery; `load_quran()` performs integrity verification.

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
- `verb_words`: lazily selected words with a verb stem.
- `noun_words`: lazily selected words with a noun stem.

### Part-of-speech shortcuts

These methods return cached `QuerySet[Token]` results in corpus order, with ordinary
zero-based result indexing. Use `list(quran.verbs())` if you need a mutable Python list.

| Method | Selected QAC tags |
|---|---|
| `verbs()` | `V` |
| `nouns()` | `N` (not `PN`) |
| `proper_nouns()` | `PN` |
| `adjectives()` | `ADJ` |
| `pronouns()` | `PRON`, `DEM`, `REL` |
| `adverbs()` | `T`, `LOC` |
| `prepositions()` | `P` |
| `conjunctions()` | `CONJ`, `SUB` |
| `nominals()` | `N`, `PN`, `ADJ`, `IMPN`, `PRON`, `DEM`, `REL`, `T`, `LOC` |
| `particles()` | The particle family listed below, plus `DET` |

The particle tags are `P`, `EMPH`, `IMPV`, `PRP`, `CONJ`, `SUB`, `ACC`, `AMD`,
`ANS`, `AVR`, `CAUS`, `CERT`, `CIRC`, `COM`, `COND`, `EQ`, `EXH`, `EXL`, `EXP`,
`FUT`, `INC`, `INT`, `INTG`, `NEG`, `PREV`, `PRO`, `REM`, `RES`, `RET`, `RSLT`,
`SUP`, `SUR`, `VOC`, and `DET`. This follows the
[QAC tag families](https://corpus.quran.com/documentation/tagset.jsp), adding the
source's segmented determiner `DET`. Disconnected letters (`INL`) are excluded.
These are selection groups, not changes to source tags. Affixes are included:
`pronouns()` includes pronoun suffixes, and `particles()` includes emphatic suffixes.

```python
assert quran.verbs().all() == quran.tokens.with_tag("V").all()
emphatic = quran.verbs().with_nun_of_emphasis()
non_emphatic = quran.verbs().without_nun_of_emphasis()
```

**Migration from the 0.3.0 TestPyPI preview:** the former `quran.verbs` and `quran.nouns` properties
returned **words**. Replace those with `quran.verb_words` and `quran.noun_words` to
preserve behavior. Use `quran.verbs()` / `quran.nouns()` for **tokens** instead.
On tokens, `verb_form` is the morphological form, while `form` / `get_form()` is
the surface spelling. Use the word collections for whole-word text or word-only
helpers such as `get_baab()`. Word filters aggregate stems; token filters ensure
every condition applies to the same stem.

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
quran.stats()  # dict[str, int]; verbs/nouns entries still count whole words
quran.provenance()  # deep-copied installed manifest
quran.licenses()  # summarized source/license records
```

## `QuerySet`

Every operation returns a new `QuerySet` unless the documented return type is a tuple,
set, dictionary, scalar, or printed output.

### Sequence and conversion

```python
len(results)
bool(results)
results[index]  # zero-based result position
results[start:stop]  # another QuerySet
results.all()  # tuple
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
quran.verb_words.where(**{"address.chapter": 2})
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
with_nun_of_emphasis(present=True)
without_nun_of_emphasis()
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

The nun filters apply to `Token` and `Word`. `with_nun_of_emphasis(False)` and
`without_nun_of_emphasis()` are equivalent. The argument must be a boolean (not the
string `"false"`). Absence does not imply verbhood: filter `quran.verbs()` first
when you only want verbs. Both filters preserve order and return new QuerySets.

### `Token.has_nun_of_emphasis()` / `Word.has_nun_of_emphasis()`

Return a boolean based on an explicit `SUFFIX|+n:EMPH` annotation. During word
construction, the suffix is associated with its preceding verb stem, stopping at
any new stem. A word matches if any of its verb stems matches. Non-verb tokens,
including the emphatic suffix itself, return `False`. A standalone `Token` has no
suffix context and returns `False` until assembled into a `Word`.

An ordinary final nun, an emphatic lam prefix, or the tag `EMPH` alone does not
qualify. The result is an in-memory relationship, not a new source annotation or
persisted derived-record field.

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
results.select(field_or_callable)  # tuple
results.unique(field_or_callable)  # ordered tuple
results.group_by(field_or_callable)  # dict[value, QuerySet]
results.count_by(field_or_callable)  # dict[value, int]
results.most_common(field, limit=None, include_none=False)
results.sorted_by(field_or_callable, reverse=False)
results.roots()  # frozenset
results.lemmas()  # frozenset
results.forms()  # frozenset
results.most_common_forms(limit=None)  # tuple[(form, count), ...]
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

## Chapter names and surface-word comparison

```python
chapter_name(2)  # "al-Baqarah"
quran.chapter(2).name  # ASCII transliteration
quran.chapter(2).name_arabic
quran.chapter(2).name_english  # meaning of the chapter name, not verse translation
quran.chapter(2).get_name("arabic")
quran.verse(2, 123).get_chapter_name("english")

quran.verse(2, 123).surface_words(ignore_pause_marks=True)  # tuple[str, ...]
split_surface_words(text, ignore_pause_marks=False)

compare_verses(quran.verse(27, 68), quran.verse(23, 83), ignore_pause_marks=True)
```

Chapter-name representations are `transliteration`/`ascii`, `arabic`, and
`english`/`translation`; names and case-insensitive representation aliases are
independent of translation layers. Chapter numbers must be integers 1 through 114.
Chapter label attribution is in [Third-party notices](../THIRD_PARTY_NOTICES.md).

Surface words are literal-space-delimited sequences, not QAC morphology words.
Empty fragments are omitted; tabs are not delimiters. Optional pause deletion
removes only `QURANIC_PAUSE_MARKS`. No Unicode NFC, vowel removal, alif/ya folding,
or spelling normalization is performed, and original displayed Arabic is unchanged.

Pairwise comparison returns `QuerySet[VerseMatch]`. Fields are `kind`, `verse_a`, `verse_b`,
`word_a`, `word_b`, `position_a`, and `position_b`; `.verses` returns `(verse_a, verse_b)`.
Positions are 1-based surface positions under the chosen comparison policy, not
QAC word indices. Addition orients A as shorter and sets `word_a`/`position_a` to None.
Substitution orients A as the earlier-addressed verse. Shift moves A's word later
in B. Ambiguous shifts choose the earliest A/B addresses, then earliest positions.
Only the two supplied verses are compared. Identical texts or the same verse
address return no changes. The result has zero or one deterministic explanation;
an adjacent swap may have several equivalent shift descriptions but appears once.
Use `list(changes)` or `[m.verses for m in changes]` for ordinary Python lists.
Task-specific corpus-wide pair searches and output exclusions belong in client
scripts rather than the package API.

## Translation layers

```python
translation_sources()  # tuple[TranslationSource, ...]; no network
download_translation(
    "en.qarai",
    cache_dir=None,
    offline=False,
    refresh=False,
    timeout=30.0,
)  # Translation; explicit network opt-in, pinned and cached
load_translation(path, name=None, translator=None, language=None)  # Translation; local only
quran.translation  # Translation | None
quran.translation_metadata()  # copied dict[str, str] | None
quran.translation_coverage(verses=None)  # TranslationCoverage
quran.require_translation(verses=None)  # None; raises on missing text
```

`TranslationCoverage` has `total`, `translated`, `missing`, `complete`, and `fraction`.
`Translation` has `path`, read-only `texts`/`metadata`, `fingerprint`,
`coverage(addresses=None)`, and `require_complete(addresses=None)`.
The download catalog currently contains Qara'i from Tanzil. Raw bytes, source URL,
hash, retrieval time, author, language, and third-party terms are retained in the
user cache. No translation ships in either distribution. See
[Translations](TRANSLATIONS.md) for input formats, limits, licensing, and offline use.

## Errors

- `DataPackageNotInstalledError`: core installed without a discoverable data package.
- `DataIntegrityError`: unsupported or modified source/manifest/cache derivation.
- `CorpusAlignmentError`: source morphology and Quran text word boundaries disagree.
- `TranslationNotAvailableError`: translation output requested for an untranslated
  item.
- `TranslationDownloadError`: explicit download failed, exceeded limits, or offline
  cache entry is absent.
- `TranslationIntegrityError`: translation bytes differ from their pin or a curated
  response has invalid coverage.
- `TranslationLicenseWarning`: non-blocking usage-terms warning before a download.
- `KeyError`: valid collection type but nonexistent semantic address.
- `ValueError`: invalid representation, search level, or helper argument.

All data-related errors inherit from `DataError`; `CorpusError` is a compatibility
alias for `DataError`.
