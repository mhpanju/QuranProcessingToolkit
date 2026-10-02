# Data model and indexing

The public object model represents Quranic structure and QAC segmentation without
inventing dummy index-zero objects.

## Hierarchy

```text
QuranCorpus
├── chapters: OneBasedCollection[Chapter]
│   └── Chapter.verses: OneBasedCollection[Verse]
│       └── Verse.words: OneBasedCollection[Word]
│           └── Word.tokens: OneBasedCollection[Token]
├── verses: IndexedCollection[(chapter, verse), Verse]
├── words: IndexedCollection[(chapter, verse, word), Word]
├── tokens: IndexedCollection[(chapter, verse, word, part), Token]
└── juzs: OneBasedCollection[Juz]
    └── Juz.verses: QuerySet[Verse]
```

The nested and global indexes reference the same objects. For example:

```python
assert quran.chapters[2].verses[255] is quran.verses[2, 255]
assert quran.verses[2, 255].words[1] is quran.words[2, 255, 1]
```

## Three collection types

### `OneBasedCollection`

Used when keys are consecutive Quranic numbers: chapters, verses within a chapter,
words within a verse, token parts within a word, and juzs.

```python
quran.chapters[1]
quran.chapters.keys()       # (1, 2, ..., 114)
quran.chapters.items()      # ((1, Chapter(...)), ...)
```

Zero and out-of-range Quranic numbers raise `KeyError`. Non-integer keys raise
`TypeError`.

### `IndexedCollection`

Used for global compound addresses:

```python
quran.verses[2, 255]
quran.words[2, 255, 1]
quran.tokens[2, 255, 1, 1]
```

It supports `keys()`, `values()`, `items()`, iteration in corpus order, and fast
keyed lookup.

### `QuerySet`

Every filter returns an immutable `QuerySet`. A result set is not itself a semantic
Quranic index, so it follows Python sequence conventions:

```python
results = quran.verbs.with_form("IV")
first = results[0]
first_ten = results[:10]
also_first_ten = results.take(10)
```

Filtering never mutates the source collection. QuerySets store a tuple so results can
be safely reused, iterated repeatedly, grouped, and passed between functions.

## Addresses

Addresses are immutable, ordered dataclasses:

- `VerseAddress(chapter, verse)`
- `WordAddress(chapter, verse, word)`
- `TokenAddress(chapter, verse, word, part)`

Their string representations match the source convention:

```python
str(quran.word(2, 255, 1).address)  # "2:255:1"
```

Word and token addresses provide `as_tuple()`. Verse addresses can be unpacked because
all address objects are iterable.

## Tokens and words

QAC morphology is segmented. A written word can be represented by a prefix token, a
stem token, and a suffix token. Consequently:

```python
word.tokens          # every segment, 1-based
word.stem_tokens     # only STEM segments
word.transliteration # concatenation of every segment form
```

Word-level morphology normally aggregates stems only:

```python
word.roots
word.lemmas
word.parts_of_speech
word.values("CASE")
```

Plural properties always return tuples. Their singular counterparts return:

- `None` when no stem supplies a value;
- the value itself when exactly one distinct value exists; or
- a tuple when multiple distinct values exist.

For example, `word.roots` is always a tuple, while `word.root` may be `None`, a string,
or a tuple. The package retains this complexity because 486 source words have multiple
stems; silently selecting one would lose information.

Pass `stems_only=False` to `word.values()` only when affix annotations are relevant:

```python
word.values("POS", stems_only=False)
```

## Text-bearing objects

`Token`, `Word`, and `Verse` share `TextMixin`, but available representations differ:

| Object | Arabic | Buckwalter | Translation |
|---|---:|---:|---:|
| `Token` | no | yes | no |
| `Word` | yes | yes | no |
| `Verse` | yes | yes | optional |

Requesting a representation that an object cannot supply raises a descriptive error.
Translation output specifically raises `TranslationNotAvailableError` when no matching
user-supplied translation exists.

## Chapters and juzs

`Chapter` is a lightweight structural container with `number` and `verses`. `Juz` has
`number`, `start`, and a sequential `verses` QuerySet. Juz boundaries are a parallel
division of verses, not parents in the chapter hierarchy; words therefore do not store
a duplicated juz number.

To work with a juz:

```python
juz_30 = quran.juzs[30]
print(juz_30.start)
print(len(juz_30))
juz_30.verses.show("arabic", limit=3)
```

## Immutability and identity

Addresses and `Juz` are frozen dataclasses. QuerySets are immutable containers. Model
objects are mutable only internally during construction and should be treated as
read-only public values. `Token.data` returns a copy specifically so mutation does not
change the corpus.

`load_quran()` caches a complete corpus instance in process by default, so repeated
equivalent loads return identical objects. Call `clear_memory_cache()` to discard all
such instances, or `load_quran(cache=False)` to bypass reuse for one call.
