# Release process

Core and source data are independent distributions with separate versions and
licenses. The current first production release is core **0.4.0** and data **0.4.0**.
Never combine their artifacts or upload the historical `corpus/` directory.

## Trusted Publishing configuration

A new project can be created through a pending publisher; an initial token upload
is not required. In [PyPI account publishing](https://pypi.org/manage/account/publishing/),
configure these GitHub publishers:

| PyPI project | Owner | Repository | Workflow filename | Environment |
|---|---|---|---|---|
| `quran-processing-toolkit-qac-data` | `mhpanju` | `QuranProcessingToolkit` | `publish-data.yml` | `pypi` |
| `quran-processing-toolkit` | `mhpanju` | `QuranProcessingToolkit` | `publish-core.yml` | `pypi` |

If the project already exists, add the publisher in that project's publishing
settings. Workflow filenames are case-sensitive and exclude `.github/workflows/`.
See [PyPI's pending publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

The repository's `pypi` environment permits `data-v*` and `core-v*` tags and requires
review. Keep these protections. Approve the waiting deployment for the intended
release commit after its checks pass. No long-lived PyPI API token is needed.

For TestPyPI, configure the same two projects to trust `publish-test.yml` in the
`testpypi` environment. The **Publish to TestPyPI** workflow accepts `data` or `core`
via manual dispatch. A version already uploaded there cannot be uploaded again.

## Prepare a release

1. Update the core `__version__` in `quran_processing_toolkit/__init__.py` and, only
   when releasing data, the data `__version__` in its `src` package.
2. Keep the core's `data` extra pinned to the intended data version in `pyproject.toml`.
3. Update `CHANGELOG.md`, README, API reference, guides, and examples to match.
4. Review the diff, including licensing boundaries and source hashes.
5. Merge the release commit to `master` after CI passes.

The original source bytes, derived transformation version, and canonical digest
must remain unchanged unless a separate source/interpretation change is reviewed.

## Local checks and artifacts

```bash
python -m pip install -e packages/quran_processing_toolkit_qac_data
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy quran_processing_toolkit packages/quran_processing_toolkit_qac_data/src
python -m unittest discover -s tests -v
python -m quran_processing_toolkit.build --check
python -m quran_processing_toolkit validate

# Use a new output directory for each release to avoid stale uploads.
python -m build --outdir /tmp/qpt-release/core
python -m build packages/quran_processing_toolkit_qac_data --outdir /tmp/qpt-release/data
python -m twine check --strict /tmp/qpt-release/core/* /tmp/qpt-release/data/*
```

Inspect wheel and sdist contents: the core must not contain Quran text, morphology,
translations, caches, or generated research results. Both distributions must include
their declared license files. Install built wheels in a fresh virtual environment
outside the checkout and run `quran-toolkit validate` and `quran-rebuild --check`.
The README and AI-guide starting examples run in the documentation test suite.

## Publish data before core

Example for 0.4.0; substitute reviewed versions for later releases:

```bash
git tag -a data-v0.4.0 -m "Release source data 0.4.0" <release-commit>
git push origin data-v0.4.0
```

The tag runs the full CI matrix on Python 3.10–3.14, builds wheel and sdist, checks
metadata, and requires exact tag/version agreement. A separate job publishes those
artifacts after environment review. Wait for success and verify the data project on
PyPI before publishing the core:

```bash
git tag -a core-v0.4.0 -m "Release toolkit 0.4.0" <release-commit>
git push origin core-v0.4.0
```

Then install from **production PyPI** in a new environment outside the checkout:

```bash
python -m venv /tmp/qpt-pypi-smoke
/tmp/qpt-pypi-smoke/bin/python -m pip install --index-url https://pypi.org/simple \
  "quran-processing-toolkit[data]==0.4.0"
cd /tmp
/tmp/qpt-pypi-smoke/bin/quran-toolkit stats
/tmp/qpt-pypi-smoke/bin/quran-toolkit validate
/tmp/qpt-pypi-smoke/bin/quran-rebuild --check
```

The manual **Verify production PyPI release** (`verify-pypi.yml`) workflow repeats
the public-index installation on a GitHub runner. Supply the published core version;
it checks the installed API, release documentation examples, corpus validation, and
deterministic rebuild outside the checkout. Use it when local network/DNS issues
prevent a reliable download.

Confirm installed versions, execute a morphology query, and check the project-page
README and documentation links. Create GitHub release notes from `CHANGELOG.md`.

Published versions/files cannot be replaced. Fixes need a new version; do not delete
and reuse a released version or move a published release tag. A core-only update can
continue pinning an already published data version.
