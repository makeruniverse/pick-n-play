"""pnp-cam: camera controls live, saved to cam.json for every game start.

  pnp-cam                     current values of both cameras
  pnp-cam top exposure 60     manual exposure in 100 us (1..10000), lower = darker
  pnp-cam arm exposure auto   back to the camera's own exposure
  pnp-cam top zoom 46         also gain, brightness, gamma, or any v4l2 name
  pnp-cam snap                both frames, top with the detection box, as jpg
  pnp-cam --test              self-test, no hardware
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
NAMES = {"exposure": "exposure_time_absolute", "zoom": "zoom_absolute"}
SHOW  = "auto_exposure,exposure_time_absolute,gain,brightness,gamma,zoom_absolute"


def plan(name, value):
    """('exposure', '60') -> the controls to set, in order: exposure_time is
    refused while auto_exposure isn't manual (1)."""
    name = NAMES.get(name, name)
    if name == "exposure_time_absolute":
        return {"auto_exposure": 3} if value == "auto" else {"auto_exposure": 1, name: int(value)}
    return {name: int(value)}


def main(argv):
    from config import CAM_INDEXES, CAM_CTRLS_FILE
    roles = dict(zip(("arm", "top"), CAM_INDEXES))

    def ctl(role, *args):
        r = subprocess.run(["v4l2-ctl", "-d", f"/dev/video{roles[role]}", *args],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"{role}: {r.stderr.strip()}")
        return r.stdout

    if argv == ["snap"]:
        # The game holds the cameras, so it saves the frames itself (SIGUSR1).
        # ^/ skips pnp-start's `timeout` wrapper, which USR1 would kill.
        t = time.time()
        if subprocess.run(["pkill", "-USR1", "-f", "^/[^ ]*/python game/main.py"]).returncode:
            sys.exit("game isn't running")
        time.sleep(1)
        for d in ("/run/pnp", "/tmp"):
            for r in roles:
                p = f"{d}/cam-{r}.jpg"
                if os.path.exists(p) and os.path.getmtime(p) >= t:
                    print(p)
        return
    if argv:
        if len(argv) != 3 or argv[0] not in roles:
            sys.exit(__doc__)
        role, name, value = argv
        ctrls = plan(name, value)
        for k, v in ctrls.items():
            ctl(role, "-c", f"{k}={v}")
        try:
            with open(CAM_CTRLS_FILE) as f:
                saved = json.load(f)
        except FileNotFoundError:
            saved = {}
        saved.setdefault(role, {}).update(ctrls)
        if value == "auto":
            saved[role].pop("exposure_time_absolute", None)
        with open(CAM_CTRLS_FILE, "w") as f:
            json.dump(saved, f, indent=1)
    for r in roles:
        print(f"{r:4}", "  ".join(l.strip() for l in ctl(r, "-C", SHOW).splitlines()))


if __name__ == "__main__":
    if "--test" in sys.argv:
        assert plan("exposure", "60") == {"auto_exposure": 1, "exposure_time_absolute": 60}
        assert plan("exposure", "auto") == {"auto_exposure": 3}
        assert plan("zoom", "46") == {"zoom_absolute": 46}
        assert plan("gain", "80") == {"gain": 80}
        print("ok")
    else:
        main(sys.argv[1:])
