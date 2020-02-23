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

3. Define a `PROJECT_PATH` in the settings as the root folder of the project::

        PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

4. Define a `SETTINGS_PATHS` in the settings to contain the paths of all setting files (settings.py + any local_settings.pyor similar file you may have defined)::

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
-----------

1. Add package.json files into one or more of your apps. All package.json files will be merged.

2. Import in your JS files from any of the npm modules specified in your package.json files.

3. Run `./manage.py transpile`.

4. Run `./manage.py runserver`.

Referring to the transpile version within JavaScript sources
------

In your JavaScript sources, you can refer to the version string of the last transpile run like this::

        transpile.VERSION

For example::

        let downloadJS = `download.js?v=${transpile.VERSION}` // Latest version of transpiled version of download.mjs
