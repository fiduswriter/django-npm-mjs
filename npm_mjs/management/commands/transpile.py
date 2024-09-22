import json
import os
import shutil
import subprocess
import time
from subprocess import call
from urllib.parse import urljoin

from django.apps import apps
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand
from django.templatetags.static import PrefixNode

from .collectstatic import Command as CSCommand
from .npm_install import install_npm
from npm_mjs import signals
from npm_mjs.paths import PROJECT_PATH
from npm_mjs.paths import STATIC_ROOT
from npm_mjs.paths import TRANSPILE_CACHE_PATH
from npm_mjs.tools import set_last_run

# Run this script every time you update an *.mjs file or any of the
# modules it loads.

OLD_RSPACK_CONFIG_JS = ""

RSPACK_CONFIG_JS_PATH = os.path.join(TRANSPILE_CACHE_PATH, "rspack.config.js")

try:
    with open(RSPACK_CONFIG_JS_PATH) as file:
        OLD_RSPACK_CONFIG_JS = file.read()
except OSError:
    pass


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
        js_paths = finders.find("js/", True)
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
            newest_file = max(files, key=os.path.getmtime)
            if (
                os.path.commonprefix([newest_file, transpile_path]) == transpile_path
                and not npm_install
                and not force
            ):
                # Transpile not needed as nothing has changed and not forced
                return
            # Remove any previously created static output dirs
            shutil.rmtree(transpile_path, ignore_errors=True)
        self.stdout.write("Transpiling...")
        if not os.path.exists(TRANSPILE_CACHE_PATH):
            os.makedirs(TRANSPILE_CACHE_PATH)
        # We reload the file as other values may have changed in the meantime
        set_last_run("transpile", start)
        # Create a static output dir
        out_dir = os.path.join(transpile_path, "js/")
        os.makedirs(out_dir)
        with open(os.path.join(transpile_path, "README.txt"), "w") as f:
            f.write(
                "These files have been automatically generated. "
                "DO NOT EDIT THEM! \n Changes will be overwritten. Edit "
                "the original files in one of the django apps, and run "
                "./manage.py transpile.",
            )

        mainfiles = []
        sourcefiles = []
        lib_sourcefiles = []
        for path in js_paths:
            for mainfile in (
                subprocess.check_output(
                    ["find", path, "-type", "f", "-name", "*.mjs", "-print"],
                )
                .decode("utf-8")
                .split("\n")[:-1]
            ):
                mainfiles.append(mainfile)
            for sourcefile in (
                subprocess.check_output(
                    ["find", path, "-type", "f", "-wholename", "*js"],
                )
                .decode("utf-8")
                .split("\n")[:-1]
            ):
                if "static/js" in sourcefile:
                    sourcefiles.append(sourcefile)
                if "static-libs/js" in sourcefile:
                    lib_sourcefiles.append(sourcefile)
        # Collect all JavaScript in a temporary dir (similar to
        # ./manage.py collectstatic).
        # This allows for the modules to import from oneanother, across Django
        # Apps.

        cache_path = os.path.join(TRANSPILE_CACHE_PATH, "js/")
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        # Note all cache files so that we can remove outdated files that no
        # longer are in the prject.
        cache_files = []
        # Note all plugin dirs and the modules inside of them to crate index.js
        # files inside of them.
        plugin_dirs = {}
        for sourcefile in sourcefiles:
            relative_path = sourcefile.split("static/js/")[1]
            outfile = os.path.join(cache_path, relative_path)
            cache_files.append(outfile)
            dirname = os.path.dirname(outfile)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            shutil.copyfile(sourcefile, outfile)
            # Check for plugin connectors
            if relative_path[:8] == "plugins/":
                if dirname not in plugin_dirs:
                    plugin_dirs[dirname] = []
                module_name = os.path.splitext(os.path.basename(relative_path))[0]
                if module_name != "init" and module_name not in plugin_dirs[dirname]:
                    plugin_dirs[dirname].append(module_name)

        for sourcefile in lib_sourcefiles:
            relative_path = sourcefile.split("static-libs/js/")[1]
            outfile = os.path.join(cache_path, relative_path)
            cache_files.append(outfile)
            dirname = os.path.dirname(outfile)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
                shutil.copyfile(sourcefile, outfile)
            elif not os.path.isfile(outfile):
                shutil.copyfile(sourcefile, outfile)
            elif os.path.getmtime(outfile) < os.path.getmtime(sourcefile):
                shutil.copyfile(sourcefile, outfile)

        # Write an index.js file for every plugin dir
        for plugin_dir in plugin_dirs:
            index_js = ""
            for module_name in plugin_dirs[plugin_dir]:
                index_js += 'export * from "./%s"\n' % module_name
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
        for existing_file in (
            subprocess.check_output(["find", cache_path, "-type", "f"])
            .decode("utf-8")
            .split("\n")[:-1]
        ):
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
        end = int(round(time.time()))
        self.stdout.write("Time spent transpiling: " + str(end - start) + " seconds")
        signals.post_transpile.send(sender=None)
