import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import django
from django.apps import apps as django_apps
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        USE_TZ=True,
    )
    django.setup()

from npm_mjs.package_discovery import _iter_package_dirs
from npm_mjs.package_discovery import get_package_dirs


class TestPackageDiscovery(unittest.TestCase):
    """Tests for npm_mjs.package_discovery."""

    def _make_top_level_pkg(self, parent_dir, name):
        """Create a minimal importable top-level package directory."""
        pkg_dir = os.path.join(parent_dir, name)
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
            f.write("")
        return pkg_dir

    def test_iter_package_dirs_namespace_fallback_to_top_level(self):
        """When a configured namespace is not importable, top-level packages
        are still discovered so that symlinked/development plugins are not
        silently ignored.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = self._make_top_level_pkg(tmpdir, "pandoc")
            with open(os.path.join(pkg_dir, "package.json5"), "w") as f:
                f.write('{dependencies: {"pandoc-wasm": "1.0.0"}}')

            # Namespace does not exist anywhere
            with patch.object(
                settings,
                "NPM_MJS_PACKAGE_NAMESPACES",
                ["fiduswriter"],
                create=True,
            ):
                with patch.object(sys, "path", [tmpdir] + sys.path):
                    found = list(_iter_package_dirs())

            self.assertIn(pkg_dir, found)

    def test_iter_package_dirs_namespace_subpackages(self):
        """When a namespace package is importable, its subpackages are
        discovered.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ns_dir = os.path.join(tmpdir, "fiduswriter")
            os.makedirs(ns_dir)
            sub_dir = self._make_top_level_pkg(ns_dir, "pandoc")

            # Make the namespace importable by adding tmpdir to sys.path and
            # clearing any cached fiduswriter module.
            with patch.object(sys, "path", [tmpdir] + sys.path):
                if "fiduswriter" in sys.modules:
                    del sys.modules["fiduswriter"]
                if "fiduswriter.pandoc" in sys.modules:
                    del sys.modules["fiduswriter.pandoc"]

                with patch.object(
                    settings,
                    "NPM_MJS_PACKAGE_NAMESPACES",
                    ["fiduswriter"],
                    create=True,
                ):
                    found = list(_iter_package_dirs())

            self.assertIn(sub_dir, found)

    def test_get_package_dirs_includes_apps_and_extra_packages(self):
        """get_package_dirs merges configured Django apps and discovered
        extra packages.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = self._make_top_level_pkg(tmpdir, "pandoc")

            app_dirs = [config.path for config in django_apps.get_app_configs()]

            with patch.object(
                settings,
                "NPM_MJS_PACKAGE_NAMESPACES",
                ["fiduswriter"],
                create=True,
            ):
                with patch.object(sys, "path", [tmpdir] + sys.path):
                    found = get_package_dirs()

            self.assertTrue(found.issuperset(app_dirs))
            self.assertIn(pkg_dir, found)


if __name__ == "__main__":
    unittest.main()
