import os
import re
import shutil
import time
from subprocess import call
from subprocess import check_output

from django.apps import apps as django_apps
from django.core.management import call_command
from django.core.management.base import BaseCommand

from npm_mjs import signals
from npm_mjs.paths import SETTINGS_PATHS
from npm_mjs.paths import TRANSPILE_CACHE_PATH
from npm_mjs.tools import get_last_run
from npm_mjs.tools import set_last_run


def install_npm(force, stdout, post_npm_signal=True):
    change_times = [0]
    for path in SETTINGS_PATHS:
        change_times.append(os.path.getmtime(path))
    settings_change = max(change_times)
    package_path = os.path.join(TRANSPILE_CACHE_PATH, "package.json")
    rspack_bin_path = os.path.join(TRANSPILE_CACHE_PATH, "node_modules/.bin/rspack")
    if os.path.exists(package_path) and os.path.exists(rspack_bin_path):
        package_change = os.path.getmtime(package_path)
    else:
        package_change = -1
    app_package_change = 0
    configs = django_apps.get_app_configs()
    for config in configs:
        app_package_path = os.path.join(config.path, "package.json")
        if os.path.exists(app_package_path):
            app_package_change = max(
                os.path.getmtime(app_package_path),
                app_package_change,
            )
        else:
            app_package_path = os.path.join(config.path, "package.json5")
            if os.path.exists(app_package_path):
                app_package_change = max(
                    os.path.getmtime(app_package_path),
                    app_package_change,
                )
    npm_install = False
    if (
        settings_change > get_last_run("npm_install")
        or app_package_change > package_change
        or force
    ):
        stdout.write("Installing npm dependencies...")
        if not os.path.exists(TRANSPILE_CACHE_PATH):
            os.makedirs(TRANSPILE_CACHE_PATH)
        set_last_run("npm_install", int(round(time.time())))
        node_modules_path = os.path.join(TRANSPILE_CACHE_PATH, "node_modules")
        if os.path.exists(node_modules_path):
            shutil.rmtree(node_modules_path, ignore_errors=True)
        call_command("create_package_json")
        if "SUDO_UID" in os.environ:
            del os.environ["SUDO_UID"]
        os.environ["npm_config_unsafe_perm"] = "true"
        node_version = int(
            re.search(r"\d+", str(check_output(["node", "--version"]))).group(),
        )
        if node_version > 16:
            os.environ["NODE_OPTIONS"] = "--openssl-legacy-provider"
        call(["npm", "install"], cwd=TRANSPILE_CACHE_PATH)
        if post_npm_signal:
            signals.post_npm_install.send(sender=None)
        npm_install = True
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
