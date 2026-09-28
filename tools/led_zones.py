"""pnp-led: mark which LED is side and which is top center, saved right away.

  s ... s     side span: s on its first LED, walk, s on its last LED.
              The time bar drains toward the first one: start a wall at the floor
  c ... c     top-center span, same way
  Esc         drop the span you started      u   undo the last saved span

  <- ->  1 LED    up down  10 LEDs    PgUp PgDn  100 LEDs    g  go to LED number
  t      preview idle / game / hurry / score with these zones      q  quit

  On the strip: white = cursor, green = side, blue = center, faint red = every
  50th LED. The span you're marking right now is lit brighter.
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


def picture(n, zones, cur, open_):
    rgb = np.full((n, 3), 6)
    rgb[::50] = (70, 0, 0)
    for name, spans in zones.items():
        for a, b in spans:
            rgb[led_span(a, b, n)] = COLORS[name]
    if open_:
        name, start = open_
        rgb[led_span(start, cur, n)] = np.multiply(COLORS[name], 2.5)
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
    cur, open_ = 0, None      # open_: (zone, first LED) while a span is being marked
    fd = sys.stdin.fileno()
    tty_mode = termios.tcgetattr(fd)
    leds = Leds()
    print(__doc__)
    say = lambda msg: print(f"\r\x1b[K  {msg}")   # a line that stays
    try:
        tty.setcbreak(fd)     # keys without Enter; Ctrl-C still works
        while True:
            leds.show(picture(n, zones, cur, open_))
            # One short line, rewritten in place -- if it wrapped, \r would
            # only go back to the start of the last row.
            nxt = (f"{open_[0]} from {open_[1]}: {open_[0][0]} = ends here, Esc = drop"
                   if open_ else "s = side starts here, c = center starts here")
            print(f"\r\x1b[K  LED {cur:>4}   {nxt}", end="", flush=True)
            for k in tokens(os.read(fd, 64).decode(errors="ignore")):
                if isinstance(k, int):
                    cur = min(max(cur + k, 0), n - 1)
                elif k in ("s", "c"):
                    name = "side" if k == "s" else "center"
                    if open_ and open_[0] == name:
                        zones[name].append([open_[1], cur])
                        done.append(name)
                        save(zones)
                        say(f"saved: {name} {open_[1]} -> {cur}   "
                            f"({len(zones['side'])} side, {len(zones['center'])} center)")
                        open_ = None
                    else:     # new span, or the other key: switch type, keep the start
                        open_ = (name, open_[1] if open_ else cur)
                elif k == "\x1b":
                    open_ = None
                elif k == "u":
                    if done:
                        name = done.pop()
                        a, b = zones[name].pop()
                        save(zones)
                        say(f"undone: {name} {a} -> {b}")
                    else:
                        say("nothing to undo")
                elif k == "g":
                    termios.tcsetattr(fd, termios.TCSADRAIN, tty_mode)
                    try:
                        cur = min(max(int(input("\r\x1b[K  go to LED: ")), 0), n - 1)
                    except ValueError:
                        pass
                    tty.setcbreak(fd)
                elif k == "t":
                    preview(leds, n, zones)
                    say("preview done")
                elif k == "q":
                    return
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, tty_mode)
        leds.close()
        print(f"\n\n  side   {zones['side']}\n  center {zones['center']}\n"
              f"  in {os.path.normpath(LED_ZONES)}. The game reads it at start: pnp-expo")


if __name__ == "__main__":
    main()
