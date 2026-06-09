import hashlib
import importlib.util
import json
import os
import pkgutil
import shutil
import time
from shutil import which
from subprocess import call

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from npm_mjs import signals
from npm_mjs.paths import SETTINGS_PATHS
from npm_mjs.paths import TRANSPILE_CACHE_PATH
from npm_mjs.tools import get_last_run
from npm_mjs.tools import set_last_run


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


def get_package_hash():
    """Generate a hash of all package.json files"""
    hash_md5 = hashlib.md5()
    for package_dir in get_package_dirs():
        for filename in ["package.json", "package.json5"]:
            filepath = os.path.join(package_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    hash_md5.update(f.read())
    return hash_md5.hexdigest()


def install_npm(force, stdout, post_npm_signal=True):
    change_times = [0]
    for path in SETTINGS_PATHS:
        change_times.append(os.path.getmtime(path))
    settings_change = max(change_times)
    package_hash = get_package_hash()
    cache_file = os.path.join(TRANSPILE_CACHE_PATH, "package_hash.json")

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached_hash = json.load(f).get("hash")
    else:
        cached_hash = None

    npm_install = False
    if (
        settings_change > get_last_run("npm_install")
        or package_hash != cached_hash
        or force
    ):
        stdout.write("Installing pnpm dependencies...")
        os.makedirs(TRANSPILE_CACHE_PATH, exist_ok=True)
        set_last_run("npm_install", int(round(time.time())))
        call_command("create_package_json")

        stdout.write("Installing dependencies...")
        node_modules_path = os.path.join(TRANSPILE_CACHE_PATH, "node_modules")
        if os.path.exists(node_modules_path):
            shutil.rmtree(node_modules_path, ignore_errors=True)
        env = os.environ.copy()
        env["CI"] = "true"
        pnpm_args = ["install", "--config.strict-dep-builds=false"]
        if which("pnpm"):
            returncode = call(["pnpm"] + pnpm_args, cwd=TRANSPILE_CACHE_PATH, env=env)
        else:
            returncode = call(
                ["npx", "-y", "pnpm"] + pnpm_args,
                cwd=TRANSPILE_CACHE_PATH,
                env=env,
            )
        if returncode != 0:
            raise CommandError(
                "pnpm install failed with exit code %d. "
                "If you see an ENOTEMPTY error, try clearing the npx cache: "
                "rm -rf ~/.npm/_npx/" % returncode,
            )

        # Update cache
        with open(cache_file, "w") as f:
            json.dump({"hash": package_hash}, f)

        if post_npm_signal:
            signals.post_npm_install.send(sender=None)
        npm_install = True
    else:
        stdout.write("No changes detected, skipping pnpm install.")

    return npm_install


class Command(BaseCommand):
    help = "Run npm install on package.json files in app folders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help="Force npm install even if no change is detected.",
        )

        parser.add_argument(
            "--nosignal",
            action="store_false",
            dest="post_npm_signal",
            default=True,
            help="Send a signal after finishing npm install.",
        )

    def handle(self, *args, **options):
        install_npm(options["force"], self.stdout, options["post_npm_signal"])
