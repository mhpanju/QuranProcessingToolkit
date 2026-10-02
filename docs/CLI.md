# Command-line reference

Installing the core package creates two commands:

- `quran-toolkit` for inspection, search, provenance, and validation;
- `quran-rebuild` for deterministic morphology rebuilds.

The data package must be installed unless `--data-dir` points at a supported source
directory.

## Global input options

Global options appear before the subcommand:

```bash
quran-toolkit \
  --data-dir /path/to/data \
  --translation /path/to/translation.txt \
  stats
```

- `--data-dir PATH`: override source-data discovery.
- `--translation PATH`: load a user-supplied numbered translation.

Environment variables provide the same defaults:

- `QURAN_PROCESSING_TOOLKIT_DATA`
- `QURAN_PROCESSING_TOOLKIT_TRANSLATION`
- `QURAN_PROCESSING_TOOLKIT_CACHE`

## `stats`

```bash
quran-toolkit stats
```

Prints chapter, verse, word, token, juz, verb-word, and noun-word counts.

## `search`

```bash
quran-toolkit search muwsaY
quran-toolkit search muwsaY --level word --limit 10
quran-toolkit search "مُوسَى" --level verse
```

Options:

- `--level verse|word` (default: `verse`)
- `--representation auto|arabic|buckwalter|transliteration|translation|english`
  (default: `auto`)
- `--strip-diacritics`
- `--strip-quranic-marks`
- `--normalize-alif`
- `--normalize-ya`
- `--remove-spaces`
- `--limit N` (default: 20)

Results are printed in Arabic with addresses when representation inference is
automatic. An explicit Buckwalter or translation representation prints that same
representation. Translation search also requires global `--translation PATH`. The
final line reports the complete match count even when display is limited.

## `word`

```bash
quran-toolkit word 2:255:1
```

Prints the address, Arabic surface form, Buckwalter transliteration, parts of speech,
roots, and lemmas for one word. Addresses are 1-based.

## `sources`

```bash
quran-toolkit sources
```

Prints each installed source's title, version, SHA-256, license identifier, and official
URL. Source integrity is verified before output.

## `validate`

```bash
quran-toolkit validate
```

Runs source, structure, deterministic transformation, aspect, passive voice, and juz
coverage checks. A clean result prints `Corpus validation passed` and exits with status
0. Any error prints a machine-readable issue code and exits nonzero.

## `quran-rebuild`

Verify complete deterministic derivation:

```bash
quran-rebuild --check
```

Write a local derived representation for inspection:

```bash
quran-rebuild --check --output /tmp/quran-derived.json
```

Options:

- `--data-dir PATH`: use a specific supported source directory.
- `--check`: compare record count and canonical derived SHA-256.
- `--output PATH`: atomically write canonical derived JSON to an explicit path.

At least one of `--check` and `--output` is required. The command never overwrites or
modifies installed source data. The output is a local derived artifact and should not
be mistaken for an upstream source file.

## Module invocation

The main CLI is also available as:

```bash
python -m quran_processing_toolkit stats
```

The deterministic builder is available as:

```bash
python -m quran_processing_toolkit.build --check
```
