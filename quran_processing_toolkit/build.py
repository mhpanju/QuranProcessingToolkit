"""Parse verbatim QAC data and deterministically derive the toolkit representation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

TRANSFORMATION_VERSION = 2
SUPPORTED_DERIVED_DIGESTS = {
    "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46": (
        "01505a13b870567b38bc510cf7ab185072f4f70c473f68b02088c9602826ca79"
    )
}

CONJUGATION = {
    "3MS": 1,
    "3MD": 2,
    "3MP": 3,
    "3FS": 4,
    "3FD": 5,
    "3FP": 6,
    "2MS": 7,
    "2MD": 8,
    "2MP": 9,
    "2FS": 10,
    "2FD": 11,
    "2FP": 12,
    "1S": 13,
    "1P": 14,
    "2D": 8,
}
GENDER = {
    "M": "MASC",
    "MP": "MASC",
    "MS": "MASC",
    "MD": "MASC",
    "F": "FEM",
    "FP": "FEM",
    "FS": "FEM",
    "FD": "FEM",
}
COUNT = {
    "MP": "PLURAL",
    "MD": "DUAL",
    "MS": "SINGULAR",
    "FP": "PLURAL",
    "FD": "DUAL",
    "FS": "SINGULAR",
}
TOKEN_ROLE = {"PREFIX": "PREFIX", "SUFFIX": "SUFFIX", "STEM": "STEM"}
ASPECT = {"PERF": "PERFECT", "IMPF": "IMPERFECT", "IMPV": "IMPERATIVE"}
TENSE = {"PERF": "PAST", "IMPF": "PRESENT", "IMPV": "IMPERATIVE"}

# Historical coordinate-specific interpretations of the source's ambiguous 2D label.
# These are an explicit toolkit overlay; the untouched source feature remains available.
CONJUGATION_OVERRIDES = {
    (4, 171, 4, 1): 9,
    (5, 77, 5, 1): 9,
    (28, 23, 15, 1): 5,
    (35, 41, 7, 1): 5,
    (66, 4, 2, 1): 11,
}


class SourceFormatError(ValueError):
    """Raised when a supposedly verbatim QAC source file is malformed."""


def parse_source_record(line: str, line_number: int) -> dict[str, Any]:
    """Parse one tab-separated QAC v0.4 record without changing its source values."""
    try:
        location, form, tag, feature_text = line.split("\t")
        chapter, verse, word, part = map(int, location.strip("()").split(":"))
    except ValueError as error:
        raise SourceFormatError(f"Malformed morphology record on line {line_number}") from error

    record: dict[str, Any] = {
        "CHAPTER": chapter,
        "VERSE": verse,
        "WORD": word,
        "WORD_PART": part,
        "TAG": tag,
        "FORM": form,
        "FEATURES": feature_text,
    }
    features: list[str] = []
    for feature in feature_text.split("|"):
        if ":" in feature:
            key, value = feature.split(":", 1)
            record[key] = value
        else:
            features.append(feature)
    record["SOURCE_FEATURES"] = features
    return record


def load_source_records(path: Path) -> list[dict[str, Any]]:
    """Load every annotation record from a verbatim QAC v0.4 text file."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.rstrip("\r\n")
            if line.startswith("("):
                records.append(parse_source_record(line, line_number))
    if not records:
        raise SourceFormatError(f"No morphology records found in {path}")
    return records


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Construct one derived record while retaining the original annotation fields."""
    result = {key: value for key, value in record.items() if key != "SOURCE_FEATURES"}
    features: list[str] = record["SOURCE_FEATURES"]
    address = (record["CHAPTER"], record["VERSE"], record["WORD"], record["WORD_PART"])

    verb_form = next(
        (
            feature[1:-1]
            for feature in features
            if feature.startswith("(") and feature.endswith(")")
        ),
        None,
    )
    if verb_form is None and record.get("POS") == "V":
        verb_form = "I"
    if verb_form is not None:
        if len(record.get("ROOT", "")) == 4:
            verb_form = "r" + verb_form
        result["VERB_FORM"] = verb_form

    for feature in features:
        if feature in CONJUGATION:
            result["CONJUGATE"] = CONJUGATION[feature]
            break
    if address in CONJUGATION_OVERRIDES:
        result["CONJUGATE"] = CONJUGATION_OVERRIDES[address]

    for case in ("GEN", "NOM", "ACC"):
        if case in features:
            result["CASE"] = case
            break
    if record.get("MOOD") == "SUBJ":
        result["CASE"] = "ACC"
    elif record.get("MOOD") == "JUS":
        result["CASE"] = "JUS"
    elif "IMPF" in features and "CASE" not in result:
        result["CASE"] = "NOM"
    elif "IMPV" in features:
        result["CASE"] = "MABNI"

    for feature in features:
        if feature in TOKEN_ROLE:
            result["TOKEN_ROLE"] = TOKEN_ROLE[feature]
            break
    if "3D" in features:
        result["PRON"] = "3D"

    for source_value, aspect in ASPECT.items():
        if source_value in features:
            result["ASPECT"] = aspect
            result["TENSE"] = TENSE[source_value]
            break

    if record.get("POS") == "V":
        result["VOICE"] = "PASSIVE" if "PASS" in features else "ACTIVE"

    for feature in features:
        if feature in GENDER:
            result["GENDER"] = GENDER[feature]
            break
    for feature in features:
        if feature in COUNT:
            result["COUNT"] = COUNT[feature]
            break
    if "PCPL" in features:
        if "ACT" in features:
            result["DERIVED_NOUN"] = "VERB_SUBJECT"
        elif "PASS" in features:
            result["DERIVED_NOUN"] = "VERB_OBJECT"
    if "VN" in features:
        result["DERIVED_NOUN"] = "VERBAL_NOUN"
    if "INDEF" in features:
        result["DEFINITENESS"] = "INDEFINITE"
    if "P" in features:
        result["COUNT"] = "PLURAL"
        result["UNUSUAL_PLURAL_ORIGINALLY_P_FEATURE"] = True
    return result


def rebuild_records(source_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive convenience fields for every parsed source record in order."""
    return [normalize_record(record) for record in source_records]


