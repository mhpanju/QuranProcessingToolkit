"""Command-line entry points for corpus inspection and validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from .corpus import QuranCorpus
from .validation import validate_corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quran-toolkit")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--translation", type=Path, help="User-supplied numbered translation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats", help="Show corpus object counts")
    commands.add_parser("sources", help="Show source provenance and licenses")
    commands.add_parser("validate", help="Validate structure and reproducibility")
    word_parser = commands.add_parser("word", help="Inspect a word at chapter:verse:word")
    word_parser.add_argument("address")
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
        for label in ("chapters", "verses", "words", "tokens", "juzs"):
            print(f"{label}: {len(getattr(corpus, label)):,}")
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
