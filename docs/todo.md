# To-dos — As of 2026-09-17

Order follows the project's principle: something runs after every step.
Legend: ● done · ◐ started · ○ open · ✱ waiting on a decision

---

## 0 · From the first cabinet test (2026-09-16)

The game is harder than expected. The scoring scales stay as they are.

- ◐ **Geofencing the arms**: code done (2026-09-17), limits still to dial in, see section 1
- ● **Remove the vignette**: the panel has poor viewing angles, so dark corners look even darker
- ● **Slightly brighter background**: the whole screen looks a bit dark
- ● **Smaller detection window**: right now everything on the surface falls inside it
- ● **Footer prompts (◀ BACK / ▶ START …)**: too dark and outside the field of view
- ● **Round length 90 s instead of 30 s**

---

## 1 · Hardware integration

### ◐ Geofencing the arms
`SO101FollowerConfig` only knows `max_relative_target` — that limits the
**step size**, not the **position**. LeRobot has no absolute joint limits.

Done 2026-09-17: `teleop/run.py` replaces `run_teleop.sh`. It reads the
leader, clamps each joint into its band from `LIMITS`, writes the follower,
and pings the systemd watchdog. At the edge only that joint stops.

Open: `LIMITS` is still the full range. On the machine run `pnp-arm-limits`,
move the leader to the safe edges, Ctrl-C, paste the printed table.
Idle torque shutoff, park pose and wake ramp have a home now, not built.

### ○ Self-healing: calibration without us
If teleop can't start because the calibration doesn't match (motor swapped,
`~/.cache` wiped), `connect()` asks on stdin, and under systemd that's a
restart loop. Goal: a layperson can recalibrate at the booth, guided by the
screen and the four buttons, no keyboard. Needs: teleop reports "needs
calibration" to the game, a calibration scene, LeRobot's calibrate() driven
without `input()`. Not started.

### ● Buttons on GPIO
Pins **17 · 27 · 22 · 23** (header 11 · 13 · 15 · 16), buttons against GND,
internal pull-up. Reasoning and pinout: see `docs/operation.md`.
Polled once per frame in the loop — no callback thread, no queue.

### ◐ LED strip — SPI directly on the Pi
Decided on 2026-09-10, code has been in place since 2026-09-11: `hw.Leds`, a
worker thread with a state slot, writes directly to `/dev/spidev0.0` — one
`ioctl` and one `write`, hence no `rpi5-ws2812`/`Pi5Neo`. Four states from
the scenes: `idle` (running candy cane), `game` (time remaining as a bar),
`hurry` (red, 2 Hz, from `WARN_SECONDS` on), `score` (candy cane, fast).
Silent without the device, so simply off on the Mac. Encoding is covered in
`hw.py`'s self-test.

**Unverified, because the strip is missing:** everything on the real wire.
Open:
- level shifter 3.3 → 5 V
- which strip: 3 contacts (addressable) or 4 (single color only)? 5 or 24 V?
- count/check `LED_COUNT` and `LED_ORDER` in `config.py` against the actual strip
- enable SPI on the Pi and raise `spidev.bufsiz`, see `docs/operation.md`
- measure the thread's load on the Pi (~15 ms write time per frame, releases the GIL)

---

## 2 · Data storage and leaderboard

### ● Every round gets saved, not just the best run
New table `runs(ts, name, off, goal, total)`. The leaderboard is a query
over it (`MIN(off) GROUP BY name`), not a second table. That gets "the same
name improving the next day" for free, without a line of special-case logic
— the old run stays on record, and every attempt is fully preserved. The 16
rows of the old `scores` table get carried over on first start.

### ○ Confirmation prompt for a known name
`db.best(name)` returns the previous best score (points since the scoring
session, no longer `off` — higher is better). The confirmation prompt
belongs in the new name entry screen and comes with the UI rework.

---

## 3 · UI/UX rework

The big item. Goal: someone who's never seen the game understands it from
3–8 m in a few scanned words. Covers:

- **Explanation/onboarding** — three lines of text explain nothing. Needs an
  image or animation, not more words.
- ● **`OFF BY` and the layout during the round** — replaced by a bar plus an
  action instruction. The screen now says `ADD POINTS 60`, and the bar shows
  direction and distance without reading. The bar's scale is the sum of all
  ten pucks, so it's the same across every round.
- ● **Four buttons in green, red, blue, yellow** — every arrow on the screen
  has the color of its button. Green ▶, red ◀, blue ▲, yellow ▼.
- ● **Scoring system** — done on 2026-09-11, see "Scoring" in the Overview. 0
  to 1000, higher is better, counting up on the score screen, prices instead
  of points during the round. Both crutch lines are gone: the leaderboard
  sorts descending and explains itself that way.
- ○ **Explanation/onboarding** — three lines of text explain nothing.
- ○ **Leaderboard flow** — score screen → name entry → idle is currently
  three screens for one result. Was blocked on the scoring system and is now
  free.
- ○ **The large `◀` in the name entry screen** — doesn't yet carry the red
  color of its button, because yellow already means "selected" there. Falls
  under the leaderboard flow.
