from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quran_processing_toolkit.build import (
    SUPPORTED_DERIVED_DIGESTS,
    load_source_records,
    rebuild_records,
    records_digest,
)
from quran_processing_toolkit.source_data import (
    DataIntegrityError,
    default_data_directory,
    load_normalized_records,
    verify_data_directory,
)


class RebuildTests(unittest.TestCase):
    def test_verbatim_source_rebuild_is_deterministic(self) -> None:
        data = default_data_directory()
        manifest = verify_data_directory(data)
        source = manifest["sources"]["morphology"]
        records = rebuild_records(load_source_records(data / source["filename"]))
        self.assertEqual(len(records), 128219)
        self.assertEqual(records_digest(records), SUPPORTED_DERIVED_DIGESTS[source["sha256"]])

    def test_local_cache_is_derived_outside_the_distribution(self) -> None:
        data = default_data_directory()
        with TemporaryDirectory() as temporary:
            cache_dir = Path(temporary)
            first, _ = load_normalized_records(data, cache_dir=cache_dir)
            cache_files = tuple(cache_dir.glob("*.json"))
            self.assertEqual(len(cache_files), 1)
            second, _ = load_normalized_records(data, cache_dir=cache_dir)
        self.assertEqual(first, second)

    def test_modified_source_file_is_rejected(self) -> None:
        source = default_data_directory()
        with TemporaryDirectory() as temporary:
            copied = Path(temporary) / "data"
            shutil.copytree(source, copied)
            boundaries = copied / "juzz-breakdown.tsv"
            boundaries.write_bytes(boundaries.read_bytes() + b"x")
            with self.assertRaisesRegex(DataIntegrityError, "Size mismatch"):
                verify_data_directory(copied)


if __name__ == "__main__":
    unittest.main()
