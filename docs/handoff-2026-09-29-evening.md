# Handoff: fair day 2026-09-29, evening

Read `docs/handoff-2026-09-29.md` first: access (`ssh pnp-messe`), the deploy
block with rollback, the test list, and the rule **deploy only when Vadim
says "jetzt"**. Everything there still holds. This file is what changed since
and what's open.

## State right now

- Pi runs **cdf2a70** (= GitHub `expo` = `detect-robust` = `layout-topdown`).
  Last good before it: 14d7989, before that 1651a9e.
- Drop-ins on the Pi (`/etc/systemd/system/pnp-expo.service.d/`):
  `layout.conf` → `PNP_LAYOUT=fpv`, `mirror.conf` → `PNP_ARM_MIRROR=1`.
  Old `time.conf` (round 120 s) / `think.conf` may exist too, check with
  `systemctl show -p Environment --value pnp-expo`.
- Health at 01:33 UTC (Pi clock): NRestarts 0, no Traceback, game process
  **92 % CPU**, load 2.95–3.7. That is the likely cause of Vadim's "arm cam
  big in the middle kracht total": stutter, not a crash (unverified).

## What was built today (all live)

Game flow for a new player, all in `GameScene` (`game/scenes.py`):
`tut_intro` (Bella: "up next: practice, doesn't count" + camera rule) →
`tutorial` (fuse, `TUT_SECONDS` = 30) → `tut_done` → `read` (Oskar's order,
no prices, no clock) → `order` (think time, price ladder, `THINK_SECONDS`) →
`play`. Returning players start at `read`.

- Dialog pages turn themselves after `PAGE_SECONDS` = 6 once typed
  (`Dialog.due`), in Story, `tut_intro`, `tut_done`, `read`. Never in
  `tutorial` (▶ = skip) or `order` (▶ = start).
- `IDLE_TIMEOUT` 60 s (was 20).
- Layout switch `PNP_LAYOUT` (`game/config.py`, block after `TRAY_ROI`):
  `top` (default: top-down big center, arm cam small left), `split` (two
  equal panes), `solo` (no arm cam), `fpv` (arm cam big, top-down cropped to
  the tray via `TOP_CROP`, small left). `hw.CameraView` has `mirror`, `ud`,
  `crop`; `scenes.GameScene.overlay` maps marker coords through `TOP_CROP`.
- Arm cam orientation: `PNP_ARM_MIRROR` / `PNP_ARM_UD` (display only).
- Pi aliases (`source ~/picknplay/tools/pi_aliases.sh`, each restarts the
  game): `pnp-layout top|split|solo|fpv`, `pnp-mirror on|ud|180|off`.
- New events: `think` (`read` = seconds spent reading), `tut_timeout`,
  `auto` (page turned itself).

## Open: Vadim's feedback from the floor (priority order)

1. **Layout back, arm cam on the right.** "Arm-Kamera groß in der Mitte
   kracht total. Layout wieder zurück, aber FPV auf der rechten Seite."
   Most likely meaning: the `top` layout (top-down big center) with the arm
   cam inset on the **right**, so Oskar/pop-up (`GUEST_X`) move to the left
   side. Ask if unsure; `split` with the panes swapped is the other reading.
   Immediate mitigation without a deploy: `pnp-layout top`.
   Also check CPU with the big arm pane vs. small (`top -bn1`).
2. **Practice timer runs while Bella's text still types.** `self.tut -= dt`
   in `GameScene.update` counts from the moment `tutorial` starts. Start it
   only once `self.dialog.typing` is False (plus a moment to read).
3. **Practice ends too abruptly; failing must feel OK.** On `tut_timeout`
   it jumps straight to `read`. Needs a short screen/page: "didn't work? no
   problem, it was only practice" before Oskar. Same problem at the end of
   the think time: `start("timer")` drops people into the round with no
   transition.
4. **Big "short game starts now" splash before the main round.** A big
   interstitial (e.g. "GLEICH GEHT'S LOS!" / countdown 3-2-1) between
   `order` and `play`, both for ▶ and for the timer path.
5. **Rethink the math part (treats/prices).** Vadim: "beim Rechnen der
   Treats müssen wir das nochmal überdenken". Not specified. Ask him what
   isn't working before building (observed so far: people don't read, don't
   press ▶, and don't get that they should plan a combination).

Keep every new screen short: the queue is the main problem ("Leute warten
so lange, dass sie wieder gehen").

## Working notes

- Worktree used today: `.claude/worktrees/ux-lesescreen`, branch
  `layout-topdown`. Start fresh from `origin/expo`.
- Tests: the list in the first handoff, plus run `game/scenes.py` with
  `PNP_LAYOUT=split|solo|fpv` and `game/hw.py` (camera flip/crop checks).
- Screenshots with a real frame: `tools/shots.py` only has placeholders; the
  old raw top frame is `docs/shots/roi-0-raw.png` (pre-fair, unzoomed).
- Name clashes: never call a scene attribute `next` (scene switch); `read`
  and `plan` are GameScene methods, `think` is the countdown float.
