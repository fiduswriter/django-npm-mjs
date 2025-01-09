import hashlib
import json
import os
import time
from subprocess import call

from django.apps import apps as django_apps
from django.core.management import call_command
from django.core.management.base import BaseCommand

from npm_mjs import signals
from npm_mjs.paths import SETTINGS_PATHS
from npm_mjs.paths import TRANSPILE_CACHE_PATH
from npm_mjs.tools import get_last_run
from npm_mjs.tools import set_last_run


def get_package_hash():
    """Generate a hash of all package.json files"""
    hash_md5 = hashlib.md5()
    for config in django_apps.get_app_configs():
        for filename in ["package.json", "package.json5"]:
            filepath = os.path.join(config.path, filename)
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
        if not os.path.exists(TRANSPILE_CACHE_PATH):
            os.makedirs(TRANSPILE_CACHE_PATH)
        set_last_run("npm_install", int(round(time.time())))
        call_command("create_package_json")

        stdout.write("Installing dependencies...")
        call(["npx", "pnpm", "install"], cwd=TRANSPILE_CACHE_PATH)

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
