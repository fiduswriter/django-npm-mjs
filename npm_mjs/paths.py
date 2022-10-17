import os

from django.conf import settings

PROJECT_PATH = str(
    getattr(settings, "PROJECT_PATH", getattr(settings, "PROJECT_DIR", "./")),
)

TRANSPILE_CACHE_PATH = os.path.join(PROJECT_PATH, ".transpile/")
TRANSPILE_TIME_PATH = os.path.join(TRANSPILE_CACHE_PATH, "time")

SETTINGS_PATHS = [str(x) for x in getattr(settings, "SETTINGS_PATHS", [])]

STATIC_ROOT = str(getattr(settings, "STATIC_ROOT", "./static/"))
