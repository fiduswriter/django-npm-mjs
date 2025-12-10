# django-npm-mjs
A Django package to use npm.js dependencies and transpile ES2015+

This package is used by Fidus Writer to bundle JavaScript. We try to keep it as generic as possible, so if there is something that seems very odd and specific to Fidus Writer, it is likely just an oversight from us. Please contact us and we'll see what we can do about it.

This package similar to django-compressor in that it treats JavaScript files before they are served to the user. But there are some differences:

* It does not mix different JavaScript module entry files. It only bundles everything imported from one entry file. With ES2015+ there is not as much need to have lots of JavaScript files operating in the global namespace.

* It allows importing from one django app in another app within the same project as if they were in the same folder similar to how static files and templates are handled by Django.

* It includes handling of npm.js imports.

* The JavaScript entry files' base names do not change and an automatic version query is added to be able to wipe the browser cache (`/js/my_file.mjs` turns into `/js/my_file.js?v=239329884`). This way it is also possible to refer to the URL from JavaScript (for example for use with web workers).

* It allows for JavaScript plugin hooks between django apps used in cases when a django project can be used both with or without a specific app, and the JavaScript from one app needs to import things from another app.


Quick start
-----------
1. Install "npm_mjs"

        pip install django-npm-mjs

2. Add "npm_mjs" to your INSTALLED_APPS setting like this::

        INSTALLED_APPS = [
            ...
            'npm_mjs',
        ]

3. Define a `PROJECT_PATH` in the settings as the root folder of the project (`PROJECT_DIR` will also be accepted)::

        PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

4. Define a `SETTINGS_PATHS` in the settings to contain the paths of all setting files (settings.py + any local_settings.py or similar file you may have defined) - this is to transpile again whenever settings have changed::

        SETTINGS_PATHS = [os.path.dirname(__file__), ]

5. Add the `static-transpile` folder inside the `PROJECT_PATH` to the `STATICFILES_DIRS` like this::

        STATICFILES_DIRS = (
            os.path.join(PROJECT_PATH, 'static-transpile'),
            ...
        )

6. Load transpile, and use `static` template tags to your templates to refer to JavaScript files.
All entry files to ES2015+ modules need to have \*.mjs endings. Entries can look like this::

        {% load transpile %}
        ...
        <script type="text/javascript" src="{% static "js/index.mjs" %}"></script>

You can continue to load other resources such as CSS files as before using the `static` template tag::

        <link type="text/css" rel="stylesheet" href="{% static "css/fonts.css" %}" />

7. Run `./manage.py transpile`.

8. Run `./manage.py runserver`. Your ES2015+ modules will be served as browser compatible JS files and all static files will have a versioned ending so that you can set your static server to let browsers cache static files indefinitely as long as DEBUG is set to False.


NPM.JS dependencies
-------------------

1. Add package.json or package.json5 files into one or more of your apps. All package files will be merged.

2. Import in your JS files from any of the npm modules specified in your package files.

3. Run `./manage.py transpile`.

4. Run `./manage.py runserver`.

Referring to the transpile version within JavaScript sources
------------------------------------------------------------

In your JavaScript sources, you can refer to the version string of the last transpile run like this::

        transpile.VERSION

For example::

        let downloadJS = `download.js?v=${transpile.VERSION}` // Latest version of transpiled version of download.mjs


ManifestStaticFilesStorage
--------------------------
If you use `ManifestStaticFilesStorage`, import it from `npm_mjs.storage` like this:

```py
from npm_mjs.storage import ManifestStaticFilesStorage
```

If you use that version, you can refer to other static files within your JavaScript files using the `staticUrl()` function like this:

```js
const cssUrl = staticUrl('/css/document.css')
```

Note that you will need to use absolute paths starting from the `STATIC_ROOT` for the `staticUrl()` function. Different from the default `ManifestStaticFilesStorage`, our version will generally interprete file urls starting with a slash as being relative to the `STATIC_ROOT`.

Translations
------------

Commands such as `./manage.py makemessages` and `./manage.py compilemessages` will work as always in Django, with some slightly different defaults. Not specifying any language will default to running with `--all` (all languages). Not specifying any domain will default to running for both "django" and "djangojs" (Python and Javascript files). The `static-transpile` directory will also be ignored by default.

**NOTE: JavaScript files that contain template strings will require at least xgettext version 0.24 or higher. See below for installation instructions.**


Install xgettext 0.24
---------------------

First check which xgettext version your OS comes with:

```bash
xgettext --version
```

If it is below version 0.24, you will need to install a newer version. For example in your current virtual environment:

Step 1: Activate Your Virtual Environment
```bash
source /path/to/venv/bin/activate
```

Step 2: Install Build Dependencies
Install tools required to compile software:

```bash
sudo apt-get update
sudo apt-get install -y build-essential libtool automake autoconf
```

Step 3: Download and Extract Gettext 0.24

```bash
wget https://ftp.gnu.org/pub/gnu/gettext/gettext-0.24.tar.gz
tar -xzf gettext-0.24.tar.gz
cd gettext-0.24
```

Step 4: Configure and Install into the Venv
Install to your venv's directory using --prefix:

```bash
./configure --prefix=$VIRTUAL_ENV
make
make install
```

Step 5: Verify Installation
Ensure the new xgettext is in your venv and check the version:

```bash
which xgettext  # Should output a path inside your venv
xgettext --version  # Should show 0.24
```

Step 6: Cleanup

```bash
cd ..
rm -rf gettext-0.24 gettext-0.24.tar.gz
```

Testing
-------

The package includes a comprehensive test suite to ensure reliability and prevent regressions.

### Running Tests

Run all tests using the provided test runner:

```bash
python runtests.py
```

Or use Python's unittest directly:

```bash
python -m unittest discover npm_mjs/tests
```

If you have pytest installed:

```bash
pytest
```

### Critical Regression Tests

The test suite includes specific tests for previously encountered bugs:

- **Double slashes in strings** (`"path//to//file"` should not be treated as comments)
- **Single quotes inside double-quoted strings** (proper quote conversion)
- **Long lines** (handling files with line 7, column 178 errors)
- **URLs in strings and comments** (preserving `https://` patterns)

For more details, see `npm_mjs/tests/README.md`.

### Debugging JSON5 Parse Errors

If you encounter errors when parsing package.json5 files, the parser provides helpful debug output using Python's logging module. The Django management command automatically enables debug mode, which shows:

- The processed content after comment removal and quote conversion
- The exact line and column where parsing failed
- The specific error message

Example debug output:

```
================================================================================
JSON5 Parser Error - Processed content that failed to parse:
================================================================================
 -->   4:   "key": "value with problem",
================================================================================
Error at line 4, column 26: Expecting ',' delimiter
================================================================================
```

When using the parser directly in your code, you can enable debug output:

```python
import logging
from npm_mjs.json5_parser import parse_json5

# Configure logging to see debug output
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# Enable debug output for troubleshooting
try:
    result = parse_json5(content, debug=True)
except json.JSONDecodeError as e:
    # Debug info logged as ERROR before exception is raised
    pass
```

By default, `debug=False` to keep the output clean in automated scripts and tests. When `debug=True`, error details are logged at the ERROR level using Python's standard logging module.
