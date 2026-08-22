"""Tests for the assets directory finder used by the transpile command."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        USE_TZ=True,
    )
    django.setup()

from npm_mjs.management.commands.transpile import finders


class TestAssetsDirectoriesFinder(unittest.TestCase):
    def _make_top_level_pkg(self, parent_dir, name):
        """Create a minimal importable top-level package directory."""
        pkg_dir = os.path.join(parent_dir, name)
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
            f.write("")
        return pkg_dir

    def test_finds_assets_js_and_ts_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = self._make_top_level_pkg(tmpdir, "someapp")
            assets_js = os.path.join(pkg_dir, "assets", "js")
            assets_ts = os.path.join(pkg_dir, "assets", "ts")
            os.makedirs(assets_js)
            os.makedirs(assets_ts)

            with patch.object(sys, "path", [tmpdir] + sys.path):
                js_matches = finders.find("js/", all=True)
                ts_matches = finders.find("ts/", all=True)
                css_matches = finders.find("css/", all=True)

            self.assertIn(assets_js, js_matches)
            self.assertIn(assets_ts, ts_matches)
            # Static folders are no longer scanned for JS sources.
            static_js = os.path.join(pkg_dir, "static", "js")
            os.makedirs(static_js)
            with patch.object(sys, "path", [tmpdir] + sys.path):
                js_matches = finders.find("js/", all=True)
            self.assertNotIn(static_js, js_matches)
            self.assertEqual(css_matches, [])

    def test_find_single_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = self._make_top_level_pkg(tmpdir, "someapp")
            assets_js = os.path.join(pkg_dir, "assets", "js")
            os.makedirs(assets_js)

            with patch.object(sys, "path", [tmpdir] + sys.path):
                match = finders.find("js/", all=False)

            self.assertEqual(match, assets_js)


if __name__ == "__main__":
    unittest.main()
