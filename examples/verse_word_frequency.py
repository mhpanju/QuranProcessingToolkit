"""Export per-verse مِن and repeated-word rankings from the local QAC corpus.

Run from the repository root: PYTHONPATH=. python3 examples/verse_word_frequency.py
The outputs are UTF-8 TSV files in results/. The corpus may also be selected by
setting QURAN_PROCESSING_TOOLKIT_DATA as supported by the toolkit.

مِن is identified by QAC lemma 'min' and tag P, counting morphological segments
(including attached conjunctions and contractions). Repeated words are complete
QAC-aligned written words, with Arabic diacritics removed, not morphological
lemmas; attached prefixes/suffixes remain part of the word. This deliberately
merges homographs differing only in diacritics. All tied verses are reported.
Rankings break ties by verse address or Unicode spelling, respectively, to give
exactly 10 and 30 rows; ties at the cutoff are therefore not all included.
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

from quran_processing_toolkit import load_quran

OUTPUT = Path(__file__).resolve().parents[1] / "results"


def write_tsv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main():
    quran = load_quran(disk_cache=False)
    min_counts = Counter(
        (token.chapter, token.verse) for token in quran.prepositions() if token.lemma == "min"
    )
    min_rows = sorted(min_counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    maxima = {}
    verses_at_max = defaultdict(list)
    for verse in quran.verses:
        counts = Counter(
            word.normalized_text("arabic", strip_diacritics=True, strip_quranic_marks=True)
            for word in verse.words
        )
        for word, count in counts.items():
            if count > maxima.get(word, 0):
                maxima[word] = count
                verses_at_max[word] = [verse.address]
            elif count == maxima[word]:
                verses_at_max[word].append(verse.address)
    word_rows = sorted(maxima.items(), key=lambda item: (-item[1], item[0]))[:30]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_tsv(
        OUTPUT / "top_min_verses.tsv",
        ("rank", "verse", "occurrences"),
        (
            (rank, f"{address[0]}:{address[1]}", count)
            for rank, (address, count) in enumerate(min_rows, 1)
        ),
    )
    write_tsv(
        OUTPUT / "top_repeated_words.tsv",
        ("rank", "word", "max_occurrences", "verses"),
        (
            (rank, word, count, ", ".join(str(address) for address in verses_at_max[word]))
            for rank, (word, count) in enumerate(word_rows, 1)
        ),
    )


if __name__ == "__main__":
    main()
