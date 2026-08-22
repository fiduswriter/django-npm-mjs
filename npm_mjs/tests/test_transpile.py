"""Tests for the transpile command's source file discovery."""

import os
import tempfile
import unittest

from npm_mjs.management.commands.transpile import get_mainfiles
from npm_mjs.management.commands.transpile import get_source_files


class TestSourceFileDiscovery(unittest.TestCase):
    def test_get_source_files_finds_js_and_ts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_js = os.path.join(tmpdir, "assets", "js")
            os.makedirs(os.path.join(assets_js, "modules", "doc"))

            expected = {
                os.path.join(assets_js, "index.mjs"),
                os.path.join(assets_js, "plain.js"),
                os.path.join(assets_js, "modules", "doc", "editor.ts"),
                os.path.join(assets_js, "modules", "doc", "component.tsx"),
            }
            for path in expected:
                with open(path, "w") as f:
                    f.write("")

            # Files that must not be discovered.
            ignored = {
                os.path.join(assets_js, "data.json"),
                os.path.join(assets_js, "styles.css"),
                os.path.join(assets_js, "modules", "doc", "README.md"),
            }
            for path in ignored:
                with open(path, "w") as f:
                    f.write("")

            found = set(get_source_files(tmpdir))

            self.assertTrue(expected.issubset(found))
            self.assertFalse(ignored & found)

    def test_get_source_files_in_assets_ts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_ts = os.path.join(tmpdir, "assets", "ts")
            os.makedirs(os.path.join(assets_ts, "modules"))

            expected = {
                os.path.join(assets_ts, "index.ts"),
                os.path.join(assets_ts, "modules", "helper.tsx"),
            }
            for path in expected:
                with open(path, "w") as f:
                    f.write("")

            found = set(get_source_files(tmpdir))
            self.assertTrue(expected.issubset(found))

    def test_get_mainfiles_only_mjs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_js = os.path.join(tmpdir, "assets", "js")
            os.makedirs(os.path.join(assets_js, "nested"))

            entries = [
                os.path.join(assets_js, "app.mjs"),
                os.path.join(assets_js, "nested", "worker.mjs"),
            ]
            for path in entries:
                with open(path, "w") as f:
                    f.write("")
            # .ts modules must not become entry points.
            with open(os.path.join(assets_js, "types.ts"), "w") as f:
                f.write("")

            found = set(get_mainfiles(tmpdir))
            self.assertEqual(found, set(entries))


if __name__ == "__main__":
    unittest.main()
