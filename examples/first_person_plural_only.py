"""Find roots used in first-person plural but not first-person singular verbs."""

from quran_processing_toolkit import load_quran

quran = load_quran()

plural = quran.verbs.with_person(1).with_number("PLURAL")
singular = quran.verbs.with_person(1).with_number("SINGULAR")
plural_only_roots = plural.roots() - singular.roots()

print("Roots:", ", ".join(sorted(plural_only_roots)))
print("\nExample occurrences in Buckwalter:")
plural.with_any_root(plural_only_roots).show("buckwalter", limit=20)
