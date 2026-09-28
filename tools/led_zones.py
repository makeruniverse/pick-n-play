"""pnp-led: mark which LED is side and which is top center, saved right away.

  s ... s     side span: s on its first LED, walk, s on its last LED
  c ... c     top-center span, same way
  Esc         drop the span you started

  <- ->  1 LED    up down  10 LEDs    PgUp PgDn  100 LEDs    g  go to LED number

  Cursor on a saved span:   r  flip its direction    x  delete it
  u  undo the last saved span      q  quit (everything is saved already)

On the strip, live:
  white          the cursor              faint red   every 50th LED
  marching dash  the span you're marking, running from its first LED to the cursor
  fuse           a side span as in a round: it burns down toward its first LED,
                 every 4 s. Burning the wrong way? Cursor on it, r
  full white     a center span, lighting the playfield as in a round
"""
import json
import os
import select
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
COLORS = {"side": (0, 255, 0), "center": (0, 80, 255)}   # span being marked
DRAIN = 4.0     # s for one side fuse to burn down in the live view


def tokens(data):
    """Bytes from one read -> moves (int) and keys (str). A held arrow key
    delivers several escape sequences per read."""
    out = []
    while data:
        seq = next((s for s in MOVES if data.startswith(s)), data[0])
        out.append(MOVES.get(seq, seq))
        data = data[len(seq):]
    return out


def picture(n, zones, cur, open_, t):
    """The strip while marking: saved spans play what they'll show in a round."""
    rgb = np.full((n, 3), 6.0)
    rgb[::50] = (70, 0, 0)
    live = led_frame("game", 1 - t % DRAIN / DRAIN, t, n, zones["side"], zones["center"])
    for spans in zones.values():
        for a, b in spans:
            idx = led_span(a, b, n)
            rgb[idx] = live[idx]
    if open_:
        name, start = open_
        idx = led_span(start, cur, n)
        on = ((np.arange(len(idx)) - int(t * 15)) // 3) % 2 == 0    # dashes march start -> cursor
        rgb[idx] = np.where(on[:, None], COLORS[name], np.multiply(COLORS[name], 0.15))
    rgb[cur] = 255
    return rgb


def under(zones, cur):
    """(zone, index) of the saved span the cursor sits on, or None."""
    return next(((name, i) for name, spans in zones.items()
                 for i, (a, b) in enumerate(spans) if min(a, b) <= cur <= max(a, b)), None)


def save(zones):
    """Temp file + rename: a pulled plug leaves the old file, not half a one."""
    with open(LED_ZONES + ".tmp", "w") as f:
        json.dump(zones, f)
    os.replace(LED_ZONES + ".tmp", LED_ZONES)


def status(zones, cur, open_):
    if open_:
        name, start = open_
        return (f"marking {name} {start} -> {cur}   {name[0]} = ends here, "
                f"{'c' if name == 'side' else 's'} = make it {'center' if name == 'side' else 'side'}, Esc = drop")
    on = under(zones, cur)
    if on:
        a, b = zones[on[0]][on[1]]
        return f"on {on[0]} {a} -> {b}   r = flip, x = delete   (s / c starts a new span here)"
    return "s = side starts here   c = center starts here"


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
    shown, t0 = None, time.monotonic()
    try:
        tty.setcbreak(fd)     # keys without Enter; Ctrl-C still works
        while True:
            leds.show(picture(n, zones, cur, open_, time.monotonic() - t0))
            # One short line, rewritten in place -- if it wrapped, \r would
            # only go back to the start of the last row.
            line = f"LED {cur:>4}   {status(zones, cur, open_)}"
            if line != shown:
                print(f"\r\x1b[K  {line}", end="", flush=True)
                shown = line
            if not select.select([fd], [], [], 1 / LED_FPS)[0]:
                continue      # no key: next frame of the animation
            shown = None
            for k in tokens(os.read(fd, 64).decode(errors="ignore")):
                if isinstance(k, int):
                    cur = min(max(cur + k, 0), n - 1)
                elif k in ("s", "c"):
                    name = "side" if k == "s" else "center"
                    if open_ and open_[0] == name:
                        zones[name].append([open_[1], cur])
                        done.append(name)
                        save(zones)
                        say(f"saved: {name} {open_[1]} -> {cur}")
                        open_ = None
                    else:     # new span, or the other key: switch type, keep the start
                        open_ = (name, open_[1] if open_ else cur)
                elif k == "\x1b":
                    open_ = None
                elif k in ("r", "x") and under(zones, cur):
                    name, i = under(zones, cur)
                    a, b = zones[name][i]
                    if k == "r":
                        zones[name][i] = [b, a]
                        say(f"flipped: {name} {b} -> {a}")
                    else:
                        del zones[name][i]
                        done.remove(name)
                        say(f"deleted: {name} {a} -> {b}")
                    save(zones)
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