def canonical_records_bytes(records: list[dict[str, Any]]) -> bytes:
    """Return the stable byte representation used for cache and reproducibility checks."""
    return json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def records_digest(records: list[dict[str, Any]]) -> str:
    """Return the SHA-256 of the canonical complete derived representation."""
    return hashlib.sha256(canonical_records_bytes(records)).hexdigest()


def write_records(records: list[dict[str, Any]], output: Path) -> None:
    """Atomically write derived records without touching the source data."""
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output.name + ".", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_records_bytes(records))
        os.replace(temporary_name, output)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


def main(argv: list[str] | None = None) -> int:
    """Run deterministic verification and/or write an explicit derived artifact."""
    from .source_data import default_data_directory, verify_data_directory

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--output", type=Path, help="Write derived JSON to this explicit path")
    parser.add_argument("--check", action="store_true", help="Verify source and derived records")
    arguments = parser.parse_args(argv)
    if not arguments.check and not arguments.output:
        parser.error("choose --check and/or --output")

    data_dir = arguments.data_dir or default_data_directory()
    manifest = verify_data_directory(data_dir)
    source = manifest["sources"]["morphology"]
    records = rebuild_records(load_source_records(data_dir / source["filename"]))
    if len(records) != source["records"]:
        print(f"Derived record count differs: {len(records):,} != {source['records']:,}")
        return 1
    digest = records_digest(records)
    if arguments.check:
        expected = SUPPORTED_DERIVED_DIGESTS.get(source["sha256"])
        if expected is None or digest != expected:
            print(f"Derived digest mismatch: {digest} != {expected or 'unsupported source'}")
            return 1
        print(
            f"Verified source {source['sha256']} and deterministically derived "
            f"{len(records):,} records ({digest})"
        )
    if arguments.output:
        write_records(records, arguments.output)
        print(f"Wrote {len(records):,} locally derived records to {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
