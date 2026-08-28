"""Compare two verse endings using Buckwalter input only."""

from quran_processing_toolkit import load_quran

quran = load_quran()

ending_in_nun = quran.verses.ends_with("n", strip_diacritics=True)
ending_in_tanween_alif = quran.verses.ends_with("FA")

print("Ending in nun:", len(ending_in_nun))
print("Ending in fathah tanween plus alif:", len(ending_in_tanween_alif))

print("\nExamples in Arabic:")
ending_in_nun.show("arabic", limit=3)

print("\nExamples in Buckwalter:")
ending_in_tanween_alif.show("buckwalter", limit=3)
