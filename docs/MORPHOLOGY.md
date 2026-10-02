# Morphology reference

The morphology layer has two simultaneous views:

1. the exact QAC form, tag, and feature column; and
2. documented convenience fields derived deterministically at load time.

The first is evidence. The second makes routine queries readable. A convenience field
never replaces or rewrites source data.

## Inspecting a token

```python
token = quran.token(2, 255, 1, 1)

print(token.form)                 # Buckwalter surface segment
print(token.tag)                  # QAC tag
print(token.source_feature_text)  # exact complete source feature column
print(token.source_features)      # non-keyed source features
print(token.data)                 # copied complete processed record
```

The source feature column contains both plain features and keyed features:

```text
STEM|POS:PN|LEM:{ll~ah|ROOT:Alh|NOM
```

`source_feature_text` returns that string unchanged. `source_features` returns only
non-keyed entries such as `STEM` and `NOM`. Keyed values are retained in `token.data`
and exposed through named properties where useful.

## Token properties

| Property | Meaning | Typical values |
|---|---|---|
| `form` | Source Buckwalter segment | `kataba` |
| `tag` | Source QAC tag | `V`, `N`, `PN`, `PRP` |
| `role` | Segment role | `PREFIX`, `STEM`, `SUFFIX` |
| `part_of_speech` | Keyed `POS` value | `V`, `N`, `PN` |
| `root` | Buckwalter root | `ktb` |
| `lemma` | Buckwalter lemma | source-dependent |
| `verb_form` / `baab` | Derived Roman-numeral form | `I`, `IV`, `rI` |
| `aspect` | Source aspect made explicit | `PERFECT`, `IMPERFECT`, `IMPERATIVE` |
| `tense` | Convenience temporal label | `PAST`, `PRESENT`, `IMPERATIVE` |
| `voice` | Finite verb voice | `ACTIVE`, `PASSIVE` |
| `conjugation` | Legacy compact identifier | `1` through `14` |
| `person` | Derived grammatical person | `1`, `2`, `3` |
| `grammatical_number` | Number | `SINGULAR`, `DUAL`, `PLURAL` |
| `gender` | Gender | `MASC`, `FEM` |
| `case` | Case or toolkit state | `NOM`, `ACC`, `GEN`, `JUS`, `MABNI` |
| `mood` | Keyed source mood | `SUBJ`, `JUS`, source-dependent |
| `definiteness` | Derived definiteness | `INDEFINITE` when marked |
| `derived_noun` | Participle/verbal noun | `VERB_SUBJECT`, `VERB_OBJECT`, `VERBAL_NOUN` |

Less common keyed fields remain available without a bespoke property:

```python
token.get("PRON")
token.data["FEATURES"]
```

For compatibility, `token.SOME_UPPERCASE_FIELD` also resolves against the processed
record. Prefer `get()` when absence is expected.

## Word aggregation

A word aggregates distinct values from its stem tokens. These plural forms are always
tuples:

- `roots`
- `lemmas`
- `parts_of_speech`
- `conjugation_labels`

Their singular counterparts (`root`, `lemma`, `part_of_speech`) return one value when
unambiguous and a tuple when a multi-stem word genuinely has several values.

The following word properties summarize stem fields:

- `verb_form` and alias `baab`
- `baab_name`
- `aspect`
- `tense`
- `voice`
- `conjugation`
- `person`
- `grammatical_number`
- `gender`
- `case`
- `mood`
- `definiteness`
- `derived_noun`

`grammatical_number` uses finite conjugation when available and otherwise falls back
to nominal `COUNT`, so `quran.nouns.with_number("plural")` works naturally.

## Named morphology queries

The same helpers work on compatible word or token collections:

```python
quran.verbs.with_root("ktb")
quran.verbs.with_lemma("...")
quran.verbs.with_form("IV")
quran.verbs.with_tense("present")
quran.verbs.with_aspect("impf")
quran.verbs.with_voice("pass")
quran.verbs.with_person(1)
quran.verbs.with_number("pl")
quran.nouns.with_gender("f")
quran.nouns.with_case("acc")
quran.nouns.with_definiteness("indefinite")
quran.nouns.with_derived_noun("verbal_noun")
quran.tokens.with_tag("V")
quran.tokens.with_role("stem")
quran.tokens.with_source_feature("IMPF")
```

Accepted shorthand includes:

| Method | Shorthand | Canonical value |
|---|---|---|
| `with_tense()` | `PRES` | `PRESENT` |
| `with_aspect()` | `PERF` | `PERFECT` |
| `with_aspect()` | `IMPF` | `IMPERFECT` |
| `with_aspect()` | `IMPV` | `IMPERATIVE` |
| `with_voice()` | `ACT` | `ACTIVE` |
| `with_voice()` | `PASS` | `PASSIVE` |
| `with_number()` | `S`, `SG` | `SINGULAR` |
| `with_number()` | `D` | `DUAL` |
| `with_number()` | `P`, `PL` | `PLURAL` |
| `with_gender()` | `M` | `MASC` |
| `with_gender()` | `F` | `FEM` |

These category helpers are case-insensitive. Roots, lemmas, forms, and exact source
features remain case-sensitive because Buckwalter character case carries meaning.

## Aspect is not tense

QAC's `PERF`, `IMPF`, and `IMPV` are retained as source features. The toolkit exposes
them as:

| Source | `aspect` | convenience `tense` |
|---|---|---|
| `PERF` | `PERFECT` | `PAST` |
| `IMPF` | `IMPERFECT` | `PRESENT` |
| `IMPV` | `IMPERATIVE` | `IMPERATIVE` |

Use `with_aspect()` when grammatical aspect matters and `with_tense()` when the simple
past/present convenience terminology is appropriate.

Canonical finite-verb counts in this source are:

- 9,150 perfect;
- 8,330 imperfect;
- 1,876 imperative; and
- 1,140 passive.

These counts are validation invariants, not corrections written into the source.

## Verb forms and “baab”

Roman-numeral forms are exposed as `verb_form`; `baab` is a convenience alias retained
for the project's intended audience. `baab_name` maps codes to familiar transliterated
names. The terms are not perfectly interchangeable in every traditional grammar,
especially for Form I, so research code should prefer `verb_form` where precision
matters.

Quadriliteral forms receive an `r` prefix, for example `rI`. If a verb token has no
explicit parenthesized form, the convenience model uses Form I. See
[Source-preserving interpretation decisions](PROPOSED_CORPUS_CHANGES.md).

## Root-oriented helpers

```python
quran.verbs.roots()
quran.nouns.with_root_length(3)
quran.nouns.with_minimum_root_letter_count("Awy", 2)
quran.verbs.with_any_root({"ktb", "qwl"})
```

Roots and lemmas are Buckwalter because that is how QAC stores them. The package does
not silently Arabic-normalize linguistic identifiers.

## Generic escape hatch

Named methods are intentionally not exhaustive. `where()` can access lowercase public
properties or raw uppercase processed-record keys:

```python
quran.verbs.where(case="NOM", voice="ACTIVE")
quran.tokens.where(POS="V", MOOD="SUBJ")
```

Callable conditions remain available for genuinely custom research:

```python
quran.words.where(root=lambda value: value is not None)
quran.tokens.filter(lambda token: token.get("SOMETHING") == "value")
```

The goal is that common programs need neither of these escape hatches, while unusual
questions remain expressible without expanding the core API indefinitely.
