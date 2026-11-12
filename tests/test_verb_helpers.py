from __future__ import annotations

import json
import unittest
from pathlib import Path

from examples.export_verb_index import build_index, find_verbs
from quran_processing_toolkit import QuerySet, Token, Word, WordAddress, load_quran


class VerbHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quran = load_quran()

    def test_shortcuts_are_ordered_cached_token_queries(self) -> None:
        selections = {
            "verbs": {"V"},
            "nouns": {"N"},
            "proper_nouns": {"PN"},
            "adjectives": {"ADJ"},
            "pronouns": {"PRON", "DEM", "REL"},
            "adverbs": {"T", "LOC"},
            "prepositions": {"P"},
            "conjunctions": {"CONJ", "SUB"},
            "nominals": {"N", "PN", "ADJ", "IMPN", "PRON", "DEM", "REL", "T", "LOC"},
            "particles": {
                "P",
                "EMPH",
                "IMPV",
                "PRP",
                "CONJ",
                "SUB",
                "ACC",
                "AMD",
                "ANS",
                "AVR",
                "CAUS",
                "CERT",
                "CIRC",
                "COM",
                "COND",
                "EQ",
                "EXH",
                "EXL",
                "EXP",
                "FUT",
                "INC",
                "INT",
                "INTG",
                "NEG",
                "PREV",
                "PRO",
                "REM",
                "RES",
                "RET",
                "RSLT",
                "SUP",
                "SUR",
                "VOC",
                "DET",
            },
        }
        for name, tags in selections.items():
            with self.subTest(shortcut=name):
                shortcut = getattr(self.quran, name)
                result = shortcut()
                self.assertIsInstance(result, QuerySet)
                self.assertIs(result, shortcut())
                self.assertEqual(
                    result.all(), tuple(token for token in self.quran.tokens if token.tag in tags)
                )
        self.assertEqual(len(self.quran.verbs()), 19356)
        self.assertEqual(len(self.quran.nouns()), 25136)
        self.assertEqual(
            len(self.quran.nominals())
            + len(self.quran.particles())
            + len(self.quran.verbs())
            + len(self.quran.tokens.with_tag("INL")),
            len(self.quran.tokens),
        )
        self.assertTrue(self.quran.prepositions().with_role("PREFIX"))
        self.assertTrue(self.quran.pronouns().with_role("SUFFIX"))

    def test_word_collections_keep_previous_semantics(self) -> None:
        for name, predicate in (("verb_words", Word.is_verb), ("noun_words", Word.is_noun)):
            selected = getattr(self.quran, name)
            self.assertIs(selected, getattr(self.quran, name))
            self.assertEqual(selected.all(), self.quran.words.filter(predicate).all())
        self.assertIn(self.quran.words[2, 90, 1], self.quran.verb_words)
        self.assertEqual(
            self.quran.verbs().most_common_forms(), self.quran.verb_words.most_common_forms()
        )
        stats = self.quran.stats()
        self.assertEqual(stats["verbs"], len(self.quran.verb_words))
        self.assertEqual(stats["nouns"], len(self.quran.noun_words))

    def test_nun_annotation_and_stem_ownership(self) -> None:
        verb = self.quran.tokens[2, 38, 6, 1]
        suffix = self.quran.tokens[2, 38, 6, 2]
        self.assertTrue(verb.has_nun_of_emphasis())
        self.assertTrue(self.quran.words[2, 38, 6].has_nun_of_emphasis())
        self.assertFalse(suffix.has_nun_of_emphasis())
        self.assertFalse(self.quran.tokens[2, 38, 6, 3].has_nun_of_emphasis())
        self.assertEqual(suffix.get("+n"), "EMPH")
        self.assertNotIn("_nun_of_emphasis", verb.data)

        # Independently reconstruct expectations from the untouched source column.
        expected = []
        for word in self.quran.words:
            stem = None
            for token in word.tokens:
                if token.role == "STEM":
                    stem = token
                elif (
                    token.role == "SUFFIX"
                    and "+n:EMPH" in token.source_feature_text.split("|")
                    and stem is not None
                    and stem.tag == "V"
                ):
                    expected.append(stem)
        emphatic = self.quran.verbs().with_nun_of_emphasis()
        self.assertEqual(emphatic.all(), tuple(expected))
        self.assertEqual(len(emphatic), 243)
        self.assertEqual(len(self.quran.verb_words.with_nun_of_emphasis()), 243)
        self.assertEqual(self.quran.tokens.with_nun_of_emphasis().all(), emphatic.all())

    def test_nun_filters_compose_and_partition(self) -> None:
        verbs = self.quran.verbs()
        absent = verbs.without_nun_of_emphasis()
        self.assertEqual(absent.all(), verbs.with_nun_of_emphasis(False).all())
        self.assertEqual(len(absent), 19113)
        self.assertEqual(len(absent) + len(verbs.with_nun_of_emphasis()), len(verbs))
        self.assertFalse(set(absent).intersection(verbs.with_nun_of_emphasis()))
        matches = (
            verbs.with_root("Aty")
            .with_tense("present")
            .with_form("I")
            .with_conjugation(1)
            .with_voice("active")
            .with_nun_of_emphasis()
        )
        self.assertEqual(
            [token.address_tuple[:3] for token in matches],
            [(2, 38, 6), (7, 35, 4), (20, 123, 9), (27, 21, 7), (29, 53, 8)],
        )
        self.assertFalse(QuerySet().with_nun_of_emphasis())
        self.assertFalse(self.quran.nouns().with_nun_of_emphasis())
        with self.assertRaises(TypeError):
            verbs.with_nun_of_emphasis("false")

    def test_multiple_stems_and_false_positives(self) -> None:
        def token(role, tag, **fields):
            return Token({"TOKEN_ROLE": role, "TAG": tag, **fields})

        prefix = token("PREFIX", "EMPH")
        first = token("STEM", "V", FORM="n")
        second = token("STEM", "V")
        suffix = token("SUFFIX", "EMPH", **{"+n": "EMPH"})
        word = Word(WordAddress(1, 1, 1), [prefix, first, second, suffix], "")
        self.assertFalse(prefix.has_nun_of_emphasis())
        self.assertFalse(first.has_nun_of_emphasis())
        self.assertTrue(second.has_nun_of_emphasis())
        self.assertTrue(word.has_nun_of_emphasis())

        # A new non-verb stem interrupts ownership too; ordinary nun is not emphatic.
        first = token("STEM", "V")
        noun = token("STEM", "N")
        word = Word(WordAddress(1, 1, 1), [first, noun, suffix], "")
        self.assertFalse(first.has_nun_of_emphasis())
        self.assertFalse(word.has_nun_of_emphasis())
        word = Word(WordAddress(1, 1, 1), [token("STEM", "V", FORM="n")], "")
        self.assertFalse(word.has_nun_of_emphasis())
        standalone = token("STEM", "V")
        self.assertFalse(standalone.has_nun_of_emphasis())

    def test_export_example_round_trip(self) -> None:
        document = json.loads(json.dumps(build_index(), ensure_ascii=False))
        self.assertEqual(document["occurrence_count"], 19356)
        matches = find_verbs(
            document,
            root="qwl",
            tense="PAST",
            form="I",
            conjugation=1,
            voice="ACTIVE",
            nun_emphasis=False,
        )
        self.assertEqual(len(matches), 530)
        self.assertEqual(matches[0]["address"], "2:30")
        self.assertEqual(matches[0]["word_index"], 2)
        self.assertEqual(matches[0]["arabic"], self.quran.verse(2, 30).get_arabic())
        self.assertEqual(matches[1]["word_index"], 23)
        self.assertEqual(
            find_verbs(
                document,
                root="no-such-root",
                tense="PAST",
                form="I",
                conjugation=1,
                voice="ACTIVE",
                nun_emphasis=False,
            ),
            [],
        )

        # No occurrence is dropped or indexed under a different stem's attributes.
        stack = [((), document["index"])]
        addresses = []
        while stack:
            keys, bucket = stack.pop()
            if isinstance(bucket, dict):
                stack.extend(((*keys, key), value) for key, value in bucket.items())
                continue
            for hit in bucket:
                chapter, verse = map(int, hit["address"].split(":"))
                token = self.quran.token(chapter, verse, hit["word_index"], hit["token_part"])
                self.assertEqual(
                    keys,
                    (
                        token.root,
                        token.tense,
                        token.verb_form,
                        str(token.conjugation),
                        token.voice,
                        "with_nun" if token.has_nun_of_emphasis() else "without_nun",
                    ),
                )
                addresses.append(token.address_tuple)
        self.assertEqual(sorted(addresses), [token.address_tuple for token in self.quran.verbs()])
        script = Path(__file__).parents[1] / "examples" / "export_verb_index.py"
        self.assertTrue(script.read_text(encoding="utf-8").isascii())


if __name__ == "__main__":
    unittest.main()
