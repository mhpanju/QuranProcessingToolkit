from __future__ import annotations

import unittest
from pathlib import Path

from quran_processing_toolkit import QuranCorpus, load_quran


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quran = load_quran(cache=False)

    def test_canonical_counts(self) -> None:
        self.assertEqual(len(self.quran.chapters), 114)
        self.assertEqual(len(self.quran.verses), 6236)
        self.assertEqual(len(self.quran.words), 77429)
        self.assertEqual(len(self.quran.tokens), 128219)

    def test_semantic_indexes_are_one_based(self) -> None:
        self.assertEqual(self.quran.chapters[1].number, 1)
        self.assertEqual(self.quran.chapters[1].verses[1].address.chapter, 1)
        self.assertEqual(self.quran.verses[2, 255].address.verse, 255)
        self.assertEqual(self.quran.words[1, 1, 1].arabic_text, "بِسْمِ")
        with self.assertRaises(KeyError):
            _ = self.quran.chapters[0]

    def test_juzs_cover_every_verse_without_sentinel(self) -> None:
        self.assertEqual(len(self.quran.juzs), 30)
        self.assertEqual(sum(len(juz) for juz in self.quran.juzs), 6236)
        self.assertEqual(self.quran.juzs[30].start.chapter, 78)
        with self.assertRaises(KeyError):
            _ = self.quran.juzs[31]

    def test_multi_stem_verbs_remain_verbs(self) -> None:
        word = self.quran.words[2, 90, 1]
        self.assertTrue(word.is_multi_stem)
        self.assertTrue(word.is_verb())
        self.assertIn("bAs", word.roots)

    def test_cached_loader_reuses_instance(self) -> None:
        self.assertIs(QuranCorpus.load(), QuranCorpus.load())

    def test_source_annotation_is_retained(self) -> None:
        token = self.quran.tokens[1, 1, 1, 1]
        self.assertEqual(token.source_feature_text, "PREFIX|bi+")
        self.assertEqual(token.source_features, ("PREFIX", "bi+"))

    def test_provenance_exposes_verified_source_hashes(self) -> None:
        morphology = self.quran.provenance()["sources"]["morphology"]
        self.assertEqual(morphology["version"], "0.4")
        self.assertEqual(
            morphology["sha256"],
            "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46",
        )
        self.assertIn("Quranic Arabic Corpus", self.quran.licenses()[0]["source"])

    def test_translation_is_user_supplied(self) -> None:
        self.assertFalse(self.quran.verses[1, 1].has_translation)
        translation = Path(__file__).parent / "fixtures" / "translation-sample.txt"
        translated = load_quran(translation=translation, cache=False)
        self.assertEqual(
            translated.verses[1, 1].get_translation(),
            "Sample English translation for testing.",
        )
        self.assertFalse(translated.verses[1, 3].has_translation)


if __name__ == "__main__":
    unittest.main()
