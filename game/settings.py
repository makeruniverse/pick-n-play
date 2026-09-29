"""settings.json: the machine's own settings, one file for the secret menu
and the pnp-* commands alike.

    python game/settings.py                     show everything that's set
    python game/settings.py ROUND_SECONDS 150   set (the game reads it at start)
    python game/settings.py ROUND_SECONDS -     back to the default in config.py
    python game/settings.py --test              self-test

Untracked like cam.json, so neither an update nor a re-clone resets it.
Values are strings, exactly like the PNP_* environment variables they stand
in for: config.env() reads the environment first (development, one-off
runs), then this file, then the default.

Replaces the systemd drop-ins of 29.9.: those needed root and a
daemon-reload, and the game couldn't write them from its own menu.

A change goes on trial. Every start after it counts one; if the game gets to
start a third time before it has run TRIAL_OK seconds, the change is what
kills it, and the previous file comes back by itself. That makes every
setting in the menu safe to try at the fair: the worst case is two
restarts, not a machine that's dead until someone with SSH turns up.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FILE = os.path.join(ROOT, "settings.json")
PREV, TRIAL = FILE + ".prev", FILE + ".trial"
TRIAL_OK = 60     # seconds of healthy running that make a change stick


def load(path=FILE):
    """The settings, {} for a missing or broken file -- never an exception:
    this runs while config.py is imported, and a crash there is a loop."""
    try:
        with open(path) as f:
            d = json.load(f)
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(path, d):
    """Whole file or nothing: a pulled plug mid-write keeps the old one."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def save(changes, path=FILE):
    """Apply {key: value}, None removes the key. Keeps the old file as .prev
    and puts the change on trial. Returns the new settings."""
    old = load(path)
    new = {**old, **{k: str(v) for k, v in changes.items() if v is not None}}
    for k, v in changes.items():
        if v is None:
            new.pop(k, None)
    if new != old:
        _write(path + ".prev", old)
        _write(path, new)
        with open(path + ".trial", "w") as f:
            f.write("0")
    return new


def boot(path=FILE):
    """Called first thing in main.py, before config is imported. Counts the
    starts of a change on trial and rolls it back on the third."""
    try:
        with open(path + ".trial") as f:
            n = int(f.read() or 0)
    except (OSError, ValueError):
        return None
    if n < 2:
        with open(path + ".trial", "w") as f:
            f.write(str(n + 1))
        return None
    _write(path, load(path + ".prev"))
    os.remove(path + ".trial")
    print("settings: the last change crashed the game twice, rolled back", flush=True)
    return "rolled back"


def ok(path=FILE):
    """The game has run TRIAL_OK seconds: the change sticks."""
    try:
        os.remove(path + ".trial")
    except FileNotFoundError:
        pass


def test():
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "s.json")
    assert load(p) == {}
    open(p, "w").write("{broken")
    assert load(p) == {}, "a broken file reads as empty"
    save({"ROUND_SECONDS": 150}, p)
    assert load(p) == {"ROUND_SECONDS": "150"}
    ok(p)
    save({"LAYOUT": "top"}, p)
    assert boot(p) is None and boot(p) is None, "two starts are allowed"
    assert boot(p) == "rolled back" and load(p) == {"ROUND_SECONDS": "150"}
    assert boot(p) is None, "trial is over"
    save({"ROUND_SECONDS": None}, p)
    assert load(p) == {}
    print("ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--test"]:
        test()
    elif len(a) == 2:
        save({a[0]: None if a[1] == "-" else a[1]})
        ok()    # set by hand over SSH: whoever did it is watching
        print(f"{a[0]} = {load().get(a[0], 'default')}")
    elif len(a) == 1:
        print(load().get(a[0], "default"))
    else:
        for k, v in sorted(load().items()):
            print(f"{k}={v}")
