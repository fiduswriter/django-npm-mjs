# django-npm-mjs
A Django package to use npm.js dependencies and transpile ES2015+


Quick start
-----------

1. Add "npm_mjs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'npm_mjs',
    ]

2. Add "static-transpile" template tags to your templates. All entry files to ES2015+ modules need to have \*.mjs endings.

3. Run `./manage.py transpile`.

4. Run `./manage.py runserver`. Your ES2015 modules will be served as browser compatible ES5 files.


NPM.JS dependencies
-----------

1. Add package.json files into one or more of your apps. All package.json files will be merged.

2. Import in your JS files from any of the npm modules specified in your package.json files.

3. Run `./manage.py transpile`.

4. Run `./manage.py runserver`.
