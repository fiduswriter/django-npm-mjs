# django-npm-mjs
A Django package to use npm.js dependencies and transpile ES2015+

This package is used by Fidus Writer to bundle JavaScript. We try to keep it as generic as possible, so if there is something that seems very odd and specific to Fidus Writer, it is likely just an oversight from us. Please contact us and we'll see what we can do about it.

This package similar to django-compressor in that it treats JavaScript files before they are served to the user. But there are some differences:

* It does not mix different JavaScript module entry files. It only bundles everything imported from one entry file. With ES2015+ there is not as much need to have lots of JavaScript files operating in the global namespace.

* It allows importing from one django app in another app within the same project as if they were in the same folder similar to how static files and templates are handled by Django.

* It includes handling of npm.js imports.

* The JavaScript entry files' base names do not change and an automatic optional version query is added to be able to wipe the browser cache (`/js/my_file.mjs` turns into `/js/transpile/my_file.js?v=239329884`). This way it is also possible to refer to the URL from JavaScript (for example for use with web workers).

* It allows for JavaScript plugin hooks between django apps used in cases when a django project can be used both with or without a specific app, and the JavaScript from one app needs to import things from another app.


Quick start
-----------

1. Add "npm_mjs" to your INSTALLED_APPS setting like this::

        INSTALLED_APPS = [
            ...
            'npm_mjs',
        ]

2. Define a `PROJECT_PATH` in the settings as the root folder of the project::

        PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

3. Define a `SETTINGS_PATHS` in the settings to contain the paths of all setting files (settings.py + any local_settings.pyor similar file you may have defined)::

        SETTINGS_PATHS = [os.path.dirname(__file__), ]

3. Add the `static-transpile` folder inside the `PROJECT_PATH` to the `STATICFILES_DIRS` like this::

        STATICFILES_DIRS = (
            os.path.join(PROJECT_PATH, 'static-transpile'),
            ...
        )

4. Load transpile, and use `static` template tags to your templates to refer to JavaScript files.
All entry files to ES2015+ modules need to have \*.mjs endings. Entries can look like this::

        {% load transpile %}
        ...
        <script type="text/javascript" src="{% static "js/index.mjs" %}"></script>

You can continue to load other resources such as CSS files as before using the `static` template tag::

        <link type="text/css" rel="stylesheet" href="{% static "css/fonts.css" %}" />

5. Run `./manage.py transpile`.

6. Run `./manage.py runserver`. Your ES2015+ modules will be served as browser compatible JS files and all static files will have a versioned ending so that you can set your static server to let browsers cache static files indefinitely as long as DEBUG is set to False.


NPM.JS dependencies
-----------

1. Add package.json files into one or more of your apps. All package.json files will be merged.

2. Import in your JS files from any of the npm modules specified in your package.json files.

3. Run `./manage.py transpile`.

4. Run `./manage.py runserver`.

Referring to static files from JavaScript
-----------

There is two ways of adding URLs for static files as well as a timestamped version number of the last transpile run to JavaScript:

Adding static url variables with a template tag
------
1. Add `static_urls_js` template tags to your templates like this::

        {% load transpile %}
        ...
        {% static_urls_js %}

2. In your JavaScript sources, you can now use three variables to refer to urls and the version.

The base url of all static files::

        StaticUrls.base

For example::

        let userAvatar = `${StaticUrls.base}img/default_avatar.png`

The base url of transpiled JavaScript files::

        StaticUrls.transpile.base

For example::

        let downloadJS = `${StaticUrls.transpile.base}download.js` // Transpiled version of download.mjs

The version string from the last transpile run::

        StaticUrls.transpile.version

For example::

        let downloadJS = `${StaticUrls.transpile.base}download.js?v=${StaticUrls.transpile.version}` // Latest version of transpiled version of download.mjs


Adding static url variables by string replacement
------
This changes the strings directly in the produced JS files. The is useful if the files are directly consumed and no template is called. The variable names are the same. There is just a $-character before and after it.

1. In your JavaScript sources, you can now use three variables to refer to urls and the version.

The base url of all static files::

        $StaticUrls.base$

For example::

        let userAvatar = `${$StaticUrls.base$}img/default_avatar.png`

The base url of transpiled JavaScript files::

        $StaticUrls.transpile.base$

For example::

        let downloadJS = `${$StaticUrls.transpile.base$}download.js` // Transpiled version of download.mjs

The version string from the last transpile run::

        $StaticUrls.transpile.version$

For example::

        let downloadJS = `${$StaticUrls.transpile.base$}download.js?v=${$StaticUrls.transpile.version$}` // Latest version of transpiled version of download.mjs
