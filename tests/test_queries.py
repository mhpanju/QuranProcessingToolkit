from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO

from quran_processing_toolkit import (
    QuerySet,
    load_quran,
    normalize_arabic,
    normalize_buckwalter,
)


class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quran = load_quran()

    def test_general_text_predicates(self) -> None:
        self.assertTrue(self.quran.words[1, 1, 1].starts_with("ب"))
        self.assertTrue(self.quran.words[1, 1, 1].starts_with("b"))
        self.assertTrue(self.quran.words[1, 1, 1].contains_letter("s"))
        self.assertTrue(
            self.quran.verses[114, 6].ends_with(
                "س", strip_diacritics=True, strip_quranic_marks=True
            )
        )
        self.assertGreater(len(self.quran.verses.contains("مُوسَى")), 0)

    def test_normalization_is_opt_in(self) -> None:
        self.assertEqual(normalize_arabic("إِلَىٰ", strip_diacritics=True, normalize_alif=True), "الى")
        self.assertEqual(normalize_buckwalter("bisomi", strip_diacritics=True), "bsm")

    def test_ascii_input_automatically_uses_buckwalter(self) -> None:
        automatic = self.quran.verses.ends_with("n", strip_diacritics=True)
        explicit = self.quran.verses.ends_with(
            "n", representation="transliteration", strip_diacritics=True
        )
        self.assertEqual(automatic.all(), explicit.all())
        self.assertGreater(len(automatic), 0)

    def test_morphology_queries(self) -> None:
        present = self.quran.verbs.where(tense="PRES")
        self.assertGreater(len(present), 0)
        self.assertIn("I", present.count_by("baab"))
        self.assertEqual(present.where(baab="I").first().baab_name, "Thulathy Mujarrad")
        first_plural = self.quran.verbs.where(person=1, grammatical_number="PLURAL")
        self.assertGreater(len(first_plural), 0)

    def test_named_morphology_helpers(self) -> None:
        present = self.quran.verbs.with_tense("PRES")
        self.assertEqual(present.all(), self.quran.verbs.where(tense="PRES").all())
        self.assertEqual(present.with_form("I").first().get_form(), "I")
        self.assertEqual(present.most_common_forms()[0][0], "I")

        plural = self.quran.verbs.with_person(1).with_number("PLURAL")
        singular = self.quran.verbs.with_person(1).with_number("SINGULAR")
        plural_only_roots = plural.roots() - singular.roots()
        self.assertTrue(plural_only_roots)
        self.assertTrue(plural.with_any_root(plural_only_roots))

        weak = self.quran.nouns.with_root_length(3).with_minimum_root_letter_count("Awy", 2)
        self.assertGreater(len(weak), 0)

    def test_output_representations(self) -> None:
        verse = self.quran.get_verse(1, 1)
        self.assertEqual(verse.get_text("buckwalter"), verse.get_transliteration())
        self.assertEqual(verse.get_text("english"), verse.get_translation())
        self.assertEqual(verse.get_text("arabic"), verse.get_arabic())

        output = StringIO()
        with redirect_stdout(output):
            self.quran.verses.show("english", limit=2, include_address=False)
        self.assertEqual(len(output.getvalue().splitlines()), 2)

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

        friendly = self.quran.longest_word_sequence_without_letters("mn", strip_diacritics=True)
        self.assertGreater(len(friendly), 0)
        self.assertTrue(
            all(word.contains_no_letters("mn", strip_diacritics=True) for word in friendly)
        )


if __name__ == "__main__":
    unittest.main()
