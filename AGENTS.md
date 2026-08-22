# AGENTS.md — django-npm-mjs

`django-npm-mjs` is a Django app used by Fidus Writer to manage JavaScript
build assets. It merges `package.json5` files from installed Django apps,
installs npm dependencies with pnpm, and runs `rspack` to transpile the browser
bundle.

## Repository layout

| Path | Purpose |
|------|---------|
| `npm_mjs/management/commands/` | Django management commands: `transpile`, `create_package_json`, `npm_install`, `collectstatic`, `makemessages`. |
| `npm_mjs/package_discovery.py` | Discovers npm packages in installed Django apps and namespace packages. |
| `npm_mjs/json5_parser.py` | JSON5 parser used to read `package.json5` files. |
| `npm_mjs/storage.py` | Static-file storage helpers. |
| `npm_mjs/tests/` | Unit tests. |

## Test

```bash
python runtests.py
```

## Lint / formatting

The project uses `pre-commit`:

```bash
pre-commit run --all-files
```

## How Fidus Writer uses this package

- Each Django app may declare npm dependencies in a `package.json5` file.
- `django-npm-mjs` merges these into a single `package.json` in the
  `.transpile/` cache directory.
- `pnpm install` is run in `.transpile/` to install dependencies.
- Since version 5.0, JS/TS **sources** are read from each app's
  `assets/js/` and `assets/ts/` folders (previously `static/js/`). The app's
  `static/` folder is output-only territory (plus non-transpiled files such as
  CSS/images).
- `rspack` transpiles entry-point `*.mjs` files into
  `static-transpile/js/`.
- After transpilation, missing third-party source maps are copied from
  `node_modules` into `static-transpile/js/` so that static-file servers do
  not log errors for missing `.map` requests.

## Release checklist

1. Make the source changes.
2. Run `python runtests.py` and `pre-commit run --all-files`.
3. Bump the version in `pyproject.toml` (or with your build backend's
   preferred mechanism).
4. Build and publish to PyPI.
5. Push commits and tags.
6. Update `django-npm-mjs` in Fidus Writer's `requirements.txt` and install
   the new version in the Fidus Writer environment.
