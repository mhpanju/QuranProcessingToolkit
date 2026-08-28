# Release process

The core and source data are independent distributions with independent versions and
licenses. Never combine their artifacts or upload the old `corpus/` directory.

## One-time configuration

1. Create `quran-processing-toolkit-qac-data` and `quran-processing-toolkit` on
   TestPyPI, then PyPI.
2. Configure each project to trust its corresponding GitHub Actions workflow and the
   `pypi` environment.
3. Protect the `pypi` environment with required review.
4. Configure equivalent publishers for the manual `publish-test.yml` workflow and
   the `testpypi` environment.

## Pre-release checks

Run from a clean checkout:

```bash
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy quran_processing_toolkit packages/quran_processing_toolkit_qac_data/src
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate
```

CI additionally builds both distributions, runs `twine check`, and installs the two
wheels into a clean environment outside the checkout.

## Versions and tags

- Data tags have the form `data-v0.4.0` and publish only the data distribution.
- Core tags have the form `core-v0.3.0` and publish only the core distribution.

The data package must be published first because the core package's optional `data`
extra refers to its exact version. Published files and versions cannot be replaced;
fixes require a new version such as `0.4.0.post1`.

Before a production tag, run the **Publish to TestPyPI** workflow manually for `data`
and then `core`. Install both resulting wheels from TestPyPI in a clean environment.

Before pushing a tag, confirm that it points to the reviewed commit and its version
matches the corresponding package metadata. The tag-triggered workflows use PyPI
Trusted Publishing and require no long-lived API token.
