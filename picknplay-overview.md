# PICK'N'PLAY — Project Overview

**Title:** PICK'N'PLAY (previous working title: TRAY RUNNER)
**Status:** August 2026 · concept finished, hardware in progress, software in progress
**Platform:** Raspberry Pi · Python · pygame

---

## UX overhaul: story, practice, visible prices (2026-09-21)

The first cabinet test showed that the arm is much harder than expected.
The game stacked two hard things on top of each other: steering the arm and
mental arithmetic with hidden prices. Now the arm is the only challenge,
and everything else is there to help. The players are grades 7 to 12.

**One concept instead of a Frankenstein.** You're helping out in Bella's
bakery. Oskar has a birthday and exactly X euros, and you put together
treats for him. Bigger means more expensive, and **the prices are visible
the whole time** in a strip under the bar. The hidden price (decision from
2026-09-11) is dropped: it could be computed from the ADD value anyway, so
it only ever created arithmetic, never a secret.

**Flow:** Idle → name → Bella (player number) → practice → order → round →
score. The practice waits until the camera sees the first treat. That's the
first success, before any clock is running. The treat stays on the tray,
and `gap(on, up=True)` rolls the target from there.

**Feedback where people are looking:**
- every detected marker gets a frame in the camera image
- every change gets a pop-up ("+3,20") between the panes
- Oskar sweats when the tray is over budget and beams when it's exact
- after 20 s without a change, the treat that gets you closest hops

The red screen is gone. Only the LEDs still show "hurry", as a signal for
the team.

**Timer as a fuse** around the screen edge. It takes no space from the
cameras, and the spot between the panes now belongs to Oskar.

**Score:** stars instead of five numbers. One star for any treat on the
tray, two from 700, three for exact. Plus "#4 of 23" and a line from Oskar.
The idle leaderboard shows names only, as a podium.

**Player number instead of a hash** for linking to the sign-up form. The
reason: two MAX are two people. Playing again means entering the number,
and the best round counts. `db.py export` writes the CSV, see
`docs/operation.md`.

**German/English** via `TEXT` in the theme, default `en`, ▲▲ in idle
switches. Press Start 2P draws Ä/Ö/Ü shortened (no room for the dots above
capitals at 8×8). That's the font, not a bug.

**Characters:** 32×32 grids in the theme (`EXTRAS`), mirrored from left
halves. Bella and Oskar are fictional on purpose. The text box talks with
four random blips (`talk0..3`), like Animal Crossing.

**Measured, not guessed:** `runs.first` stores the seconds until the first
treat. That's the number that shows whether people fail at the arm or at
the puzzle.

**Not tested:** real camera, real buttons, and the Pi (heat with the
additional sprites). Everything else, headless: layout self-test in both
languages, one full run with music and DB.

---

## Scoring (2026-09-11)

The scoring system had been completely open since 2026-09-10 and no longer is.

**Before:** `score = |target − tray sum|`, low is good, leaderboard sorted
ascending — plus two explanatory lines (`THE LOWER THE BETTER`,
`LOWER MEANS BETTER`), without which you'd read the list backwards. The
finding was that the number needed a set of instructions.

**Now:** 0 to 1000, high is good, made of two parts:

```
accuracy = 900 · (1 − off/distance) ²      distance = gap at round start
time     = 100 · time_left/(30 − 3)        only ≠ 0 when perfect
```

Three decisions are baked into this:

