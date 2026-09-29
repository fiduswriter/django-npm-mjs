import json
import os
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

from npm_mjs.management.commands.create_package_json import Command


class TestCreatePackageJsonMerge(unittest.TestCase):
    """Merging package.json5 files must be order-deterministic."""

    def _write_pkg(self, parent, name, dep_version):
        pkg_dir = os.path.join(parent, name)
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "package.json5"), "w") as f:
            f.write('{dependencies: {"some-lib": "%s"}}' % dep_version)
        return pkg_dir

    def _merge(self, dirs, out_dir):
        with patch(
            "npm_mjs.management.commands.create_package_json.get_package_dirs",
            return_value=set(dirs),
        ), patch(
            "npm_mjs.management.commands.create_package_json.TRANSPILE_CACHE_PATH",
            out_dir,
        ):
            Command().handle()
        with open(os.path.join(out_dir, "package.json")) as f:
            return json.load(f)

    def test_conflicting_ranges_resolve_by_sorted_dir_order(self):
        # get_package_dirs() returns a set whose iteration order varies
        # per process; the merge must not. Whatever the discovery order,
        # the directory that sorts last wins a conflicting range, so the
        # merged package.json (and the pnpm frozen-lockfile check built
        # on it) is stable across runs.
        with tempfile.TemporaryDirectory() as tmpdir:
            aaa = self._write_pkg(tmpdir, "aaa", "^1.0.0")
            zzz = self._write_pkg(tmpdir, "zzz", "^2.0.0")
            first = self._merge([aaa, zzz], tempfile.mkdtemp())
            second = self._merge([zzz, aaa], tempfile.mkdtemp())
            self.assertEqual(first, second)
            self.assertEqual(first["dependencies"]["some-lib"], "^2.0.0")


if __name__ == "__main__":
    unittest.main()
