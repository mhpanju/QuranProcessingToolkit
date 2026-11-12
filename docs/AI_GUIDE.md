# Usage guide for AI assistants

This guide describes **quran-processing-toolkit 0.4.0**, the first production PyPI
release. It is also a compact reference for people writing research scripts.
Authoritative details are in [API reference](API_REFERENCE.md) and
[Morphology](MORPHOLOGY.md). Do not infer methods from their English names.

## Install

Requires Python 3.10+. Distribution names use hyphens; imports use underscores.

```bash
python -m pip install "quran-processing-toolkit[data]"
```

The `data` extra installs `quran-processing-toolkit-qac-data==0.4.0`. The core alone
has zero mandatory dependencies and does not include Quran text or morphology.
Normal loading is offline. The optional `fast` extra installs `orjson`.

## Executable starting point

This complete example needs no network after installation and is checked by tests:

```python
from quran_processing_toolkit import compare_verses, load_quran

quran = load_quran()
assert len(quran.chapters) == 114
assert len(quran.verses) == 6236
assert len(quran.words) == 77429
assert len(quran.tokens) == 128219

verse = quran.verse(2, 255)
print(verse.address, verse.get_arabic())
print(quran.chapter(2).name)  # al-Baqarah

# Select verb stems, with every condition applied to the same token.
verbs = quran.verbs().with_root("qwl").with_tense("past").with_voice("active")
assert verbs
print(verbs[0].address, verbs[0].verb_form)
print(verbs.count_by("verb_form"))

# Search uses Buckwalter for ASCII input.
quran.search("muwsaY").show("arabic", limit=2)
assert len(quran.verbs().with_nun_of_emphasis()) == 243

# Compare only these two verses, using space-delimited surface words.
changes = compare_verses(quran.verse(27, 68), quran.verse(23, 83), ignore_pause_marks=True)
assert changes
for match in changes:
    print(match.kind, match.position_a, match.position_b)
```

## Choose the right object

| Need | Use | Meaning |
|---|---|---|
| Chapter, verse, word, token, juz | `quran.chapters[1]`, `quran.verses[2, 255]`, `quran.words[2, 255, 1]`, `quran.tokens[2, 255, 1, 1]`, `quran.juzs[1]` | Semantic 1-based addresses |
| Verb stems | `quran.verbs()` | `QuerySet[Token]`, QAC tag `V` |
| Noun stems | `quran.nouns()` | `QuerySet[Token]`, tag `N`; excludes proper nouns |
| Other parts of speech | `proper_nouns()`, `adjectives()`, `pronouns()`, `adverbs()`, `prepositions()`, `conjunctions()`, `nominals()`, `particles()` | Methods on `quran`; includes affixes where tagged |
| Complete words containing a verb or noun | `quran.verb_words`, `quran.noun_words` | Properties returning `QuerySet[Word]` |
| First filtered result | `results[0]` or `results.first()` | Zero-based sequence; `first()` returns `None` if empty |

A token is a segment inside a QAC-aligned orthographic word. Word morphology
aggregates stems and may return a tuple when multiple values occur. Chained word
filters can match different stems; use tokens for same-stem requirements.

## Compose queries

```python
# These fragments assume quran = load_quran().
quran.verbs().with_form("IV").with_aspect("imperfect").in_chapter(2)
quran.verbs().with_person(1).with_number("plural").with_nun_of_emphasis()
quran.nouns().with_case("acc").with_gender("f")
quran.tokens.with_role("suffix").with_tag("PRON")
quran.verses.ends_with("n", strip_diacritics=True)
quran.words.without_letters("mn", strip_diacritics=True)
quran.words.where(root="ktb")
quran.verbs().roots()  # frozenset[str]
quran.verbs().most_common_forms(limit=5)  # tuple[(form, count), ...]
quran.verbs().count_by("voice")  # dict[value, int]
quran.verbs().select("address")  # tuple of address objects
```

Results preserve corpus order unless explicitly sorted. QuerySets are immutable
result sequences. Use `list(results)` to obtain a mutable list. `show()` prints
and returns `None`; use `texts()` or `select()` for programmatic export.
`most_common("root")` treats a multi-root word's tuple as one value; query tokens
or flatten `word.roots` when counting individual roots.

## Text rules and common mistakes

- Quranic addresses start at 1; filtered QuerySets start at 0.
- `quran.verbs()` is a method; `quran.verb_words` is a property. Preview 0.3.0
  used `quran.verbs` and `quran.nouns` for whole-word properties.
- On tokens, `form` / `get_form()` is surface text; `verb_form` is the morphological
  form. `with_form("IV")` selects the morphological form on either tokens or words.
- Roots, lemmas, and surface text are case-sensitive Buckwalter. For example,
  `with_root("qwl")`; do not translate a root to English or lowercase it blindly.
- Categorical values accept aliases: `with_aspect("IMPF")`,
  `with_tense("present")`, `with_voice("PASS")`. Tense is a derived convenience
  classification; [Morphology](MORPHOLOGY.md) explains its limits.
- ASCII search input is Buckwalter. For English text, use
  `representation="translation"` and load a translation first.
- Text comparisons are literal unless normalization options are explicitly supplied.
  Arabic verse text comes from Tanzil; Buckwalter comes from QAC annotations, so
  independently searching both representations need not produce identical results.
- `surface_words()` splits literal spaces and differs from QAC word segmentation.
  `compare_verses()` explains a single-word edit, not arbitrary similarity or a
  corpus-wide search. Match positions are surface positions, not QAC addresses.
- `token.source_feature_text`, `token.source_features`, and `token.data` expose
  original features and derived fields; do not modify source data to answer a query.

## Translation, errors, and reproducibility

`load_quran(translation="/path/to/translation.txt")` accepts UTF-8 numbered
`chapter|verse|text` or [structured JSON](TRANSLATIONS.md). Local files may be partial.
`load_translation()` attaches descriptive author/language metadata. Translation
output for missing verses raises `TranslationNotAvailableError`; call
`quran.require_translation(verses)` to require coverage of your result subset.

Only `download_translation("en.qarai")` explicitly opts into networking. It checks a
pinned hash, caches outside the package, and supports `offline=True`. Tanzil's
translation terms specify non-commercial use unless permission is obtained.
No translation is bundled or silently downloaded.

Missing data raises `DataPackageNotInstalledError`; install the `data` extra.
Modified or unsupported source bytes raise `DataIntegrityError`; restore the exact
supported source rather than weakening verification. Invalid addresses raise
`KeyError` in indexed collections. [API reference](API_REFERENCE.md#errors) lists
other errors.

For a fresh object and source derivation, use
`load_quran(cache=False, disk_cache=False)`. Preserve `quran.provenance()` alongside
research output and record `quran_processing_toolkit.__version__`. See
[Data provenance](DATA_PROVENANCE.md) before redistributing data or derived output.

## Further examples

- [Query cookbook](QUERY_COOKBOOK.md): full research recipes and multi-root counting.
- [Verb JSON export](../examples/export_verb_index.py): every verb occurrence indexed
  by root, tense, form, conjugation, voice, and nun of emphasis.
- [Word-frequency export](../examples/verse_word_frequency.py): per-verse TSV rankings.
- [CLI reference](CLI.md): terminal search, validation, provenance, and rebuild.
- [Known limits](ROADMAP.md): supported divisions, performance, and future work.
