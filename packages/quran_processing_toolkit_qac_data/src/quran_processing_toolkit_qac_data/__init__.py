"""Paths and metadata for the verbatim Quranic source-data distribution."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

__version__ = "0.4.0"


def data_directory() -> Path:
    """Return the installed directory containing the verbatim source files."""
    return Path(str(files(__package__) / "data"))


def manifest() -> dict[str, Any]:
    """Return a copy of the source provenance and hash manifest."""
    path = data_directory() / "manifest.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


__all__ = ["data_directory", "manifest"]
