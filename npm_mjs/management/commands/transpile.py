import json
import os
import re
import shutil
import time
from subprocess import call
from urllib.parse import urljoin

import importlib.util
import pkgutil

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.templatetags.static import PrefixNode

from .collectstatic import Command as CSCommand
from .npm_install import install_npm
from npm_mjs import signals
from npm_mjs.paths import PROJECT_PATH
from npm_mjs.paths import STATIC_ROOT
from npm_mjs.paths import TRANSPILE_CACHE_PATH
from npm_mjs.tools import set_last_run


class AssetsDirectoriesFinder:
    """Finds asset source directories in Django apps and Python packages.

    Since version 5.0, JavaScript/TypeScript sources live in an "assets"
    folder inside each app (assets/js/ and assets/ts/) rather than inside
    the "static" folder. The static folders are only used for generated
    output and for files that need no transpilation.
    """

    def find(self, path, all=False):
        matches = []
        checked = set()
        package_dirs = set()
        for config in apps.get_app_configs():
            package_dirs.add(config.path)
        # Also scan all top-level packages so that sources are found even in
        # apps that are not in INSTALLED_APPS. This lets a single bundle be
        # compiled before packaging while plugins are enabled at runtime.
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
                package_dirs.add(package_dir)
        for package_dir in package_dirs:
            full_path = os.path.normpath(os.path.join(package_dir, "assets", path))
            if full_path in checked:
                continue
            checked.add(full_path)
            if os.path.isdir(full_path):
                if all:
                    matches.append(full_path)
                else:
                    return full_path
        return matches if all else None


finders = AssetsDirectoriesFinder()

SOURCE_MAP_RE = re.compile(r"//# sourceMappingURL=(\S+)")


def copy_missing_source_maps(out_dir, cache_path):
    """Copy source maps referenced by generated JS files from node_modules.

    Third-party bundles may carry their original sourceMappingURL comments
    into rspack output chunks, but rspack does not copy the referenced .map
    files. This makes those maps available next to the generated JS so that
    static file servers do not log 500 errors for missing .map requests.
    """
    node_modules_path = os.path.join(cache_path, "node_modules")
    if not os.path.isdir(node_modules_path):
        return

    # Index available source maps in node_modules by basename.
    available_maps = {}
    for nm_root, _dirs, filenames in os.walk(node_modules_path):
        for filename in filenames:
            if filename.endswith(".js.map"):
                available_maps.setdefault(filename, []).append(
                    os.path.join(nm_root, filename),
                )

    for root, _dirs, filenames in os.walk(out_dir):
        for filename in filenames:
            if not filename.endswith(".js"):
                continue
            js_path = os.path.join(root, filename)
            with open(js_path, encoding="utf-8") as f:
                content = f.read()
            for match in SOURCE_MAP_RE.finditer(content):
                map_filename = match.group(1)
                if os.path.isabs(map_filename):
                    continue
                map_path = os.path.join(root, map_filename)
                if os.path.exists(map_path):
                    continue
                # Only copy unambiguous source maps to avoid serving the wrong
                # file for generic names such as index.js.map. If multiple
                # packages ship the same filename, copy only when their contents
                # are identical (e.g. the same file referenced by two versions
                # of one package).
                sources = available_maps.get(map_filename, [])
                if len(sources) == 1:
                    shutil.copyfile(sources[0], map_path)
                elif len(sources) > 1 and _all_files_identical(sources):
                    shutil.copyfile(sources[0], map_path)


def _all_files_identical(paths):
    """Return True if all files at the given paths have identical content."""
    with open(paths[0], "rb") as first_file:
        first_content = first_file.read()
    for path in paths[1:]:
        with open(path, "rb") as other_file:
            if other_file.read() != first_content:
                return False
    return True


# Run this script every time you update an *.mjs file or any of the
# modules it loads.

OLD_RSPACK_CONFIG_JS = ""

RSPACK_CONFIG_JS_PATH = os.path.join(TRANSPILE_CACHE_PATH, "rspack.config.js")

try:
    with open(RSPACK_CONFIG_JS_PATH) as file:
        OLD_RSPACK_CONFIG_JS = file.read()
except OSError:
    pass


# JavaScript and TypeScript source files. .mjs files are the entry points;
# .ts/.tsx files can be imported from any .mjs entry.
JS_EXTENSIONS = {".js", ".mjs", ".ts", ".tsx"}

