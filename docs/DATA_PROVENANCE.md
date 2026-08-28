# Data provenance and licensing

The project intentionally separates Apache-2.0 Python code from source data carrying
different terms.

## Distribution boundary

`quran-processing-toolkit` contains code only. It does not contain Quranic annotation,
Quran text, or a translation.

`quran-processing-toolkit-qac-data` contains the source files used by the loader. Its
wheel includes complete upstream notices and accurately identifies its mixed terms;
the Apache license applies only to the project's packaging code, manifest, and
juz-boundary table.

## Quranic Arabic Corpus morphology

The data distribution contains `quranic-corpus-morphology-0.4.txt` unchanged. Its
complete QAC and Tanzil copyright blocks remain embedded in the file.

- Version: Quranic Arabic Corpus morphology 0.4
- Copyright: Copyright (C) 2011 Kais Dukes
- Official source and terms: https://corpus.quran.com/download/
- Bytes: 6,309,503
- Records: 128,219
- SHA-256: `a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46`

The checked-in artifact was compared across the `bnjasim/quranic-corpus` and
`cltk/arabic_morphology_quranic-corpus` public mirrors. The files were byte-for-byte
identical. Their locations are recorded in the installed manifest rather than being
presented as the copyright holder's official download service.

The toolkit parses this file and constructs convenience fields in memory. The source
feature column remains available through `Token.source_feature_text` and
`Token.source_features`. No normalized morphology file is redistributed.

## Tanzil Uthmani Quran text

The data distribution contains `uthmani-numbered.txt` unchanged, including its
complete footer notice.

- Version: Tanzil Quran Text (Uthmani) 1.1
- Copyright: Copyright (C) 2007-2024 Tanzil Project
- License: Creative Commons Attribution 3.0 with the embedded Tanzil terms
- Official source and terms: https://tanzil.net/download/ and
  https://tanzil.net/docs/Text_License
- Bytes: 1,396,080
- Verses: 6,236
- SHA-256: `7919b8a04d63b164273a743e0d2538a9704582dd72c2f49e8d557b77dd819e40`

Non-verse basmalas and selected pause marks are removed only from the in-memory view
needed to align morphology words. The installed source file is not changed.

## Translation

No translation is included in either distribution. Users may supply a numbered
translation to `load_quran(translation=...)`, subject to that translation's terms.
The previously bundled Ali Quli Qarai translation was removed because Tanzil describes
its translations as non-commercial unless separate permission is obtained:
https://tanzil.net/trans/

## Reproducibility

The installed `manifest.json` declares the exact filenames, versions, byte sizes,
SHA-256 hashes, upstream locations, license identifiers, and canonical counts.
`load_quran()` verifies the files before interpreting them.

Transformation version 2 maps the exact morphology source hash above to the canonical
derived-record SHA-256
`01505a13b870567b38bc510cf7ab185072f4f70c473f68b02088c9602826ca79`.
That mapping is tested and checked by `quran-rebuild --check`.

Derived caches are generated on the user's machine, keyed by both source hash and
transformation version, and are not part of either published distribution.
