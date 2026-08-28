"""Find nouns with three-letter roots containing two or more weak letters."""

from quran_processing_toolkit import load_quran

quran = load_quran()

weak_nouns = quran.nouns.with_root_length(3).with_minimum_root_letter_count("Awy", 2)

print("Occurrences:", len(weak_nouns))
weak_nouns.show("arabic", limit=20)
