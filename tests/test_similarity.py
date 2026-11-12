from __future__ import annotations

import unittest
from itertools import combinations, product

from quran_processing_toolkit import (
    Verse,
    VerseAddress,
    chapter_name,
    compare_verses,
    load_quran,
    split_surface_words,
)
from quran_processing_toolkit.chapter_names import CHAPTERS


def verse(number, text):
    return Verse(VerseAddress(2, number), [], text, None)


class SimilarityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quran = load_quran()

    def test_chapter_names_and_counts(self):
        self.assertEqual(chapter_name(2), "al-Baqarah")
        self.assertEqual(self.quran.chapter(2).name_arabic, "البقرة")
        self.assertEqual(self.quran.chapter(2).name_english, "The Cow")
        self.assertEqual(self.quran.verse(113, 2).get_chapter_name(), "al-Falaq")
        self.assertEqual(self.quran.chapter(2).get_name("ARABIC"), chapter_name(2, "arabic"))
        self.assertEqual(sum(row[3] for row in CHAPTERS), 6236)
        for chapter in self.quran.chapters:
            self.assertEqual(len(chapter.verses), CHAPTERS[chapter.number - 1][3])
        for invalid in (0, 115, -1, True, 1.5):
            with self.assertRaises(ValueError):
                chapter_name(invalid)
        with self.assertRaises(ValueError):
            chapter_name(1, "unsupported")

    def test_surface_words_do_not_normalize(self):
        self.assertEqual(split_surface_words(" a  ۗ bۚ c ", ignore_pause_marks=True), ("a", "b", "c"))
        self.assertEqual(split_surface_words("a ۗ b"), ("a", "ۗ", "b"))
        self.assertEqual(split_surface_words("a\tb c"), ("a\tb", "c"))
        self.assertNotEqual(split_surface_words("e\u0301"), split_surface_words("\u00e9"))
        self.assertNotEqual(split_surface_words("إِلَى"), split_surface_words("الى"))
        v = verse(1, "a ۗ b")
        self.assertEqual(v.surface_words(ignore_pause_marks=True), ("a", "b"))
        self.assertEqual(v.get_arabic(), "a ۗ b")

    def test_pair_orientation_and_ambiguity(self):
        a, b = verse(1, "a b"), verse(2, "b a")
        matches = compare_verses(a, b)
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.kind, "shift")
        self.assertEqual(match.verses, (a, b))
        self.assertEqual((match.word_a, match.position_a, match.position_b), ("a", 1, 2))
        self.assertEqual(compare_verses(b, a).all(), matches.all())
        self.assertFalse(compare_verses(a, a))
        self.assertFalse(compare_verses(a, verse(3, "a b")))
        addition = compare_verses(verse(4, "a x a"), verse(5, "a a"))[0]
        self.assertEqual(addition.verse_a.verse, 5)
        self.assertEqual((addition.word_a, addition.word_b, addition.position_b), (None, "x", 2))

    def test_pairwise_single_words_and_pause_marks(self):
        self.assertEqual(compare_verses(verse(1, "a"), verse(2, "b"))[0].kind, "substitution")
        self.assertEqual(compare_verses(verse(1, "a"), verse(2, "a b"))[0].kind, "addition")
        self.assertFalse(compare_verses(verse(1, "a ۗ b"), verse(2, "a b"), ignore_pause_marks=True))

    def test_exhaustive_pairwise_matches_independent_edit_oracle(self):
        sequences = [p for n in range(1, 5) for p in product(("a", "b", "c"), repeat=n)]
        samples = [verse(i, " ".join(sequence)) for i, sequence in enumerate(sequences, 1)]
        samples.append(verse(121, "a b"))  # identical text at another address remains distinct
        expected = set()
        for left, right in combinations(samples, 2):
            a, b = left.surface_words(), right.surface_words()
            key = (left.verse, right.verse)
            if len(a) + 1 == len(b) and any(b[:i] + b[i + 1 :] == a for i in range(len(b))):
                expected.add(("addition", key))
            if len(b) + 1 == len(a) and any(a[:i] + a[i + 1 :] == b for i in range(len(a))):
                expected.add(("addition", key))
            if len(a) != len(b) or a == b:
                continue
            if sum(x != y for x, y in zip(a, b, strict=True)) == 1:
                expected.add(("substitution", key))
            for source, target in ((a, b), (b, a)):
                for i in range(len(source)):
                    for j in range(i + 1, len(source)):
                        moved = list(source)
                        moved.insert(j, moved.pop(i))
                        if tuple(moved) == target:
                            expected.add(("shift", key))
        matches = [match for a, b in combinations(samples, 2) for match in compare_verses(a, b)]
        actual = {(m.kind, tuple(sorted((m.verse_a.verse, m.verse_b.verse)))) for m in matches}
        self.assertEqual(actual, expected)
        self.assertEqual(len(matches), len(actual))
        for match in matches:
            a, b = match.verse_a.surface_words(), match.verse_b.surface_words()
            if match.kind == "shift":
                moved = list(a)
                moved.insert(match.position_b - 1, moved.pop(match.position_a - 1))
                self.assertLess(match.position_a, match.position_b)
                self.assertEqual(tuple(moved), b)

    def test_canonical_examples_and_no_bulk_search_api(self):
        import quran_processing_toolkit as toolkit

        self.assertFalse(hasattr(toolkit, "find_verse_pairs"))
        self.assertFalse(hasattr(self.quran, "find_verse_pairs"))
        shift = compare_verses(
            self.quran.verse(23, 83), self.quran.verse(27, 68), ignore_pause_marks=True
        )[0]
        self.assertEqual(str(shift.verse_a.address), "27:68")
        self.assertEqual(str(shift.verse_b.address), "23:83")
        addition = compare_verses(
            self.quran.verse(3, 51), self.quran.verse(43, 64), ignore_pause_marks=True
        )[0]
        self.assertEqual(addition.kind, "addition")
        self.assertEqual(addition.word_b, "هُوَ")


if __name__ == "__main__":
    unittest.main()
