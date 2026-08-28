"""Deterministically rebuild the current processed morphology from its base."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from .corpus import default_data_directory

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
TOKEN_ROLE = {"PREFIX": "PREFIX", "SUFFIX": "SUFFIX", "STEM": "STEM", "sSTEM": "STEM"}

# Historical, coordinate-specific interpretation of otherwise ambiguous 2D labels.
# These reproduce the existing processed corpus; they are documented for review rather
# than silently presented as general rules.
CONJUGATION_OVERRIDES = {
    (4, 171, 4, 1): 9,
    (5, 77, 5, 1): 9,
    (28, 23, 15, 1): 5,
    (35, 41, 7, 1): 5,
    (66, 4, 2, 1): 11,
}


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Apply the exact historical normalization used by the checked-in corpus."""
    result = {key: value for key, value in record.items() if key != "features"}
    features: list[str] = record["features"]
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
    elif "IMPF" in features:
        result["CASE"] = "NOM"
    elif "IMPV" in features:
        result["CASE"] = "MABNI"

    for feature in features:
        if feature in TOKEN_ROLE:
            result["TOKEN_ROLE"] = TOKEN_ROLE[feature]
            break
    if "3D" in features:
        result["PRON"] = "3D"

    # Names intentionally reproduce the current modified corpus exactly. Potential
    # terminology changes are tracked separately and require corpus-owner approval.
    if "IMPF" in features:
        result["TENSE"] = "PAST"
    elif "PERF" in features:
        result["TENSE"] = "PRES"
    elif "IMPV" in features:
        result["TENSE"] = "IMPV"

    if record.get("POS") == "V":
        result["VOICE"] = "ACTIVE"

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
        result["DERIVED_NOUN"] = "VERB_OBJECT"
    if "INDEF" in features:
        result["DEFINITENESS"] = "INDEFINITE"
    if "P" in features:
        result["COUNT"] = "PLURAL"
        result["UNUSUAL_PLURAL_ORIGINALLY_P_FEATURE"] = True
    return result


def rebuild_records(base_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_record(record) for record in base_records]


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def compare_records(generated: list[dict[str, Any]], expected: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    if len(generated) != len(expected):
        problems.append(
            f"record count differs: generated={len(generated)}, expected={len(expected)}"
        )
    for index, (actual, wanted) in enumerate(zip(generated, expected, strict=False)):
        if actual != wanted or tuple(actual) != tuple(wanted):
            address = tuple(
                actual.get(field) for field in ("CHAPTER", "VERSE", "WORD", "WORD_PART")
            )
            differing = sorted(
                key for key in actual.keys() | wanted.keys() if actual.get(key) != wanted.get(key)
            )
            if not differing:
                differing = ["field order"]
            problems.append(f"record {index} {address} differs in {differing}")
            if len(problems) >= 20:
                problems.append("additional differences omitted")
                break
    return problems


def write_records(records: list[dict[str, Any]], output: Path) -> None:
    """Atomically write normalized records without risking a partial corpus file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output.name + ".", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=1)
        os.replace(temporary_name, output)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data_directory())
    parser.add_argument("--output", type=Path, help="Write rebuilt JSON to this explicit path")
    parser.add_argument("--check", action="store_true", help="Compare with quran-morphologies.json")
    arguments = parser.parse_args(argv)
    base = load_records(arguments.data_dir / "quran-morphologies_base.json")
    generated = rebuild_records(base)
    if arguments.check:
        expected = load_records(arguments.data_dir / "quran-morphologies.json")
        problems = compare_records(generated, expected)
        if problems:
            print("Rebuild differs from the checked-in corpus:")
            print("\n".join(f"- {problem}" for problem in problems))
            return 1
        print(f"Exact record match: {len(generated):,} records")
    if arguments.output:
        write_records(generated, arguments.output)
        print(f"Wrote {len(generated):,} records to {arguments.output}")
    if not arguments.check and not arguments.output:
        parser.error("choose --check and/or --output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