# Asset folders inside each Django app that are scanned for sources. Listed
# in reverse precedence order: the list is reversed below together with the
# app order, so identically named files from "assets/js" are copied last and
# take precedence over files from "assets/ts".
ASSET_SUBFOLDERS = ["js", "ts"]


def get_source_files(path):
    """Yield all JavaScript/TypeScript source files under ``path``."""
    for root, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in JS_EXTENSIONS:
                yield os.path.join(root, filename)


def get_mainfiles(path):
    """Return all ``*.mjs`` entry point files under ``path``."""
    mainfiles = []
    for root, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".mjs"):
                mainfiles.append(os.path.join(root, filename))
    return mainfiles


class Command(BaseCommand):
    help = (
        "Transpile ES2015+ JavaScript to ES5 JavaScript + include NPM " "dependencies"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help="Force transpile even if no change is detected.",
        )

    def handle(self, *args, **options):
        if options["force"]:
            force = True
        else:
            force = False
        start = int(round(time.time()))
        npm_install = install_npm(force, self.stdout)
        js_paths = []
        for asset_subfolder in ASSET_SUBFOLDERS:
            js_paths.extend(finders.find(asset_subfolder + "/", True))
        # Remove paths inside of collection dir
        js_paths = [x for x in js_paths if not x.startswith(STATIC_ROOT)]
        # Reverse list so that overrides function as expected. Static file from
        # first app mentioned in INSTALLED_APPS has preference.
        js_paths.reverse()

        transpile_path = os.path.join(PROJECT_PATH, "static-transpile")

        if os.path.exists(transpile_path):
            files = []
            for js_path in js_paths:
                for root, _dirnames, filenames in os.walk(js_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            out_dir = os.path.join(transpile_path, "js/")
            if os.path.isdir(out_dir):
                for root, _dirnames, filenames in os.walk(out_dir):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            if files:
                newest_file = max(files, key=os.path.getmtime)
                if (
                    os.path.commonprefix([newest_file, transpile_path])
                    == transpile_path
                    and not npm_install
                    and not force
                ):
                    # Transpile not needed as nothing has changed and not forced
                    return
            # Remove any previously created static output dirs
            shutil.rmtree(transpile_path, ignore_errors=True)
        self.stdout.write("Transpiling...")
        os.makedirs(TRANSPILE_CACHE_PATH, exist_ok=True)
        # We reload the file as other values may have changed in the meantime
        set_last_run("transpile", start)
        # Create a static output dir
        out_dir = os.path.join(transpile_path, "js/")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(transpile_path, "README.txt"), "w") as f:
            f.write(
                "These files have been automatically generated. "
                "DO NOT EDIT THEM! \n Changes will be overwritten. Edit "
                "the original files in one of the django apps, and run "
                "./manage.py transpile.",
            )

        mainfiles = []
        # Source files as (source_path, relative_path, django_app_name) tuples,
        # relative to the app's assets/js or assets/ts folder.
        sourcefiles = []
        for path in js_paths:
            # path is "<app dir>/assets/js" or "<app dir>/assets/ts" - the app
            # name is the directory containing the assets folder.
            django_app = os.path.basename(
                os.path.dirname(os.path.dirname(os.path.normpath(path))),
            )
            for mainfile in get_mainfiles(path):
                mainfiles.append(mainfile)
            for sourcefile in get_source_files(path):
                relative_path = os.path.relpath(
                    sourcefile,
                    os.path.normpath(path),
                ).replace(os.sep, "/")
                sourcefiles.append((sourcefile, relative_path, django_app))

        # Collect all JavaScript in a temporary dir (similar to
        # ./manage.py collectstatic).
        # This allows for the modules to import from oneanother, across Django
        # Apps.

        cache_path = os.path.join(TRANSPILE_CACHE_PATH, "js/")
        os.makedirs(cache_path, exist_ok=True)
        # Note all cache files so that we can remove outdated files that no
        # longer are in the prject.
        cache_files = []
        # Note all plugin dirs and the modules inside of them to crate index.js
        # files inside of them.
        plugin_dirs = {}
        plugin_names = []
        for [sourcefile, relative_path, django_app] in sourcefiles:

            outfile = os.path.join(cache_path, relative_path)
            cache_files.append(outfile)
            dirname = os.path.dirname(outfile)
            os.makedirs(dirname, exist_ok=True)
            shutil.copyfile(sourcefile, outfile)
            # Check for plugin connectors
            if relative_path[:8] == "plugins/":
                if dirname not in plugin_dirs:
                    plugin_dirs[dirname] = []
                module_name = os.path.splitext(os.path.basename(relative_path))[0]
                if module_name != "init":
                    if f"{dirname}/{django_app}/{module_name}" not in plugin_names:
                        plugin_dirs[dirname].append([django_app, module_name])
                        plugin_names.append(f"{dirname}/{django_app}/{module_name}")

        # Write an index.js file for every plugin dir
        for plugin_dir in plugin_dirs:
            index_js = ""
            for [_django_app, module_name] in plugin_dirs[plugin_dir]:
                index_js += 'import * as {} from "./{}"\n'.format(
                    module_name,
                    module_name,
                )
            index_js += "export const plugins = [\n"
            for [django_app, module_name] in plugin_dirs[plugin_dir]:
                index_js += f"  ['{django_app}', {module_name}],\n"
            index_js += "]\n"
            outfile = os.path.join(plugin_dir, "index.js")
            cache_files.append(outfile)
            if not os.path.isfile(outfile):
                index_file = open(outfile, "w")
                index_file.write(index_js)
                index_file.close()
            else:
                index_file = open(outfile)
                old_index_js = index_file.read()
                index_file.close()
                if old_index_js != index_js:
                    index_file = open(outfile, "w")
                    index_file.write(index_js)
                    index_file.close()

        # Check for outdated files that should be removed
        for root, _dirnames, filenames in os.walk(cache_path):
            for filename in filenames:
                existing_file = os.path.join(root, filename)
                if existing_file not in cache_files:
                    self.stdout.write("Removing %s" % existing_file)
                    os.remove(existing_file)
        if apps.is_installed("django.contrib.staticfiles"):
            from django.contrib.staticfiles.storage import staticfiles_storage

            static_base_url = staticfiles_storage.base_url
        else:
            static_base_url = PrefixNode.handle_simple("STATIC_URL")
        transpile_base_url = urljoin(static_base_url, "js/")
        if (
            hasattr(settings, "RSPACK_CONFIG_TEMPLATE")
            and settings.RSPACK_CONFIG_TEMPLATE
        ):
            rspack_config_template_path = settings.RSPACK_CONFIG_TEMPLATE
        else:
            rspack_config_template_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "rspack.config.template.js",
            )
        entries = {}
        for mainfile in mainfiles:
            basename = os.path.basename(mainfile)
            modulename = basename.split(".")[0]
            file_path = os.path.join(cache_path, basename)
            entries[modulename] = file_path
        find_static = CSCommand()
        find_static.set_options(
            **{
                "interactive": False,
                "verbosity": 0,
                "link": False,
                "clear": False,
                "dry_run": True,
                "ignore_patterns": ["js/", "admin/"],
                "use_default_ignore_patterns": True,
                "post_process": True,
            },
        )
        found_files = find_static.collect()
        static_frontend_files = (
            found_files["modified"]
            + found_files["unmodified"]
            + found_files["post_processed"]
        )
        transpile = {
            "OUT_DIR": out_dir,
            "VERSION": start,
            "BASE_URL": transpile_base_url,
            "ENTRIES": entries,
            "STATIC_FRONTEND_FILES": [
                urljoin(static_base_url, x) for x in static_frontend_files
            ],
        }
        with open(rspack_config_template_path) as f:
            rspack_config_template = f.read()
        settings_dict = {}
        for var in dir(settings):
            if var in ["DATABASES", "SECRET_KEY"]:
                # For extra security, we do not copy DATABASES or SECRET_KEY
                continue
            try:
                settings_dict[var] = getattr(settings, var)
            except AttributeError:
                pass
        rspack_config_js = rspack_config_template.replace(
            "window.transpile",
            json.dumps(transpile),
        ).replace("window.settings", json.dumps(settings_dict, default=lambda x: False))

        if rspack_config_js is not OLD_RSPACK_CONFIG_JS:
            with open(RSPACK_CONFIG_JS_PATH, "w") as f:
                f.write(rspack_config_js)
        call(["./node_modules/.bin/rspack"], cwd=TRANSPILE_CACHE_PATH)
        copy_missing_source_maps(out_dir, TRANSPILE_CACHE_PATH)
        end = int(round(time.time()))
        self.stdout.write("Time spent transpiling: " + str(end - start) + " seconds")
        signals.post_transpile.send(sender=None)
