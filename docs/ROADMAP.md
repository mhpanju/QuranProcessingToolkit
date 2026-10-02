# Design review and roadmap

This document records gaps found while documenting the package. It distinguishes
issues fixed in the current API from larger changes that need measurement, new source
data, or a deliberate compatibility decision.

## Improvements completed during the documentation pass

- Token morphology now has lowercase properties, so named filters work on
  `quran.tokens` as well as aggregated words.
- Nominal `with_number()` queries now use source `COUNT` when finite conjugation is not
  present.
- Categorical helpers accept lowercase input and common aliases.
- `in_chapter()`, `in_verse()`, and `in_word()` remove routine address lambdas.
- `QuranCorpus.search()` provides a simple Arabic/Buckwalter search entry point.
- `equals()` supports normalized exact-text queries on objects and collections.
- `stats()` centralizes canonical object/subset counts for Python and the CLI.
- `take()` provides a readable limited QuerySet without tuple conversion.
- `count_by()` counts directly rather than allocating one QuerySet per group.
- process-cache keys now include disk-cache policy and cache location.
- Buckwalter normalization now mirrors alif, ya, and whitespace options where those
  operations have clear equivalents.
- the CLI now provides text search and reports noun/verb counts.

## High-value next features

### Chapter metadata

`Chapter` currently knows only its number and verses. Common programs would benefit
from Arabic/transliterated names, Meccan/Medinan classification, and perhaps canonical
English names. This requires choosing and licensing a trustworthy metadata source; it
should not be hard-coded from memory.

### More Quranic divisions

Juz is supported. Hizb, quarter-hizb, ruku, page, and manzil divisions are not. Each
requires an explicit sourced boundary table and provenance record. The object model
should generalize to a `Division` concept before adding several nearly identical
classes.

### Individual-value frequency helpers

`most_common("root")` counts a multi-root word's tuple as one value. The cookbook shows
how to flatten roots with `Counter`, while `most_common_forms()` already performs the
specialized flattening. A general `most_common_values(field)` helper could flatten
multi-valued properties consistently, but its behavior for strings, mappings, and
missing values needs a precise contract.

### Export adapters

Researchers often want CSV, JSON Lines, pandas, or Polars. Export belongs in optional
adapters so the core keeps zero mandatory dependencies. A good design should expose
documented stable columns rather than dumping internal object dictionaries.

### Multiple translation layers

One translation file can be loaded at a time. Comparative translation work would be
simpler with named layers, for example `translations={"qarai": path, "pickthall":
path}`. That would change `Verse.translation_text` and output APIs, so it should be
introduced as a versioned design rather than squeezed into the current property.

### Text indexes

Text search currently scans 6,236 verses or 77,429 words, which is fast for occasional
interactive use. Repeated large search workloads might benefit from normalized indexes
keyed by representation and normalization policy. Benchmarks should show a real need
before accepting the memory cost and cache invalidation complexity.

## Performance opportunities requiring benchmarks

### Lower-memory token storage

Every token retains a dictionary so all source and derived fields remain inspectable.
This is simple and traceable but relatively memory-heavy. Possible alternatives include
interned strings, immutable record objects, or columnar arrays. Any replacement must:

- preserve unknown source fields;
- keep `token.data` and uppercase compatibility access useful;
- maintain deterministic ordering;
- avoid a heavy mandatory dependency; and
- demonstrate meaningful end-to-end memory or latency improvement.

### Lazy object construction

The complete object graph is built eagerly. Lazy chapters or verses could improve
startup and memory for tiny queries, but global queries would become more complex and
could repeatedly parse records. A separate lazy backend may be cleaner than changing
the predictable behavior of `load_quran()`.

### Binary derived cache

Canonical JSON is portable, inspectable, and hashable, but about 23 MB locally. A
binary cache could be smaller/faster. It would need a safe format—never pickle—and a
canonical validation strategy. The optional `orjson` path already improves decode time
without changing the format, so a binary replacement needs measured justification.

## Linguistic/API questions requiring care

### Form I “baab” detail

The current `baab` alias means Roman-numeral verb form. Traditional Form I baab
classification can encode vowel patterns more specifically. Adding a separate
`form_i_baab` would require an evidence-based derivation and validation, not just a
renaming.

### Case, mood, and mabni

The historical convenience model stores nominative/accusative/genitive, jussive, and
`MABNI` under `CASE`. A cleaner future model may separate nominal case, verbal mood,
and indeclinability. Source `MOOD` remains available now, preventing information loss
while that design is evaluated.

### Corpus corrections

Suspected upstream errors should be listed with addresses and evidence before any
semantic overlay changes. The verbatim source remains untouched. See
[Interpretation decisions](PROPOSED_CORPUS_CHANGES.md).

## Things intentionally not planned

- a SQL requirement for ordinary analysis;
- bundled translations with unclear redistribution rights;
- zero-based Quranic semantic addresses;
- silent selection of one stem from a multi-stem word;
- mutation of installed source files; or
- task-specific helpers whose names encode one answer rather than a reusable concept.
