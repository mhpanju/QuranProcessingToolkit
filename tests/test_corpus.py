from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
