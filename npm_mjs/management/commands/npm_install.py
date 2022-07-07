import os
import shutil
import time
from subprocess import call

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.apps import apps as django_apps

from npm_mjs import signals
from npm_mjs.tools import get_last_run, set_last_run
from npm_mjs.paths import SETTINGS_PATHS, TRANSPILE_CACHE_PATH


def install_npm(force, stdout):
    change_times = [0]
    for path in SETTINGS_PATHS:
        change_times.append(os.path.getmtime(path))
    settings_change = max(change_times)
    package_path = os.path.join(TRANSPILE_CACHE_PATH, "package.json")
    webpack_bin_path = os.path.join(TRANSPILE_CACHE_PATH, "node_modules/.bin/webpack")
    if os.path.exists(package_path) and os.path.exists(webpack_bin_path):
        package_change = os.path.getmtime(package_path)
    else:
        package_change = -1
    app_package_change = 0
    configs = django_apps.get_app_configs()
    for config in configs:
        app_package_path = os.path.join(config.path, "package.json")
        if os.path.exists(app_package_path):
            app_package_change = max(
                os.path.getmtime(app_package_path), app_package_change
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
        os.environ["NODE_OPTIONS"] = "--openssl-legacy-provider"
        call(["npm", "install"], cwd=TRANSPILE_CACHE_PATH)
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

    def handle(self, *args, **options):
        if options["force"]:
            force = True
        else:
            force = False
        install_npm(force, self.stdout)
