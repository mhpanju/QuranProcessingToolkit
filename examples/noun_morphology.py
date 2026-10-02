"""Use named nominal morphology filters without lambdas or raw field names."""

from quran_processing_toolkit import load_quran

quran = load_quran()

plural_feminine_nouns = quran.nouns.with_number("plural").with_gender("f")
verbal_nouns = quran.nouns.with_derived_noun("verbal_noun")

print("Plural feminine noun occurrences:", len(plural_feminine_nouns))
plural_feminine_nouns.show("arabic", limit=10)

print("\nVerbal noun occurrences:", len(verbal_nouns))
verbal_nouns.show("buckwalter", limit=10)
