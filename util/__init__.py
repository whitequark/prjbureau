import os
import sys
import atexit


root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


unfinished = False


def progress(what=None):
    global unfinished
    if what is None:
        if unfinished:
            print(file=sys.stderr, flush=True)
        unfinished = False
    elif isinstance(what, str):
        if unfinished:
            print(file=sys.stderr, flush=True)
        print(what, end='', file=sys.stderr, flush=True)
        unfinished = True
    elif isinstance(what, int):
        print('.-+!*'[what], end='', file=sys.stderr, flush=True)
        unfinished = True
    elif isinstance(what, tuple):
        print(f"{what[0]}/{what[1]}", end='', file=sys.stderr, flush=True)
        unfinished = True
    else:
        assert False


atexit.register(progress)
