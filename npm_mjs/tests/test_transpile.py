"""Tests for the transpile command's source file discovery."""

import os
import tempfile
import unittest

from npm_mjs.management.commands.transpile import get_source_files


class TestSourceFileDiscovery(unittest.TestCase):
    def test_get_source_files_finds_js_and_ts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            static_js = os.path.join(tmpdir, "static", "js")
            os.makedirs(os.path.join(static_js, "modules", "doc"))

            expected = {
                os.path.join(static_js, "index.mjs"),
                os.path.join(static_js, "plain.js"),
                os.path.join(static_js, "modules", "doc", "editor.ts"),
                os.path.join(static_js, "modules", "doc", "component.tsx"),
            }
            for path in expected:
                with open(path, "w") as f:
                    f.write("")

            # Files that must not be discovered.
            ignored = {
                os.path.join(static_js, "data.json"),
                os.path.join(static_js, "styles.css"),
                os.path.join(static_js, "modules", "doc", "README.md"),
            }
            for path in ignored:
                with open(path, "w") as f:
                    f.write("")

            found = set(get_source_files(tmpdir))

            self.assertTrue(expected.issubset(found))
            self.assertFalse(ignored & found)


if __name__ == "__main__":
    unittest.main()
