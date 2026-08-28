"""Structural, provenance, and semantic validation of installed source data."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .build import SUPPORTED_DERIVED_DIGESTS, load_source_records, rebuild_records, records_digest
from .corpus import QuranCorpus
from .source_data import DataError, default_data_directory, verify_data_directory


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str


def validate_corpus(data_dir: Path | None = None) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    path = data_dir or default_data_directory()
    try:
        manifest = verify_data_directory(path)
        corpus = QuranCorpus(path)
    except DataError as error:
        return (ValidationIssue("error", "source-data", str(error)),)

    expected_counts = {"chapters": 114, "verses": 6236, "words": 77429, "tokens": 128219}
    for field, expected in expected_counts.items():
        actual = len(getattr(corpus, field))
        if actual != expected:
            issues.append(
                ValidationIssue(
                    "error", "unexpected-count", f"{field}: {actual}, expected {expected}"
                )
            )
    if len(corpus.juzs) != 30 or sum(len(juz) for juz in corpus.juzs) != len(corpus.verses):
        issues.append(
            ValidationIssue(
                "error", "juz-coverage", "Juz boundaries do not cover 30 complete parts"
            )
        )

    source = manifest["sources"]["morphology"]
    records = rebuild_records(load_source_records(path / source["filename"]))
    digest = records_digest(records)
    expected_digest = SUPPORTED_DERIVED_DIGESTS.get(source["sha256"])
    if digest != expected_digest:
        issues.append(
            ValidationIssue(
                "error",
                "derived-digest",
                f"derived morphology SHA-256 is {digest}, expected {expected_digest}",
            )
        )

    aspects = Counter(record.get("ASPECT") for record in records if record.get("POS") == "V")
    expected_aspects = Counter(PERFECT=9150, IMPERFECT=8330, IMPERATIVE=1876)
    if aspects != expected_aspects:
        issues.append(ValidationIssue("error", "verb-aspects", f"verb aspects differ: {aspects}"))
    passive = sum(
        record.get("VOICE") == "PASSIVE" for record in records if record.get("POS") == "V"
    )
    if passive != 1140:
        issues.append(
            ValidationIssue("error", "passive-verbs", f"passive finite verbs: {passive} != 1140")
        )
    return tuple(issues)
