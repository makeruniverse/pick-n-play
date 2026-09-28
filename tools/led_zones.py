"""Find out which LED sits where on the cabinet, and write it down as zones.

On the Pi, game stopped: `pnp-zones` (or `pnp-zones 0.3` for dimmer). A
white cursor walks the strip, every 50th free LED is a faint red ruler
mark. Mark where a span starts, walk to where it ends, say what it is.
Marked side spans turn green, center spans blue.

    123         cursor to LED 123
    +20 / -5    move the cursor, enter repeats the last move
    a           a span starts at the cursor
    side        ... and ends at the cursor: a side span. The time bar
                drains toward its start, so start a wall at the floor
    center      ... and ends at the cursor: a top-center span
    u           undo the last span
    t           preview idle / game / hurry / score with these zones
    q           done

It starts from what config.py has and prints LED_SIDES / LED_CENTER at the
end. Those two lines go into game/config.py *in git* (branch expo): the
Pi's auto-update checks out with -f and drops edits made on the Pi.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
from config import LED_COUNT, LED_SIDES, LED_CENTER, LED_FPS  # noqa: E402
from hw import Leds, led_frame, led_span                        # noqa: E402

COLORS = {"side": (0, 90, 0), "center": (0, 0, 120)}


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
        print(" ", state, flush=True)
        end = time.monotonic() + 4
        while (now := time.monotonic()) < end:
            # game: the whole round squeezed into 4 s, so the bars visibly drain
            leds.show(led_frame(state, (end - now) / 4, now - t0, n,
                                zones["side"], zones["center"]))
            time.sleep(1 / LED_FPS)


def main():
    n = LED_COUNT
    zones = {"side": list(LED_SIDES), "center": list(LED_CENTER)}
    done = ["side"] * len(LED_SIDES) + ["center"] * len(LED_CENTER)  # for u
    cur, start, step = 0, None, 1
    leds = Leds()
    print(__doc__)
    try:
        while True:
            leds.show(picture(n, zones, cur, start))
            span = "" if start is None else f"  (span from {start})"
            cmd = input(f"LED {cur}{span} > ").strip()
            if cmd == "q":
                break
            try:
                if cmd == "" or cmd[0] in "+-":
                    step = int(cmd or step)
                    cur += step
                elif cmd.isdigit():
                    cur = int(cmd)
                elif cmd == "a":
                    start = cur
                elif cmd in zones:
                    if start is None:
                        print("mark the start with a first")
                        continue
                    zones[cmd].append((start, cur))
                    done.append(cmd)
                    start = None
                elif cmd == "u" and done:
                    print("  undone:", zones[done[-1]].pop(), done.pop())
                elif cmd == "t":
                    preview(leds, n, zones)
                else:
                    print(__doc__)
            except ValueError:
                print(__doc__)
            cur = min(max(cur, 0), n - 1)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        leds.close()
        print(f"\n# into game/config.py:\nLED_SIDES   = {zones['side']}\n"
              f"LED_CENTER  = {zones['center']}")


if __name__ == "__main__":
    main()
