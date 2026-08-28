"""Rank verb forms used by present-tense verbs."""

from quran_processing_toolkit import load_quran

quran = load_quran()
present_verbs = quran.verbs.with_tense("PRES")

for form, count in present_verbs.most_common_forms():
    print(form, count)
