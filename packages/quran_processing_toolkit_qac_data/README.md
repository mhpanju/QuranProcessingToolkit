# Quran Processing Toolkit — QAC data

This is the separately licensed source-data provider for
[`quran-processing-toolkit`](https://github.com/mhpanju/QuranProcessingToolkit).
Most users install both distributions through:

```bash
python -m pip install "quran-processing-toolkit[data]"
```

## Contents

- verbatim Quranic Arabic Corpus morphology version 0.4;
- verbatim Tanzil Uthmani Quran text version 1.1;
- the toolkit's Apache-2.0 juz-boundary table;
- an integrity and provenance manifest; and
- complete source-specific legal notices.

The morphology and Quran text are not licensed under Apache-2.0. Their embedded
copyright blocks are retained unchanged, and their complete terms are installed in the
distribution's `licenses` metadata directory.

No translation is included. Users may supply one separately to the core toolkit,
subject to that translation's terms.

## What the package does

It exposes only paths and metadata:

```python
from quran_processing_toolkit_qac_data import data_directory, manifest

print(data_directory())
print(manifest())
```

Parsing, integrity enforcement, runtime transformations, text alignment, and the query
API belong to the core package. Keeping this provider deliberately small makes the
code/data licensing boundary visible and auditable.

The core loader verifies supported hashes independently rather than trusting the
installed manifest alone. It may create derived JSON in the user's cache directory,
but it never modifies files inside this distribution.

See the repository's
[`docs/DATA_PROVENANCE.md`](https://github.com/mhpanju/QuranProcessingToolkit/blob/master/docs/DATA_PROVENANCE.md)
for filenames, byte sizes, hashes, upstream URLs, and transformation details.
