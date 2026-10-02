from __future__ import annotations

import inspect
import unittest

import quran_processing_toolkit


class DocumentationTests(unittest.TestCase):
    def test_every_exported_callable_has_a_docstring(self) -> None:
        undocumented = []
        for name in quran_processing_toolkit.__all__:
            value = getattr(quran_processing_toolkit, name)
            if (inspect.isclass(value) or inspect.isfunction(value)) and not inspect.getdoc(value):
                undocumented.append(name)
        self.assertEqual(undocumented, [])


if __name__ == "__main__":
    unittest.main()
