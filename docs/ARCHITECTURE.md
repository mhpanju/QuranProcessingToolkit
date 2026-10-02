# Architecture and performance

This document explains what happens between `load_quran()` and a usable corpus, why
code and data are separate, and where time and memory are spent.

## Package boundary

The repository builds two distributions:

```text
quran-processing-toolkit
└── Python loader, transformation, model, queries, CLI, and validation

quran-processing-toolkit-qac-data
├── verbatim QAC morphology 0.4
├── verbatim Tanzil Uthmani text 1.1
├── project-authored juz boundaries
├── integrity manifest
└── complete legal notices
```

The code package is Apache-2.0. The data wheel necessarily carries the terms attached
to each source. A translation is deliberately outside both distributions.

## Load pipeline

```text
discover data directory
        │
        ▼
read manifest and verify every size + SHA-256
        │
        ▼
read verified derived cache ───────────────┐
        │ cache miss                        │ cache hit
        ▼                                   │
parse 128,219 QAC source records            │
        │                                   │
derive documented convenience fields        │
        │                                   │
verify complete canonical derived digest    │
        │                                   │
atomically write user cache                  │
        └───────────────────────┬───────────┘
                                ▼
read Uthmani verse text and optional translation
                                │
                                ▼
group Token → Word → Verse → Chapter and align words
                                │
                                ▼
build global compound indexes and 30 Juz objects
```

Any failure before the final object graph raises rather than returning a partial or
unverified corpus.

## Data discovery

`default_data_directory()` tries, in order:

1. `QURAN_PROCESSING_TOOLKIT_DATA`;
2. the installed `quran_processing_toolkit_qac_data` provider; and
3. the data package's source directory in this monorepo.

The monorepo fallback lets editable development work without copying source data into
the Apache-licensed package.

## Integrity model

The installed manifest is not trusted by itself. The code package contains supported
source hashes and checks that the manifest declares one of them. It then verifies the
actual file size and streams each file through SHA-256.

The morphology transformation is also pinned:

- `TRANSFORMATION_VERSION` names cache compatibility;
- source SHA-256 selects an expected canonical derived digest; and
- `quran-rebuild --check` reparses everything and compares record count and digest.

Changing transformation behavior therefore requires a new transformation version and
expected digest. Changing source content requires an explicit supported source hash.

## Source-preserving transformation

`build.parse_source_record()` retains:

- address components;
- source tag;
- Buckwalter form;
- complete feature text;
- each keyed feature; and
- non-keyed features used while deriving convenience values.

`build.normalize_record()` copies retained fields and adds convenience fields such as
`VERB_FORM`, `ASPECT`, `TENSE`, `VOICE`, and `TOKEN_ROLE`. It never edits the source
file and never publishes the resulting JSON.

Five coordinate-specific interpretations of ambiguous `2D` annotations are explicit
in `CONJUGATION_OVERRIDES`; they are not hidden source patches. See
[Interpretation decisions](PROPOSED_CORPUS_CHANGES.md).

## Arabic alignment

Morphology defines the number and addresses of words. Uthmani text supplies the Arabic
surface spelling. Loading groups morphology records by word and verse, removes only
non-verse basmalas needed for alignment, removes selected pause marks from the in-memory
alignment view, and compares word counts.

Two known orthographic contractions are joined only in memory because Tanzil displays
spaces where QAC treats the sequence as one word. A mismatch anywhere raises
`CorpusAlignmentError` with the verse and both counts.

## Two independent caches

### Process cache

`load_quran(cache=True)` stores complete `QuranCorpus` instances under a key containing:

- resolved data directory;
- translation path, size, and nanosecond modification time;
- disk-cache choice; and
- resolved cache directory.

This makes repeated calls effectively free while ensuring a changed translation or
different loading policy does not silently reuse the wrong object. The cache is
protected by a lock. `clear_memory_cache()` empties it.

### Derived disk cache

The disk cache stores canonical normalized record JSON—not Python objects. Its filename
includes transformation version and source hash. Before use, the complete payload hash
must equal the expected derived digest and its record count must match the manifest.

The default location is:

```text
$XDG_CACHE_HOME/quran-processing-toolkit/
```

or `~/.cache/quran-processing-toolkit/` when `XDG_CACHE_HOME` is unset. Override it with
`QURAN_PROCESSING_TOOLKIT_CACHE` or `cache_dir=...`.

Writes use a temporary file followed by atomic replacement. Cache creation failure in
a read-only or restricted environment is nonfatal; verified records remain usable in
memory.

## Performance characteristics

The important distinction is:

- first uncached process: verify, parse, transform, align, construct;
- disk-cached process: verify, decode cache, align, construct; and
- repeated call in one process: dictionary lookup of the complete corpus instance.

The optional `orjson` dependency accelerates cache decoding when installed. It does
not change results, source verification, or serialization format.

QuerySets materialize result tuples. This makes them deterministic and reusable, at
the cost of allocating a tuple per query. Most operations are linear in the current
result size. Exact `find_words(field=value)` queries build and reuse a lazy inverted
index for the first criterion. `count_by()` counts directly and does not construct a
QuerySet for every group.

The object graph retains one dictionary per token to keep all source and derived fields
available. A future lower-memory backend could store columnar records or intern common
strings, but that would add complexity and must preserve the current public semantics.
For the complete Quran corpus, clarity and traceability currently outweigh that
optimization.

## Why there is no database

The corpus is small enough for an in-memory object model, and the project aims to let
users write normal Python rather than SQL. A database would add schema migration,
platform, packaging, and query-language burdens while duplicating Python indexes.

The generic query operations provide the useful relational ideas—filter, project,
group, count, and sort—without making SQL a prerequisite.

## Threading and mutation

Cache lookup and creation are lock-protected. Once returned, a corpus is designed for
read-only analysis. Query operations do not mutate it. `Token.data` and `provenance()`
return copies to keep callers from changing internal records or manifest state.

Simultaneous reads are safe under normal Python object semantics. The project does not
promise that user mutation of model attributes is safe or supported.

## Validation layers

`quran-toolkit validate` checks:

- source package integrity;
- canonical object counts;
- complete 30-juz coverage;
- canonical derived digest;
- aspect counts; and
- passive finite-verb count.

Unit tests additionally exercise indexing, multi-stem words, translation loading,
text normalization, named queries, source modification rejection, caching, and
reproducibility. CI runs these checks across every supported Python version and smoke
installs the built wheels outside the repository checkout.
