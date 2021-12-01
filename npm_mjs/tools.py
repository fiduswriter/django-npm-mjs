import os
import pickle

from django.conf import settings


if settings.PROJECT_PATH:
    PROJECT_PATH = settings.PROJECT_PATH
else:
    PROJECT_PATH = "./"

TRANSPILE_CACHE_PATH = os.path.join(PROJECT_PATH, ".transpile/")
TRANSPILE_TIME_PATH = os.path.join(TRANSPILE_CACHE_PATH, "time")

_last_run = {}


def load_last_name():
    global _last_run
    try:
        with open(TRANSPILE_TIME_PATH, "rb") as f:
            _last_run = {**_last_run, **pickle.load(f)}
    except (EOFError, IOError, TypeError):
        pass


def get_last_run(name):
    if name not in _last_run:
        load_last_name()
        if name not in _last_run:
            return 0
    return _last_run[name]


def set_last_run(name, timestamp):
    global _last_run
    load_last_name()
    _last_run[name] = timestamp
    with open(TRANSPILE_TIME_PATH, "wb") as f:
        pickle.dump(_last_run, f)
