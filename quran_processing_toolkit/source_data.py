"""Discovery, integrity verification, and local caching for source data."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

SUPPORTED_SOURCE_SHA256 = {
    "quranic-corpus-morphology-0.4.txt": (
        "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
    ),
    "uthmani-numbered.txt": ("7919b8a04d63b164273a743e0d2538a9704582dd72c2f49e8d557b77dd819e40"),
    "juzz-breakdown.tsv": ("ee3e1e72be6bebe5e0dea0571b2a03a16ebc1fc3ae33397576341a529fb087f2"),
}


class DataError(RuntimeError):
    """Base class for source discovery, integrity, and corpus-loading failures."""


class DataPackageNotInstalledError(DataError):
    """Raised when no override, installed provider, or checkout data is available."""


class DataIntegrityError(DataError):
    """Raised when source bytes or deterministic derivation fail verification."""


def default_data_directory() -> Path:
    """Find an override, installed data provider, or monorepo source package."""
    override = os.environ.get("QURAN_PROCESSING_TOOLKIT_DATA")
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_dir():
            raise DataError(f"Configured source-data directory does not exist: {path}")
        return path

    try:
        from quran_processing_toolkit_qac_data import data_directory

        return data_directory()
    except ImportError:
        pass

    checkout = (
        Path(__file__).resolve().parents[1]
        / "packages"
        / "quran_processing_toolkit_qac_data"
        / "src"
        / "quran_processing_toolkit_qac_data"
        / "data"
    )
    if (checkout / "manifest.json").is_file():
        return checkout
    raise DataPackageNotInstalledError(
        "Quran source data is not installed. Install "
        "quran-processing-toolkit-qac-data or pass data_dir=... to load_quran()."
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(data_dir: Path) -> dict[str, Any]:
    """Load and minimally validate the source-data manifest schema."""
    path = data_dir / "manifest.json"
    try:
        with path.open(encoding="utf-8") as handle:
            manifest: dict[str, Any] = json.load(handle)
    except FileNotFoundError as error:
        raise DataIntegrityError(f"Source-data manifest is missing: {path}") from error
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("sources"), dict):
        raise DataIntegrityError(f"Unsupported source-data manifest: {path}")
    return manifest


def verify_data_directory(data_dir: Path) -> dict[str, Any]:
    """Verify every source file against its declared byte size and SHA-256."""
    data_dir = data_dir.expanduser().resolve()
    manifest = load_manifest(data_dir)
    for name, source in manifest["sources"].items():
        path = data_dir / source["filename"]
        expected_digest = SUPPORTED_SOURCE_SHA256.get(path.name)
        if expected_digest is None or source["sha256"] != expected_digest:
            raise DataIntegrityError(
                f"Unsupported declared SHA-256 for {path.name}: {source['sha256']}"
            )
        if not path.is_file():
            raise DataIntegrityError(f"Missing {name} source file: {path}")
        actual_size = path.stat().st_size
        if actual_size != source["bytes"]:
            raise DataIntegrityError(
                f"Size mismatch for {path.name}: {actual_size} != {source['bytes']}"
            )
        actual_digest = _sha256(path)
        if actual_digest != source["sha256"]:
            raise DataIntegrityError(
                f"SHA-256 mismatch for {path.name}: {actual_digest} != {source['sha256']}"
            )
    return manifest


def default_cache_directory() -> Path:
    """Return the environment override or platform-style user cache directory."""
    override = os.environ.get("QURAN_PROCESSING_TOOLKIT_CACHE")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "quran-processing-toolkit"


def _read_cached_records(path: Path, expected_digest: str) -> list[dict[str, Any]] | None:
    try:
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            return None
        try:
            import orjson  # type: ignore[import-not-found]

            records: list[dict[str, Any]] = orjson.loads(payload)
        except ImportError:
            records = json.loads(payload)
        return records
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None


def _write_cache(path: Path, payload: bytes) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=path.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
            os.replace(temporary_name, path)
        except BaseException:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name)
            raise
    except OSError:
        # Read-only homes and restricted execution environments should still load.
        return


def load_normalized_records(
    data_dir: Path,
    *,
    disk_cache: bool = True,
    cache_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Verify source bytes, then load or deterministically derive normalized records."""
    from .build import (
        SUPPORTED_DERIVED_DIGESTS,
        TRANSFORMATION_VERSION,
        canonical_records_bytes,
        load_source_records,
        rebuild_records,
    )

    manifest = verify_data_directory(data_dir)
    source = manifest["sources"]["morphology"]
    try:
        expected_digest = SUPPORTED_DERIVED_DIGESTS[source["sha256"]]
    except KeyError as error:
        raise DataIntegrityError(
            f"Unsupported morphology source SHA-256: {source['sha256']}"
        ) from error
    cache_path = (cache_dir or default_cache_directory()) / (
        f"morphology-v{TRANSFORMATION_VERSION}-{source['sha256'][:16]}.json"
    )
    if disk_cache:
        cached = _read_cached_records(cache_path, expected_digest)
        if cached is not None and len(cached) == source["records"]:
            return cached, manifest

    records = rebuild_records(load_source_records(data_dir / source["filename"]))
    if len(records) != source["records"]:
        raise DataIntegrityError(
            f"Derived {len(records)} morphology records; expected {source['records']}"
        )
    payload = canonical_records_bytes(records)
    actual_digest = hashlib.sha256(payload).hexdigest()
    if actual_digest != expected_digest:
        raise DataIntegrityError(
            f"Derived morphology digest mismatch: {actual_digest} != {expected_digest}"
        )
    if disk_cache:
        _write_cache(cache_path, payload)
    return records, manifest
