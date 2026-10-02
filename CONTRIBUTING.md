# Contributing

Contributions are welcome, particularly readable query helpers, documentation, tests,
performance improvements with measured benefit, and source-preserving morphology
interpretations.

## Non-negotiable data rule

Do not edit Quranic text, morphology records, tags, roots, lemmas, or other material
annotations in place.

If an upstream record appears wrong:

1. record the exact address and source feature text;
2. explain the linguistic evidence;
3. propose either a documented runtime interpretation or an upstream report;
4. add a focused test; and
5. obtain explicit project approval before changing any semantic overlay.

Verbatim third-party source files must remain byte-identical to their declared hashes.
Any accepted transformation change must increment `TRANSFORMATION_VERSION`, update the
canonical derived digest, and be documented in
[`docs/PROPOSED_CORPUS_CHANGES.md`](docs/PROPOSED_CORPUS_CHANGES.md).

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Required checks

```bash
ruff check .
ruff format --check .
mypy quran_processing_toolkit packages/quran_processing_toolkit_qac_data/src
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

Also run every relevant script in `examples/`. CI repeats checks across supported
Python versions, builds both distributions, runs `twine check`, and smoke-installs the
wheels outside the checkout.

## API design principles

Good additions make a family of questions easier rather than encoding one answer.

Prefer:

- `starts_with(prefix)` over `starts_with_alif()`;
- `with_number("plural")` over `first_person_plural_verbs()`;
- `in_verse(chapter, verse)` over a helper named after one famous verse; and
- composable immutable results over functions that print immediately.

Named helpers are valuable when they remove routine lambdas or knowledge of internal
uppercase fields. They should delegate to the generic query machinery where practical
so named and advanced queries behave consistently.

Public text input should remain ASCII-friendly through Buckwalter. New categorical
arguments should normally be case-insensitive and accept obvious source abbreviations.
Roots, lemmas, surface forms, and raw features remain case-sensitive because character
case may be meaningful.

## Documentation expectations

Any public API change should update:

- its Python docstring;
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md);
- the relevant conceptual guide or cookbook example; and
- tests demonstrating expected behavior and failure cases.

Comments should explain invariants, source mismatches, or non-obvious decisions—not
translate straightforward Python line by line.

## Testing guidance

- Use canonical addresses for focused regression tests.
- Assert source fields and derived fields separately.
- Include multi-stem behavior when an aggregation API changes.
- Test both Arabic and Buckwalter for text operations.
- Test aliases and canonical categorical values.
- Avoid copying copyrighted translation text into fixtures; authored placeholder text
  is sufficient.
- Never weaken source hash or derived digest verification to make a test pass.

## Performance changes

Measure at least:

- a fresh uncached process load;
- a derived-disk-cache process load;
- a repeated in-process `load_quran()` call; and
- the target query on the complete corpus.

Report Python version, platform, command, and whether `orjson` was installed. Avoid
performance changes that discard source traceability, alter public ordering, or turn
simple imports into mandatory compiled dependencies.

## Compatibility

The public package supports Python 3.10 and newer. Preserve:

- Quranic 1-based semantic indexing;
- normal zero-based positions inside filtered QuerySets;
- deterministic corpus order;
- source-feature visibility;
- the separate code/data distribution boundary; and
- user-installed rather than bundled translation files.

Deprecated compatibility aliases may remain when inexpensive, but new documentation
should teach the clearest current API.

## Releases

Core and data distributions have independent versions and tags. Do not publish either
manually with a long-lived token. Follow [`docs/RELEASING.md`](docs/RELEASING.md),
publishing the data distribution before a core release whose `data` extra pins it.
