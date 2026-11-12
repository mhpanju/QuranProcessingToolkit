"""Export every verb occurrence, indexed by six exact morphology criteria.

Run: python examples/export_verb_index.py /path/to/verbs.json
The source is ASCII-only; the output preserves readable Arabic verse text.
"""

import argparse
import json

from quran_processing_toolkit import __version__, load_quran


def build_index():
    """Collect verb references, storing each full Arabic verse only once."""
    quran = load_quran()
    document = {
        "schema_version": 1,
        "package_version": __version__,
        "provenance": quran.provenance(),
        "key_order": ["root", "tense", "form", "conjugation", "voice", "nun_emphasis"],
        "occurrence_count": 0,
        "verses": {},
        "index": {},
    }
    for verb in quran.verbs():
        fields = (verb.root, verb.tense, verb.verb_form, verb.conjugation, verb.voice)
        if any(value is None for value in fields):
            raise ValueError(f"Missing verb annotation at {verb.address}")
        keys = [
            verb.root,
            verb.tense,
            verb.verb_form,
            str(verb.conjugation),
            verb.voice,
            "with_nun" if verb.has_nun_of_emphasis() else "without_nun",
        ]
        address = f"{verb.chapter}:{verb.verse}"
        if address not in document["verses"]:
            document["verses"][address] = quran.verse(verb.chapter, verb.verse).get_arabic()
        bucket = document["index"]
        for key in keys[:-1]:
            bucket = bucket.setdefault(key, {})
        bucket.setdefault(keys[-1], []).append(
            {
                "address": address,
                "word_index": verb.word,
                "token_part": verb.part,
            }
        )
        document["occurrence_count"] += 1
    return document


def find_verbs(document, *, root, tense, form, conjugation, voice, nun_emphasis):
    """Look up all six criteria and attach the full Arabic verse to each hit."""
    keys = [
        root,
        tense.upper(),
        form,
        str(conjugation),
        voice.upper(),
        "with_nun" if nun_emphasis else "without_nun",
    ]
    bucket = document["index"]
    for key in keys:
        if key not in bucket:
            return []
        bucket = bucket[key]
    return [{"arabic": document["verses"][hit["address"]], **hit} for hit in bucket]


def main():
    """Write the index and demonstrate an exact lookup without corpus reload."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="verbs.json")
    args = parser.parse_args()
    document = build_index()
    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(document, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(f"Saved {document['occurrence_count']:,} verb occurrences to {args.output}")
    matches = find_verbs(
        document,
        root="qwl",
        tense="PAST",
        form="I",
        conjugation=1,
        voice="ACTIVE",
        nun_emphasis=False,
    )
    print(f"Example lookup: {len(matches)} occurrences")
    print(json.dumps(matches[:1], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