**What's scored is the fraction of the distance closed, not the absolute
error.** An absolute scale needs a constant ("this many points per 10
cents") that has to be re-guessed every time prices change. The fraction
needs none. A side effect that almost single-handedly solves the tie
problem: two players, both EUR 0.30 off, get different scores if their
starting distance was different.

**The time bonus can only be earned on a perfect score — no special-case
branch needed.** The round only ends early via `PERFECT_HOLD`, so time
left > 0 is equivalent to a hit. Someone who's off and thinks instead of
rushing loses nothing because of it, and that matters: the skill of the
game is estimating.

**The database keeps storing the physical truth** (`off`, `dist`,
`secs`), not the score. A changed formula therefore applies retroactively
to old rounds too. The price: the leaderboard is no longer an `ORDER BY`,
because the score is a ratio — `top()` reads every row and computes in
Python. A trade-show day is a few hundred rows.

**Prices instead of points.** Ten cupcakes from EUR 1.40 to EUR 5.20.
Calculated in 10-cent units, because the prices must be coprime — round
prices in cents would have a GCD of 10, and the game would be binary
again (distance divisible by the divisor → one grab is enough, otherwise
unreachable at all). Division happens exactly once, in `euro()` in
`scenes.py`.

**Round length and difficulty are now a mode.** `MODES` in
`config.py`, switchable with `PNP_MODE`, individual values with
`PNP_ROUND_SECONDS=20` — the numbers are still being tuned a lot, and a
hard mode is just another entry in the dict, not a code change.

**Two follow-on findings, both measured instead of guessed:**

`GAP_MOVES` had to go from 3 to 2. A teleoperated pick takes 10–20 s; with
a 30-second round, three moves would be a promise the arm can't keep —
and the old self-test showed that 113 of 200 rounds would actually have
needed three.

The bar had the wrong scale. It was the sum of all ten cupcakes
(EUR 31.10), but since the tray starts empty, everything now plays out
under `GAP_MAX` (EUR 9.80) — the finish line and the fill sat in the left
quarter. Now `SCALE = GAP_MAX`.

**Open, and only to be settled at the machine:** whether `GAP_ONE_MAX = 25`
gives the right variety. With an empty tray, the set of possible targets
is finite and the same every day — at 15 there would be 14 targets, at
25 there are 21. The self-test in `balance.py` prints the number on
every run.

## Status: 2026-09-11

**The game runs on the Mac**, no branch needed: `config.MAC` sets window
mode, arrow keys, and the built-in webcam as the default there for both
panes. The machine itself is Linux, nothing changes for it.

**The objects are cupcakes, their value is their price** — harder to
grab means pricier. Markers as SVG (`tools/marker_svg.py`), a cone
topping with the marker extruded into it from above, a chocolate cake
with an inverted marker (`detectInvertedMarker`). A color test against
the Bambu PLA mat table is in `docs/todo.md`.

**New look "Sugar Rush"**: chocolate background, pink instead of yellow,
pixel sprites in `game/sprites.py`, conveyor belts in idle, candy-cane
bars, sprinkles. The layout coordinates are unchanged. **Not measured on
the Pi yet** — drawing there was 1.5 ms per frame, the sprites are
pre-rendered blits, but it hasn't been re-measured.

**The theme is swappable.** Colors, text, sprites, LED colors, and the
marker → sprite mapping live in one file, `game/themes/sugar_rush.py`.
`config.py` loads it via `PNP_THEME` and `THEME_KEYS` names what every
theme must provide. Scenes never name a sprite, they read `LADDER` (the
objects by price). A second theme (PCB components) is a copy of the
file. Deliberately not in the theme: HPI red/orange, button colors,
`VALUES`, title, music.

**LED module written** (`hw.Leds`, direct SPI), untested on the actual
strip.

---

## Status: 2026-09-10

**The machine runs at a stable 30 fps, with the game and teleop running
at the same time.** That had been the open item blocking sign-off since
2026-09-09. Measured on the machine, 45 seconds straight: 29.4 to
30.3 fps, no drop, while going from 61.5 to 75.7 °C.

Four changes, in order of their yield:

1. **`pygame.SCALED` is gone, rendering is now native at 1920 × 1080.**
   This was by far the biggest item and the worst-estimated one: the
   guess was 8.5 ms, the actual figure was around 20. The scene itself
   draws in 1.4 to 2.0 ms — the 25 ms that used to be booked as "scene +
   flip" were almost entirely the 1200 → 1080 scaling.
2. **The curvature no longer warps the image, it warps the scanlines.**
   It now lives in the darkening map that's built once at startup and
   costs nothing at runtime. See "Measurement on the Pi".
3. **Target frame rate 30 instead of 60**, idle 15 instead of 20.
   Rationale in `config.py` and below.
4. **`cv2.setNumThreads(3)`** — otherwise OpenCV grabs all four cores
   and crowds out exactly the teleop loop, the one process that's
   actually time-critical.

To make this work, the layout was **re-laid-out for the 1080 grid, not
scaled**: a plain ×0.9 would have compressed the line spacing relative
to the unchanged glyph height, and that's exactly where the clipping bug
from 2026-08-28 sat. The cursor bar in `LeaderboardScene` went in the
process from a magic number to `CURSOR_Y`/`CURSOR_H` — it used to be a
`fill()` and therefore invisible to the layout self-test, blind to
exactly the class of bug the test was built for.

**Two incidental findings:**

The git repo on the Pi was corrupted — six objects, five of them zero
bytes long. That's the signature of a hard power-off, not a dying card:
`dmesg` shows not a single I/O or EXT4 message. Fixed by setting the
broken objects aside and re-fetching from origin.

The Pi throttles when measuring even with teleop *stopped*: from 63.7 to
80.7 °C in 25 seconds. The same `remap` cost 8.7 ms cold and 12.5 warm —
35% difference from temperature alone. **Any measurement without a fan
is also measuring the throttling.** Active cooling is therefore no
longer a precaution but a prerequisite for reliable numbers.

---

## Status: 2026-08-28

**UX pass over all five scenes.** The trigger was a clipping bug on the
leaderboard: the fifth leaderboard row and the cancel confirmation
overlapped by 528 × 30 px, visible only once there were five entries in
the DB. The bug wasn't a transposed digit but a missing invariant — a
data-dependent-length list and an overlay sharing the same space without
coordinating.

Four changes, all written up in "UI Layout":

1. **Footer band** (`FOOTER_Y`, `SAFE_BOTTOM`, `footer()`) — one line
   per scene, in the same place, for the four buttons. The confirmation
   *replaces* it instead of sitting next to it: that way this class of
   bug can't come back.
2. **A price row instead of a price table** in `DisplayScoreScene` — the
   ArUco ID column is gone, the values are sorted, and the ones that
   actually were on the tray are yellow.
3. **`BEST — LOWEST WINS`** above both leaderboards, and `TOP 10!` is
   now `ENTER YOUR NAME` — the old headline promised a gate that doesn't
   exist.
4. **`OFF BY` during the round** — the difference the visitor
   previously had to compute in their head is now shown large.
   `PERFECT n` inherits the same spot.

Plus a **layout self-test** in `scenes.py`, following house convention:
`uv run game/scenes.py` → `ok`. It intercepts every `draw()` call and
checks screen bounds, `SAFE_BOTTOM`, and overlap across all scenes and
states. Verified that it can actually fail.

---

## Status: 2026-08-27

**What works:** The skeleton is click-through. All four scenes draw
according to the layout below, `FakeDetector` returns changing numbers,
SQLite stores and sorts correctly. The six findings in `scenes.py` are
fixed (see below).

As of today the look is also in place: **Press Start 2P** as the font,
the color ID on HPI red and orange, and the **CRT overlay** with
curvature, scanlines, and vignette. Both covered in their own sections
further below.

Source code has lived in `game/` since today. No import changes because
of it: `uv run game/main.py` sets `sys.path[0]` to `game/`, so the
modules still find each other flat. The folder maps to the process
boundary from "Process architecture" — a later `teleop/` will sit next
to it, not inside it.

| File | State |
|---|---|
| `game/config.py` | done — timing, colors, font, CRT, keymap, values, hardware constants |
| `game/app.py` | done — `Ctx`, `SceneBase`, `action_of`, `run_game`, CRT overlay |
| `game/assets/` | Press Start 2P (SIL OFL) + `OFL.txt` |
| `game/scenes.py` | **five** scenes incl. `render()`, `footer()`, layout self-test (`uv run game/scenes.py` → `ok`) |
| `game/db.py` | done, with an `assert` self-test (`uv run game/db.py` → `ok`) |
| `game/hw.py` | `FakeDetector`, `Camera` (with warmup guard), `ArucoDetector`, `CameraView`, `VideoView` done; `Buttons` open |
| `game/main.py` | done — wiring, four font sizes from `FONT_SIZES` |
| `game/music.py` | done — notation, synthesis, ducking, `Ctx.music`, self-test (`uv run game/music.py` → `ok`) |
| `game/balance.py` | done — target-value picking from the tray, self-test (`uv run game/balance.py` → `ok`) |

### Findings in `game/scenes.py` — resolved

The six findings from 2026-08-27 (duplicate `handle`, missing
`self.top`, `tray_sum()` in the wrong block, `top(TOP_N)` instead of
`top(5)`, magic number `3.0`, mixed languages) are all fixed in the
code. Re-checked the same day, played through headless: Idle → Round →
Score → Initials → Idle, the name shows up in the leaderboard
afterward.

`scenes.py` and `app.py` mixed tabs and spaces; every file in `game/`
now uses four spaces (`expand -t4`). The mix wasn't a cosmetic issue but
a trap for any tool that touches the file.

### Workflow on this project

**Per feature — four steps, in this order:**

1. **Vadim asks for a feature.**
2. **The assistant thinks it through and presents it** — the approach,
   the alternatives it rejected and why, and the code. Plus a *short*
   explanation of the spots where something new is happening. Short
   means short: if the explanation is longer than the code, something's
   wrong with the code.
3. **Vadim gives the go-ahead** — or corrects the direction. No `.py`
   file gets touched without a go-ahead.
4. **The assistant implements it** and afterward states what was
   actually checked and what wasn't.

The point of steps 2 and 3 isn't the approval — it's that the design
decision gets said out loud once before it ends up in the code. A
feature that can't be explained in five sentences is cut too big.

For suggestions, the ladder principle's order applies: does it need to
exist at all → standard library → native platform feature → existing
dependency → one line → only then custom code.

The assistant keeps this document up to date on an ongoing basis. It's
written in German as the working language; **everything that appears on
the machine's screen is in English** (see "Display language").

### Order from here

Rule: something runs after every step, and every step is visible on
screen. Steps 1–3 are doable today, 4–5 need hardware.

1. ~~Fix findings 1–5~~ — done, milestones 1–4 stand.
2. ~~`music.py`~~ — done, see "Sound". Still open: listening on the
   machine's actual speaker — volumes are set on headphones, the hall is
   louder. The tunes are strings in `PIECES` — tweaking them is a
   one-line change, not a rebuild.
3. ~~CRT overlay in `run_game`~~ — done, including curvature and the
   pixel font. Frame rate has been signed off since 2026-09-10: a stable
   30 fps with teleop running, see "Measurement on the Pi". Still open:
   dialing in the settings in the hall (`SCANLINE_ALPHA`,
   `VIGNETTE_ALPHA`).
4. ~~`Camera` + `ArucoDetector`~~ — done, including the passthrough
   inset. Still open: the detection rate against the *printed* markers
   under hall lighting.
5. Teleop process: torque state machine, heartbeat receiver, wake ramp.
6. `Buttons` (GPIO), LEDs, systemd.

Not to be squeezed in ahead of schedule: `db.qualifies()` as a gate
before the leaderboard (a balancing question, see Open Items). The demo
clip has its spot (`HowToScene`, `DEMO_VIDEO` in `config.py`) and is
just waiting on a setup to film — until then the scene runs as a text
page.

---

## What

An arcade machine with a real robot arm. Visitors teleoperate an SO-101
follower arm and play a valuation game against the clock. Commissioned
work for a STEM trade fair recruiting prospective HPI students.

The arcade framing isn't decoration, it's the instruction manual:
everyone instantly understands an arcade machine. No explanatory text,
no staff needed to explain how to get started.

## Game mechanics

Adapted from Google's *Price-a-Tray* (GDC demo). Sequence:

1. The tray is empty. Next to it sits the display case: ten cupcakes,
   each with a hidden price.
2. The display shows a target price, e.g. `GOAL €6.30`.
3. 30 seconds: place cupcakes on the tray (and take them off again if
   you get it wrong).
4. During the round **no score** is shown on screen, only the price.
   Over and under count the same — there's no failing, only a number. If
   the sum stays exactly on target for `PERFECT_HOLD` seconds, the round
   ends early — hands are on the leader arm, a "done" button would be
   out of reach.
5. Afterward the score screen counts the score up, like a boxing
   machine. See "Scoring".
6. Below that: a reveal of the full price table. A learning moment and a
   second reward.

The skill lies in the inference ("what was that thing worth?"), not in
fine motor control. That's a deliberate choice — the arm has too much
gear backlash for a precision game.

**An empty tray and 30 seconds** are the central adaptation from
Google's version: teleoperated picks take 10–20 s instead of 1–2 s by
hand, so two moves make a full round. The tray is cleared after every
round — that way everyone starts from the same state, and nobody
inherits their predecessor's task.

Until 2026-09-11 it was thought the other way around (a pre-loaded tray,
swap instead of build up, 60 s). Clearing the tray between rounds tipped
it over: if you start empty, you can't swap.

## Arcade framing

| Element | Implementation |
|---|---|
| Cabinet | Aluminum extrusion box (follower inside), leader arm in front on a pedestal |
| Marquee | Lit sign on top, game title + HPI logo. Physical, not on screen |
| Attract mode | When idle: LED loop on the cabinet, display alternates between high scores and title. **The arm doesn't move** — see "Idle, cooldown, power" |
| Controls | **Four arcade buttons in a cross layout, nothing else.** Right = forward/confirm, left = back/cancel, up/down = select. The same four buttons start the game, cancel it, and type initials. No keyboard, no joystick, no separate start button. |
| Timer | Background color: black at start, running toward HPI red from 5 s remaining. Readable from 8 m. |
| High score | Top 10, three-letter initials, entered with the same four buttons |
| Visuals | **Press Start 2P** (pixel font, no antialiasing), monospace, high contrast, black background. On top of that a **CRT overlay** — curvature, scanlines, vignette, see its own section |
| Sound | **Low-bit arcade music**, notated declaratively and synthesized at runtime, see its own section. The trade-show hall is loud — sound is garnish, never a carrier of information. |
| LED strip | Addressable, status indicator on the cabinet: idle loop, round in progress, last 5 s, score reveal |
| E-stop | Red mushroom button. Functionally necessary, fits visually perfectly. |

**Display language: English.** Decided on 2026-08-27. Arcade convention
— `PRESS`, `GOAL`, `TIME`, `TOP 10` reads instantly as arcade-speak to
anyone, even an eleven-year-old. German words are also longer, and width
is the scarcest resource on screen at font size 200. This document stays
in German, the strings in the code are English.

**Readability over effect.** The target audience stands 3–8 m away in a
brightly lit hall. Target value, current sum, and time remaining are the
three numbers that are always large and always in the same place.
Everything else is garnish.

## Hardware

- **Computer: Raspberry Pi** (model still to be decided, see Open Items)
- SO-101 follower (12 V, STS3215) in the box, leader (7.4 V) outside
- **Two cameras:**
  - *Top-down*, fixed mount, autofocus and exposure locked — provides
    marker detection
  - *Arm camera*, pure passthrough on the display, no processing — this
    still holds, the overlay only sits on the top-down camera
- **Display: Asus MB169CK, 15.6", 1920 × 1080 (16:9).** Read out via
  EDID on the Pi on 2026-09-09. **Correction:** this used to say
  "1920 × 1200 (16:10)", which was wrong — the MB169 series is FHD.
  Since 2026-09-10 the design resolution is the same number and
  `pygame.SCALED` is gone — scaling by a factor of 0.9 cost around
  20 ms per frame and the pixel font's sharpness, see "Resolution and
  fullscreen". A second display is optional for onlookers.
- **Four arcade buttons** (up/down/left/right) on GPIO, plus an e-stop.
  **3 mm panel** — snap-in (Sanwa OBSF-30, rated for 2–4 mm) is within
  range, but for plywood, screw-mount buttons (Seimitsu PS-14-KN,
  OBSN-30) with a nut are the more durable choice. 30 mm hole, 2.8 mm
  spade terminals.
- WS2812B strip. On the Pi 5, `rpi_ws281x` doesn't work (RP1); options:
  PIOLib, the SPI route (`rpi5-ws2812`, `Pi5Neo`), or offloading to an
  ESP32 with WLED via UDP/DDP. The latter takes timing, power supply,
  and level shifting off the Pi.
- 3D-printed pucks: flat base, low center of gravity, uniform grip rib,
  ArUco marker flat on top
- Tray with a rim

**No Jetson.** The only justification for a Jetson would be CUDA
inference, and ML is deliberately not part of the game. The existing
Jetson Nano is stuck on JetPack 4.6 / Ubuntu 18.04 / Python 3.6, and
LeRobot requires Python ≥3.12. Old stack, unused GPU, nothing gained.

## Software

Python · OpenCV (ArUco) · pygame · SQLite

**ArUco instead of machine learning.** Marker IDs map deterministically
to values. No training, no dataset, no lighting risk, values changeable
via a dictionary reload. Replaces Google's entire Vertex AI/GCS stack.

**pygame instead of a browser frontend.** One process, one language, no
Chromium, no web server, no JPEG encoding per frame. Fullscreen directly
over KMSDRM without a desktop environment. The arcade button comes in as
a normal event. The price for that: layout is manual work in
coordinates, no CSS. With this look — monospace, big numbers, black
background — that's not a loss.

If ML is supposed to be shown at the booth: only as a parallel showpiece
on a second monitor, **never in the critical path of game logic.**

## Process architecture

**Two separate processes. They don't talk to each other.**

| Process | Job | Dependencies |
|---|---|---|
| Teleop | Read leader → write follower, ~30–50 Hz constant | LeRobot (or the Feetech SDK directly) |
| Game | Camera → ArUco → state → render | OpenCV, pygame, SQLite |

The game logic needs the camera image, marker IDs, a timer, and button
presses. It **never** needs arm state. The visitor pushes pucks, the
camera sees the result — the arm is purely an input method.

Consequences:

- No shared loop. Rendering must not make the arm control stutter.
- No protocol between the two. Nothing to synchronize, nothing to
  debug.
- One crashing doesn't kill the other.
- If needed, they can run on two machines. If LeRobot acts up on the
  Pi: teleop on a laptop, game on the Pi.

**Teleop runs continuously, not per round.** No starting LeRobot from
within the game logic. Motor init and calibration for every visitor
would mean seconds of waiting plus a crash risk drawn fresh every round.

**Camera passthrough on the game screen is optional.** The real arm is
visible in the cabinet; a live feed is unreadable from 8 m anyway. If
used at all, then as a small inset ("what the machine sees") at low
resolution, never as the main area.

**LeRobot installation:** check the Pi's Python version. Bookworm ships
3.11, current LeRobot requires ≥3.12 — then either miniforge/pyenv, or
pin to LeRobot 0.4.x (≥3.10). On ARM, LeRobot automatically falls back
from TorchCodec to pyav for video decoding — that's expected, not a
bug.

Servo calibration (offsets, rotation directions, end stops) is not
being written from scratch. That's exactly the kind of bug that looks
like a wiring fault for hours.

---

## Code structure (game process)

```
picknplay/
  game/         # game process, started with: uv run game/main.py
    main.py     # wiring: build Ctx, build the start scene, call run_game
    config.py   # constants: timing, colors, font, CRT, keymap, values, paths
    app.py      # Ctx, SceneBase, action_of, run_game, CRT overlay
    assets/     # PressStart2P-Regular.ttf, OFL.txt
    scenes.py   # IdleScene, GameScene, DisplayScoreScene, LeaderboardScene
    hw.py       # camera grabber, ArucoDetector, FakeDetector, Buttons, LEDs
    db.py       # SQLite high scores
    music.py    # notation -> square-wave synthesis -> pygame.mixer.Sound
  markers/      # generated ArUco PNGs
  archive/      # earlier drafts, not imported
  scores.db     # created on first run, relative to the working directory
```

**Flat instead of packages, but in one subfolder.** The original plan
had `app/`, `scenes/`, `hw/`, `data/` as packages. At around 500 lines of
total code, that only buys `__init__.py` noise and long import paths;
seven files that each fit on one screen are faster to take in. Split
them up once one of them stops fitting.

`game/` is **not a package** — no `__init__.py`, no relative imports.
Python sets `sys.path[0]` to the directory of the file that was
started, so the modules still find each other flat, same as before. The
folder separates source code from markers, the archive, and the
document, and marks the process boundary: a later `teleop/` will sit
next to it, since the two processes share nothing.

**`scenes.py` never imports `hw.py`.** Only `main.py` knows both sides
and wires them together. A wrong import stands out immediately because
of this.

### Four principles

**The loop owns time, the scene only owns state.**
`clock.tick(fps)` returns `dt` in seconds, the loop passes it through.
`update(dt)` computes, `render(screen)` only draws what's already been
computed. A slow frame must not let game logic drift.

**`Ctx` is a seam, not a container.**
Scenes call `self.ctx.detector.tray_sum()` and never know whether OpenCV
or a stand-in sits behind it. That makes the entire game writable and
testable without an arm, camera, or LEDs; swapping in real hardware is
one line in `main.py`. Duck typing, no framework.

**Scenes know actions, not keys.**
`action_of(event)` translates arrow keys *and* GPIO into four strings:
`"up"`, `"down"`, `"left"`, `"right"`. The loop translates once,
centrally, and calls `scene.handle(action)`; unknown keys are discarded
beforehand, so no scene ever has to check a special case. Keyboard while
developing, arcade button at the show, scenes unchanged.

Deliberately *no* semantic names like `"start"`/`"back"`. With exactly
four unlabeled buttons, direction is the meaning, and a layer
translating `"right"` into `"start"` would be an abstraction with
exactly one implementation. The convention (right = forward, left =
back) instead lives in a comment in `config.py` and is applied the same
way in every scene.

`pygame.key.set_repeat()` provides repeat-on-hold — needed to scroll
through the alphabet. **Watch out during integration:** GPIO callbacks
have no auto-repeat, `hw.py` has to generate that itself.

**No `on_enter`/`on_exit`. Scenes are throwaway objects.**
Every transition builds a new instance (`self.switch_to(GameScene(self.ctx))`),
so `__init__` is the entry point and the end of the reference is the
exit. A second hook pair for the same moment would just be one more
place where state can be forgotten. The only cost: `__init__` runs about
one frame before activation — irrelevant for 60-second rounds.

**One time source per round.**
No `set_timer` running alongside a `t_start`. Time remaining is a
`float` on the scene that `update(dt)` counts down; both the display
*and* the transition follow from the same number. Two clocks drift
apart, and on a machine with an audience that looks like a bug because
it is one.

### Scenes and transitions

| Scene | Leaves on | Target |
|---|---|---|
| Idle | `right` | HowTo |
| HowTo | `right` | Game |
| HowTo | `left` or timeout | Idle |
| Game | 60 s elapsed | Score |
| Game | `left` twice within 3 s | Idle |
| Score | `right` | Leaderboard |
| Score | `left` | Idle |
| Leaderboard | `right` on the last field (saves) | Idle |
| Leaderboard | `left` on the back arrow | Idle |

The leaderboard input is a single cursor index: `0` = back arrow, `1..3`
= the three letters. `up`/`down` change the letter under the cursor,
`left`/`right` move it. That means the scene needs no input mode —
position *is* the mode.

**Every non-idle scene has an inactivity timeout back to idle.**
Visitors walk away mid-input; the machine has to reset itself without
staff.

### Concurrency in the game process

- **The camera grabber and detection run as threads, not processes.**
  `read()` and `detectMarkers()` are C++ code and release the GIL — a
  thread gets real parallelism there. Shared memory between processes
  only becomes necessary once actual computation happens in Python
  itself.
- **Pattern: a thread writes into an attribute (under lock), the loop
  reads.** Never the other way around.
- **The grabber always holds the newest frame**, not the oldest.
  Otherwise the V4L2 buffer delivers old frames and detection visibly
  lags behind.
- **GPIO callbacks run on a foreign thread.** Put key presses into a
  `queue.SimpleQueue`, drain it once per frame in the loop.
- **LEDs never block.** `set_state()` returns immediately — for WLED
  that's a `sendto`, for local LEDs a worker thread with a state slot.
- **Core assignment happens in the systemd unit (`CPUAffinity=`)** at
  the process level, not in the Python code. Pin only once measurement
  shows stuttering.

---

## Idle, cooldown, power

Decided on 2026-08-27, once hardware integration was on the agenda.

**In idle, the follower is powered off.** The STS3215 hold position via
continuous current against gravity — that's the heat source, and it
only goes away once holding stops. Six hours at the trade show at 100%
duty cycle is the sure way to lose the gripper servo. With power-off
between rounds, 100% becomes roughly 67% (a 60 s round out of 90 s per
visitor), and the breaks are evenly spread across the day.

**Price for that: the arm falls.** It needs a pose in which it stands
stable with power off and doesn't tip onto the tray. That's a
mechanical design task (a stop or a rest), not a software task, and it
blocks torque shutdown until it's solved.

**The attract-mode arm movement is cut.** It contradicted the point
above: an idle movement loop is 100% duty cycle in exactly the phases
when nobody is playing — the single biggest heat and wear item on the
booth, for an audience that isn't there right now. The LEDs handle the
movement in attract mode. They're better visible from 8 m than an arm
in the cabinet anyway.

**Waking up is the dangerous part.** Follower powered off, visitor
moves the leader somewhere, torque turns on — the follower would snap
instantly to the leader's pose. The order that prevents that: set the
goal position to the follower's **actual position**, *then* enable
torque, then ramp the goal to the leader's pose over ~1.5 s. Skip these
three steps and you've traded servo heat for a jerk per visitor, 240
times a day. An EEPROM torque limit doesn't help against this — the
jump happens within the allowed torque.

**The process boundary gets exactly one channel.** "Robot off while
idle" means the game has to tell the teleop process its state. Chosen:
a UDP datagram to localhost, a few times per second, content is the
scene name. One-way, lossy-tolerant, connectionless, protocol-free.

The decisive property isn't the mechanism but the intent behind it: **no
packet means "off."** If the game process dies, the camera hangs, or a
cable gets pulled, the arm cools down instead of quietly overheating
unattended. A channel where silence reads as "last state still applies"
turns every crash into six hours of continuous load. Teleop never waits
on the game; that would be exactly the coupling the two-process
architecture is meant to avoid.

**Cooldown is not a game mechanic.** The servos track their temperature
in a register; it's read at 1 Hz, not on the teleop tick — temperature
changes over tens of seconds, and every read costs bus time in the
30–50 Hz cycle. The value goes into the log and onto the LED color.
Only at a hard limit does the teleop process cut torque, independent of
game state. Deliberately *no* round lockout: "please wait" is a visible
outage at a booth with a queue, and if the hard limit ever triggers,
something else is already broken anyway.

**Cores: only teleop gets pinned.** `CPUAffinity=3` and `Nice=-10` in
the teleop unit, `CPUAffinity=0-2` for the game. The teleop loop is
CPU-light — it waits on the serial bus — but time-critical: late cycles
show up as jitter in the arm. Those are two different problems;
affinity solves "must not get preempted," priority solves "must not run
late." IRQ affinity is left alone until measurement shows it's missing.

What pinning does **not** separate: memory bandwidth, the USB host
controller, and the thermal budget. If the Pi throttles, clock speed
drops for all four cores at once — including the pinned teleop loop.

**The e-stop physically disconnects the 12 V rail.** A mushroom button
that a Python loop polls via GPIO isn't an e-stop, it's a button: if
the process hangs — the exact case you're guarding against — it does
nothing. The software task here isn't triggering the stop, it's the
clean startup afterward, because the follower then sits somewhere (see
wake ramp).

**LEDs stay on the ESP32.** WLED over UDP takes timing, level shifting,
and the power supply off the Pi. A WS2812B strand at full white with
~60 mA per LED is the single largest power draw at the booth, well
ahead of the Pi — brightness limiting is therefore power management and
thermal management in one number.

**Two failure modes that will definitely get misdiagnosed at the trade
show:** undervoltage on the Pi shows up as throttling *and* as USB
dropouts — "the camera cuts out sporadically" is usually the power
supply, not the code. And inrush current: everything switching on at
once on the same switch can push power supplies into current limiting,
then the machine "sometimes doesn't start," which looks like software.

**The idle screen renders at 20 FPS instead of 60**
(`IDLE_FPS` in `config.py`, `TICK` as a class attribute of the scene).
It shows text that blinks twice a second and a leaderboard that doesn't
change at all — pushing 2.3 megapixels through the barrel distortion 60
times a second for that is six hours of heat in a closed aluminum
cabinet for an image nobody is looking at. The least visible lever in
the whole project and the cheapest.

Active cooling and an airflow path in the cabinet remain first-order
regardless; every software saving is second-order.

### What needs to be measured

- Holding current and servo temperature of the follower in working
  pose, with a puck in the gripper, over 10 minutes
- Whether and where the arm stands stable with power off
- Both cameras simultaneously on the real Pi, in the formats that get
  chosen
- Pi temperature in the closed cabinet under full load
- Teleop cycle-time jitter, measured *while* the game is rendering —
  before that, any statement about cores is a guess

### Camera and passthrough (implemented 2026-08-27)

`Camera` is a grabber thread with `BUFFERSIZE=1`, `ArucoDetector` a
second thread with `DETECT_HZ`. Two threads instead of one because on
the dev machine *one* webcam serves both: if detection ran in the
grabber thread, the passthrough frame rate would be tied to detection
time.

**Format before resolution.** `MJPG` is set before width and height are
set. As YUYV, 720p costs a multiple of the USB bandwidth, and that's
exactly what decides whether two cameras can run on one controller.

**`Camera` fails loudly** if the device can't be opened, instead of
silently falling back to `FakeDetector`. Made-up numbers on the machine
wouldn't register as an error at the trade show; a startup abort does.

**Passthrough only in `GameScene`**, both images 800 × 450 side by
side. In idle, USB bandwidth stays free and the Pi stays cool — same
rule as for the servos. Measured 1.5 ms per frame for the whole scene,
including both panes; `CameraView` only converts when the camera has
actually delivered a new frame (a sequence counter in `Camera`). Since
the target frame rate is now 30, source and rendering run at the same
speed and the counter rarely saves anything — it stays anyway: it costs
one comparison and covers the case where a camera drops out or hangs.

**`CAM_INDEXES` is a pair**, `(arm, top-down)`. If the same 0 appears
twice, `main.py` still only opens the device once (`set()`) and feeds
both panes from one grabber — that's the layout mock with a single
webcam. Real hardware is `(0, 1)`, one number. The detector always
hangs off the second, the top-down camera. `pygame.image.frombuffer(..., "BGR")`
saves the `cvtColor` call — pygame-ce accepts OpenCV's channel order
directly.

### Finding: race in `tray_sum()` (fixed)

`seen` was written by the detector thread and read by the render loop
without a lock. An update to an existing key is harmless, a **new** key
during iteration is not: `RuntimeError: dictionary changed size during
iteration`. Reproduced, not theoretical. The moment it strikes is
exactly the moment a marker first appears — i.e. mid-round. Unlikely per
round, not unlikely over 240 visitors. `fresh()` now holds a
`threading.Lock`.

### Overlay on the top-down camera

**Only the top-down pane gets a detector.** The arm camera stays pure
passthrough — it sees the tray from a different angle, the corners
wouldn't apply there, and a second detector would cost compute time for
decoration. `CameraView(cam, det=None)` carries the mapping: the pane
knows whether it has anything to overlay.

**Prices have not been shown in the image since 2026-09-11.** Before
that, the overlay drew the value of every detected marker at the
centroid of its four corners. That contradicted the game's basic rule:
"EVERY TREAT HAS A HIDDEN PRICE" — anyone who can read the prices during
the round calculates instead of estimating, and the reveal at the end
loses its learning moment. From 8 m nobody read it anyway; at the
machine, where hands are on the leader arm and the screen is an arm's
length away, they did.

The code sits commented out in `GameScene.overlay`, because while
setting up the camera it's the only thing that shows *which* marker
detection sees, not just that it sees one. `MARK_FONT` in `config.py`
only still exists for that.

What remains is the detection window — chrome in `GREY`, not a game
value.

**Occluded markers stay put**, for exactly as long as they do in the
sum: `TOTAL` and the sum read the same `MARKER_HOLD` window from the
same snapshot that `update()` pulls once per frame. They can't
disagree.

### Detection window (`TRAY_ROI`)

The top-down camera is wide-angle and sees half the booth. `TRAY_ROI`
limits detection to a rectangle in image fractions.

**Implemented as a crop, not a filter.** The detector cuts the region
out of the frame (a numpy view, not a copy) and only detects within it.
That does both jobs in one step and is cheaper: measured **1.21 ms
instead of 2.00 ms** per pass at 60% × 70%. A marker at the image edge
simply disappears instead of being detected and then discarded.

The corners then come back as fractions of the *whole* image, so the
scene only has to multiply by the pane rectangle.

**The rectangle is drawn in `GREY`** — chrome, not a game value, hence
not yellow. It's visible because you set `TRAY_ROI` while aligning the
camera in the hall, and would otherwise have to aim blind. Same rule as
`SCANLINE_ALPHA`.

**Unknown marker IDs are discarded.** Anything not in `VALUES` isn't
part of the game — a printed test sheet on the table can't score points
because of this.

### Sound on new detection

`"blip"` in `SFX`: a single high note, `duty=0.125`, `vol=1200` versus
2600 for `"ok"`, 200 ms. No recycling of the button sound — otherwise a
puck sounds like a button press and the signifier mechanism loses its
uniqueness.

Triggered on **newly detected**, not on visible, otherwise it fires
`DETECT_HZ` times per second. The comparison sits in `GameScene.update`,
a set difference against the last frame. Two things fall out of that
for free: five pucks at once produce **one** sound, and a briefly
occluded marker doesn't beep again, because the hysteresis never lets
it leave in the first place.

The logic sits in the scene, not in the thread — `hw.py` still doesn't
import `music`, and "thread writes, loop reads" stays intact.

**`INTER_LINEAR` instead of `INTER_AREA`:** measured 0.17 ms instead of
3.5 ms per frame. AREA averages over all source pixels when shrinking
and is twenty times more expensive at a factor of 3. Behind scanlines
nobody sees the difference — 3.5 ms would be a fifth of the frame
budget on the Pi for an inset that, per the layout principle, is
garnish.

---

## UI layout

### Resolution and fullscreen

**Design resolution = panel resolution: 1920 × 1080, Asus MB169CK.**
Moved there on 2026-09-10. Every coordinate in `scenes.py` is an
absolute number for this grid; on the target monitor the mapping is
1:1, nothing gets scaled, nothing gets blurred. What you write is what
shows up.

**`pygame.SCALED` is gone.** Until 2026-09-09 the design resolution was
1920 × 1200, i.e. a panel that doesn't exist — the 16:10 figure was
wrong — and `SCALED` scaled every frame down to 1080. That measured at
around 20 ms per frame, more than CRT and curvature combined, and it
put the 8×8 pixel font onto a grid with a factor of 0.9: unequal glyph
pixel sizes, exactly the bug all the font sizes being divisible by 8
exists to prevent.

```python
flags = pygame.FULLSCREEN if FULLSCREEN else 0
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=VSYNC)
except pygame.error:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.mouse.set_visible(False)
```

The `try` isn't decoration: `vsync` without `SCALED` is
backend-dependent, and a machine that starts with an exception instead
of a picture on the trade-show day is worse than one with tearing.
`PNP_VSYNC=0` turns it off for re-measuring.

`vsync` prevents tearing in the timer's color gradient, the one spot
where a large area changes per frame. It measured a cost of 12 to 19%
at 60 Hz; at 30 fps there's budget for it. `set_visible(False)` removes
the mouse cursor, which would otherwise sit in the middle of the screen
in fullscreen.

**`FULLSCREEN` is a switch in `config.py`**, not a fixed value: off
while developing (windowed, `q` quits), on at the machine. One flag,
two modes of operation, no second codebase.

**Consequence:** a different panel now means touching the layout, not
just flipping a flag. That's a deliberately paid price — the fallback
cost four times what it insured against, and the monitor is fixed
hardware.

**Target frame rate 30, not 60.** Two reasons, both independent of
compute power. First, 30 divides the panel's 60 Hz evenly: every frame
stays up for exactly two refreshes. At 40 fps, 60/40 = 1.5, so
alternately one and two refreshes — visible judder at a *higher* frame
rate. Below 60, 30 is the only even number. Second, the cameras deliver
30 frames/s; anything above that shows the same camera frame twice
during the round. There's no 60 Hz motion in this game at all: a
seconds counter, a sum, blinking text, a camera image. The arcade look
comes from scanlines, curvature, and hard pixel edges, not from the
frame rate. `IDLE_FPS` is set to 15, half of that, so the cadence stays
even in idle too.

### Font sizes

`big` 168, `mid` 88, `small` 48, `tiny` 32 — all divisible by 8,
rationale in its own section further below.

### Coordinates

All coordinates for **1920 × 1080**, screen center x = 960. Drawing is
manual work in numbers — that's the deliberately paid price for pygame
instead of CSS. So it doesn't spiral into magic numbers, three rules
apply:

- **One helper, no layout system.** `draw(screen, font, text, x, y, color)`
  draws text centered on `(x, y)`. Centered, not left-aligned, because
  numbers change width (`9` → `10`) and a left-aligned value would
  visibly jump.
- **`font.render(text, False, color)`** — the second parameter is
  antialiasing, and it has to be `False`. A pixel font with
  antialiasing looks mushy from 8 m instead of sharp.
- **Color carries meaning, not decoration.** Six colors, one ladder
  from quiet to loud, each with exactly one job. As long as that holds,
  "which color do I use here" is no longer a decision, just a lookup.

> **Since 2026-09-11 ("Sugar Rush"):** `BLACK` is now called `BG` and is
> `#28101E` (dark chocolate), `YELLOW` is now called `ACCENT` and is
> `#FF65BD` (pink), `WHITE` is `#FFECF6` (cream), `GREY` is `#B0809E`.
> The jobs are the same. New is `CANDY` — candy colors for titles and
> sprinkles, never for game values. The tables in this section still
> use the old names.

| Color | Hex | Job |
|---|---|---|
| `BLACK` | `#000000` | background, always |
| `GREY` | `#787878` | labels (`GOAL`, `TOTAL`) |
| `WHITE` | `#F0F0F0` | neutral values |
| `YELLOW` | `#FFC800` | what the visitor is *currently* affecting |
| `ORANGE` | `#DE6207` | warning — HPI orange |
| `RED` | `#B1073A` | the final seconds — HPI red |

Red and orange are pulled from the HPI logo SVG, not eyeballed.
`YELLOW` is brighter than the HPI yellow `#F7A900`, because on black
from 8 m the brighter one wins, and the difference isn't visible next
to the logo. `GREEN` and `DARKRED` were dropped: green isn't HPI, and a
green background contradicts "black background." `ORANGE` doesn't have
a home in the code yet — the cancel warning in `GameScene` is the
obvious spot.

### Font sizes

`main.py` builds a dict and stores it in `Ctx.fonts`. Four sizes are
enough, more would just be decisions with no payoff.

| Key | Size | For |
|---|---|---|
| `big` | 168 | The numbers that must be readable from 8 m |
| `mid` | 88 | Time remaining, headings |
| `small` | 48 | Labels, leaderboard |
| `tiny` | 32 | Control hints, price table |

**The font is Press Start 2P** (SIL OFL, in `game/assets/`) — the
literal arcade font, traced from 1980s NAMCO machines. Chosen on
2026-08-27 over VT323, Silkscreen, and Silkscreen Bold. The criterion
was width per digit height, because width is the scarcest resource on
screen at these sizes:

| Font | Size for 200 px digits | `"180"` | `"PICK'N'PLAY"` |
|---|---|---|---|
| **Press Start 2P** | 228 | 628 px | 2480 px |
| VT323 | 357 | 378 px | 1547 px |
| Silkscreen | 320 | 600 px | 2240 px |
| Silkscreen Bold | 320 | 720 px | 2680 px |

VT323 is by far the narrowest and would have been the obvious choice —
but its strokes are a design-pixel thin, and thin loses out from 8 m in
a bright hall. Press Start 2P has the thickest strokes and only gets
wide on the title, and the title is the one string nobody has to read
under time pressure.

**Why these four numbers.** Press Start 2P has an **8×8 grid**: font
size ÷ 8 is the edge length of one glyph pixel. Only multiples of 8 are
pixel-exact, anything else makes the pixels *within* one glyph unequal
sizes. `big 168` hits the digit height of the old placeholder almost
exactly (147 px instead of 154) and makes `PICK'N'PLAY` 1848 px wide —
36 px margin, exactly right for a marquee.

All 17 strings from `scenes.py` have been checked against their
available width, none overflows: **no coordinate changes.** `main.py`
now builds the dict in one line from `FONT_SIZES`.

The arrow glyphs `▶ ◀ ▲ ▼` exist in the font (checked, not assumed), as
do umlauts and `€`. **Since 2026-08-27 they're used everywhere**, the
ASCII fallbacks `<`, `>`, `^v` are gone. The glyphs are filled triangles
on the same 8×8 grid as everything else — a hand-drawn
`pygame.draw.polygon` was briefly in the code and got pulled again: it
breaks the pixel grid, doesn't scale with the font size, and is code
for something the font can already do.

**`pygame.font.Font(path, size)` with a bundled TTF is more robust on
the Pi than `SysFont`** — no fontconfig, no question of which fonts are
on the Raspberry OS image. The repository gets 118 kB heavier and is
reproducible in exchange. The path is built from `__file__`, not
relative to the working directory, otherwise the systemd start breaks.

### Footer band (2026-08-28)

Two constants in `config.py` and a seven-line helper in `scenes.py`:

```python
FOOTER_Y    = 1000   # the one line that says what the buttons do
SAFE_BOTTOM =  920   # no scene content below this. Ever.
```

**The trigger was a real clipping bug.** The fifth leaderboard row sat
at y 1096…1144, the confirmation `PRESS ◀ AGAIN TO DISCARD` at
1114…1146 — 528 × 30 px of overlap. It only became visible once the DB
had five entries, hence "clips sometimes." The cause wasn't the number
1130 but that a *data-dependent-length* list and an overlay shared the
same space without coordinating.

**The confirmation replaces the hint line instead of sitting next to
it.** That means nothing can collide anymore — not because the numbers
now fit, but because there's no second element. And it's the better
feedback: the response to a button press appears exactly where it
already says what the button does. Before, the cursor `◀` (510, 470)
and its response sat 660 px apart.

Both numbers are **distances from the bottom edge**, not fractions of
height: the band is a fixed line at the screen edge and doesn't scale.
When moving to 1080, they therefore stayed at 80 and 160 px from the
edge — only the scene content above them shifted.

```python
footer(screen, f, left=None, right=None, note=None)
```

`note` yellow and centered, otherwise `left` at x = 600 and `right` at
x = 1320, both `tiny` / `GREY`. **The arrow always comes first**
(`◀ BACK`, `▶ NEXT`) — direction is carried by position in the footer,
not by word order. Before, `◀ BACK  START ▶` mirrored and
`▲▼ LETTER ◀▶ FIELD` didn't.

| Scene | left | right | `note` |
|---|---|---|---|
| `HowToScene` | `◀ BACK` | `▶ START` | — |
| `GameScene` | `◀ QUIT` | — | `◀ AGAIN TO QUIT` |
| `DisplayScoreScene` | `◀ BACK` | `▶ NEXT` | — |
| `LeaderboardScene` | `▲▼ LETTER`, at `cursor == 0`: `◀ DISCARD` | `▶ SAVE` at `cursor == 3`, otherwise `▶ NEXT` | `◀ AGAIN TO DISCARD` |

`IdleScene` has no footer — the blinking `PRESS ▶` in `mid` is the
signifier there, and a second gray hint below it would only weaken it.

**`◀ QUIT` sits permanently in the round**, not only after the first
press. A hidden control isn't a control; the double confirmation
catches the accidental press, not the invisibility.

### Layout self-test (`uv run game/scenes.py` → `ok`)

Same convention as `db.py`, `music.py`, `balance.py`. The test
intercepts every `draw()` call from the *real* `render()` methods and
checks the rectangles: screen bounds, `SAFE_BOTTOM`, and pairwise
overlap — including the two camera panes and the cursor bar, which
aren't a `draw()`. The bar was only added on 2026-09-10: it used to be
a `fill()` with a magic number and was therefore invisible to the test,
blind to exactly the class of bug the test was built for. Now it's
`CURSOR_Y`/`CURSOR_H` on the class and the test reads it from there.
Every scene gets played through, `GameScene` in three states and
`LeaderboardScene` in eight (four cursor positions × confirmation
on/off).

No screenshot comparison: a reference image would have to be maintained
for every color change and still wouldn't say *which* two elements
overlap. Verified that the test can actually fail — with the old
coordinates it reports the collision that actually existed.

### IdleScene

**Silent** (`MUSIC = None` plus `ctx.music.stop()` in the constructor).
Six hours of chiptune straight is tiring — and it doesn't mark
anything. Only with a silent idle does the music kicking in during
`HowToScene` become a signal that "it's starting." `stop()` also clears
out the deferred idle music that `DisplayScoreScene` scheduled via
`MUSIC_IN`.

`▶` now leads into `HowToScene` instead of directly into the game, and
returns `"ok"` instead of `"start"` — the start fanfare belongs at the
actual start of the round.

| Element | Position | Font / Color |
|---|---|---|
| `PICK'N'PLAY` | 960, 260 | `big` / `YELLOW` |
| `PRESS ▶` — blinks at 1 Hz | 960, 560 | `mid` / `WHITE` |
| `BEST — LOWEST WINS` | 960, 690 | `tiny` / `GREY` |
| Top 5 from `db.top(5)` | 960, 750 + i·66 | `small` / `WHITE` |

**`LOWEST WINS` is mandatory, not decoration.** Every leaderboard a kid
knows sorts the biggest number to the top. Here the smallest wins, and
without this line you'd read the list backwards. The same line appears
in `LeaderboardScene`.

The blinking needs no timer: `self.t += dt` in `update`, and `render`
checks `int(self.t * 2) % 2`. One time source, same rule as with the
round timer.

### GameScene

The three numbers from the readability principle. Target value and
tray sum sit next to each other, so the eye compares them directly —
that's exactly the thinking task of the game.

Since 2026-08-27, **both camera images sit large, side by side** under
a three-column header row. Column centers 490 / 960 / 1430 apply to
both number *and* image, so both align vertically.

| Element | Position | Font / Color |
|---|---|---|
| `GOAL` | 490, 70 | `small` / `GREY` |
| Target value | 490, 145 | `mid` / `WHITE` |
| `TIME` | 960, 70 | `small` / `GREY` |
| Time remaining, whole seconds | 960, 145 | `mid` / `WHITE` |
| `TOTAL` | 1430, 70 | `small` / `GREY` |
| Tray sum | 1430, 145 | `mid` / `YELLOW` |
| `OFF BY`, `PERFECT` on a hit | 960, 265 | `small` / `GREY` |
| Difference, countdown on a hit | 960, 380 | `big` / `YELLOW` |
| Arm camera (passthrough) | 880 × 495 around 490, 740 | frame `GREY` |
| Top-down camera | 880 × 495 around 1430, 740 | frame `GREY` |
| Detection window | `TRAY_ROI` in the right pane | `GREY`, `MARK_WIDTH` |
| Marker values | centroid of marker corners | `MARK_FONT` / `YELLOW` |
| `◀ QUIT` / cancel warning | Footer | see Footer band |

**`OFF BY` during the round (2026-08-28).** Before, `GOAL` and `TOTAL`
sat 940 px apart and the visitor had to compute the difference in
their head — under time pressure, from 8 m, in a loud hall. The
thinking task of this game is pushing pucks, not mental math. `GOAL`
and `TOTAL` were downgraded from `big` to `mid` for this; the
difference gets `big`.

It's **the same word as on the score screen** — learned once, used
twice. The score screen thus becomes "your final result," not a new
term.

**`PERFECT n` inherits exactly this spot.** Once the sum sits on
target, the large yellow field turns into a countdown. That means
there's no longer a second spot where the countdown and the cancel
warning fight over the same line — before, both sat at 960, 1120 and an
`elif` papered over it.

Both `YELLOW`: `TOTAL` and the difference are the same thing — what the
visitor is affecting, once as a value and once as a remainder. `GOAL`
and `TIME` are the given. Size separates them (168 vs. 88), not color.

The camera panes moved from 690 to 740, so there's breathing room below
the difference. Verified in the self-test, not eyeballed.

`CAM_VIEW` is 16:9 like `CAM_SIZE`. A different ratio distorts the
image, because `CameraView` stubbornly scales to the target size
instead of cropping. A letterbox branch would be code for a problem
that two numbers in `config.py` never let arise in the first place.

**Developer shortcut (`CHEAT_TAPS`, 2026-08-27).** Pressing `>` five
times in a row sets `self.left = 0.0` — the round then ends through its
normal path in `update()`, including the finish sound and music stage.
A `switch_to()` called directly from `handle()` would be a second round
ending next to the real one; that's exactly what you don't want to
shortcut while testing. Any other action resets the counter, and
`CHEAT_TAPS = 0` in `config.py` disables the whole thing at the
machine.

Side effect from `KEY_REPEAT`: holding the key down fires the five
repeats in ~0.6 s. On GPIO there's no repeat logic, there it's five
real presses — irrelevant, because the cheat is off there anyway.

**Early end at `OFF BY 0`.** If the sum sits exactly on target for
`PERFECT_HOLD` seconds, the round ends — via the same path as the clock
running out, including the finish sound and scene change. The
hysteresis in `fresh()` catches the flicker, the five seconds catch the
intent. The countdown on screen is mandatory: an abrupt end without
warning looks like a crash on the machine. If fewer than `PERFECT_HOLD`
seconds remain, the counter never fills and the round ends normally —
"right before the end" needs no special case, because there's only one
time source.

**The target value comes from `balance.gap()`**, computed against the
tray as it actually sits at round start. `__init__` reads `fresh()`
once for this — side effect: the blip sound no longer fires for the
five pucks that were already there at the start.

**Displaying time remaining:** `int(self.left) + 1`. Without the `+ 1`,
the machine would already show `59` in the first second and `0` in the
last, while the round is still running.

**Background as a timer.** No extra element, the surface itself is the
display:

```
k  = 0.0 while left > WARN_SECONDS, otherwise linear to 1.0 at left == 0
bg = BLACK + (RED - BLACK) * k         component-wise
```

From black to HPI red instead of from green to dark red. The start is
thus the same black background as everywhere else, and the final five
seconds color the whole screen — that's the signal that carries from
8 m. White text on `#B1073A` stays readable; the gray labels lose
contrast during those five seconds, which is acceptable because `GOAL`
and `TOTAL` are long since known by then.

### HowToScene

New on 2026-08-27. Explanation, demo clip, and **this is where the
music starts** (`MUSIC_IN = (0.0, 800)` — 0.8 s fade-in, instead of
slamming in out of silence).

| Element | Position | Font / Color |
|---|---|---|
| `HOW TO PLAY` | 960, 110 | `mid` / `YELLOW` |
| Demo clip, only if `DEMO_VIDEO` is set | `DEMO_SIZE` around 960, 500 | frame `GREY` |
| Three lines from `HOWTO` | 960, 900 + i·60 (no clip: 500 + i·60) | `tiny` / `WHITE` |
| `◀ BACK` / `▶ START` | Footer | see Footer band |

**Without a clip, the text moves to the middle.** `DEMO_VIDEO = None`
is the shipping default, not the exception case — the film won't exist
until there's a setup to film it, and until then the feature must
neither be blocked nor look half-finished.

**`VideoView` is `CameraView` with a clock.** pygame can't do video,
but `cv2.VideoCapture` takes a file just like a device — the player is
the same class as the passthrough, the same `frombuffer(..., "BGR")`
line, no new dependency. The one real difference: a camera *pushes*
frames (grabber thread, sequence counter), a file gets *pulled* (`dt`).
Mix those up and you build one thread too many or one too few.

**The clip is silent.** No audio track, no sync, no second audio path
— the music carries the scene. A narration voice over chiptune in a
loud hall would be exactly the sensory overload that the silent idle
removes.

**Price: roughly 5–8 s per visitor**, at 240 visitors about 25 minutes
of queuing over the trade-show day. Against that: there's no minimum
duration — anyone who already knows the explanation taps `▶` right
through.

### DisplayScoreScene

| Element | Position | Font / Color |
|---|---|---|
| `OFF BY` | 960, 150 | `small` / `GREY` |
| `self.score` | 960, 380 | `big` / `YELLOW` |
| `GOAL` | 660, 600 | `small` / `GREY` |
| Target value | 660, 690 | `mid` / `WHITE` |
| `TOTAL` | 1260, 600 | `small` / `GREY` |
| Tray sum | 1260, 690 | `mid` / `WHITE` |
| `PRICES` | 960, 860 | `tiny` / `GREY` |
| Price row, 10 values | x = 204 + i·168, y = 940 | `small` / `YELLOW` if on the tray, otherwise `WHITE` |
| `◀ BACK` / `▶ NEXT` | Footer | see Footer band |

**The price table is a price *row* (2026-08-28).** Before, this showed
`0 = 4`, `1 = 7`, … in five columns. The left column was the ArUco ID —
and that isn't written as a digit on any puck, the visitor only ever
saw a black-and-white pattern. Half the table content demanded a
mapping whose key nobody has. That's exactly what made it confusing: it
looked like information and was noise.

Now: just the values, **sorted ascending**, and **the ones that
actually were on the tray at the end of the round are yellow**. That
makes it not a lookup table anymore but a picture of the round — the
price catalog and what you got out of it. The color follows the
existing ladder, no new vocabulary.

The reveal remains the learning moment from the game mechanics, and it
still runs off `sorted(VALUES.values())`, not a second list —
otherwise the display and the scoring drift apart the moment someone
changes a value. All ten values stay on screen, not just your own: the
full catalog is exactly the knowledge that makes the second round
better than the first.

**The constructor takes `marks` instead of `total`.** The sum is
contained in it, and the price row needs to know *which* values were
there anyway. One marker per puck and all-distinct values, so
`{VALUES[i] for i in marks}` loses nothing.

`GOAL` and `TOTAL` are laid out as two columns with a label above each
— the same arrangement as the header row during the round, which the
visitor has just spent 60 s reading. Before, it was a cramped line
`GOAL 180    TOTAL 165`.

### LeaderboardScene

Cursor model, as described under "Scenes and transitions." The marker
is a rectangle or underline beneath the field at `self.cursor`.

| Element | Position | Font / Color |
|---|---|---|
| `ENTER YOUR NAME` | 960, 130 | `mid` / `YELLOW` |
| `◀` (back field, `cursor == 0`) | 510, 470 | `big` / `WHITE` |
| Letter 1..3 | 840 / 1050 / 1260, 470 | `big` / `WHITE`, active field `YELLOW` |
| Cursor bar | `COLS[cursor] − 68`, 580, 135 × 9 | `YELLOW` |
| `BEST — LOWEST WINS` | 960, 660 | `tiny` / `GREY` |
| Top 5 from `db.top(5)` | 960, 720 + i·64 | `small` / `WHITE` |
| Button hints / confirmation | Footer | see Footer band |

**`TOP 10!` was a lie (2026-08-28).** `db.qualifies()` is never called,
everyone lands here — even at `OFF BY` 200. The heading promised
something the code doesn't check, and it showed five rows instead of
ten. The screen is an input, so it's named like one: `ENTER YOUR NAME`.
The `qualifies()` gate is untouched by this and remains open (a
balancing question, see Open Items) — the honest heading doesn't
prejudge that decision.

**The list moves from 860/65 to 720/64.** Before, the fifth row sat at
1096…1144 and collided with the confirmation; now it ends at 1004,
under `SAFE_BOTTOM`.

**`▶ SAVE` on the last field.** That pressing right from the third
letter saves used to be written nowhere — you had to discover it. The
footer says what `▶` does *right now*.

**Confirmation when discarding (2026-08-27).** `◀` on the field
`cursor == 0` discards the score just played. That happens by accident
if you tap left once too often, hence the same double confirmation as
for canceling a round: the first press sets `self.confirm =
CONFIRM_SECONDS`, a second press within the window goes to idle. No
dialog state, no second screen — one float in `update()` carries both
states and runs down on its own.

The field color comes from `self.cursor`, not a second flag. If
`render` needed its own "which field is active" attribute, the state
would live in two places and could drift apart.

### CRT overlay

The machine is supposed to look like a tube, not an LCD. Three layers,
all in `run_game`, between `scene.render(...)` and `pygame.display.flip()`:
**curvature**, **scanlines**, **vignette**. Implemented on 2026-08-27.

```python
overlay = crt_overlay(width, height) if CRT else None
maps    = barrel_maps(width, height, BARREL_K) if CRT and BARREL_K else None
frame   = pygame.Surface((width, height)).convert(screen) if maps else screen
...
    scene.render(frame)
    if maps:
        cv2.remap(px(frame), *maps, cv2.INTER_NEAREST, dst=px(screen))
    if overlay:
        screen.blit(overlay, (0, 0))
    pygame.display.flip()
```

**The loop carries the effect, not the scene.** It sits over
everything, so it belongs at the one place where everything converges.
No scene knows about it, no scene can forget it, and turning it off is
a flag in `config.py` instead of four changes in `scenes.py`.

**Built once, not computed per frame.** Scanlines, vignette, and the
curvature table are created at startup. Per frame, what's left is one
`remap` and one blit — both C, both constant. Same rule as with
`db.top()` in `render`: what doesn't change doesn't get recomputed.

**The vignette is a 16×10 alpha grid, scaled up.** A soft radial
gradient costs nothing if you compute it tiny and let `smoothscale`'s
bilinear filter do the work — 160 pixels instead of 2.3 million. It's
composited with `BLEND_RGBA_ADD`: both layers are pure black, only the
alpha adds up, and that doesn't depend on any pygame version.

**Barrel distortion: yes after all, and it costs little.** The earlier
entry here said "needs a shader, so too expensive." That was wrong —
`cv2.remap` has long been a dependency anyway, because ArUco brings in
OpenCV. For every target pixel, the source coordinate is computed once
and stored as a fixed-point table (`cv2.convertMaps`, `CV_16SC2`); per
frame it's a single C call.

```python
f = 1 + k * (nx² + ny²)      # points further out reach even further out = curvature
```

`BARREL_K = 0.05` is visible without being silly. `0` only turns off
the curvature and keeps scanlines and vignette — that's the emergency
exit if the Pi can't keep up.

**`INTER_NEAREST`, not `INTER_LINEAR`.** Not only faster: bilinear
filtering blurs the pixel font, and "no antialiasing" is the rule one
level up. The price is slightly frayed glyph edges at the border, which
doesn't look wrong on a tube.

**The overlay comes after the curvature, not before.** Curved
scanlines would be more authentic, but 1-px lines through
nearest-neighbor resampling produce moiré. Straight scanlines on a
curved image cost nothing and stay clean. The vignette conveniently
covers the black corners the curvature creates.

**Two traps in memory layout**, both expensively learned and therefore
noted here:

1. The obvious route, `pygame.surfarray.pixels3d`, cost **8.3 ms**, the
   chosen one **1.4 ms**. Reason: `pixels3d` returns RGB, pygame stores
   BGRA — the view has stride **−1** on the color axis, and OpenCV
   can't scan a backward-running array, it copies first. `get_view("2")`
   returns the 32-bit pixels as laid out, `.T` flips pygame's axis
   order `(w, h)` to the image convention `(h, w)` and makes it
   contiguous in the process. Color order doesn't matter, because
   `remap` only moves pixels around.
2. A held numpy view **locks** its surface, and the blit underneath
   then fails with "Surfaces must not be locked during blit." That's
   why the `px(...)` calls sit directly as arguments in the call: the
   views die with the line, the lock lifts.

**Measured** (Mac, headless, 1920 × 1200, real scenes):

| | ms/frame |
|---|---|
| scene + `flip` only | 2.5 |
| **+ curvature + scanlines + vignette** | **5.8** |
| Budget at 60 FPS | 16.7 |

The CRT share is about **3.3 ms**. On the Pi that's the item that tips
over first — that has to be measured there, not guessed.

#### Measurement on the Pi, 2026-09-09

Measured on the machine: Pi 5 (8 GB), Ubuntu 24.04, KMSDRM fullscreen,
both cameras active, teleop stopped. The idle screen was driven up to
game-scene load via `PNP_IDLE_FPS=60`, because no key press reaches the
machine over SSH under KMSDRM and the game scene would otherwise be
unreachable.

| Target 60 fps | CPU | achieved |
|---|---|---|
| everything on | 268% | **19.6** |
| without curvature (`BARREL_K = 0`) | 195% | **26.5** |
| without CRT | 189% | **36.6** |
| without CRT, without cameras | 92% | **40.0** |

**60 fps is not reachable on this Pi.** Not even stripped down. The
last row is the real finding: 40 fps at 92% CPU means there's nothing
left to parallelize, the path hangs on a single thread.

Three hypotheses were checked, two of them disproven:

**It wasn't text rendering.** `font.render()` ran fresh for every
string in every frame, Press Start 2P at up to 168 px. An `lru_cache`
on it brought 10% in one variant, nothing in others. The cache stays
in, it costs nothing and does no harm, but it wasn't the cause.

**`vsync=1` costs 12 to 19%**, but buys that with tearing and still
doesn't get to 60. Stays in.

**Native 1080 instead of downscaled 1200 helps the most**, in the
no-curvature variant 26.5 → 34.2 fps. That's why the resolution
question above is under "Open items."

On top of that, a heat finding independent of frame rate: with the
game **and** teleop running at the same time, the Pi hits 83 °C in
under a minute and throttles (`throttled=0xe0008`), the frame rate
keeps dropping as it does. Without active cooling, continuous operation
at the trade show isn't sustainable like this.

#### Decided on 2026-09-10: all three, plus a fourth

Measured on the same machine, native at 1920 × 1080, both cameras
active.

| Target unlimited | 2026-09-09 (1200, `SCALED`) | 2026-09-10 (1080 native) |
|---|---|---|
| everything on | 19.6 | **28.5 cold → 26 warm** |
| without curvature | 26.5 | **42** |
| without CRT | 36.6 | **61** |

Render-path stages measured individually, on the cold Pi: drawing the
scene 1.4–2.0 ms, `remap` 8.7 ms, scanlines 7.0 ms. For comparison, the
floor — a plain copy of the same amount of data — costs 1.83 ms.
`remap` runs at roughly five times that: the gather is compute-bound,
not bandwidth-bound, and there's nothing left to gain there with
OpenCV. Four variants were measured against each other (4× uint8, 1×
int32, `BORDER_REPLICATE`), all within 2% of each other.

**Two earlier hypotheses didn't hold up.** First: the 25 ms for "scene
+ flip" were almost entirely the `SCALED` scaling, not the drawing —
the scene itself costs 1.5 ms. Second: switching the overlay from
pygame's alpha blit to `cv2.multiply` was supposed to save 6 ms and
saved nothing. On the Pi the multiplication costs 7.2 ms and the blit
6.4; in the full render path, 21.4 against 21.5 ms — a tie. The
multiplication stayed anyway — half as much code, exact instead of
approximated vignette, and the whole post-processing path now hangs on
one thread setting instead of two. As a speedup it was a wrong guess.

**The fourth lever wasn't on the list and beats all three others: the
curvature moves from the image into the darkening map.** Instead of
sending every frame through a `cv2.remap`, the static scanline and
vignette map gets the curvature baked in — the lines curve like on a
tube and draw together toward the edge of the screen, the image itself
stays geometrically flat. The map is built at startup, the curvature
costs nothing at runtime.

| Variant | ms/frame | ceiling |
|---|---|---|
| curvature in the image (until 2026-09-09) | 24.95 | 40 fps |
| **curved scanlines, image flat** | **11.12** | **90 fps** |
| without curvature | 11.65 | 86 fps |

So curved scanlines cost exactly as much as *no* curvature at all.

**The second reason weighs heavier than the milliseconds: curvature
was breaking up the pixel font.** `remap` samples with
`INTER_NEAREST`, and an 8×8 glyph grid sampled at non-integer
positions frays — letter edges turn stepped, glyph pixels become
unequal sizes. That's the same bug that's the reason all font sizes are
divisible by 8, just approached from the other side. From 3–8 m a tube
reads by its lines anyway, not its geometry — the same argument that
kept chromatic aberration out.

The scanline phase comes from the curved source row and is computed
**as a coverage fraction, not sampled**. A pointwise-warped 3-px
pattern would otherwise give moiré stripes at the screen edge — that
was the reason the more obvious variant (put the scanlines before the
curvature) was rejected before it was even code. At `BARREL_K = 0` the
map falls back bit-exact to the old flat pattern.

**Result: 30 fps, 45 seconds straight, with teleop running.** 29.4 to
30.3, no drop, while going from 61.5 to 75.7 °C.

**The GPU shader remains open.** Curving *the image* with a sharp font
would be possible as a GLES fragment shader on the VideoCore, with
correct filtering and no frame-rate cost. Deliberately not built: a new
dependency, a GLES context under KMSDRM, a texture upload per frame,
and the layout self-test would no longer run headless. The code for
image curvature (`barrel_maps`, `cv2.remap` in the loop) is in the
history up through and including `6ed2b4a`, in case that option gets
picked up.

**The trade-off deserves naming:** scanlines remove brightness, and
readability from 8 m in a bright hall is this project's top priority.
`SCANLINE_ALPHA` therefore lives in `config.py` and gets tuned **in the
hall**, not at the desk. When in doubt, readability wins.

**No chromatic aberration.** It would need three remaps instead of one,
and from 3–8 m it doesn't read as an effect, just as blur.

### Sound: low-bit arcade music, notated declaratively

Music is **written as data, not as code**: one string per piece, which
`music.py` turns into sound at runtime. No audio files in the
repository, no dependency, no licensing question — and changing a tune
is changing one line.

```python
# game/music.py
ATTRACT = "c4 e4 g4 c5 - g4 e4 c4 -"     # note name + octave, "-" is a rest
```

How that works, in four steps:

1. **Note name → frequency** is one line: `440 * 2 ** ((halbton - 69) / 12)`.
   That's the MIDI formula, 69 is concert A.
2. **Frequency → samples** is a square wave: alternate `+A` and `-A`.
   That exact waveform *is* the chiptune sound — it exists because an
   NES or a C64 couldn't do anything but switch a level on and off.
   "Low-bit" here isn't an imitation, it's the direct approach.
3. **Samples → `Sound`** via `pygame.mixer.Sound(buffer=...)` with the
   stdlib module `array`. **No numpy** — `pygame.sndarray` would need
   it, the `buffer` route doesn't, and numpy isn't among the
   dependencies.
4. **The whole piece is rendered once at startup** and looped with
   `play(loops=-1)`. No scheduler, no timer thread, no note-by-note
   output. A loop running in the audio driver doesn't drift — same
   reasoning as "one time source per round," just for audio.

`pygame.mixer.pre_init(...)` has to run **before** `pygame.init()`,
otherwise the buffer size is already fixed and you hear latency.

It's wired up the same way as the detector: `Ctx` gets a `music` field,
scenes call `self.ctx.music.play("attract")` and never know what's
behind it. That gives a silent stand-in for tests without an audio
device, and the headphone test on the laptop is the same codebase as
the trade show.

**Sound stays garnish.** The hall is loud; nothing in the game may
depend on anyone hearing anything. The piece plays in attract mode, a
short beep confirms button presses, a jingle marks the score. Nothing
more.

#### Implemented on 2026-08-27

Six tokens in the notation, one token is a sixteenth note: `f4` note,
`.` sustain, `-` rest, `f4/a4/c5` chord, `a#2^f2` glide, `k s h`
kick/snare/hat. Two data tables at the top of the file — `PIECES` and
`SFX` — everything below them is just wiring.

**The loop runs per cycle, not per sample.** That's the decision
everything else follows from. One square-wave cycle is 30 to 500
samples long; recomputing volume and frequency once per cycle does a
hundred times less work than per sample — and you don't hear a
difference, because nothing can change within a cycle anyway. This one
loop is therefore where **envelope, vibrato, glide, arpeggio, and the
kick drum** live, each as two lines. All pieces and effects render in
0.12 s.

**Without an envelope, every note sounds like a test tone.** `ENV`
holds five curves (`pluck`, `hit`, `punch`, `swell`, `flat`), argument
is seconds since the note started. That was the actual reason the
first version sounded "computer-generated" — not the melody.

**Tuning: the cycle isn't rounded, only its endpoint is.** A rounded
cycle length pulls high notes off pitch — F5 at 44100 Hz lands 12 cents
flat, F6 even 23 — and because every note rounds differently, the
*intervals* end up wrong. That's exactly what reads as "off." With a
fractional position, the mean frequency is exact, the rest is half a
sample of jitter. The self-test counts zero crossings over one second
of tone across the whole range and requires ±1 Hz.

**Mixing is the mixer's job.** A piece has up to four tracks, each on
its own channel (`set_reserved(4)` out of twelve, eight stay for
effects). All tracks in a piece are the same length, so looped they
stay in sync forever. There's no summing loop in Python.

**Intensity isn't automation, it's four pieces.** `round0`–`round3`,
the same riff in F major at 118 / 132 / 148 / 158 BPM, the drums get
denser from a half-note backbeat to sixteenth-note hats. Major, not
minor: the tension comes from tempo and drums, not from sadness. Stage
3, the final five seconds, lays a ticking clock on every quarter note —
the melody keeps going. An earlier version replaced it with an alarm
over sixteenth-note bass drum; that was hardcore techno and clearly too
much for the trade-show audience. **Panic comes from the ticking, not
from more bass drum.**
`GameScene.update` calls `music.stage(self.left)` every frame,
switching only happens on a stage change. Measured: 60 → 40 → 20 → 5
seconds remaining; stage 3 kicks in with `WARN_SECONDS`, i.e. in the
same frame the screen turns red.

**Silence follows the finish sound.** `SceneBase.MUSIC_IN` is a pair
`(pause in seconds, fade-in in milliseconds)`, `DisplayScoreScene` sets
`(2.2, 1500)`: the round music stops immediately, the fanfare rings out
freely, two seconds of nothing happens, then the idle music fades in.
The silence is the effect. The fade-in is done by
`Channel.play(..., fade_ms=...)`, the waiting by `Music.update()` —
called in `run_game`, where something happens every frame anyway. No
timer thread, no second time source.

**A scene change is a music change, declaratively.** `SceneBase.MUSIC`
is a class attribute, `SceneBase.__init__` plays it. Every scene states
once what plays during it; `GameScene` sets `MUSIC = None`, because its
stage depends on time remaining. That way no future scene can forget to
turn off the round music — idle, score, and leaderboard inherit
`"idle"` and switch back automatically.

**The error sound costs one line.** `handle()` returns the name of the
sound, `None` means "not taken." In `run_game` there's accordingly:

```python
scene.ctx.music.sfx(scene.handle(action) or "nope")
```

That makes *every* button press make a sound, without any scene having
to think about it — pressing `>` during the round buzzes, pressing `^`
on the `<` field in the leaderboard buzzes. That one line is the entire
signifier mechanism.

`Music.REPEAT_MS = 90` swallows the same effect firing right after
itself. Without it, `KEY_REPEAT` fires 16 blips a second while
scrolling through letters.

**Without an audio device, `Music` is silent instead of broken.**
`pygame.mixer.get_init()` has to return exactly `(44100, -16, 1)`,
otherwise the constructor renders nothing and every method returns
immediately. No second stand-in class. `pre_init` sits as the first
line in `main()` — after `pygame.init()` the buffer size is fixed.

`uv run game/music.py` checks bar lengths, tuning, and track lengths
and writes WAV files to `/tmp/picknplay-audio`, including
`session.wav`: idle, start fanfare, 60 seconds of build-up, finish
sound, back to back. You can listen without starting the game.

#### Where the tones came from

`Dream_Sound.mp3` (101 s) was analyzed by FFT, not transcribed by ear:
tempo ≈ 85 BPM, key F major, bass moves F2 – Bb2 – C3 – A2/D2, the
melody sits between F4 and A5. That's exactly what became the idle
music — 84 BPM, F – Dm – Bb – C, wide half notes in the bass, a thin
pulse (duty 0.125) for the arpeggios. The round takes the same tones in
D minor: related enough that the switch doesn't sound like a different
game.

So what got carried over was the *description* of the piece, not a
single note. No sample, no file in the repository, no licensing
question.

---

## Interfaces of the still-empty files

No `abc`, no `Protocol`, no base class. A detector is anything that has
`tray_sum()` — no more of a contract is needed, and swapping stand-in
for hardware stays one line in `main.py`.

### `db.py`

```python
class DB:
    def __init__(self, path=DB_PATH)      # CREATE TABLE IF NOT EXISTS
    def top(self, n=TOP_N)  -> list[tuple[str, int]]
    def qualifies(self, score) -> bool
    def add(self, initials, score) -> None
```

**`ORDER BY score ASC`.** The score is the *distance* to the target
value, `0` is perfect. Set to `DESC`, the leaderboard is silently
backwards and nobody notices at the trade show. A `rowid ASC` tiebreak
keeps the order stable on ties.

`qualifies(score)` is `len(top) < TOP_N or score < top[-1][1]`.

This file gets an `if __name__ == "__main__":` block with `assert`s —
insertion, sort direction, eviction once the top 10 is full. The only
spot in the project with non-trivial comparison logic, and the only one
whose bugs you don't see on the trade-show floor.

### `hw.py`

```python
class FakeDetector:                       # build first, without a camera
    def tray_sum(self) -> int

class Camera:                             # grabber thread
    def __init__(self, index=CAM_INDEX, size=CAM_SIZE)
    def read(self)      -> frame | None   # always the LATEST frame
    def close(self)     -> None

class ArucoDetector:
    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI)
    def fresh(self) -> dict[int, quad]    # same signature as FakeDetector

class CameraView:                         # one pane
    def __init__(self, cam, det=None, size=CAM_VIEW)
    def surface(self) -> pygame.Surface | None
```

**The contract has been `fresh()`, not `tray_sum()`, since
2026-08-27.** A detector is anything that has `fresh()`: a dict from
marker ID to a quad, both of which the scene needs anyway. Summing
happens in the scene, because `VALUES` is a game rule, not sensor
knowledge — a detector that knows point values would be a sensor with
an opinion. `tray_sum()` was dropped with no replacement, it had
exactly one caller.

`uv run game/hw.py` checks, without a camera, against a synthetically
drawn tray: that `DICT_4X4_50` matches `markers/`, that the quads land
where the markers were drawn (±3 px), that `TRAY_ROI` filters out
anything outside it, that the hysteresis holds and then decays
correctly, and that `FakeDetector` has the same interface.

**`FakeDetector` first.** The stand-in should change its sum on its
own (say, reroll every 3 s), otherwise the tray number sits still for
the whole round and you can't tell whether the display updates at all.

**`Camera` as a thread, not a process.** `cap.read()` is C++ code and
releases the GIL. The thread writes the frame into an attribute under
lock, the loop reads — never the other way around.
`CAP_PROP_BUFFERSIZE = 1`, otherwise the V4L2 buffer delivers old
frames and detection visibly lags behind.

**Hysteresis in `ArucoDetector`:** a dictionary `marker_id -> time of
last sighting`. `tray_sum()` sums everything younger than
`MARKER_HOLD`. That's the solution for a hand hovering over the tray,
not for pucks that actually disappear — that would need position
tracking, and that's deliberately out of scope.

Running `detectMarkers()` at `DETECT_HZ` instead of at 60 FPS:
detection is expensive and the game doesn't need it more often than the
visitor actually moves pucks.

### `Buttons` (later, milestone 10)

gpiozero callbacks run on a foreign thread. The button press goes into
a `queue.SimpleQueue`, `run_game` drains it once per frame and pushes
the actions through the same spot as `action_of`. Not one line in
`scenes.py` changes because of this.

**Watch out:** `pygame.key.set_repeat()` only applies to the keyboard.
Scrolling through letters on hold has to be generated by `Buttons`
itself — otherwise initials entry behaves differently at the trade show
than during development.

### `main.py`

```python
def main():
    pygame.init()
    fonts = {"big": ..., "mid": ..., "small": ..., "tiny": ...}
    ctx = Ctx(detector=FakeDetector(), db=DB(), fonts=fonts)
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS)
```

The only file that imports both `scenes` **and** `hw`. Switching to
real hardware is exactly one line: `FakeDetector()` →
`ArucoDetector(Camera())`.


---

## Constraints

- **Throughput:** ~90 s per person including changeover. 6 h trade show
  ≈ 240 visitors.
- **Tolerance:** any required placement accuracy ≥ 1 cm. Servo backlash
  and dead zone don't allow anything finer.
- **Servo protection:** conservative torque and overload registers in
  EEPROM, software joint limits, a watchdog on load and temperature.
- **Wear:** the gripper servo dies first. Spare servos, printed spare
  parts, ideally a complete second arm as a hot spare.
- **USB bandwidth:** two UVC cameras on one bus over-allocate bandwidth
  ("No space left on device"). Test before the build, separate buses or
  lower resolution if needed.
- **Ergonomics:** a step stool for shorter visitors. Hand sanitizer at
  the leader.
- **GDPR:** if contact data is collected, mostly minors are involved.
  Clarify in advance.
- **Autostart:** both processes as systemd services. The machine has to
  come back up after a power outage without a keyboard.

## Balancing: prices and target value

Decided on 2026-08-27, revised on 2026-09-11 along with the scoring.

**The target value isn't rolled freely.** `randrange(50, 300, 5)`
alongside a tray sum meant chance decided whether someone had to bridge
EUR 0.30 or EUR 20. That was the actual unfairness — not the values,
but the missing coupling. `balance.gap()` therefore reads the real tray
and picks the *distance*:

1. exactly closable in `GAP_MOVES` (2) moves — no round is impossible
2. the best single move lands between `GAP_ONE_MISS` (2) and
   `GAP_ONE_MAX` (25) off, i.e. EUR 0.20 to EUR 2.50

The lower bound prevents the lucky grab that lands directly on zero.
The upper bound prevents the opposite: a round that still leaves
EUR 6.70 open after the best single move can't be closed within the
round time.

**The tray starts empty, and that makes the target set finite.**
Because every round starts from the same state, the set of valid
targets is also the same every round — with the current price set
that's 21, and they're the entire supply of tasks for a trade-show day.
The binding knob for that is `GAP_ONE_MAX`: at 15 there would be 14
targets, at 25 there are 21. The band `GAP_MIN`/`GAP_MAX` is *not* it —
it doesn't cut anything that the single-move condition doesn't already
cut.

`gap()` still reads the real tray instead of using a constant: a
cupcake left lying around then changes the task along with it, instead
of breaking it.

**The prices share no common divisor.** Calculated in 10-cent units —
`{14, 17, 21, 24, 28, 32, 36, 41, 46, 52}`, shown as EUR 1.40 to
EUR 5.20. If these were round prices in cents, the GCD would be 10 and
the game would be binary: distance divisible by the divisor, then one
grab is enough, otherwise it's *completely* unreachable. Only
coprimality gives you "just barely off" — and with it a leaderboard
with resolution instead of a list of zeros and impossibles.

**One marker per physical cupcake, ten of them.** `ArucoDetector.marks`
is a dict keyed by ID: two cupcakes with the same marker count once.
Printing duplicates would be a silent scoring bug that looks like a
detection problem at the trade show. Ten also fits the grid of the
price table on the score screen.

## Prizes

Three tiers, all reachable — everyone wins something:

- **Participation** — sticker or 3D-printed keychain
- **Score band** — better prize, tiered by accuracy
- **Daily leaderboard** — grand prize at the end of the trade-show day

The band boundaries aren't set yet. They belong on `off`, not on the
score, because `off` is the physical truth of the round: proposal `0` /
`≤ 5` (i.e. up to EUR 0.50 off) / everything else, to be confirmed once
someone has watched real results for an afternoon.

## MVP milestones

Order follows the principle: something runs after every step. The
software is finished against stand-ins before hardware gets connected.

**Software (without hardware)**

1. ● Skeleton runs — scene logic, transitions, `main.py`/`db.py`/`hw.py`
   in place, click-through
2. ◐ Readability — layout drawn, color timer in place; not yet checked
   from 8 m
3. ◐ Game logic — `FakeDetector` returns numbers; `tray_sum()` sits in
   the wrong branch (finding 3)
4. ◐ High score — cursor model and SQLite in place, `handle` duplicated
   (finding 1)
5. ◐ Attract mode — timeouts and title screen in place, demo video
   missing
5a. ● CRT overlay — curvature, scanlines, vignette in `run_game`; Press
    Start 2P as the font. Tune strength in the hall, measure cost on
    the Pi
5b. ● Music — `music.py`, declarative notation, square-wave synthesis,
    ducking
5d. ● Balancing — `balance.py`, target value from the tray, values with
    no common divisor; `GAP_MOVES` stays a guess until someone measures
5c. ● Fullscreen — native 1920 × 1080 without `SCALED`, `FULLSCREEN`
    switch in `config.py`, 30 fps signed off on the machine (2026-09-10)

Legend: ● done · ◐ started · ○ open

**Hardware**

6. Arm runs — teleop 10 min without a fault
7. Grabbing works — 9 of 10 pucks without tipping
8. ◐ Markers get detected — code in place and running against the
   webcam; unverified against the printed markers under hall lighting
9. ◐ Tray gets read — hysteresis in place (`MARKER_HOLD`), unverified
   in reality

**Integration**

10. ● `FakeDetector` → `ArucoDetector` done (`CAMERA` in `config.py`);
    `FakeButtons` → `Buttons` open
11. LED states, systemd autostart for both processes, UDP heartbeat

Milestones 1–5 need neither the arm nor the camera and run in parallel
with the hardware. One integration step falls away: both processes just
get started next to each other.

## Out of scope

Jetson, browser frontend, WebSocket, Flask, Kubernetes, ConfigSync,
GCS, Vertex pipelines, trained CV models, autonomous operation without
teleop, FPV as its own game (only as an optional hard-mode switch).
Video decoding in **attract mode** stays out — the demo clip runs in
`HowToScene`, a few seconds per visitor instead of six hours in a
closed cabinet.

## Open Items

- Which Pi (model and RAM)
- **Powered-off parking pose for the follower** — blocks torque
  shutdown in idle
- Python version of the Pi image, which determines the LeRobot version
- Number of arms available
- Trade-show duration and booth staffing
- ArUco detection rate under hall lighting (don't test in the studio)
- Real action count for an untrained user in 60 s — currently sits as
  `GAP_MOVES = 3` in `config.py`. The mechanism works at any value,
  only the constant is a guess; once someone measures it, it's a
  one-line change
- Whether the intermission scene gets its own, thinner music instead of
  the idle loop — one string in `PIECES`, no code change
- `up` runs backward through the alphabet in name entry (A → Z). With
  real arrows instead of `^v` this now stands out more; a one-line
  change in `LeaderboardScene.handle` if it should be flipped
- Tune `TRAY_ROI` on the assembled machine — depends on camera height
  and tray size
- CRT scanline strength under hall lighting: at what point does the
  effect cost more readability than it gains in looks
  (`SCANLINE_ALPHA`, `VIGNETTE_ALPHA`)
- ~~Whether the Pi has the 3.3 ms to spare for the curvature~~ — done
  2026-09-10. The curvature now lives in the static darkening map and
  costs nothing at runtime
- **Active cooling.** Without a fan, the Pi throttles under double load
  and skews any measurement by up to 35%. First order, blocks
  continuous operation at the trade show
- Whether the GPU shader gets built (curving the image with a sharp
  font). Optional, not blocking
- ~~Whether `cv2` loads cleanly next to `pygame` on the Pi~~ — done
  2026-09-09. On Ubuntu 24.04, OpenCV 5.0.0 and pygame-ce 2.5.8 load
  under Python 3.13 without a symbol conflict
- Audio output on the Pi (jack, HDMI, or USB) and whether anything is
  even audible at the booth
- ~~Whether the 60 px bars top/bottom disappear behind the cabinet
  bezel~~ — moot, the panel is 16:9 and rendering is native
- ~~Whether rendering is native at 1920 × 1080 instead of downscaled
  from 1200~~ — done 2026-09-10, layout has moved
- Pi power supply on shutdown: a hard cut broke the git repo on
  2026-09-09 (five zero-byte objects). At the trade show, that's the
  machine's SD card
- Snap-in vs. screw-mount buttons on 3 mm plywood — test tear-out
  behavior
- Two cameras at once: verify bandwidth on the real Pi (the arm
  camera's index isn't fixed yet, `CAM_INDEX` is one)
- FPV latency, in case hard mode happens

## Workflow

Originally: the MVP deliberately built without AI assistance. Primary
sources, try before you look it up, ask a colleague instead of a tool
if stuck for two hours. Time budget set two to three times higher
accordingly.

**Adjusted (August 2026):** the assistant is used as a reviewer and
explainer — it reads code, names bugs by file and line, explains design
questions, and maintains this document. Everything was initially
hand-written: the learning effect depends on the keystrokes happening
yourself.

**Adjusted (2026-08-27):** the skeleton is in place and understood —
scene model, loop, the `Ctx` seam, layout coordinates all came from
hand and are therefore internalized. From here on the assistant writes
the code, but only after the four-step process above. Understanding
thus shifts from "I typed it" to "I made the decision and could defend
it" — and the latter is what counts at 9 a.m. at the booth when
something needs fixing. The process is the condition for that: without
steps 2 and 3 it would just be dictation.
