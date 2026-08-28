"""Find the longest within-verse word sequence with neither mim nor nun."""

from quran_processing_toolkit import load_quran

quran = load_quran()
longest = quran.longest_word_sequence_without_letters("mn", strip_diacritics=True)

print("Words:", len(longest))
print("Arabic:")
longest.show("arabic", include_address=False)
print("\nBuckwalter:")
longest.show("buckwalter", include_address=False)
