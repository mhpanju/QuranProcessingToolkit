from __future__ import annotations

import contextlib
import inspect
import io
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

import quran_processing_toolkit


class DocumentationTests(unittest.TestCase):
    def test_every_exported_callable_has_a_docstring(self) -> None:
        undocumented = []
        for name in quran_processing_toolkit.__all__:
            value = getattr(quran_processing_toolkit, name)
            if (inspect.isclass(value) or inspect.isfunction(value)) and not inspect.getdoc(value):
                undocumented.append(name)
        self.assertEqual(undocumented, [])

    def test_readme_and_ai_guide_starting_examples_execute(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for name in ("README.md", "docs/AI_GUIDE.md"):
            with self.subTest(document=name):
                source = (root / name).read_text(encoding="utf-8")
                example = re.search(r"```python\n(.*?)\n```", source, re.DOTALL)
                self.assertIsNotNone(example)
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(example.group(1), name, "exec"), {})

    def test_documentation_links_resolve_to_repository_files(self) -> None:
        root = Path(__file__).resolve().parents[1]
        documents = [*root.glob("*.md"), *root.joinpath("docs").glob("*.md"), root / "llms.txt"]
        missing = []
        for document in documents:
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                url = urlsplit(target)
                if url.netloc == "raw.githubusercontent.com":
                    prefix = "/mhpanju/QuranProcessingToolkit/master/"
                elif url.netloc == "github.com":
                    prefix = "/mhpanju/QuranProcessingToolkit/blob/master/"
                else:
                    prefix = ""
                if prefix and url.path.startswith(prefix):
                    path = root / unquote(url.path[len(prefix) :])
                elif not url.scheme and url.path:
                    path = document.parent / unquote(url.path)
                else:
                    continue
                if not path.exists():
                    missing.append((str(document.relative_to(root)), target))
        self.assertEqual(missing, [])

    def test_api_reference_covers_all_exports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        reference = (root / "docs/API_REFERENCE.md").read_text(encoding="utf-8")
        missing = [name for name in quran_processing_toolkit.__all__ if name not in reference]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
