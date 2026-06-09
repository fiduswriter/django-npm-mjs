import importlib.util
import json
import os
import pkgutil

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand

from npm_mjs.json5_parser import parse_json5
from npm_mjs.paths import TRANSPILE_CACHE_PATH


def deep_merge_dicts(old_dict, merge_dict, scripts=False):
    for key in merge_dict:
        if key in old_dict:
            if isinstance(old_dict[key], dict) and isinstance(merge_dict[key], dict):
                if key == "scripts":
                    deep_merge_dicts(old_dict[key], merge_dict[key], True)
                else:
                    deep_merge_dicts(old_dict[key], merge_dict[key])
            else:
                # In the scripts section, allow adding to hooks such as
                # "preinstall" and "postinstall"
                if scripts and key in old_dict:
                    old_dict[key] += " && %s" % merge_dict[key]
                else:
                    old_dict[key] = merge_dict[key]
        else:
            old_dict[key] = merge_dict[key]


def _iter_package_dirs():
    """Yield directories of installed packages to scan for package.json."""
    namespaces = getattr(settings, "NPM_MJS_PACKAGE_NAMESPACES", None)

    if namespaces is None:
        # Default: scan all top-level packages
        for _, modname, ispkg in pkgutil.iter_modules():
            if not ispkg:
                continue
            spec = importlib.util.find_spec(modname)
            if spec is None:
                continue
            if spec.origin:
                package_dir = os.path.dirname(spec.origin)
            elif spec.submodule_search_locations:
                package_dir = list(spec.submodule_search_locations)[0]
            else:
                continue
            if package_dir:
                yield package_dir
    else:
        # Restricted: scan only specified namespace packages
        for ns in namespaces:
            try:
                ns_module = importlib.import_module(ns)
                ns_path = getattr(ns_module, "__path__", None)
                if not ns_path:
                    continue
                for _, modname, ispkg in pkgutil.iter_modules(ns_path):
                    if ispkg:
                        spec = importlib.util.find_spec(f"{ns}.{modname}")
                        if spec and spec.submodule_search_locations:
                            yield list(spec.submodule_search_locations)[0]
            except ImportError:
                pass


def get_package_dirs():
    """Find directories of all Django apps and configured extra packages."""
    dirs = set()

    # Add all configured Django apps
    for config in django_apps.get_app_configs():
        dirs.add(config.path)

    # Add extra packages
    for package_dir in _iter_package_dirs():
        dirs.add(package_dir)

    return dirs


class Command(BaseCommand):
    help = "Join package.json files from apps into common package.json"

    def handle(self, *args, **options):
        package = {}
        for package_dir in get_package_dirs():
            json5_package_path = os.path.join(package_dir, "package.json5")
            json_package_path = os.path.join(package_dir, "package.json")
            if os.path.isfile(json5_package_path):
                with open(json5_package_path, encoding="utf-8") as data_file:
                    data = parse_json5(data_file.read(), debug=True)
            elif os.path.isfile(json_package_path):
                with open(json_package_path, encoding="utf-8") as data_file:
                    data = json.loads(data_file.read())
            else:
                continue
            deep_merge_dicts(package, data)
        os.makedirs(TRANSPILE_CACHE_PATH, exist_ok=True)
        package_path = os.path.join(TRANSPILE_CACHE_PATH, "package.json")
        with open(package_path, "w") as outfile:
            json.dump(package, outfile)
