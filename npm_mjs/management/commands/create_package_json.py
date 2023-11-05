import json
import os

import pyjson5
from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

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


class Command(BaseCommand):
    help = "Join package.json files from apps into common package.json"

    def handle(self, *args, **options):
        package = {}
        configs = django_apps.get_app_configs()
        for config in configs:
            json5_package_path = os.path.join(config.path, "package.json5")
            json_package_path = os.path.join(config.path, "package.json")
            if os.path.isfile(json5_package_path):
                with open(json5_package_path) as data_file:
                    data = pyjson5.decode(data_file.read())
            elif os.path.isfile(json_package_path):
                with open(json_package_path) as data_file:
                    data = json.loads(data_file.read())
            else:
                continue
            deep_merge_dicts(package, data)
        if not os.path.exists(TRANSPILE_CACHE_PATH):
            os.makedirs(TRANSPILE_CACHE_PATH)
        package_path = os.path.join(TRANSPILE_CACHE_PATH, "package.json")
        with open(package_path, "w") as outfile:
            json.dump(package, outfile)
