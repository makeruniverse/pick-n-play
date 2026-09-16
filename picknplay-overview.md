# PICK'N'PLAY — Project Overview

**Titel:** PICK'N'PLAY (previous working title: TRAY RUNNER)
**Stand:** August 2026 · Concept stands, hardware in construction, software in construction
**Plattform:** Raspberry Pi · Python · pygame

---

## Stand: 28. August 2026

**UX Pass over all five scenes.** The reason was a clipp error on
Leaderboard: the fifth best list line and the demolition query
by 528 × 30 px, visible only from five entries in the DB.
The error was not a numberdriver, but a missing invariant — a
long list and an overlay shared the same space without
Bye.

Four changes, all written in 'UI-Layout':

1. **Footer band** (`FOOTER_Y`, `SAFE_BOTTOM`, `footer()`— one line per
Scene at the same place for the four buttons. The question *replaces* it,
instead of standing next: the error class cannot come back.
Two. **Price line instead of price table** in `DisplayScoreScene`— the ArUco ID column
is out, the values are sorted, and yellow are those who actually lay.
3. **`BEST — LOWEST WINS`** on both lists, and`TOP 10!`now
   `ENTER YOUR NAME`— the old heading promised a gate that there was no.
4. **`OFF BY`in the round** — the difference the visitor before in the head
has to form, is now big.`PERFECT n` erbt denselben Platz.

Dazu ein **Layout-Selbsttest** in `scenes.py`according to the house convention:
`uv run game/scenes.py` → `ok`. He catches everyone`draw()`- Call and check
Image boundaries, `SAFE BOTTOM`and coverage of all scenes and states.
Conversely, he can fail.

---

## Stand: 27. August 2026

**What's going on:** The skeleton is clickable. All four scenes draw after
Layout below, `FakeDetector`delivers changing numbers, SQLite stores and
sorted right. The six findings in`scenes.py`are fixed (see below).

Since today, the optics have also been: **Press Start 2P** as a font that
color ID on HPI red and orange, and the **CRT overlay** with curvature,
Scanlines and Vignette. Both in own sections further down.

Quellcode liegt seit heute in `game/`. No import changes:
`uv run game/main.py` setzt `sys.path[0]`on`game/`, so find the modules
still flat. The folder forms the process limit
'Process architecture' — a later`teleop/`not in it.

| Datei | Zustand |
|---|---|
| `game/config.py` | finished — times, colors, font, CRT, keymap, values, hardware constants |
| `game/app.py` | fertig — `Ctx`, `SceneBase`, `action_of`, `run_game`, CRT-Overlay |
| `game/assets/` | Press Start 2P (SIL OFL) + `OFL.txt` |
| `game/scenes.py` |** scenes incl.`render()`, `footer()`, Layout-Selbsttest (`uv run game/scenes.py` → `ok`) |
| `game/db.py` |finished, with`assert`-Selbsttest (`uv run game/db.py` → `ok`) |
| `game/hw.py` | `FakeDetector`, `Camera`(with warm-up guard),`ArucoDetector`, `CameraView`, `VideoView` fertig; `Buttons`Open|
| `game/main.py` |finished — wiring, four font sizes`FONT_SIZES` |
| `game/music.py` | fertig — Notation, Synthese, Ducking, `Ctx.music`, Selbsttest (`uv run game/music.py` → `ok`) |
| `game/balance.py` |finished — target value finding from the tray, self test (`uv run game/balance.py` → `ok`) |

### Befunde in `game/scenes.py` — erledigt

The six findings of 27 August (double`handle`, fehlendes `self.top`,
`tray_sum()` im falschen Block, `top(TOP_N)` instead of `top(5)`, Magic Number
`3.0`, voice mix) are all fixed in the code. Reviewed the same day,
headless played through: Idle → Round → Score → Initials → Idle, the name
is in the best list.

`scenes.py`and`app.py`mix tabs and spaces; all files in`game/`
are now in four spaces (`expand -t4`). The mixture was not
Cosmetic query, but a trap for any tool that touches the file.

### Arbeitsweise in diesem Projekt

**Departure per feature — four steps in this order:* *

1. **Vadim asks for a feature. **
Two. **The wizard reconsiders and presents** — the way in which the alternatives
he has rejected and why, and the code. A *short* explanation of
Places where something new happens. In short, if the explanation
is longer than the code, something is wrong with the code.
3. **Vadim gives release** — or corrects direction. Without release
No`.py`-Datei angefasst.
4. **The wizard implements** and says afterwards what is actually tested
and what not.

The point at step 2 and 3 is not the approval, but the
Draft decision before it is in the code. A
Feature that you can't explain in five sentences is cut too big.

The order of the Ladder principle applies to proposals:
→ Standard library → native platform feature → existing
Dependence → one line → only then own code.

This document is used by the wizard. It is in working language
English written; **Everything on the machine screen is
Englisch** (see "Display language")..

### Order from here

Rule: after each step something is running, and each step is too
see. Steps 1–3 are now possible, 4–5 need hardware.

1. ~~Recovers 1–5~ — completed, milestone 1–4.
2. ~~`music.py`'— see 'Sound'. It is open to listening
Automatic loudspeaker: Volumes are set on the headphone, the hall is
louder. The melodies stand as strings in`PIECES`— improved
change a line, no change.
3. ~~CRT-Overlay in `run_game`~~ — completed, including curvature and pixel font.
The measurement on the Pi has existed since 9.9.2026 and is negative, see
"Measurement on the Pi". The setting remains open in the hall.
4. ~~`Camera` + `ArucoDetector`~~ — completed, incl. passthrough-inset. Open
the detection rate against the *printed* marker remains under indoor light.
Five. Teleop Process: Torque state machine, Heartbeat receiver, wake ramp.
6. `Buttons` (GPIO), LEDs, systemd.

Do not push in between:`db.qualifies()` as gate in front of the leaderboard
(Balancing question, see Open Points). The demo clip has its place
(`HowToScene`, `DEMO_VIDEO` in `config.py`) and waits for one
Layout for filming — until then the scene runs as a text page.

---

## Was

An arcade machine with real robot arm. Visitors control an SO-101 follower arm by teleoperation and solve an appreciation game against the clock. Order work for an MINT trade fair to recruit prospective HPI students.

The arcade frame is not a decoration, but the user manual: Everyone understands a slot machine immediately. No explanation, no staff needed to explain the entry.

## Spielmechanik

Adaptiert von Googles *Price-a-Tray* (GDC-Demo). Ablauf:

1. On the tray are preloaded objects, each with a hidden point value.
Two. The display has a target value.
3. 60 seconds: swap, remove, add objects.
4. Score = amount of the difference between tray sum and target value. **Over and under count equal — there is no failure, only one number.** Standing`OFF BY 0`for five seconds, the round ends prematurely (`PERFECT_HOLD`) — the hands lie on the leader's arm, a 'final' button would be inaccessible.
Five. At the end: Reveal of the entire price table. Learning moment and second reward.

The Skill is in conclusion (“what this thing worth?”), not in fine motor technology. This is consciously so chosen — the poor has too much gear play for a precision game.

**Preloaded tray** is the central adjustment to Google: Teleoperated picks last 10–20 s instead of 1–2 s with hand. Switching instead of setup keeps the round playable.

## Arcade-Framing

| Element | Umsetzung |
|---|---|
|Cabinet|Aluminum extrusion box (follower inside), Leader arm before on podest|
| Marquee |Illuminated sign above, title + HPI logo. Physical, not on the screen|
| Attract Mode |When idle: LED loop at cabinet, display shows high scores alternately with title. **The arm does not move** — see 'Idle, Cooldown, Electricity'|
| Bedienung |**Vier Arcade buttons in cross order, otherwise nothing.** Right = forward/confirm, left = back/off, high/down = select. The same four buttons start the game, break and tap the initials. No keyboard, no joystick, no extra button.|
| Timer |Background color: black at start, starting from 5 s residual time after HPI-Rot running. 8 m legible.|
| High Score |Top 10, three letters initials, input via the same four buttons|
| Optik |**Press Start 2P** (Pixelfont, no antialiasing), Monospace, high contrast, black reason. On top of a **CRT overlay** — curvature, scanlines, vignette, see own section|
| Sound |**Low-bit arcade music**, declaratively notated and synthesized at runtime; see dedicated section. Exhibition halls are loud, so sound is atmosphere, never critical information.|
| LED-Streifen |Addressable, status display at cabinet: Idle-Loop, runtime, last 5 s, Score-Reveal|
| Emergency stop |Red mushroom button. Functionally required and visually fitting.|

**Display language: English.** Divorced August 27, 2026. Arcade Convention — `PRESS`, `GOAL`, `TIME`, `TOP 10`reads everyone as an automatic language, so eleven years old. German words are therefore longer, and width is the scariest resource on the screen for font size 200. This document remains German, the strings in the code are English.

**Letability before effect.** The target group is 3–8 m away in a bright hall. Target value, current sum and residual time are the three numbers that are always large and always in the same place. Everything else is supporting detail.

## Hardware

- **Rechner: Raspberry Pi** (Model still to be set, see Open Points)
- SO-101 Followers (12 V STS3215) in the box, Leader (7.4 V) outside
- **Two cameras:**
- *Top-Down*, fixed, autofocus and exposure — provides marker detection
- *Arm camera*, pure passthrough on display, no evaluation — the
continues, the overlay is only on the top down camera
- **Display: Asus MB169CK, 15.6", 1920 × 1080 (16:9). ** Read on 9.9.2026 by EDID at the Pi. **Correctification:**This was previously ‘1920 × 1200 (16:10)’, which was wrong — the MB169 series is FHD. The design resolution in`config.py`continues to stand at 1200,`pygame.SCALED`therefore calculates with factor 0.9. This costs sharpness at the pixel font and computing time, see "Measure on the Pi". Second display optional for viewers
- **Vier Arcade buttons** (high/low/left/right) to GPIO, plus emergency off. **Panel 3 mm** — Snap-in (Sanwa OBSF-30, specified for 2–4 mm) is in the range, but with plywood, screwdrivers (Seimitsu PS-14-KN, OBSN-30) are the more durable choice. Hole size 30 mm, flat plug 2.8 mm.
- WS2812B strips. Working on Pi 5`rpi_ws281x`not (RP1); Options: PIOLib, SPI path (`rpi5-ws2812`, `Pi5Neo`) or deposit on an ESP32 with WLED via UDP/DDP. The latter takes timing, power supply and level conversion from the Pi.
- 3D printed pucks: flat ground, deep center of gravity, uniform gripping rib, ArUco marker plan top
- tray with edge

**No Jetson.** The only justification for a Jetson would be CUDA interference, and ML is deliberately not in the game. The existing Jetson Nano hangs on JetPack 4.6 / Ubuntu 18.04 / Python 3.6, LeRobot requires Python ≥3.12. Old Stack, unused GPU, no return.

## Software

Python · OpenCV (ArUco) · pygame · SQLite

**ArUco instead of Machine Learning.** Marker IDs mapping deterministic to values. No training, no record, no illumination risk, values changeable by dictionary reload. Replaces Google's complete Vertex-AI/GCS stack.

**pygame instead of browser frontend.** A process, a language, no chromium, no web server, no JPEG-Encoding per frame. Full image directly via KMSDRM without desktop environment. The arcade button comes in as a normal event. Price for this: Layout is manual work in coordinates, not CSS. This optics — Monospace, large numbers, black reason — is not a loss.

If ML is to be shown at the stand: only as a parallel display value on a second monitor, **niemals in the critical path of the game logic. **

## Prozess-Architektur

**Two separate processes. They're not talking. **

| Prozess | Aufgabe |Dependencies|
|---|---|---|
| Teleop | Leader lesen → Follower schreiben, ~30–50 Hz konstant |LeRobot (or Feetech SDK directly)|
|game|Camera → ArUco → Condition → rendering| OpenCV, pygame, SQLite |

The game logic needs camera images, marker IDs, a timer, and button input. It never needs arm state. The visitor pushes pucks, the camera sees the result — the poor is pure input method.

Konsequenzen:

- No joint loop. Rendering must not put the arm control in the stutter.
- No protocol between them. Nothing to synchronize, nothing to debugging.
- One's crash doesn't kill the other.
- They're running on two computers. If LeRobot zigzags on the Pi: Teleop on a laptop, play on the Pi.

**Teleop runs throughout, not per round.** No start of LeRobot from the game logic. Engine initialization and calibration for each visitor would be seconds waiting time plus a crash risk that will be redrawn with each round.

** Camera passthrough on the game screen is optional.** The real arm is visible in the cabinet; a live image is unreadable from 8 m distance anyway. If at all, then as a small inset (which the machine sees) in low resolution, never as the main surface.

**LeRobot installation:** Check Python version of the Pi. Bookworm delivers 3.11, current LeRobot requires ≥3.12 — then miniforge/pyenv, or on LeRobot 0.4.x pinnen (≥3.10). At ARM, LeRobot automatically drops from TorchCodec to pyav during video decoding, which is expected and no mistake.

The servo calibration (offsets, directions of rotation, end stops) is not written itself. Just the type of bug that looks like a cabling error for hours.

---

## Code Structure (Game Process)

```
picknplay/
game/ # game process, started with: uv run game/main.py
    main.py     # Verdrahtung: Ctx bauen, Startszene bauen, run_game aufrufen
config.py # constants: times, colors, font, CRT, keymap, values, paths
    app.py      # Ctx, SceneBase, action_of, run_game, CRT-Overlay
    assets/     # PressStart2P-Regular.ttf, OFL.txt
    scenes.py   # IdleScene, GameScene, DisplayScoreScene, LeaderboardScene
hw.py # Camera grabber, ArucoDetector, FakeDetector, Buttons, LEDs
    db.py       # SQLite Highscore
    music.py    # Notation -> Square-Wave-Synthese -> pygame.mixer.Sound
  markers/      # generierte ArUco-PNGs
archive/ # preliminary stages, not imported
scores.db # is created at the first start, relative to the work directory
```

**Flach instead of packages, but in a subfolder.** The original plan looked`app/`, `scenes/`, `hw/`, `data/`as packages. With about 500 lines total code, this costs only`__init__.py`-Rauschen and long import paths; Seven files that ever fit on a screen are quicker to look over. Split up as soon as a file doesn't do it anymore.

`game/`is **no package** — no`__init__.py`, no relative imports. Python set`sys.path[0]`to the directory of the started file, so the modules find each other flat as before. The folder separates source code from markers, archive and document and marks the process limit: a later`teleop/`because the two processes share nothing.

**`scenes.py` importiert `hw.py`never.** Only`main.py`knows both sides and puts them together. A false import is thus immediately noticeable.

### Vier Prinzipien

* *The loop has the time, the scene has only condition. **
`clock.tick(fps)` supplies `dt`in seconds, the loop is enough.`update(dt)` calculates, `render(screen)`only draws Calcnetes. A slow frame must not let the game logic drift.

**`Ctx`is a seam, not a container. **
Scenes call `self.ctx.detector.tray sum()`and never know if there's OpenCV or an attractor behind it. This allows the entire game to be written and tested without arm, camera and LEDs; the exchange for real hardware is a line in`main.py`. Duck Typing, no framework.

**Scenes know actions, no keys. **
`action_of(event)`* and* GPIO to four strings:`"up"`, `"down"`, `"left"`, `"right"`. The loop translates centrally and calls`scene.handle(action)`; unknown keys are discarded beforehand so that no scene has to check a special case. Keyboard when developing, arcade button at the fair, scenes unchanged.

Conscious *no* semantic names like`"start"`/`"back"`. In the case of exactly four buttons without labeling, the direction is the meaning, and an intermediate layer which`"right"` in `"start"`translated, would be an abstraction with exactly one implementation. The Convention (right forward, left back) instead lives in a commentary`config.py`and is applied in every scene.

`pygame.key.set_repeat()`provides the repetition when holding — necessary to scroll through the alphabet. **Attention to integration:** GPIO-Callbacks do not have auto-repeat that needs`hw.py` selbst erzeugen.

**No`on_enter`/`on_exit`. Scenes are disposable objects. **
Each transition builds a new entity (`self.switch_to(GameScene(self.ctx))`), so is`__init__`the entry point and the end of the reference is the exit. A second hook pair for the same moment would be just another place where it can be forgotten. The only price:`__init__`runs around a frame before activation — irrelevant for 60 seconds.

**A time source per round. **
No`set_timer`parallel to a`t_start`. The rest time is a`float`in the scene, the`update(dt)`count; from the same number follow indicator *and* transition. Two watches run apart, and this looks like a bug on a machine with audience because it is one.

### Scenes and transitions

|Scene|Leaves| Ziel |
|---|---|---|
| Idle | `right` | HowTo |
| HowTo | `right` | Game |
| HowTo | `left`or timeout| Idle |
| Game | 60 s abgelaufen | Score |
| Game | `left` zweimal innerhalb 3 s | Idle |
| Score | `right` | Leaderboard |
| Score | `left` | Idle |
| Leaderboard | `right`on the last field (stored)| Idle |
| Leaderboard | `left`on the back arrow| Idle |

The Leaderboard input is a single cursor index:`0`= back arrow,`1..3`= the three letters.` up`/`down`change the letter under the cursor,`left`/`right`move him. This means that the scene does not need at input mode — Position *is* the mode.

**Every non-Idle scene has an inactivity timeout back to Idle.** visitors go away in the middle of the input; the machine must reset itself without personnel.

### Incidentity in the game process

- ** Camera grabber and detection run as threads, not as processes. **`read()`and`detectMarkers()`are C++ code and release the GIL — a thread delivers real parallelity there. Shared memory between processes is only required when the Python itself is expected.
- **Muster: Thread writes in an attribute (under lock), Loop reads.** Never the other way.
- **The graver always holds the latest picture**, not the oldest. Otherwise, the V4L2 buffer delivers old frames and the detection is visible behind.
- **GPIO-Callbacks run in a strange thread.**`queue.SimpleQueue` legen, einmal pro Frame im Loop leeren.
- **LEDs never block. ** `set state()`comes back immediately — at WLED`sendto`, at local LEDs a worker thread with state slot.
- **Kern allocation happens in the systemd unit (`CPUAffinity=`)** at process level, not in Python code. It's only when it was measured that it stutters.

---

## Idle, Cooldown, Strom

Difference on 27. August 2026, after the hardware integration is up.

* *In the Idle the follower is powerless.** STS3215 hold position over
permanent current against gravity — this is the heat source and it disappears
only if the holding stops. Six hours of trade fair at 100% turn-on time
the safe way to lose the Gripper Servo. With disconnection between
Rounds are made from 100% around 67% (60 s round of 90 s per visitor), and
Breaks are evenly distributed over the day.

**Price for this: the arm falls.** It takes a pose in which it is stable without current
and not on the tray. This is a design job
(beat or deposit), no software task, and it blocks the
Torque shutdown until it is released.

**The Attract mode arm movement is deleted.** It was contrary to
Line above: an idle movement loop is 100% turn-on time in exact
the phases in which no one plays — the largest heat and wear items
of the booth, for the audience that is not here. The movement in the Attract
Fashion the LEDs. They are visible from 8 m anyway better than an arm in
Cabinet.

**Arousing is the dangerous place.** Followers powerless, visitors introduce
Leader somewhere, Torque an — the follower jumps abruptly on the
Leader pose. The order that prevents this: Goal position on the
**Set the follower's position**, turn on Torque*, then goal
over ~1,5 s to the Leader-Pose. Without these three steps
Servo heat exchanged for a jolt per visitor, 240 times a day. One
EEPROM torque limit does not help — the jump passes within
erlaubten Moments.

**The process limit gets exactly one channel. 'Robots in the Idle' means:
that the game must tell the Teleop process its state. Selected: a
UDP datagram to localhost, a few times per second, content is the
Scene name. One-sided, loss-proof, without connection and without protocol.

The decisive characteristic is not the mechanism, but the interpretation:
**no package means "out". ** If the game process dies, hangs the camera, becomes
pulled a cable — then the arm cools off, instead of heating unattended.
A channel in which silence is read as 'last condition',
turns every crash into six hours of continuous load. Teleop never waits for
Game; that would be the coupling that should avoid the two-process architecture.

**Cooldown is not a game mechanism.** The servos lead their temperature to
a register; read it with 1 Hz, not in the Teleop cycle — Temperature
changes over tens of seconds, and every read costs bus time in
30–50 Hz cycle. The value goes to the log and to the LED color. First of all
hard limit, the teleop process switches off the torque, regardless of
Game condition. Conscious *no* Round-Sperre: "please wait" is at the booth
with queue is a visible failure, and when the hard limit reaches,
ohnehin etwas anderes kaputt.

**Kerne: only Teleop is spinning. **`CPUAffinity=3`and`Nice=-10`in the
Teleop-Unit, `CPUAffinity=0-2`for the game. The Teleop loop is CPU-light —
he waits on the serial bus — but on schedule: late cycles sees
you're in the arm as a buzz. These are two different problems; Affinity solves
'who should not be repressed', the priority is 'not too late'.
IRQ affinity remains until it is measured that it is missing.

What separates Pinning **not**: storage bandwidth, USB host controller and
the heat budget. Throat the Pi, the clock drops for all four cores
at the same time — also for the pinned Teleop loop.

**Not-off physically separates the 12 V-rail.** A mushroom button, the one
Python loop by GPIO is not an emergency stop, but a button: if the
The process depends — the case against which one is insured — it does nothing. The
Software task is not triggering, but clean up
after that, because the follower is then somewhere (see wake ramp).

**LEDs remain on the ESP32. ** WLED via UDP takes timing, level conversion and
the power supply from the Pi. A WS2812B rod is at full white with ~60 mA per LED
the largest individual consumer at the stand, clearly before the Pi —
Brightness limitation is power management and heat management in a
Zahl.

**Two mistake images that are guaranteed to be incorrectly diagnosed on the trade fair day:* *
Undervoltage at the Pi is shown as choke * and* as a USB output — ‘the
Camera is sporadic" is usually the power supply, not the code. And
Switch-on current: all at the same time at the same switch can power supplies into the
The automatic system starts 'sometimes not', which after
Software aussieht.

* *The Idle Screen renders with 20 FPS instead of 60** (`IDLE_FPS` in `config.py`,
`TICK`as a class attribute of the scene). He shows a text twice per
second flashes, and a best list that doesn't change at all — 60 times
to push 2,3 megapixels per second through the barrel distortion is six
Hours of warmth in a closed aluminium cabinett, for a picture that no one
look. The most invisible lever in the whole project and the cheapest.

Active cooling and an airway in the cabinet still remain first order; each
Software repair is second.

### What needs to be measured

- Keep current and servo temperature of the follower in work pose, with puck in
Gripper, over 10 minutes
- Whether and where the arm is unstable
- Both cameras simultaneously on the real Pi, in the formats that are selected
- Pi temperature in the closed cabinet under full load
- Teleop cycle time jitter, measured *while* renders the game — before is
any statement about cores

### Camera and Passthrough (converted on 27 August)

`Camera`is a graver thread with`BUFFERSIZE=1`, `ArucoDetector` ein zweiter
Thread with`DETECT_HZ`. Two threads instead of one because on the development computer
*a* webcam both operated: ran the detection in the Grabber thread, the
Image rate of passthrough depends on the detection time.

** Format before resolution. * *`MJPG`is set before width and height
,. As YUYV, 720p costs a multiple of USB bandwidth, and precisely
decides whether two cameras are running on a controller.

**`Camera`fails loud** if the device cannot be opened instead
quietly`FakeDetector`fall back. Results on the machine
would not be seen as errors at the booth; a start-up is it.

**Passthrough only in`GameScene`**, both pictures 880 × 495 next to each other.
In the Idle, the USB bandwidth remains free and the Pi cold — the same rule as with
the servos. Measured 1.5 ms per frame for the whole scene including both
Panes; `CameraView`converts only if the camera really is a new picture
geliefert hat (Sequenzzaehler in `Camera`), otherwise each camera image would be accompanied by
30 fps source and 60 fps renders twice converted.

**`CAM_INDEXES`is a pair**,`(Arm, Top-Down)`. Stehen zweimal dieselbe 0
darin, oeffnet `main.py`the Geraet still only once (`set()`) and feed
both panes from a tomb — this is the layout mouse with a webcam.
Real hardware is`(0, 1)`a number. The Detector is always at
second, the top down camera.`pygame.image.frombuffer(..., "BGR")`saves`cvtColor`,
pygame-ce nimmt OpenCVs Kanalreihenfolge direkt an.

### Befund: Race in `tray_sum()` (behoben)

`seen`was described by the detector thread and by the render loop without lock
read. An update to an existing key is harmless, a **new* *
Key during iteration not: `RuntimeError: dictionary changed size
during iteration. Reproducible, not theoretical. The moment in which it
is exactly the one in which a marker appears for the first time — so
in the middle of the round. Per round unlikely, over 240 visitors not.
`fresh()`now hold`threading.Lock`.

### Overlay on the top down camera

**Only the top down pin gets a detector.** The arm camera remains purer
Passthrough — she sees the tray from another angle, where the
Do not corner, and a second detector cost computing time for decoration.
`CameraView(cam, det=None)`carries the assignment: the pane knows if there is something
einzublenden hat.

** Only number**, in`MARK_FONT`/`YELLOW`centered on the
Focus of the four marker corners. No square and no base: the marker
marks itself, a frame therefore says nothing that the image does not already
shows, and covers the puck. Difference on 27 August, after both
on the screen.

The price is named and accepted: Yellow on a bright puck has
no more guaranteed contrast. If this doesn't stand in the hall, one is
black shadow behind the number (same number 2 px offset in`BLACK`)
the next smaller stage — not the backing.

Measured 1.5 ms per frame for the whole scene including both camera images.
Pre-dated number interfaces were planned and are superfluous as measured: eight
`font.render`cost 0.01 ms. A cache for nothing.

**Created markers remain **, exactly as long as in total — Overlay
and`TOTAL` read the same `MARKER HOLD` peace from the same snapshot,
the`update()`once per frame draws. You can't resist. Excluding
'TOTAL 165', while only four out of five frames are visible, and
that looked like a mistake because it was one.

### Detektionsfenster (`TRAY_ROI`)

The top down camera is wide angle and sees half the booth.
`TRAY_ROI`limits the recognition to a rectangle in image portions.

**Replaced as blank, not as filter.** The Detector cuts the
Cutout from the frame (a numpy sight, no copy) and only recognizes in it.
This is done both in one step and is cheaper: measured **1,21 ms instead
2.00 ms** per pass at 60 % × 70 %. A marker at the edge of the picture disappears
by itself, instead of being recognized and then rejected.

The corners are then returned to shares in the *ganzen* image,
so that the scene only has to multiply with the Pane rectangle.

**The rectangle is in`GREY`in image** — Chrome, no play value, therefore not
Yellow. It is visible because you`TRAY_ROI`when aligning the camera in
Set up hall and otherwise have to adjust blindly. Same rule as
`SCANLINE_ALPHA`.

**Fremde marker IDs are discarded.** What not in`VALUES`it is
not to play — a printed test sheet on the table can therefore not
Punkte erzeugen.

### Tone for new detection

`"blip"` in `SFX`: a single high note,`duty=0.125`, `vol=1200` gegen 2600
for`"ok"`200 ms. No recycling of the button — otherwise a puck sounds like a
Button pressure and the signifier mechanism loses its clarity.

Resolved is detected at **new**, not visible, otherwise it fires
`DETECT_HZ`- times a second. The comparison is`GameScene.update`, a
Quantity difference against the last frame. In this way, two kinds of
out: five pucks at the same time give **a tone, and a short concealed
Marker doesn't piept again because the hysteresis doesn't even leave him.

The logic is in the scene, not in the thread —`hw.py` importiert weiterhin
No`music`, and "Thread writes, Loop reads" remains unharmed.

**`INTER_LINEAR` instead of `INTER_AREA`:** measured 0,17 ms instead of 3,5 ms pro Frame.
AREA mediates over all source pixels and is at factor 3
20 times more expensive. Behind Scanlines sees that no one — 3.5 ms would be on the Pi
a fifth of the frame budget for an inset, according to the layout principle
is.

---

## UI-Layout

### Resolution and full image

**Design resolution = panel resolution: 1920 × 1200 (16:10), Asus 15". **
Adopted on 27 August 2026. Each coordinate in `scenes.py`is to absolute
number for this grid; on the target monitor is the image thus 1:1, it becomes
nothing scaled and nothing softly drawn. What you write is there.

The previously acquired variant — stay at 1280 × 720 and scale up — is
rejected. She would have produced 60 px black bars on 16:10 above and below
and each pixel stretched by a factor of 1.5, so *not* integer:
Pixel fonts without antialiasing will become unevenly thick letter marks.
Drawing native costs once 22 changed numbers and is then forever
erledigt.

**`pygame.SCALED`** — as insurance, not as
Werkzeug:

```python
flags = pygame.SCALED | (pygame.FULLSCREEN if FULLSCREEN else 0)
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
pygame.mouse.set_visible(False)
```

On the Asus, the flag is a enrichment and does nothing. Hangs on the fair day
other panel — and the monitor is under 'Open Points' —, scales SDL
in hardware, instead of sticking the layout in the corner. A
Flag as a fallback level is cheaper than the assumption that nothing will change.

`vsync=1` prevents tearing during the timer gradient, the only place
where a large area changes per frame. `set_visible(False)` hides the
mouse cursor, which would otherwise remain in the middle of the screen.

**`FULLSCREEN` is a switch in `config.py`**, not a fixed value:
off for development (windowed mode, `q` to quit), on for the cabinet.
One flag, two operating modes, no second codebase.

**Consequence for later:** The layout is bound to 16:10. Change
a 16:9 panel would not be a crash,`SCALED`catches him — but there would be
then lateral bars. The monitor will be considered a set hardware from here.

### font sizes

`big` 168, `mid` 88, `small` 48, `tiny`32 — all by 8; reasoning
in your own section below.

### Koordinaten

All coordinates for **1920 × 1200**, center x = 960. Drawing is manual work in numbers — this is the deliberately paid price for pygame instead of CSS. Three rules apply to ensure that it does not in Magic Numbers:

- **A helper, no layout system. **`draw(screen, font, text, x, y, color)`drawing a text centered on`(x, y)`. Centers, not to the left, because numbers change their width (`9` → `10`) and a left-handed value then jumps visible.
- **`font.render(text, False, color)`** — the second parameter is antialiasing, and it must`False`be. A pixel font with edge smoothing looks out of 8 m matte instead of sharp.
- **Colour carries meaning, not decoration.** Six colors, a ladder from quiet to loud, each with exactly one job. As long as this is true, 'what colour I take here' is no longer a decision, but a reference.

| Farbe | Hex | Job |
|---|---|---|
| `BLACK` | `#000000` | Reason, always |
| `GREY` | `#787878` | Beschriftungen (`GOAL`, `TOTAL`) |
| `WHITE` | `#F0F0` | neutral values |
| `YELLOW` | `#FFC800` |what the visitor influences *even*|
| `ORANGE` | `#DE6207` | Warnung — HPI-Orange |
| `RED` | `#B1073A` |the last seconds — HPI-Rot|

Red and orange are drawn from the HPI-Logo-SVG, not estimated.`YELLOW`is brighter than the HPI yellow`#F7A900`because on black 8 m the brighter wins and you don't see the difference next to the logo.`GREEN`and`DARKRED`are dispensed with: green is not HPI, and a green reason contradicts "black reason".`ORANGE`has no place in the code — the demolition warning in`GameScene`is the obvious.

### font sizes

`main.py`builds a dict and puts it in`Ctx.fonts`. Four sizes are enough, more are only decisions without benefit.

|Key|Size|For|
|---|---|---|
| `big` | 168 |The numbers that must be readable from 8 m|
| `mid` | 88 |Rest period, headings|
| `small` | 48 |Inscriptions, best list|
| `tiny` | 32 | Steuerungshinweise, Preistabelle |

**The font is Press Start 2P** (SIL OFL, is in`game/assets/`) — the literal arcade fund, the NAMCO automat of the 80s. Selected 27 August 2026 against VT323, Silkscreen and Silkscreen Bold. Criterion was width per digit height because width in these sizes is the lowest resource on the screen:

| Font |Size for 200 px numbers| `"180"` | `"PICK'N'PLAY"` |
|---|---|---|---|
| **Press Start 2P** | 228 | 628 px | 2480 px |
| VT323 | 357 | 378 px | 1547 px |
| Silkscreen | 320 | 600 px | 2240 px |
| Silkscreen Bold | 320 | 720 px | 2680 px |

VT323 is by far the narrowest and would have been the closest choice — but its lines are a design pixel thin, and thin loses from 8 m in bright hall. Press Start 2P has the thickest lines and will only be wide on the title, and the title is the one string that no one has to read under time pressure.

**Why these four numbers.** Press Start 2P has a **8 × 8-Raster**: font size ÷ 8 is the edge length of a glyph pixel. Only multiples of 8 are pixel-precise, everything else makes the pixels *in* of a glyph unequal.`big 168`hits the number height of the old placeholder almost exactly (147 px instead of 154) and leaves`PICK'N'PLAY`1848 px wide — 36 px edge, for a marquee exactly right.

All 17 strings from `scenes.py`are tested against their available width, no running over: **no coordinate changes. **`main.py`expands the Dict now in one line`FONT SIZES`.

The arrows`▶ ◀ ▲ ▼`exist in the font (viewed, not suspected), as well as relaunching and`€`. **Since August 27th, they are everywhere in use**, the ASCII aids`<`, `>`, `^v`are out. The glyphs are filled triangles on the same 8 × 8 rays as anything else — a self-drawn`pygame.draw.polygon`was in the code and flew out again: it breaks the pixel grid, does not scale with the font size and is code for something that the font already can.

**`pygame.font.Font(path, size)`with included TTF is more robust on the Pi than`SysFont`** — no fontconfig, no question which fonts are on the Raspberry OS image. The repository becomes 118 kB heavier and is reproducible for this. The path turns out` file  built, not relative to the work directory, otherwise the systemd start breaks.

### Footer band (28 August)

Two constants in `config.py` and a seven-line helper in `scenes.py`:

```python
FOOTER Y = 1120 # the one line that says what the buttons do
SAFE BOTTOM = 1040 # no scene content below. Never.
```

* *The occasion was a real clipp error.** The fifth best list line was
on y 1096...1144, the question`PRESS ◀ AGAIN TO DISCARD`on 1114...1146 —
528 × 30 px cover. It was only visible when the DB received five entries
had, that's why "slip sometimes." Cause was not the number 1130, but
that an *data-dependent long* list and an overlay are the same space
without agreement.

**The query replaces the message line instead of standing next to it. ** The
can no longer collide — not because the numbers now fit, but
because there is no second element. And it is the better feedback: the
Answer to a push of a button appears where anyway what the button
do. Prior to that, Cursor ` ``(510, 470) and his answer 660 px apart.

```python
footer(screen, f, left=None, right=None, note=None)
```

`note`yellow and centered, otherwise`left`for x = 600 and`right`where x = 1320,
both `tiny` / `GREY`. **Pfeil always first** (`Г BACK`, `▶ NEXT`— the
Direction carries the position in the footer, not the word position. Before
spiegelte `◀ BACK  START ▶`and`▲▼ LETTER ◀▶ FIELD`did not reflect.

|Scene| left | right | `note` |
|---|---|---|---|
| `HowToScene` | `◀ BACK` | `▶ START` | — |
| `GameScene` | `◀ QUIT` | — | `◀ AGAIN TO QUIT` |
| `DisplayScoreScene` | `◀ BACK` | `▶ NEXT` | — |
| `LeaderboardScene` | `▲▼ LETTER`,`cursor == 0`: `◀ DISCARD` | `▶ SAVE`for`cursor == 3`, sonst `▶ NEXT` | `◀ AGAIN TO DISCARD` |

`IdleScene`has no footer — the flashing`PRESS ▶` in `mid`is there
Signifier, and a second gray indication of it would only weaken him.

**`◀ QUIT`in the round is permanently there**, not only after the first
Pressure. A hidden operating element is not one; the misunderstood
Double confirmation, not invisibility.

### Layout-Selbsttest (`uv run game/scenes.py` → `ok`)

The same convention as `db.py`, `music.py`, `balance.py`. The test starts
jeden `draw()`-Review of the *`render()`- Methods and check the
Rectangles: picture boundaries, `SAFE BOTTOM`and in pairs cover — included
of the two camerapanes that do not`draw()`are. All are played
Scenes, `GameScene`in three states and`LeaderboardScene`in eight
(four cursor positions × query to/from).

No screenshot comparison: a reference image should be given for each color change
and still does not say, *what* two elements are
cover. Conversely, the test can fail — with the old
Coordinates he reports the collision that actually existed.

### IdleScene

**Stumm**`MUSIC = None` plus `ctx.music.stop()`in the constructor. Six hours
Chiptune on the piece are exhausting — and they do not mark anything. Only with silent
Idle becomes the musical instrument in`HowToScene`to the signal "going".`stop()`
also clears the pushed-on idle music, which`DisplayScoreScene` per
`MUSIC_IN` eingeplant hat.

`▶`now leads to`HowToScene`, no longer directly into the game, and gives
dabei `"ok"`back instead`"start"`— the start fanfare belongs to the
actual round start.

| Element | Position | Font / Farbe |
|---|---|---|
| `PICK'N'PLAY` | 960, 260 | `big` / `YELLOW` |
| `PRESS ▶` — blinkt 1 Hz | 960, 560 | `mid` / `WHITE` |
| `BEST — LOWEST WINS` | 960, 690 | `tiny` / `GREY` |
Top 5 from `db.top(5)` | 960, 750 + i·66 | `small` / `WHITE` |

**`LOWEST WINS`is mandatory, not decoration.** Every best list that a child
the largest number is sorted upwards. Here the smallest wins, and
without this line you read the list wrongly. The same line is in
the`LeaderboardScene`.

The flashing does not need a timer:`self.t += dt` in `update`and`render`Verification`int(self.t * 2) % 2`. A time source, again the same rule as the roundtimer.

### GameScene

The three figures from the readability principle. Target value and tray sum are next to each other so that the eye compares them directly — that is exactly what the purchase of the game is.

Since 27 August, **beide camera images are large next to each other** below
a three-column header. Column Issuers 490 / 960 / 1430 apply for
Number * and* image so that both are above each other.

| Element | Position | Font / Farbe |
|---|---|---|
| `GOAL` | 490, 70 | `small` / `GREY` |
|Objective| 490, 145 | `mid` / `WHITE` |
| `TIME` | 960, 70 | `small` / `GREY` |
| Restzeit, ganze Sekunden | 960, 145 | `mid` / `WHITE` |
| `TOTAL` | 1430, 70 | `small` / `GREY` |
| Tablet sum | 1430, 145 | `mid` / `YELLOW` |
| `OFF BY`in case of hit`PERFECT` | 960, 265 | `small` / `GREY` |
|Difference, when hit the countdown| 960, 380 | `big` / `YELLOW` |
|Arm camera (passthrough)| 880 × 495 um 490, 740 | Rahmen `GREY` |
|Top Down Camera| 880 × 495 um 1430, 740 | Rahmen `GREY` |
| Detektionsfenster | `TRAY_ROI` im rechten Pane | `GREY`, `MARK_WIDTH` |
| Marker values |Focus of marker corners| `MARK FONT` / `YELLOW` |
| `◀ QUIT` / demolition warning | Footer | see Footer band |

**`OFF BY`in the round (August 28). ** Previously`GOAL`and`TOTAL`
940 px apart and the visitor had to make the difference in the head —
under time pressure, from 8 m, in a loud hall. The purchase of the game
is to push pucks, not head Calculation.`GOAL`and`TOTAL`they are
`big`on`mid`downgraded; the difference gets`big`.

It is **named as on the score screen** — once learned, twice
used. The score screen is not a new term.

**`PERFECT n`inherits exactly this place.** If the sum is on the target, the
the large yellow field to countdown. There is no longer a second place,
dispute the countdown and demolition warning by the same line — before
both lay at 960, 1120 and`elif`closed it.

Both `YELLOW`: `TOTAL`and the difference is the same — what the visitor
influenced, once as a value and once as a rest.`GOAL`and`TIME`they are
Giving. The size separates it (168 vs 88), not the color.

The camera panels move from 690 to 740, so under the difference air
remains. In the self test, not estimated.

`CAM_VIEW` is 16:9 like `CAM_SIZE`. Another aspect ratio distorts the image because
`CameraView` scales to the target size instead of cropping. A
letterbox branch would be code for a problem that two numbers in `config.py`
already prevent.

**Entwickler-Abkuerzung (`CHEAT_TAPS`, 27. August).** Fuenfmal `>` hintereinander
setzt `self.left = 0.0`— the round ends with its normal way into
`update()`, including finish sound and music level. A`switch to()` directly from
`handle()` would be a second round close next to the real one; exactly that one wants
do not take off during testing. Each other action sets the Zaehler back, and
`CHEAT_TAPS = 0` in `config.py`shuts the whole thing off at the machine.

Side effect from `KEY REPEAT`: the button is press *hold* fires the five
Repeat in ~0,6 s. There is no repeat logic on GPIO, there are
five real drawers — no matter because the cheat is out there anyway.

**Premature end at`OFF BY 0`.** Is the sum`PERFECT_HOLD` Sekunden
long exactly on the target, the round ends — along the same path as the run
the clock, including ready-made sound and scene change. The hysteresis in
`fresh()`catch the flicker, the five seconds catch the intention. The
Countdown on the screen is mandatory: a break without warning looks at
Machines after crash. Stay less than `PERFECT HOLD`seconds, running
the counter is not full and the round ends normal — 'short before the end'
no special case because there is only one time source.

* *The target value comes from`balance.gap()`**, against the tray as it is
at the beginning of the round actually lies.`__init__`read for this`fresh()` —
Side effect: the blip tone no longer fires for the five pucks that start
schon dalagen.

**Restzeit anzeigen:** `int(self.left) + 1`. Without`+ 1`shows the machine in the first second`59`and in the last`0`while the round is still running.

**Background as a timer.** No additional element, the area itself is the display:

```
k = 0.0 as long as left > WARN SECONDS, otherwise linear to 1.0 at left ==0
bg = BLACK + (RED - BLACK) * k         komponentenweise
```

From black to HPI red instead of green to dark red. The start is thus the same black ground as anywhere else, and the last five seconds color the whole screen — that is the signal coming from 8 m. White Paper on`#B1073A`remains legible; the gray labels lose contrast in these five seconds, which is acceptable because`GOAL`and`TOTAL`that are already known.

### HowToScene

New on 27 August. Explanation, demo clip, and **here begins the music* *
(`MUSIC_IN = (0.0, 800)`— 0.8 s incarnation, instead of banging out of silence).

| Element | Position | Font / Farbe |
|---|---|---|
| `HOW TO PLAY` | 960, 110 | `mid` / `YELLOW` |
| Demo clip only when `DEMO_VIDEO` is set | `DEMO_SIZE` around 960, 500 | Frame `GREY` |
| Three lines from `HOWTO` | 960, 900 + i·60 (without clip: 500 + i·60) | `tiny` / `WHITE` |
| `◀ BACK` / `▶ START` | Footer | see Footer band |

**Without clip, the text moves into the middle. **`DEMO_VIDEO = None`the
Extradition state, not the exception — there is only the film when
a structure for filming, and until then the feature must not be blocked
be still looking half-finished.

**`VideoView`is`CameraView`with a watch.** pygame can't be a video, but
`cv2.VideoCapture`takes a file just like a device — the player is
the same class as the passthrough, the same`frombuffer(..., "BGR")`-Zeile,
no new dependence. The only real difference: a camera *pressed *
Images (Grabber thread, sequence counter), a file is *drawn* (`dt`). Wer
that mistakes, builds a thread too much or too little.

**The clip is mute.** No soundtrack, no synchronization, no second
Audio path — the music carries the scene. An explanation about chiptune in one
loud hall would be exactly the stimulus flooding that the silent idle takes away.

**Price: around 5–8 s per visitor**, with 240 visitors about 25 minutes
Waiting for the trade fair day. In contrast, there is no minimum duration
gives: who knows the explanation, type once`▶` durch.

### DisplayScoreScene

| Element | Position | Font / Farbe |
|---|---|---|
| `OFF BY` | 960, 150 | `small` / `GREY` |
| `self.score` | 960, 380 | `big` / `YELLOW` |
| `GOAL` | 660, 600 | `small` / `GREY` |
|Objective| 660, 690 | `mid` / `WHITE` |
| `TOTAL` | 1260, 600 | `small` / `GREY` |
| Tablet sum | 1260, 690 | `mid` / `WHITE` |
| `PRICES` | 960, 860 | `tiny` / `GREY` |
| Price line, 10 values | x = 204 + i·168, y = 940 | `small` / `YELLOW`if on the tablet, otherwise`WHITE` |
| `◀ BACK` / `▶ NEXT` | Footer | see Footer band |

**The price table is a price* line* (28 August).** Previously stood here
`0 = 4`, `1 = 7`in five columns. The left column was the ArUco ID, and
that is on no puck as a number, the visitor has only one
Black-white pattern seen. Half the table content required
Assignment whose key no one owns. That's what she did
confusing: she looked after information and was noise.

Now: only the values, ** ascendant**, and **
Rounding actually lay on the tray**. This is not a
more, but a picture of the round — the price catalogue and
what they had. The color follows the existing conductor, no new
Vocabulary.

The Reveal remains the learning moment from the game mechanics, and it continues
on`sorted(VALUES.values())`, not over a second list — otherwise drift
Display and review as soon as someone changes a value. All ten
values remain, not only one's own: the full catalog is exactly that
Knowledge that makes the second round better than the first.

* *The constructor takes`marks` instead of `total`.** The sum is in it, and
the price line needs anyway, *what* values were. A marker per puck and
pucks can share values, so `{VALUES[i] for i in marks}` is lossless.

`GOAL`and`TOTAL`stand as two columns with label on it — the same
Arrangement as in the header of the round, which the visitor just 60 s long
read. Before it was a squeezed line`GOAL 180    TOTAL 165`.

### LeaderboardScene

Cursor model, as described under "scenes and transitions". The marker is a rectangle or undercut under the field with`self.cursor`.

| Element | Position | Font / Farbe |
|---|---|---|
| `ENTER YOUR NAME` | 960, 130 | `mid` / `YELLOW` |
| `◀`(back field,`cursor == 0`) | 510, 470 | `big` / `WHITE` |
| Letter 1..3 | 840 / 1050 / 1260, 470 | `big` / `WHITE`, active field `YELLOW` |
| Cursor beams | `COLS[cursor] − 68`, 580, 135 × 9 | `YELLOW` |
| `BEST — LOWEST WINS` | 960, 660 | `tiny` / `GREY` |
Top 5 from `db.top(5)` | 960, 720 + i·64 | `small` / `WHITE` |
|Button notes / query| Footer | see Footer band |

**`TOP 10!`was a lie (August 28). **`db.qualifies()`nowhere
in which everyone lands — including`OFF BY`200. The heading
promised something that the code did not check, and showed five lines instead of ten.
The screen is an input, so it means like one:`ENTER YOUR NAME`. The
`qualifies()`-Gate remains unaffected and further open (balancing question,
see Open Points) — the honest heading does not take the decision
vorweg.

**The list returns from 860/65 to 720/64.** Previously, the fifth line was on
1096...1144 and collided with the query; now it ends at 1004, under
`SAFE_BOTTOM`.

**`▶ SAVE`in the last field.** That right out of the third letter
stored, stood nowhere before — you had to find it. The footer says,
what `▶`* does.

**Rueckfrage beim Verwerfen (27. August).** `◀` im Feld `cursor == 0` verwirft
the just played score. This happens accidentally when you get too often
to the left, which is why the same double determination as in the round break:
erster Druck setzt `self.confirm = CONFIRM_SECONDS`, zweiter innerhalb des
Window goes to the Idle. No dialog, no second screen — a float in
`update()`wears both of them and leaves them alone.

The field colour comes from`self.cursor`not from a second flag. If`render`a separate "which field is active" attribute would require the state at two places and could run apart.

### CRT-Overlay

The machine should look like a tube, not LCD. Three levels, all in
`run_game`between`scene.render(...)`and`pygame.display.flip()`:
**Wooden**, **Scanlines**, **Vignette**. Revised on 27 August 2026.

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

* *The loop carries the effect, not the scene.** He's above all, so
He belongs to the one place where everything goes together. No scene knows
he, no scene can forget him, and shutting off is a flag in
`config.py`instead of four changes`scenes.py`.

**Make once, not count per frame. ** Scanlines, Vignette and the
The arching table is created at the start. Per Frame stay`remap`and
Blit — both C, both constant. The same rule as with`db.top()` im
`render`: what does not change is not recalculated.

**The vignette is a 16 × 10 alpha lattice, highly scaled.** A soft
Radial course costs nothing if you calculate it tiny and the bilinear
Filter von `smoothscale`making work — 160 pixels instead of 2,3
Millions. She's getting started`BLEND_RGBA_ADD`: both levels are pure
Black, only the alpha adds up, and that doesn't depend on any pygame version.

**Barrel Distortion: yes, and it costs little.** The previous entry here
said "Uses a shaker, so too expensive." That was wrong,`cv2.remap`is
long ago a dependency because ArUco brings OpenCV. For each target pixel
once the source coordinate is calculated and stored as a fixed-point table
(`cv2.convertMaps`, `CV_16SC2`); per frame it is a single C call.

```python
f = 1 + k * (nx² + ny²)      # aussen weiter aussen greifen = Woelbung
```

`BARREL_K = 0.05`is visible without being silly.`0`only the
Wolving off and retains scanlines and vignette — this is the emergency exit if
the Pi is not coming.

**`INTER_NEAREST`Not`INTER_LINEAR`.** Not only faster: bilineare
Filtering blurs the pixelfont, and "no antialiasing" is the rule
Level up. The price is slightly frayed glyph edges on the edge,
what doesn't look wrong on a tube.

**The overlay comes after the curvature, not before.** Carved scanlines
would be more authentic but give 1-px lines through a Nearest-Resampling
Moiré. Scanlines on arched image cost nothing and stay clean.
The vignette covers the black corners that create the curvature.

**Two traps in memory layout**, both bought expensive and therefore listed here:

1. The nearby path`pygame.surfarray.pixels3d`cost **8,3 ms**, the
selected **1.4 ms** reason:`pixels3d` returns RGB, pygame stores BGRA —
the view on the color axis has step width **-1**, and over a backward
running array cannot scan OpenCV, copy it first.`get_view("2")`
gives the 32-bit pixels as they lie,`.T`turns the pygame axis sequence
   `(w, h)`on the picture convention`(h, w)`and makes them related.
The color sequence doesn't matter because`remap`Pixel only shifts.
Two. A held numpy sight ** locks her surface, and the Blit underneath
then fails with "Surfaces must not be locked during blit". That is why
Pass `px(...)` directly in the call: the views die with the line and release the lock.

**Measured** (Mac, headless, 1920 × 1200, real scenes):

| | ms/Frame |
|---|---|
|only scene +`flip` | 2,5 |
|**+ curvature + scanlines + vignette* *| **5,8** |
|Budget at 60 FPS| 16,7 |

The CRT share is about **3,3 ms**. On the Pi is that of the post which
first tilted — there is to measure, not to estimate.

#### Measurement on the Pi, 9 September 2026

Measured by the machine: Pi 5 (8 GB), Ubuntu 24.04, KMSDRM full screen, both cameras
active, Teleop stopped. The Idle screen was over`PNP_IDLE_FPS=60`on
Scene Load Driven Because SSH does not hit a button at KMSDRM and
Game scene is not accessible otherwise.

| Ziel 60 fps | CPU | erreicht |
|---|---|---|
| alles an | 268 % | **19,6** |
|without curvature (`BARREL_K = 0`) | 195 % | **26,5** |
| without CRT | 189 % | **36,6** |
| without CRT, without cameras | 92 % | **40,0** |

**60 fps are not accessible on this Pi. ** Also not drained. The last
Line is the actual finding: 40 fps at 92% CPU means that nothing more
to parallelize, the path depends on a thread.

Three hypotheses were tested, two of which were refuted:

**Textrendering wasn't. **`font.render()`run for each string
every image new, Press Start 2P in up to 168 px. A`lru_cache` darauf brachte
in a variant 10%, otherwise nothing. The cache stays in, it doesn't cost anything
and doesn't hurt, but he wasn't the cause.

**`vsync=1`costs 12 to 19 %**, but buys it with tearing and brings
the 60 still not. Stay inside.

**Native 1080 instead of downscaled 1200 brings most**, in the variant
without curvature 26,5 → 34,2 fps. This is the reason why the resolution question above
'Open points'.

In addition, a heat finding, regardless of the image rate: with game ** and** Teleop
at the same time the Pi runs under one minute to 83°C and drosselts
(`throttled=0xe0008`), the image rate continues. Without active cooling
the continuous operation on the day of the fair.

The decision to draw the three adjusting screws — remove curvature,
move to 1080, reduce target image rate to 30 — is still pending. She is a
Design decision, no configuration question.

* *The target conflict is named:** Scanlines take away brightness, and
Readability from 8 m in a bright hall is the top principle of this
Projekts. `SCANLINE_ALPHA`is therefore`config.py`and becomes ** in the hall* *
set, not at the desk. In doubt, readability is gaining.

**No chromatic aberration.** The three remaps needed instead of one, and out
3–8 m is not readable as an effect, but only as a blur.

### Sound: Low-Bit-Arcade-Musik, deklarativ notiert

Music is written ** as data, not as code**: a string per
The`music.py`changes to a sound at runtime. No audio files in
Repository, no dependency, no license theme — and changing a melody is
Change a line.

```python
# game/music.py
ATTRACT = "c4 e4 g4 c5 - g4 e4 c4 -" # Notenname + Oktave, "-" is Pause
```

How this works in four steps:

1. **Notename → Frequency** is a line:`440 * 2 ** ((halbton - 69) / 12)`.
This is the MIDI formula, 69 is the Kammerton-A.
Two. **Frequency → Samples** is a rectangle vibration: alternating`+A`and
   `-A`switch over. Exactly this curve shape *is* the chiptune sound — they
because an NES or a C64 could nothing but a level
turn on and off. "Low bit" is not a reproduction, but the
   direkte Weg.
3. **Samples → `Sound`**`pygame.mixer.Sound(buffer=...)`with
   stdlib-Modul `array`. **No numpy**`pygame.sndarray`the
   `buffer`- Don't move, and numpy isn't in dependencies.
4. **The whole piece will be rendered once at the start** and with`play(loops=-1)`
looped. No scheduler, no timer thread, no note for note output.
A loop running in the audio driver does not drift — the same
Consideration as "a time source per round", only for audio.

`pygame.mixer.pre_init(...)` must run **before** `pygame.init()`, otherwise
the buffer size is already fixed and you hear latency.

It is connected like the Detector:`Ctx` gets a `music` field, scenes
rufen `self.ctx.music.play("attract")`and never know what's behind it.
Thus there is a mute dummy for tests without audio device, and the
Headphone test on the laptop is the same code base as the fair.

**Sound stays supplement.** The hall is loud; nothing in the game
depend on someone to hear something. The piece runs in Attract Mode, a short
Beep confirms buttons, a jingle the score. That's all.

#### Umset am 27. August

Six tokens in the notation, a token is a sixteenth:`f4` Note, `.`
hold,`-` Pause, `f4/a4/c5` Akkord, `a#2^f2` Glide, `k s h` Kick/Snare/Hat.
Two data tables at the head of the file,`PIECES`and`SFX`— of which only
Anbindung.

**The loop runs per vibration, not per sample.** This is
Decision from which everything else follows. A rectangle period is 30 to 500
samples long; who recalculates volume and frequency once per period,
makes one hundred times less work than per sample — and does not hear any difference
because nothing can change within a period anyway. In this
loop is therefore **fill curve, Vibrato, Glide, Arpeggio and the
Kickdrum**, each as two lines. All pieces and effects render in 0.12 s.

**Without envelope, each note sounds like a test tone. **`ENV`keeps five curves
(`pluck`, `hit`, `punch`, `swell`, `flat`), argument has been seconds
Start of notes. That was the real reason why the first version
'computer-generated' sound — not the melody.

**Stimmation: the period is not rounded, only its end.** A rounded
Period draws high notes, F5 at 44100 Hz lands 12 cents too deep, F6
even 23 — and because each note is rounded differently, the *intervalle* does not vote.
That's what you hear as "slate." With broken position, the middle
Frequency exactly, the rest is half a sample jitter. The self test counts
over the entire range of sound, the zero crossings of a second tone and requires
±1 Hz.

**Mixing makes the mixer.** One piece has up to four tracks, each one lies on
a separate channel (`set_reserved(4)`of twelve, eight remain the effects).
All tracks of a piece are the same length, so they are looped forever
synchronous. There is no addition loop in Python.

**Intensity is not automation, but four pieces. **`round0`–`round3`,
the same reef in F major at 118 / 132 / 148 / 158 BPM, the percussion is made by
Half-backbeat to sixteenth-hats denser. Dur, not Moll: the tension
comes from speed and drums, not from sadness. Level 3, the last
five seconds, puts a ticking clock on each quarter — the melody runs
on. An earlier version replaced it with an alarm
Sixteenth century bass drum; that was hardcore techno and for the audience at
Fair stand clearly too much. **Panik emerges from the tick, not from more
Bassdrum.**
`GameScene.update` calls `music.stage(self.left)`per frame, changed only
for step change. Measured: 60 → 40 → 20 → 5 residual seconds; Stage 3
`WARN_SECONDS`one, that is, in the same frame in which the screen turns red.

**Nach dem Fertigsound kommt Stille.** `SceneBase.MUSIC_IN`is a couple
`(Pause in Sekunden, Einblendung in Millisekunden)`, `DisplayScoreScene` setzt
`(2.2, 1500)`: the round music stops immediately, the fanfare sounds free,
There's nothing happening for two seconds, then Idle music fades in. The silence is
the effect. How to hide`Channel.play(..., fade_ms=...)`, wait
`Music.update()` — aufgerufen in `run_game`, wo ohnehin jeden Frame etwas
happens. No timer thread, no second time source.

**Szenenwechsel is music change, clear. **`SceneBase.MUSIC`is a
Klassenattribut, `SceneBase.__init__`plays it off. Every scene says once,
what is going on with her;`GameScene` setzt `MUSIC = None`because their level at
Rest time hangs. No future scene can be forgotten, the round music
— Idle, score and leaderboard inherit`"idle"`and switch from
back alone.

* *The mistone costs one line. **`handle()`returns the name of the sound,
`None`is not taken. In`run_game`is therefore:

```python
scene.ctx.music.sfx(scene.handle(action) or "nope")
```

That sounds *every* button press without having to think of a scene — in
game`>`press brummt, leaderboard`^`on`<`-Field bruised. The
Line is the whole signifier mechanism.

`Music.REPEAT_MS = 90`swallows the same effect shortly after one another. Excluding
that fires`KEY_REPEAT` beim Buchstabenscrollen 16 Blips pro Sekunde.

**Without audio device`Music`mute instead of broken. **`pygame.mixer.get_init()`
Must be exact `(44100, -16, 1)`supply, otherwise the constructor renders nothing and
each method returns immediately. No second class.`pre_init`
is the first line`main()` — nach `pygame.init()`is the buffer size
fest.

`uv run game/music.py`checks cycle lengths, mood and track lengths and writes
WAV files by `/tmp/picknplay-audio`, including `session.wav`: Idle,
Startfanfare, 60 seconds increase, ready-to-use sound. Listen to me
to start the game.

#### Where the sounds come from

`Dream_Sound.mp3`(101 s) was analyzed by FFT, not written off:
Tempo ≅ 85 BPM, key F major, bass migrates F2 – Bb2 – C3 – A2/D2, the melody
sits between F4 and A5. That's exactly what Idle has become — 84 BPM,
F – Dm – Bb – C, wide half in bass, thin pulse (duty 0.125) for the
Arpeggien. The round takes the same tones in d minor: related enough that the
Don't change like a different game sounds.

So the *description* of the piece was overtaken, no note. No sample,
no file in the repository, no license theme.

---

## Interfaces of empty files

No`abc`, no`Protocol`No basic class. A detector is everything`tray_sum()`has — more contract it does not need, and the exchange Attrappe └ Hardware remains one line in`main.py`.

### `db.py`

```python
class DB:
    def __init__(self, path=DB_PATH)      # CREATE TABLE IF NOT EXISTS
    def top(self, n=TOP_N)  -> list[tuple[str, int]]
    def qualifies(self, score) -> bool
    def add(self, initials, score) -> None
```

**`ORDER BY score ASC`.** The score is the *distance* to the target value,`0`is perfect. On`DESC`the best list is set out in noisy wrong and nobody notices it at the booth. A`rowid ASC`as Tiebreak keeps the order stable with balance.

`qualifies(score)`is`len(top) < TOP_N or score < top[-1][1]`.

This file gets a`if __name__ == "__main__":`-Block with`assert`s — Insert, sorting direction, displacement at full top 10. The only place in the project with non-triviar comparison logic, and the only one whose errors are not seen on the trade fair day.

### `hw.py`

```python
class FakeDetector: # first build without camera
    def tray_sum(self) -> int

class Camera:                             # Grabber-Thread
    def __init__(self, index=CAM_INDEX, size=CAM_SIZE)
def read(self) -> frame | None # always the NEW picture
    def close(self)     -> None

class ArucoDetector:
    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI)
    def fresh(self) -> dict[int, quad]    # gleiche Signatur wie FakeDetector

class CameraView:                         # ein Pane
    def __init__(self, cam, det=None, size=CAM_VIEW)
    def surface(self) -> pygame.Surface | None
```

* *The contract has been since 27. August`fresh()`, no more`tray_sum()`.**
A detector is everything`fresh()`has: a dict of marker ID on a
Square, both of them need the scene anyway. is summed in the scene, because
`VALUES`is game rule, no sensor knowledge — a detector who knows points,
would be a sensor with opinion.`tray_sum()`has been replaced, it had
a caller.

`uv run game/hw.py`checks without camera against a synthetically drawn
Tablet:`DICT_4X4_50` zu `markers/`fits that the squares lie there,
where the markers were drawn (±3 px), that`TRAY_ROI` aussortiert, was
that the hysteresis only stops and then degrades, and that
`FakeDetector` dieselbe Schnittstelle hat.

**`FakeDetector`first.** The attractor should change its sum by itself (approximately all 3 s new cubes), otherwise the tablet number is still throughout the round and you do not see whether the ad is updated at all.

**`Camera`as a thread, not as a process. **`cap.read()`is C++ code and releases the GIL. The thread writes the image under lock into an attribute that reads loop — never vice versa.`CAP_PROP_BUFFERSIZE = 1`, otherwise the V4L2 buffer delivers old frames and the detection is visibly behind.

**Hysteresis in `ArucoDetector`:** a dictionary `marker id -> time of last viewing`. `tray sum()`adds everything younger than`MARKER HOLD`is. This is the solution for the hand over the tray, not for pucks that really disappear — it needs position tracking, and that is consciously not in scope.

`detectMarkers()`for`DETECT_HZ`run instead of 60 FPS: the detection is expensive and the game does not need it more often than the visitor moves pucks.

### `Buttons`(later, milestone 10)

gpiozero callbacks run in a strange thread. The key press goes into one`queue.SimpleQueue`, `run_game`empty it once per frame and pushes the actions through the same place as`action_of`. This changes`scenes.py`no line.

**Note:** `pygame.key.set_repeat()`applies only to the keyboard. The scrolling of the letters during holding must`Buttons`— otherwise the initial input at the fair works differently than when developing.

### `main.py`

```python
def main():
    pygame.init()
    fonts = {"big": ..., "mid": ..., "small": ..., "tiny": ...}
    ctx = Ctx(detector=FakeDetector(), db=DB(), fonts=fonts)
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS)
```

The only file that`scenes`**and* *`hw`imported. The transition to real hardware is exactly one line:`FakeDetector()` → `ArucoDetector(Camera())`.


---

## Randbedingungen

- **Durchsatz:** ~90 s pro Person inkl. Wechsel. 6 h Messe ≈ 240 Besucher.
- **Tolerance:** Any required depositing accuracy ≥ 1 cm. Backlash and dead zone of the servos don't allow anything more.
- **Servoschutz:** Torque and overload registers conservatively in the EEPROM, Software-Joint-Limits, Watchdog on load and temperature.
- **Servo dies first. Replacement servos, printed spare parts, ideally complete second arm as hot saving.
- **USB bandwidth:** Two UVC cameras on a bus allocate bandwidth (No space left on device). Test before setup, reduce separate buses or resolution.
- **Ergonomics:** Podest for smaller visitors. Disinfectant on the leader.
- **GDPR:** For the most part, minors are registered. Clear up.
- **Autostart:** Both processes as systemd services. The machine must come up without a keyboard after power failure.

## Balancing: Values and Target Value

Difference on 27. August 2026, after the best list became the question.

* * The target value is no longer thrown free. **`randrange(50, 300, 5)` next to
a tablet sum that the predecessor has left: the coincidence
decides whether someone has 3 or 200 points to bridge. That was the
actual unfairness — not the values but the coupling that was missing.
`balance.gap()`therefore reads the real tablet and selects the *Distanz*:

1. in `GAP_MOVES`(3) Trains exactly lockable — no round is impossible
Two. the best single train lands between`GAP_ONE_MISS`(2) and
   `GAP_ONE_MAX` (15) daneben

The lower limit prevents the buck that leads directly to zero. The
upper limit prevents the opposite: without it scattered the same test from 2 to
67, and a round that leaves still 67 open after the best single train is in
Not to get 60 seconds. Measured over 400 random tray states:
Median 49 permissible distances to choose from, minimum 34, never zero; Calculations
under one millisecond, once in`GameScene.__init__`.

**The values no longer have a common divider.** Old were all ten by 5
in part — the game was binary: distance divided by 5 then sufficient
Puck; otherwise *not accessible at all*. From 76 distances in the band 30–120, the
no single train, only 4 were detachable in two trains. With
`{4, 7, 12, 18, 23, 29, 36, 44, 53, 67}`are 71 out of 74. First of all
it 'napply' — and thus a best list with resolution instead of a
List of zeros and impossibilities.

**A marker per physical puck, ten pieces. **`ArucoDetector.marks`is a
Dict with the ID as key: two pucks with the same marker count once.
Printing duplicates would be a silent valuation error, which on the fair day like a
Recognition problem looks like. 10 also fits the 5×2 wheel
Preistabelle im Score-Screen.

## Preise

Three stages, all attainable — each wins something:

- **Participation** — Sticker or 3D printed keychain
- **Score band** — better reward, graded by accuracy
- **Tagesbestenliste** — Hauptpreis am Ende des Messetags

## MVP-Meilensteine

Order according to the principle: after each step something runs. The software is finished against attacks before hardware is connected.

**Software (without hardware)**

1. ● Skeleton runs — Scene logic, transitions,`main.py`/`db.py`/`hw.py` stehen, durchklickbar
2. ◐ Lessibility — Layout drawn, color timer stands; from 8 m not yet tested
3. ◐ Game logic — `FakeDetector` supplies numbers; `tray sum()`is in the wrong branch (Fund 3)
4. High Score — Cursor model and SQLite stand,`handle` doppelt (Befund 1)
5. ◐ Attract Mode — Timeouts and title picture stand, demo video missing
5a. ● CRT overlay — curvature, scanlines, vignette in`run_game`; Press Start 2P as font. Set strength in the hall, measure costs on the Pi
5b. ● Musik — `music.py`, deklarative Notation, Square-Wave-Synthese, Ducking
5d. ● Balancing — `balance.py`, target value from the tray, values without
    gemeinsamen Teiler; `GAP_MOVES` bleibt geraten bis jemand misst
5c. ○ Vollbild — `pygame.SCALED`, `FULLSCREEN`- Switch in`config.py`

Legend: ● finished · ◐ started · open

**Hardware**

6. Arm running — Teleop 10 min without error
7. Grasping works — 9 of 10 pucks without tipping
8. ◐ Markers are recognized, Code stands and runs against the webcam; against
printed markers untested under indoor light
9. ◐ Tablet is read — Hysteresis stands (`MARKER_HOLD`), real unaudited

**Integration**

10. ● `FakeDetector` → `ArucoDetector` erledigt (`CAMERA` in `config.py`);
    `FakeButtons` → `Buttons`Open
11. LED states, systemd autostart of both processes, UDP-Heartbeat

Milestones 1–5 do not need arm or camera and run parallel to the hardware. An integration step is omitted: both processes are only started next to each other.

# Not in scope

Jetson, browser frontend, WebSocket, Flask, Kubernetes, ConfigSync, GCS, Vertex pipelines, trained CV models, autonomous operation without Teleop, FPV as its own game (only as optional hard-mode switch). Video decoding in **Attract Mode** remains outside — the demo clip runs in`HowToScene`, a few seconds per visitor instead of six hours in the closed cabinet.

## Offene Punkte

- Which Pi (model and RAM)
- **Powerless parking pouch of the follower** — blocks the torque shutdown in idle
- Python-Version des Pi-Images, daraus folgt LeRobot-Version
- Number of available arms
- duration of the trade fair
- ArUco detection rate under indoor light (not testing in the studio)
- Real number of actions unskilled in 60 s — is now considered`GAP_MOVES = 3` in
  `config.py`. The mechanism is right at any value, only the constant is
the once someone measures it, it's a line
- Whether the intermediate scene gets its own thinner music instead of the Idle loop,
a string in`PIECES`, no code change
- `up`runs backwards through the alphabet (A→Z). With
  echten Pfeilen instead of `^v`it is now more noticeable; a line in
  `LeaderboardScene.handle`if it is to be turned around
- `TRAY_ROI`set on the built-up machine — depends on camera height and tray size
- CRT scanline strength under indoor light: from when the effect costs more legibility than it brings optics (`SCANLINE_ALPHA`, `VIGNETTE_ALPHA`)
- Whether the Pi has the 3.3 ms left for the curvature. If not:`BARREL_K = 0`
- ~~Ob `cv2` beside `pygame`on the Pi clean charging~ — Done at 9.9.2026. On Ubuntu 24.04 openCV 5.0.0 and pygame-ce 2.5.8 download under Python 3.13 without symbol conflict
- Audio output at the Pi (clink, HDMI or USB) and whether there is anything audible at the stand
- Whether the 60-px beams disappear at the top/bottom behind the cabinet shutter — otherwise 1280 × 800 consider design resolution
- Whether at 1920 × 1080 is rendered native instead of being scaled down at 1200. The panel cannot be 16:10, so the question is no longer *ob* 16:10 worth it, but whether the layout in`scenes.py`moved to 1080 (`FOOTER_Y = 1120`is otherwise outside the picture)
- Snap-in vs. Screwdriver at 3 mm plywood — Testing tearing behavior
- Two cameras at the same time: Verify bandwidth on the real Pi (index of the arm camera is not yet fixed,`CAM_INDEX`is one)
- FPV-Latenz, falls Hard Mode kommt

## Arbeitsweise

Originally: the MVP consciously without AI assistance. Primary sources, attempt to strike, in blockade ask for two hours of colleagues instead of tools. Time budget accordingly set two to three times.

**Adjusted (August 2026):** The wizard is used as a examiner and explainer — it reads code, names errors with file and line, explains draft questions and maintains this document. Everything was written first by hand: the learning effect depends on the keystrokes themselves passing.

**Adapted (27 August 2026):** The skeleton stands and is understood — Scene model, Loop,`Ctx`-Well, layout coordinates have been created by hand and thus penetrated. From here, the wizard writes the code, but only after the four-step run up. The understanding thus migrates from 'I have chosen it' to 'I have made the decision and could defend it' — and the latter is what counts at the trade fair stand at 9 a.m. when repairing. The process is the condition for this: without step 2 and 3, it would only be dictate.
