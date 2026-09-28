"""pnp-led: mark which LED is side and which is top center, saved right away.

  <- ->       cursor 1 LED          white = cursor, faint red = every 50th
  up down     10 LEDs               green = side, blue = center
  PgUp PgDn   100 LEDs              yellow = span being marked
  g           go to LED number
  space       span starts here
  s           span ends here: side   (the time bar drains toward its start,
                                      so start a wall at the floor)
  c           span ends here: center
  Esc         drop the started span
  u           undo the last span
  t           preview idle / game / hurry / score with these zones
  q           quit
"""
import json
import os
import sys
import termios
import time
import tty

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
from config import LED_COUNT, LED_SIDES, LED_CENTER, LED_FPS, LED_ZONES  # noqa: E402
from hw import Leds, led_frame, led_span                                  # noqa: E402

MOVES = {"\x1b[C": 1, "\x1b[D": -1, "\x1b[A": 10, "\x1b[B": -10,
         "\x1b[5~": 100, "\x1b[6~": -100}
COLORS = {"side": (0, 90, 0), "center": (0, 0, 120)}


def tokens(data):
    """Bytes from one read -> moves (int) and keys (str). A held arrow key
    delivers several escape sequences per read."""
    out = []
    while data:
        seq = next((s for s in MOVES if data.startswith(s)), data[0])
        out.append(MOVES.get(seq, seq))
        data = data[len(seq):]
    return out


def picture(n, zones, cur, start):
    rgb = np.full((n, 3), 6)
    rgb[::50] = (70, 0, 0)
    for name, spans in zones.items():
        for a, b in spans:
            rgb[led_span(a, b, n)] = COLORS[name]
    if start is not None:
        rgb[led_span(start, cur, n)] = (110, 80, 0)
    rgb[cur] = 255
    return rgb


def preview(leds, n, zones):
    t0 = time.monotonic()
    for state in ("idle", "game", "hurry", "score"):
        print(f"\r\x1b[K  preview: {state}", end="", flush=True)
        end = time.monotonic() + 4
        while (now := time.monotonic()) < end:
            # game: the whole round squeezed into 4 s, so the bars visibly drain
            leds.show(led_frame(state, (end - now) / 4, now - t0, n,
                                zones["side"], zones["center"]))
            time.sleep(1 / LED_FPS)


def save(zones):
    """Temp file + rename: a pulled plug leaves the old file, not half a one."""
    with open(LED_ZONES + ".tmp", "w") as f:
        json.dump(zones, f)
    os.replace(LED_ZONES + ".tmp", LED_ZONES)


def main():
    n = LED_COUNT
    zones = {"side": list(LED_SIDES), "center": list(LED_CENTER)}
    done = ["side"] * len(LED_SIDES) + ["center"] * len(LED_CENTER)   # for u
    cur, start = 0, None
    fd = sys.stdin.fileno()
    tty_mode = termios.tcgetattr(fd)
    leds = Leds()
    print(__doc__)
    try:
        tty.setcbreak(fd)     # keys without Enter; Ctrl-C still works
        while True:
            leds.show(picture(n, zones, cur, start))
            span = "" if start is None else f"   span from {start}"
            print(f"\r\x1b[K  LED {cur}{span}   side {zones['side']}   "
                  f"center {zones['center']}", end="", flush=True)
            for k in tokens(os.read(fd, 64).decode(errors="ignore")):
                if isinstance(k, int):
                    cur = min(max(cur + k, 0), n - 1)
                elif k == " ":
                    start = cur
                elif k == "\x1b":
                    start = None
                elif k in ("s", "c") and start is not None:
                    name = "side" if k == "s" else "center"
                    zones[name].append([start, cur])
                    done.append(name)
                    start = None
                    save(zones)
                elif k == "u" and done:
                    zones[done.pop()].pop()
                    save(zones)
                elif k == "g":
                    termios.tcsetattr(fd, termios.TCSADRAIN, tty_mode)
                    try:
                        cur = min(max(int(input("\r\x1b[K  go to LED: ")), 0), n - 1)
                    except ValueError:
                        pass
                    tty.setcbreak(fd)
                elif k == "t":
                    preview(leds, n, zones)
                elif k == "q":
                    return
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, tty_mode)
        leds.close()
        print(f"\n\nsaved in {os.path.normpath(LED_ZONES)}. "
              "The game reads it at start: pnp-expo")


if __name__ == "__main__":
    main()
