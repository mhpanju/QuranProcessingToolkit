"""Search in ASCII, then narrow morphology results to one chapter and verse."""

from quran_processing_toolkit import load_quran

quran = load_quran()

print("Verses containing the Buckwalter spelling muwsaY:")
quran.search("muwsaY").show("arabic", limit=5)

print("\nPassive verbs in chapter 2:")
quran.verbs.in_chapter(2).with_voice("passive").show("buckwalter", limit=10)

print("\nMorphological segments of the first word in 2:255:")
for token in quran.tokens.in_word(2, 255, 1):
    print(token.address, token.form, token.tag, token.source_feature_text)
