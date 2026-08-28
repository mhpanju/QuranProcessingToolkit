from __future__ import annotations

import unittest

from quran_processing_toolkit import QuerySet, load_quran, normalize_arabic


class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quran = load_quran()

    def test_general_text_predicates(self) -> None:
        self.assertTrue(self.quran.words[1, 1, 1].starts_with("ب"))
        self.assertTrue(
            self.quran.verses[114, 6].ends_with(
                "س", strip_diacritics=True, strip_quranic_marks=True
            )
        )
        self.assertGreater(len(self.quran.verses.contains("مُوسَى")), 0)

    def test_normalization_is_opt_in(self) -> None:
        self.assertEqual(normalize_arabic("إِلَىٰ", strip_diacritics=True, normalize_alif=True), "الى")

    def test_morphology_queries(self) -> None:
        present = self.quran.verbs.where(tense="PRES")
        self.assertGreater(len(present), 0)
        self.assertIn("I", present.count_by("baab"))
        self.assertEqual(present.where(baab="I").first().baab_name, "Thulathy Mujarrad")
        first_plural = self.quran.verbs.where(person=1, grammatical_number="PLURAL")
        self.assertGreater(len(first_plural), 0)

    def test_inverted_word_index(self) -> None:
        words = self.quran.find_words(root="ktb")
        self.assertGreater(len(words), 0)
        self.assertTrue(all("ktb" in word.roots for word in words))

    def test_longest_run_is_generic(self) -> None:
        result = QuerySet([1, 2, 4, 6, 3, 8]).longest_run(lambda value: value % 2 == 0)
        self.assertEqual(result.all(), (2, 4, 6))
        without_mim_or_nun = self.quran.longest_word_sequence(
            lambda word: not word.contains("م") and not word.contains("ن")
        )
        self.assertGreater(len(without_mim_or_nun), 0)


if __name__ == "__main__":
    unittest.main()
