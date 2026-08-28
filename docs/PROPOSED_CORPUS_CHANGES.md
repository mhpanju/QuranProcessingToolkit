# Proposed corpus changes requiring approval

No item in this document has been applied to the corpus. These findings are separated
from structural code changes so they can be reviewed individually.

## High-confidence candidates

1. **Review the finite-verb tense names.** In the current processed corpus, all 9,150
   base records containing `PERF` become `TENSE=PRES`, while all 8,330 containing
   `IMPF` become `TENSE=PAST`. This may be deliberate project terminology, but the
   mapping is the reverse of conventional perfect/past and imperfect/present naming.
   A non-destructive alternative is to preserve `ASPECT=PERFECT|IMPERFECT|IMPERATIVE`
   and derive a separately documented tense convenience field.

2. **Review passive finite verbs.** There are 1,140 finite verb records with the base
   feature `PASS`; the processed corpus labels each `VOICE=ACTIVE`. Passive participles
   are separately represented as `DERIVED_NOUN=VERB_OBJECT`, so this proposal concerns
   finite verbs only.

3. **Add the missing roots TSV row.** `quran-roots.tsv` has 6,235 verse rows and omits
   verse 114:6, while the other verse-level TSV files contain all 6,236 verses.

## Interpretation questions

4. **Review five `2D` coordinate overrides.** Most base `2D` values normalize to
   conjugation 8, while five addresses receive 5, 9, or 11. These overrides are now
   explicit in `build.py`, but their linguistic justification should be documented.

5. **Review `3D` storage.** Sixteen base `3D` features are moved into top-level
   `PRON=3D`, whereas other conjugation labels normally become numeric `CONJUGATE`
   values. This may correctly describe a pronoun rather than a verb conjugation, but it
   should be intentional and documented.

6. **Choose canonical form terminology.** The current API exposes `VERB_FORM` as
   `word.baab` for convenience. Traditional use of “baab” can be narrower than the
   Roman-numeral derived forms, especially for Form I. Consider exposing both a precise
   `verb_form` and a separately defined `baab` rather than treating them as aliases.

7. **Decide how multi-stem word summaries should behave.** There are 486 multi-stem
   words. The new API retains all stems and returns multiple values when appropriate;
   any rule choosing one canonical root, lemma, POS, or form would be a material
   interpretation and should be approved.

## Derived-data reproducibility

8. The JSON morphology transformation is now reproducible. The generation histories
   for `quran-full-translit.tsv`, `quran-lemmas.tsv`, `quran-roots.tsv`, and
   `quran-no-diacritics.tsv` are not yet fully recovered. They should eventually be
   regenerated from declared inputs or removed from the release if redundant.