- ● **"Sugar Rush" look** (2026-09-11) — chocolate background, pink instead
  of yellow, cream instead of white (`config.BG/ACCENT/WHITE`). 16 pixel
  sprites in `game/sprites.py` noted as text, colors from the Bambu matte
  table. Idle: counter-running marquees and a wavy title. Round: candy-cane
  bar, sprinkles on PERFECT, cream instead of pink in the last 5 s (pink on
  red is only 2.7 : 1). Price reveal: each item as a sprite, the placed ones
  bounce, sprinkle shower. Layout unchanged, self-test also checks the
  sprites. **Unmeasured on the Pi.**
- ● **Swappable theme** (2026-09-11) — everything theme-related (colors,
  text, sprites, LED colors, marker→sprite) lives in
  `game/themes/sugar_rush.py`. New theme = copy the file, `PNP_THEME=name`.
  `uv run game/sprites.py` checks every theme in `themes/` against the
  contract in `config.THEME_KEYS`. No scene code names a sprite.
- ○ **Sprite mapping** — `SPRITE` in the theme is a placeholder, cheap →
  expensive. Reassign once the printed objects are finalized. More than ten
  objects means more entries in `VALUES` — that belongs in the scoring
  session.
- ○ **Demo video** — `DEMO_VIDEO = None`, there's no setup to film yet.

---

## 4 · Build log

### ● Screenshots of all scenes without the machine
`uv run tools/shots.py` → `docs/shots/*.png`. Runs headless, without a
camera, without a window, with the CRT overlay as on the machine.

### ● Trigger
Decided on 2026-09-11: before every commit the assistant makes,
`uv run tools/shots.py` runs, and `docs/shots` goes into the same commit. No
hook, no cron. The images are deterministic (sprinkles with a fixed seed) —
if a PNG changes without a UI change, that's a finding.

---

## 5 · Objects: cupcakes

Decided on 2026-09-11: cupcakes, value = price, harder to grab = more
expensive. Cone-shaped topping stays, the marker gets extruded into it a bit
from above (vertical projection), not placed flat on top. The prices
themselves belong in the scoring session.

### ● Markers as SVG
`uv run tools/marker_svg.py [mm]` → `markers/aruco_marker_<id>.svg`, 30 mm
default, just the black cells. Every file is rasterized back and verified as
detected before it's written.

### ○ Markers as small STL/3MF to scale in Bambu Studio
Needed for the workflow: one body per ID that can be scaled to size in Bambu
with the scaling tool like any other part, and pushed into the cupcake. SVG
import in Bambu has its own sizing logic, which is the detour.

### ● Meshy prompts for every variety
`docs/meshy-prompts.md`: 24 ready-made prompts with tail, plus color pairs
(Bambu Matte and CMYK) and notes for the H2C with Vortek.

### ○ Print a test tile per color pair
First CMYK print on the H2C. Color mixing only on vertical walls, topping
and marker always from a single unmixed filament. Hold the tile up to the
Mac webcam, the game shows detection live.

### ○ Verify the cone limit on the real setup
Simulated (2026-09-11): above the marker face, at most ~5 mm of height
difference (~10°) works anywhere on the tray, 10–15 mm only in the middle.
Cross-check on the machine with a test print once camera height and tray are
finalized.

---

## Decisions

Made on 2026-09-10:

- Button colors: **green ▶, red ◀, blue ▲, yellow ▼**
- Round screen: **bar plus action instruction**
- LEDs: **SPI directly on the Pi**, dedicated power supply in place

Made on 2026-09-11:

- Objects: **cupcakes, value = price**, later cake slices and more varieties
- Marker: **cone topping, extruded in from above**; chocolate cake inverted
  (`detectInvertedMarker` is on)
- UI: **variant B, "Sugar Rush"**
- Build log: **screenshots before every commit**

Scoring session, 2026-09-11:

- **Score 0–1000, higher is better.** Accuracy as the *fraction* of the
  distance closed, time bonus only for perfects
- **Cupcake prices 1.40 € to 5.20 €**, internally in 10-cent units
- **Round length 30 s**, `GAP_MOVES = 2`, `PERFECT_HOLD = 3`
- **Difficulty is a mode** (`MODES` in `config.py`, `PNP_MODE`, individual
  values via `PNP_<KEY>`) — a hard mode is therefore just an entry in the
  dict
- **The tray starts empty.** Between rounds a staff member clears it;
  whatever's left stays left. No "tray ready?" gate in the software —
  `gap()` reads the real tray, so a forgotten cupcake changes the task along
  with it instead of breaking it.
- **No prices in the camera feed during the round.** The overlay on every
  detected marker is commented out (`GameScene.overlay`): it worked against
  "EVERY TREAT HAS A HIDDEN PRICE" and turned guessing into arithmetic. Can
  be uncommented again for aligning the camera; the detection window stays
  visible.

Open:

- **`GAP_ONE_MAX`** is set to 25 and determines how many different targets
  there are: with an empty tray that's 21 for the whole trade-show day.
  Whether that's enough, or whether the queue will notice the repeats, will
  only become clear at the booth. The self-test in `balance.py` prints the
  number on every run.
- **Band limits for the price tiers** — proposal `off = 0` / `≤ 5` /
  remainder, a guess until someone has seen a real afternoon of results.
- Leaderboard flow and onboarding, both now free
