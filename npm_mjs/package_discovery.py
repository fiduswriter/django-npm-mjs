import importlib.util
import os
import pkgutil
import sys

from django.apps import apps as django_apps
from django.conf import settings


def _iter_top_level_package_dirs():
    """Yield directories of all top-level packages."""
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
            yield package_dir


def _iter_namespace_package_dirs(ns):
    """Yield directories of subpackages under an importable namespace."""
    try:
        ns_module = importlib.import_module(ns)
        ns_path = getattr(ns_module, "__path__", None)
        if not ns_path:
            return
        for _, modname, ispkg in pkgutil.iter_modules(ns_path):
            if not ispkg:
                continue
            spec = importlib.util.find_spec(f"{ns}.{modname}")
            if spec and spec.submodule_search_locations:
                yield list(spec.submodule_search_locations)[0]
    except ImportError:
        pass


def _iter_namespace_package_dirs_from_path(ns):
    """Yield directories of subpackages by scanning sys.path for the namespace.

    This is a fallback for when the namespace package itself cannot be
    imported but its subpackages are still present on sys.path (for example
    when a namespace subpackage is installed while the parent namespace is
    provided by an un-importable source layout).
    """
    ns_parts = ns.split(".")
    for path in sys.path:
        ns_dir = os.path.join(path, *ns_parts)
        if not os.path.isdir(ns_dir):
            continue
        for _, modname, ispkg in pkgutil.iter_modules([ns_dir]):
            if not ispkg:
                continue
            subpkg_dir = os.path.join(ns_dir, modname)
            if os.path.isdir(subpkg_dir):
                yield subpkg_dir


def _iter_package_dirs():
    """Yield directories of installed packages to scan for package.json."""
    namespaces = getattr(settings, "NPM_MJS_PACKAGE_NAMESPACES", None)

    if namespaces is None:
        # Default: scan all top-level packages
        for package_dir in _iter_top_level_package_dirs():
            yield package_dir
        return

    # Restricted: scan specified namespace packages
    found_any = False
    for ns in namespaces:
        for package_dir in _iter_namespace_package_dirs(ns):
            yield package_dir
            found_any = True
        # Also scan sys.path directly for the namespace, in case the parent
        # namespace module is not importable.
        for package_dir in _iter_namespace_package_dirs_from_path(ns):
            yield package_dir
            found_any = True

    # If namespace scanning found nothing (e.g. a development setup where
    # plugins are symlinked in as top-level packages), fall back to scanning
    # all top-level packages. This keeps package discovery in sync with
    # transpile, which already scans top-level packages for static files.
    if not found_any:
        for package_dir in _iter_top_level_package_dirs():
            yield package_dir


def get_package_dirs():
    """Find directories of all Django apps and configured extra packages."""
    dirs = set()

    # Add all configured Django apps
    for config in django_apps.get_app_configs():
        dirs.add(config.path)

    # Add extra packages
    for package_dir in _iter_package_dirs():
        dirs.add(package_dir)

    return dirs
