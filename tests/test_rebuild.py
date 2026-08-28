from __future__ import annotations

import unittest

from quran_processing_toolkit.build import compare_records, load_records, rebuild_records
from quran_processing_toolkit.corpus import default_data_directory


class RebuildTests(unittest.TestCase):
    def test_base_rebuild_matches_processed_corpus(self) -> None:
        data = default_data_directory()
        base = load_records(data / "quran-morphologies_base.json")
        current = load_records(data / "quran-morphologies.json")
        self.assertEqual(compare_records(rebuild_records(base), current), [])


if __name__ == "__main__":
    unittest.main()
