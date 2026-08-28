"""Corpus validation that separates structural errors from reviewable warnings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .build import compare_records, load_records, rebuild_records
from .corpus import QuranCorpus, _read_numbered_text


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str


def validate_corpus(data_dir: Path | None = None) -> tuple[ValidationIssue, ...]:
    corpus = QuranCorpus(data_dir)
    issues: list[ValidationIssue] = []
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

    data_path = corpus.data_dir
    roots = _read_numbered_text(data_path / "quran-roots.tsv", delimiter="\t")
    missing_roots = set(corpus.verses.keys()) - {
        (address.chapter, address.verse) for address in roots
    }
    if missing_roots:
        issues.append(
            ValidationIssue(
                "warning", "roots-coverage", f"quran-roots.tsv misses {sorted(missing_roots)}"
            )
        )

    base = load_records(data_path / "quran-morphologies_base.json")
    current = load_records(data_path / "quran-morphologies.json")
    rebuild_problems = compare_records(rebuild_records(base), current)
    if rebuild_problems:
        issues.append(ValidationIssue("error", "rebuild-mismatch", rebuild_problems[0]))
    return tuple(issues)
