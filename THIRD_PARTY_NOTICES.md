# Third-party notices in the core distribution

Python code is licensed under Apache-2.0. The conventional Arabic and English
chapter labels and canonical verse counts in `chapter_names.py` are selected from
Tanzil Quran Metadata v1.0:

- Copyright `(C) 2008-2009 Tanzil.info`
- Source: https://tanzil.net/res/text/metadata/quran-data.xml
- Documentation: https://tanzil.net/docs/quran_metadata
- Source SHA-256: `8867c1d88191472adec9db694b3cd9f135b1a2ef580574d32cf888dcb22c5c7a`
- Upstream declares `license="cc-by"` without a version in the source artifact.
  We retain that declaration as `LicenseRef-Tanzil-Metadata-CC-BY`, rather than
  asserting a specific version that the artifact does not identify.

Only chapter labels and verse counts are selected; the complete XML, navigation
partitions, Quran text, and translations are not included in the core distribution.
ASCII transliterations use the project's conventional labels. The table is not a
modification of the separately licensed Quranic text or morphology annotations.

See `licenses/TANZIL-METADATA-NOTICE.txt` for the packaged attribution notice.
Downloaded translations have their own terms, retained alongside their cached source
bytes. No translation is distributed with either Python package.
