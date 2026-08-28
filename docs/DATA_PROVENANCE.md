# Data provenance and scope

The repository contains code and several datasets with different origins and terms.
The top-level Apache-2.0 license applies to original project code; it does not relicense
third-party text, translations, or annotations.

## Morphology

- `quran-morphologies_base.json` is the machine-readable source representation used by
  this project, based on Quranic Arabic Corpus morphology version 0.4.
- `quran-morphologies.json` is this project's modified, normalized representation.
- The deterministic transformation is implemented in
  `quran_processing_toolkit/build.py`.
- `python -m quran_processing_toolkit.build --check` currently reproduces the
  processed JSON byte-for-byte from the base file.

The Quranic Arabic Corpus download page identifies Kais Dukes as the annotation
copyright holder and supplies its own GNU-license terms, attribution requirements,
and restrictions. Those upstream terms must be reviewed before redistribution or
commercial use of this project's modified representation:

https://corpus.quran.com/download/default.jsp

## Quran text

`uthmani-numbered.txt` is Tanzil Uthmani text. Its complete copyright and Creative
Commons Attribution 3.0 notice is retained at the end of that file. The toolkit removes
non-verse basmalas and selected pause marks only in memory to align its word objects;
the checked-in Quran text is unchanged.

https://tanzil.net/docs/Text_License

## Translation

`translation_qarai.txt` is Ali Quli Qarai's English translation as distributed by
Tanzil. Tanzil publishes translations under separate terms, including non-commercial
use unless additional permission is obtained:

https://tanzil.net/trans/

Applications should not assume that the Qarai translation is covered by Apache-2.0.

## Derived TSV files

The transliteration, lemma, root, and no-diacritics TSVs are derived from or closely
related to the source text and morphology. Their exact generator is not yet recovered.
They are retained unchanged and are not required by the new runtime loader.
