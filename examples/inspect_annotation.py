"""Compare exact source annotation with documented convenience properties."""

from quran_processing_toolkit import load_quran

quran = load_quran()
token = quran.token(2, 255, 1, 1)

print("Address:", token.address)
print("Buckwalter form:", token.form)
print("Source tag:", token.tag)
print("Exact source features:", token.source_feature_text)
print("Non-keyed source features:", token.source_features)
print("Root:", token.root)
print("Lemma:", token.lemma)
print("Case:", token.case)
print("Complete retained/derived record:")
for key, value in sorted(token.data.items()):
    print(f"  {key}: {value}")
