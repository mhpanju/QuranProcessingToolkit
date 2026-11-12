# Changelog

## 0.4.0 — 2026-11-12

First release of `quran-processing-toolkit` on production PyPI, paired with
`quran-processing-toolkit-qac-data==0.4.0`. Earlier versions were development and
TestPyPI previews. This release is early-stage; future minor releases may introduce
changes documented here.

### Included

- Typed corpus model: 114 chapters, 6,236 verses, 77,429 QAC-aligned words,
  128,219 morphology tokens, and 30 juz divisions.
- Quranic 1-based address lookup and composable immutable query results.
- Arabic and ASCII Buckwalter text search with explicit normalization.
- Token and word morphology filters, grouping, counts, root/lemma sets, and
  nun-of-emphasis detection tied to the annotated verb stem.
- Cached part-of-speech token selections, including proper nouns, pronouns,
  adjectives, adverbs, prepositions, conjunctions, nominals, and particles.
- Arabic, ASCII, and English chapter names with attributed metadata.
- Exact pairwise surface-word comparison for a one-word addition, substitution,
  or shift, with an explicit pause-mark policy.
- Optional local TXT/JSON translation layers with provenance and coverage checks;
  explicit pinned download/cache support for Qara'i from Tanzil.
- CLI commands for stats, search, word inspection, sources, validation, and
  deterministic morphology rebuilds.
- Source hash verification and a reproducible derived-record cache outside the
  installed packages. No translation is bundled or downloaded implicitly.
- Task-oriented documentation, an AI usage guide, `llms.txt`, and runnable examples.

### Migration from the 0.3.0 TestPyPI preview

The old `quran.verbs` and `quran.nouns` properties selected whole words. Rename
these to `quran.verb_words` and `quran.noun_words` to preserve that behavior.
Use `quran.verbs()` and `quran.nouns()` for individual morphological tokens.

On a token, `form` / `get_form()` is surface spelling; `verb_form` is the
morphological Roman numeral. Query `with_form("IV")` selects the morphological form.
Word-level `get_form()` retains its morphological meaning. Use token queries when
all chained conditions must match a single stem in a multi-stem word.

### Source-data distribution 0.4.0

Packages the verbatim QAC morphology 0.4 and Tanzil Uthmani text 1.1, a juz-boundary
table, an integrity manifest, and complete source-specific license notices.
See [Data provenance](docs/DATA_PROVENANCE.md) for exact hashes and terms.
