# Source-preserving interpretation decisions

The upstream source files are never changed. This document records interpretation
decisions made by the runtime transformation and remaining questions.

## Resolved in transformation version 2

1. **Aspect and tense are distinct.** Original `PERF`, `IMPF`, and `IMPV` features are
   retained. They derive `ASPECT=PERFECT|IMPERFECT|IMPERATIVE`; the convenience tense
   values are `PAST`, `PRESENT`, and `IMPERATIVE`. This corrects the historical
   perfect/present and imperfect/past reversal without altering the source.

2. **Passive finite verbs remain passive.** A finite verb carrying source feature
   `PASS` derives `VOICE=PASSIVE`. The 1,140 affected records are validated. Other
   finite verbs derive `VOICE=ACTIVE`.

3. **Redundant derived TSVs were removed.** The incomplete roots TSV and the lemma,
   transliteration, and no-diacritics TSVs are neither runtime inputs nor published
   artifacts. Their information is queried from the verified source model instead.

4. **Verbal nouns are explicit.** Source feature `VN` derives
   `DERIVED_NOUN=VERBAL_NOUN`, rather than sharing the passive-participle label
   `VERB_OBJECT`.

## Explicit compatibility overlays

5. **Five `2D` coordinates retain historical interpretations.** Most source `2D`
   values map to conjugation 8. Five addresses derive 5, 9, or 11 through an explicit
   coordinate overlay. The original `2D` feature remains visible, so this choice can be
   revisited without changing data.

6. **`3D` remains visible in both layers.** Sixteen source `3D` features remain in
   `source_features`; the convenience record additionally exposes `PRON=3D` for
   compatibility.

## Remaining API questions

7. **Canonical form terminology.** The API exposes `VERB_FORM` as `word.baab` for
   convenience. Traditional use of “baab” can be narrower than Roman-numeral derived
   forms, especially for Form I. A future API may define these concepts separately.

8. **Multi-stem summaries.** There are 486 multi-stem words. The API retains every
   stem and returns multiple roots, lemmas, parts of speech, or forms when appropriate.
   It does not choose a canonical stem without an explicit linguistic rule.
