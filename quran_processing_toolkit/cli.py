"""Command-line inspection, text search, provenance, and validation utilities."""

from __future__ import annotations

import argparse
from pathlib import Path

from .corpus import QuranCorpus
from .validation import validate_corpus


def main(argv: list[str] | None = None) -> int:
    """Run the ``quran-toolkit`` command and return a process exit status."""
    parser = argparse.ArgumentParser(prog="quran-toolkit")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--translation", type=Path, help="User-supplied numbered translation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats", help="Show corpus object counts")
    commands.add_parser("sources", help="Show source provenance and licenses")
    commands.add_parser("validate", help="Validate structure and reproducibility")
    word_parser = commands.add_parser("word", help="Inspect a word at chapter:verse:word")
    word_parser.add_argument("address")
    search_parser = commands.add_parser("search", help="Search Arabic or Buckwalter text")
    search_parser.add_argument("text")
    search_parser.add_argument("--level", choices=("verse", "word"), default="verse")
    search_parser.add_argument(
        "--representation",
        choices=("auto", "arabic", "buckwalter", "transliteration", "translation", "english"),
        default="auto",
    )
    search_parser.add_argument("--strip-diacritics", action="store_true")
    search_parser.add_argument("--strip-quranic-marks", action="store_true")
    search_parser.add_argument("--normalize-alif", action="store_true")
    search_parser.add_argument("--normalize-ya", action="store_true")
    search_parser.add_argument("--remove-spaces", action="store_true")
    search_parser.add_argument("--limit", type=int, default=20)
    arguments = parser.parse_args(argv)

    if arguments.command == "validate":
        issues = validate_corpus(arguments.data_dir)
        if not issues:
            print("Corpus validation passed")
            return 0
        for issue in issues:
            print(f"{issue.severity.upper()} [{issue.code}] {issue.message}")
        return int(any(issue.severity == "error" for issue in issues))

    corpus = QuranCorpus.load(arguments.data_dir, translation=arguments.translation)
    if arguments.command == "stats":
        for label, count in corpus.stats().items():
            print(f"{label}: {count:,}")
        return 0
    if arguments.command == "search":
        if arguments.limit < 0:
            parser.error("--limit cannot be negative")
        results = corpus.search(
            arguments.text,
            level=arguments.level,
            representation=arguments.representation,
            strip_diacritics=arguments.strip_diacritics,
            strip_quranic_marks=arguments.strip_quranic_marks,
            normalize_alif=arguments.normalize_alif,
            normalize_ya=arguments.normalize_ya,
            remove_spaces=arguments.remove_spaces,
        )
        results.show(
            arguments.representation if arguments.representation != "auto" else "arabic",
            limit=arguments.limit,
        )
        print(f"matches: {len(results):,}")
        return 0
    if arguments.command == "sources":
        for source in corpus.provenance()["sources"].values():
            print(f"{source['title']} {source.get('version', '')}".rstrip())
            print(f"  SHA-256: {source['sha256']}")
            print(f"  license: {source['license']}")
            if source.get("official_url"):
                print(f"  source: {source['official_url']}")
        return 0
    try:
        chapter, verse, word = map(int, arguments.address.strip("()").split(":"))
    except ValueError:
        parser.error("word address must have the form chapter:verse:word")
    item = corpus.word(chapter, verse, word)
    print(f"address: {item.address}")
    print(f"arabic: {item.arabic_text}")
    print(f"transliteration: {item.transliteration}")
    print(f"parts of speech: {item.parts_of_speech}")
    print(f"roots: {item.roots}")
    print(f"lemmas: {item.lemmas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
