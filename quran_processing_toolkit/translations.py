"""Explicit, hash-verified translation downloads and user-installed text layers.

Nothing is downloaded at import or ordinary corpus load. Translations are never
bundled in either distribution or written into the installed data directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import warnings
from collections.abc import Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .chapter_names import CHAPTERS
from .source_data import DataError, default_cache_directory
from .text import TranslationNotAvailableError

Address = tuple[int, int]
_MAX_BYTES = 8 * 1024 * 1024


class TranslationDownloadError(DataError):
    """An explicit translation download or offline-cache lookup failed."""


class TranslationIntegrityError(DataError):
    """Downloaded or cached translation bytes differ from the pinned source hash."""


class TranslationLicenseWarning(UserWarning):
    """A translation download has third-party usage terms distinct from the code."""


class _HTTPSOnlyRedirect(HTTPRedirectHandler):
    """Reject a transport downgrade before urllib sends the redirected request."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme.lower() != "https":
            raise TranslationDownloadError("Refusing a non-HTTPS translation redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_translation(request: Request, *, timeout: float):
    return build_opener(_HTTPSOnlyRedirect()).open(request, timeout=timeout)


@dataclass(frozen=True)
class TranslationSource:
    """One curated external translation, including a reproducible content pin."""

    identifier: str
    name: str
    translator: str
    language: str
    url: str
    sha256: str
    terms_url: str
    terms: str


_SOURCES = (
    TranslationSource(
        "en.qarai",
        "Qarai",
        "Ali Quli Qarai",
        "English",
        "https://tanzil.net/trans/en.qarai",
        "1207b98ee7ae47891b4dd01b608416da2278820acf54cdaf3943d0a6f9823fdf",
        "https://tanzil.net/trans/",
        "Tanzil provides translations for non-commercial purposes only; other use "
        "requires permission from the translator or publisher. Check the source terms "
        "before use or redistribution. The Python code's Apache license does not apply.",
    ),
)


def translation_sources() -> tuple[TranslationSource, ...]:
    """List the curated download catalog without contacting the network."""
    return _SOURCES


@dataclass(frozen=True)
class TranslationCoverage:
    """Coverage of a requested set of verse addresses by a translation layer."""

    total: int
    translated: int
    missing: tuple[Address, ...]

    @property
    def complete(self) -> bool:
        """Return whether every requested verse has nonempty translation text."""
        return not self.missing

    @property
    def fraction(self) -> float:
        """Return translated/total, treating an empty requested set as complete."""
        return self.translated / self.total if self.total else 1.0


@dataclass(frozen=True)
class Translation:
    """An immutable user-installed translation with text and source metadata.

    Use load_translation() or download_translation() rather than constructing it
    directly. Texts retain their supplied content, including embedded newlines.
    """

    path: Path
    texts: Mapping[Address, str]
    metadata: Mapping[str, str]
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", self.path.expanduser().resolve())
        object.__setattr__(self, "texts", MappingProxyType(dict(self.texts)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        identity = json.dumps(
            (sorted(self.texts.items()), sorted(self.metadata.items())), ensure_ascii=False
        ).encode("utf-8")
        object.__setattr__(self, "fingerprint", hashlib.sha256(identity).hexdigest())

    def coverage(self, addresses: Iterable[Address] | None = None) -> TranslationCoverage:
        """Check all 6,236 canonical verses, or a caller-supplied address subset."""
        expected = set(addresses) if addresses is not None else _canonical_addresses()
        missing = tuple(sorted(expected - self.texts.keys()))
        return TranslationCoverage(len(expected), len(expected) - len(missing), missing)

    def require_complete(self, addresses: Iterable[Address] | None = None) -> None:
        """Raise TranslationNotAvailableError when any requested verse is missing."""
        coverage = self.coverage(addresses)
        if coverage.missing:
            sample = ", ".join(f"{c}:{v}" for c, v in coverage.missing[:8])
            raise TranslationNotAvailableError(
                f"Translation missing for {len(coverage.missing)} verses: {sample}"
            )


def _canonical_addresses() -> set[Address]:
    return {(c, v) for c, row in enumerate(CHAPTERS, 1) for v in range(1, row[3] + 1)}


def _parse(payload: bytes, *, json_format: bool) -> dict[Address, str]:
    text = payload.decode("utf-8-sig")
    rows: list[tuple[Any, Any, Any]] = []
    if json_format:
        data = json.loads(text)
        for surah in data["surahs"]:
            for verse in surah["verses"]:
                rows.append((surah["number"], verse["number"], verse["text"]))
    else:
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split("|", 2)
            if len(fields) != 3:
                raise ValueError(
                    f"Malformed translation line {number}: expected chapter|verse|text"
                )
            rows.append((fields[0], fields[1], fields[2]))
    canonical = _canonical_addresses()
    result = {}
    for chapter, verse_number, value in rows:
        # Reject lossy conversions such as JSON floats or boolean verse numbers.
        if isinstance(chapter, bool) or isinstance(verse_number, bool):
            raise ValueError("Translation addresses must be integer verse numbers")
        if not str(chapter).isdigit() or not str(verse_number).isdigit():
            raise ValueError("Translation addresses must be integer verse numbers")
        address = int(chapter), int(verse_number)
        if address not in canonical:
            raise ValueError(f"Invalid translation address {address[0]}:{address[1]}")
        if address in result:
            raise ValueError(f"Duplicate translation verse {address[0]}:{address[1]}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Empty translation at {address[0]}:{address[1]}")
        result[address] = value
    if not result:
        raise ValueError("Translation contains no verse records")
    return result


def load_translation(
    path: str | os.PathLike[str],
    *,
    name: str | None = None,
    translator: str | None = None,
    language: str | None = None,
) -> Translation:
    """Load numbered UTF-8 text or structured surahs/verses JSON without a network call.

    Local files may be partial. Metadata supplied by the caller is descriptive,
    not a certification of authorship. The SHA-256 identifies the exact file bytes.
    """
    path = Path(path).expanduser().resolve()
    payload = path.read_bytes()
    metadata = {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest()}
    metadata.update(
        {
            k: v
            for k, v in (("name", name), ("translator", translator), ("language", language))
            if v is not None
        }
    )
    return Translation(path, _parse(payload, json_format=path.suffix.lower() == ".json"), metadata)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
        os.replace(temporary, path)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)


def download_translation(
    identifier: str = "en.qarai",
    *,
    cache_dir: str | os.PathLike[str] | None = None,
    offline: bool = False,
    refresh: bool = False,
    timeout: float = 30.0,
) -> Translation:
    """Explicitly download a curated translation, verify its pin, and cache verbatim bytes.

    The default cache is the toolkit user cache's translations/ subdirectory, never
    either installed package. A verified cached copy is reused without networking.
    offline=True forbids networking; refresh=True deliberately re-fetches the SAME
    pinned revision, not an unreviewed upstream update. Unknown IDs fail locally.
    Third-party usage terms are retained in metadata and warned about before fetching.
    """
    identifier = {"qarai": "en.qarai"}.get(identifier.lower(), identifier.lower())
    source = next((s for s in _SOURCES if s.identifier == identifier), None)
    if source is None:
        raise ValueError(f"Unknown translation {identifier!r}; see translation_sources()")
    if offline and refresh:
        raise ValueError("offline=True and refresh=True cannot be combined")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    directory = (
        Path(cache_dir).expanduser().resolve()
        if cache_dir
        else default_cache_directory() / "translations"
    )
    path = directory / f"{source.identifier}-{source.sha256}.txt"
    manifest_path = path.with_suffix(".metadata.json")
    downloaded_at = ""
    if path.exists() and not refresh:
        payload = path.read_bytes()
        if manifest_path.exists():
            with suppress(ValueError, OSError, TypeError, AttributeError):
                downloaded_at = str(
                    json.loads(manifest_path.read_text(encoding="utf-8")).get("downloaded_at", "")
                )
    elif offline:
        raise TranslationDownloadError(f"No offline cached translation at {path}")
    else:
        warnings.warn(
            f"{source.translator}: {source.terms} {source.terms_url}",
            TranslationLicenseWarning,
            stacklevel=2,
        )
        request = Request(source.url, headers={"User-Agent": "quran-processing-toolkit"})
        try:
            with _open_translation(request, timeout=timeout) as response:
                if not response.geturl().startswith("https://"):
                    raise TranslationDownloadError("Refusing a non-HTTPS translation redirect")
                payload = response.read(_MAX_BYTES + 1)
        except (URLError, OSError) as error:
            raise TranslationDownloadError(f"Could not download {source.url}: {error}") from error
        downloaded_at = datetime.now(timezone.utc).isoformat()
    if len(payload) > _MAX_BYTES:
        raise TranslationDownloadError("Translation exceeds the 8 MiB size limit")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != source.sha256:
        raise TranslationIntegrityError(
            f"Translation SHA-256 mismatch for {source.identifier}: {digest} != {source.sha256}. "
            "An upstream change requires a reviewed catalog update; cached corruption can "
            "be repaired with refresh=True."
        )
    texts = _parse(payload, json_format=False)
    if texts.keys() != _canonical_addresses():
        raise TranslationIntegrityError("Curated translation does not cover all 6,236 verses")
    metadata = {
        "identifier": source.identifier,
        "name": source.name,
        "translator": source.translator,
        "language": source.language,
        "source_url": source.url,
        "terms_url": source.terms_url,
        "terms": source.terms,
        "sha256": digest,
        "downloaded_at": downloaded_at,
        "path": str(path),
    }
    if not path.exists() or refresh:
        _atomic_write(path, payload)
        _atomic_write(manifest_path, json.dumps(metadata, ensure_ascii=False, indent=2).encode())
    return Translation(path, texts, metadata)
