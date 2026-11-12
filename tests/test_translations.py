from __future__ import annotations

import hashlib
import json
import unittest
import warnings
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from urllib.error import URLError
from urllib.request import Request

from quran_processing_toolkit import (
    TranslationDownloadError,
    TranslationIntegrityError,
    TranslationLicenseWarning,
    TranslationNotAvailableError,
    download_translation,
    load_quran,
    load_translation,
    translation_sources,
)
from quran_processing_toolkit.chapter_names import CHAPTERS
from quran_processing_toolkit.translations import _HTTPSOnlyRedirect


class TranslationTests(unittest.TestCase):
    def test_redirect_policy_rejects_downgrades_before_request(self):
        redirect = _HTTPSOnlyRedirect()
        request = Request("https://tanzil.net/trans/en.qarai")
        for target in ("http://example.test/plain", "file:///tmp/plain"):
            with self.assertRaises(TranslationDownloadError):
                redirect.redirect_request(request, None, 302, "Found", {}, target)
        redirected = redirect.redirect_request(
            request, None, 302, "Found", {}, "https://tanzil.net/trans/en.qarai"
        )
        self.assertTrue(redirected.full_url.startswith("https://"))

    def test_local_text_json_metadata_coverage_and_corpus_identity(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "translation.txt"
            path.write_text(
                "# authored fixture\n1|1|Test text | with pipe\n1|2|Other test text\n",
                encoding="utf-8",
            )
            layer = load_translation(path, translator="Test author", language="English")
            self.assertEqual(layer.texts[1, 1], "Test text | with pipe")
            self.assertEqual(layer.coverage().translated, 2)
            self.assertEqual(layer.coverage().total, 6236)
            self.assertFalse(layer.coverage().complete)
            self.assertTrue(layer.coverage([(1, 1), (1, 1)]).complete)
            self.assertEqual(layer.coverage([]).fraction, 1)
            layer.require_complete([(1, 1), (1, 2)])
            with self.assertRaises(TranslationNotAvailableError):
                layer.require_complete()
            with self.assertRaises(TypeError):
                layer.metadata["translator"] = "edited"
            corpus = load_quran(translation=layer)
            self.assertEqual(corpus.verse(1, 1).get_translation(), "Test text | with pipe")
            self.assertEqual(corpus.translation_metadata()["translator"], "Test author")
            corpus.translation_metadata()["translator"] = "copy"
            self.assertEqual(corpus.translation_metadata()["translator"], "Test author")
            self.assertIs(corpus, load_quran(translation=layer))
            differently_labeled = load_translation(path, translator="Different metadata")
            self.assertIsNot(corpus, load_quran(translation=differently_labeled))
            self.assertIsNot(corpus, load_quran(translation=path))
            self.assertTrue(corpus.translation_coverage([corpus.verse(1, 1)]).complete)
            corpus.require_translation([corpus.verse(1, 1)])
            with self.assertRaises(TranslationNotAvailableError):
                corpus.require_translation([corpus.verse(1, 3)])
            structured = Path(folder) / "translation.json"
            structured.write_text(
                json.dumps(
                    {
                        "surahs": [
                            {"number": 1, "verses": [{"number": 1, "text": "Test\nmultiline text"}]}
                        ]
                    }
                )
            )
            layer = load_translation(structured)
            self.assertEqual(layer.texts[1, 1], "Test\nmultiline text")
            self.assertEqual(
                load_quran(translation=structured).verse(1, 1).get_translation(),
                "Test\nmultiline text",
            )

    def test_invalid_inputs_are_rejected_without_network(self):
        with (
            TemporaryDirectory() as folder,
            patch("quran_processing_toolkit.translations._open_translation") as network,
        ):
            path = Path(folder) / "translation.txt"
            for contents in ("", "garbage", "1|1|a\n1|1|b", "0|1|a", "1|8|a", "1|1| "):
                with self.subTest(contents=contents), self.assertRaises(ValueError):
                    path.write_text(contents)
                    load_translation(path)
            path = Path(folder) / "translation.json"
            for number in (True, 1.5, -1):
                path.write_text(
                    json.dumps(
                        {"surahs": [{"number": number, "verses": [{"number": 1, "text": "test"}]}]}
                    )
                )
                with self.assertRaises(ValueError):
                    load_translation(path)
            network.assert_not_called()
        plain = load_quran()
        self.assertIsNone(plain.translation_metadata())
        self.assertEqual(plain.translation_coverage().translated, 0)
        self.assertTrue(plain.translation_coverage([]).complete)

    def test_downloader_integrity_cache_offline_and_refresh(self):
        # Authored placeholder records, never a bundled third-party translation.
        payload = "".join(
            f"{c}|{v}|Test verse {c}:{v}\n"
            for c, row in enumerate(CHAPTERS, 1)
            for v in range(1, row[3] + 1)
        ).encode()
        source = replace(translation_sources()[0], sha256=hashlib.sha256(payload).hexdigest())
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = source.url
        response.read.return_value = payload
        with (
            TemporaryDirectory() as folder,
            patch("quran_processing_toolkit.translations._SOURCES", (source,)),
            patch(
                "quran_processing_toolkit.translations._open_translation", return_value=response
            ) as network,
        ):
            with self.assertWarns(TranslationLicenseWarning):
                first = download_translation("qarai", cache_dir=folder)
            self.assertTrue(first.coverage().complete)
            self.assertEqual(first.path.read_bytes(), payload)
            self.assertEqual(first.metadata["source_url"], source.url)
            network.assert_called_once()
            second = download_translation("en.qarai", cache_dir=folder, offline=True)
            self.assertEqual(second.fingerprint, first.fingerprint)
            self.assertEqual(second.metadata["downloaded_at"], first.metadata["downloaded_at"])
            network.assert_called_once()
            manifest = json.loads(first.path.with_suffix(".metadata.json").read_text())
            self.assertEqual(manifest["terms_url"], source.terms_url)
            first.path.write_bytes(payload + b"corruption")
            with self.assertRaises(TranslationIntegrityError):
                download_translation(cache_dir=folder, offline=True)
            network.assert_called_once()
            with self.assertWarns(TranslationLicenseWarning):
                repaired = download_translation(cache_dir=folder, refresh=True)
            self.assertEqual(repaired.path.read_bytes(), payload)
            self.assertEqual(network.call_count, 2)

    def test_download_errors_never_cache_unverified_content(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://tanzil.net/trans/en.qarai"
        response.read.return_value = b"untrusted changed content"
        with (
            TemporaryDirectory() as folder,
            patch(
                "quran_processing_toolkit.translations._open_translation", return_value=response
            ) as network,
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore", TranslationLicenseWarning)
            with self.assertRaises(TranslationDownloadError):
                download_translation(cache_dir=folder, offline=True)
            for kwargs in (
                {"identifier": "../../bad"},
                {"offline": True, "refresh": True},
                {"timeout": 0},
            ):
                with self.assertRaises(ValueError):
                    download_translation(cache_dir=folder, **kwargs)
            network.assert_not_called()
            with self.assertRaises(TranslationIntegrityError):
                download_translation(cache_dir=folder)
            self.assertEqual(list(Path(folder).iterdir()), [])
            response.geturl.return_value = "http://insecure.example/translation"
            with self.assertRaises(TranslationDownloadError):
                download_translation(cache_dir=folder)
            network.side_effect = URLError("test network unavailable")
            with self.assertRaises(TranslationDownloadError):
                download_translation(cache_dir=folder)

    def test_incomplete_pinned_provider_response_is_not_accepted(self):
        payload = b"1|1|Authored placeholder\n"
        source = replace(translation_sources()[0], sha256=hashlib.sha256(payload).hexdigest())
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = source.url
        response.read.return_value = payload
        with (
            TemporaryDirectory() as folder,
            patch("quran_processing_toolkit.translations._SOURCES", (source,)),
            patch("quran_processing_toolkit.translations._open_translation", return_value=response),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore", TranslationLicenseWarning)
            with self.assertRaises(TranslationIntegrityError):
                download_translation(cache_dir=folder)
            self.assertFalse(list(Path(folder).iterdir()))


if __name__ == "__main__":
    unittest.main()
