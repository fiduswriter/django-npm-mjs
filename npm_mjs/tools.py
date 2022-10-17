import pickle

from .paths import TRANSPILE_TIME_PATH

_last_run = {}


def load_last_name():
    global _last_run
    try:
        with open(TRANSPILE_TIME_PATH, "rb") as f:
            _last_run = {**_last_run, **pickle.load(f)}
    except (EOFError, OSError, TypeError):
        pass


def get_last_run(name):
    global _last_run
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
