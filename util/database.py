import os.path
import json
import contextlib

from . import root_dir


def load():
    with open(os.path.join(root_dir, "database.json")) as f:
        return json.load(f)


def save(database):
    with open(os.path.join(root_dir, "database.json.new"), "w") as f:
        json.dump(database, f, indent=2)
    os.rename(os.path.join(root_dir, "database.json.new"),
              os.path.join(root_dir, "database.json"))


@contextlib.contextmanager
def transact():
    db = load()
    yield db
    save(db)
