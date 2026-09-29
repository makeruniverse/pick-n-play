# Handoff: the fair, as of 2026-09-29 night

Replaces the two handoffs of 29.9. (morning and evening, both in git
history). The machine is at the fair and **people are playing**: every
restart kills a running round. Deploy only when Vadim says "jetzt", and never
run tests or camera snaps on the Pi while someone plays (it stutters).

## Access

- `ssh pnp-messe`: LAN cable, IPv6 link-local `fe80::8aa2:9eff:fe10:d6b3%en8`
  (USB LAN adapter on the Mac = `en8`; in `~/.ssh/config` the `%` is `%%`).
- `ssh picknplay` (WiFi, 172.22.1.2) is not reliable: `eth0` and `wlan0`
  share the static IP in netplan. `docs/operation.md` ("DHCP") is out of date.
- **The Pi has no internet.** `pnp-update.timer` pulls nothing, a push to
  origin/expo does NOT reach the Pi.
- **Clock:** no NTP and the RTC has no battery. Set by hand from the Mac on
  29.9. (was 9 h 35 min behind; all DB `ts` of that boot shifted by the same
  offset, backup `scores.backup-before-clock.db`), timezone Europe/Berlin.
  After a power cut it resumes from the mtime of
  `/var/lib/systemd/timesync/clock` (last run time), so check it:
  `date` on Pi vs Mac, then `sudo date -s @$(date +%s)` via ssh.
  `ts` columns are UTC; `events.t` is monotonic per boot.
- The Mac has no `timeout`; use `perl -e 'alarm N; exec @ARGV' ...`.

## Unattended: what heals itself

- `pnp-expo` and `teleop`: `Restart=always`, no start limit, never give up.
- Game watchdog 15 s, pinged only while every camera delivers: a camera
  gone for 5 s (`CAM_STALE`) restarts the game. Teleop watchdog 10 s.
- Hardware watchdog 30 s (`RuntimeWatchdogSec`): a hung kernel reboots.
- Staff reset: all four buttons held 5 s → game exits, systemd restarts it
  (`docs/expo-card.md`).
- Every screen moves on by itself: dialog pages after `PAGE_SECONDS`, the
  think time, the 3-2-1, the round, the score pages. A walk-away ends in idle.
- There is no `pnp-health.timer` and never was; "health check" means the
  check inside `pi/update.sh` and the deploy block below.

## Game flow (all in `game/scenes.py`)

New player: Idle ▶ → Bella (story, 3 pages) → `tut_intro` (camera rule) →
`tutorial` (fuse `TUT_SECONDS` 30, starts `TUT_GRACE` 2 s after Bella's line
is typed) → `tut_done` (a treat never seen before in this scene landed:
"nice, that one is X"; or on timeout: "no problem, just practice") → `read`
(Oskar's order, no clock) → `order` (think time `THINK_SECONDS` 20, price
ladder) → `go` (GET READY 3-2-1, `GO_SECONDS`, for ▶ and timer alike) →
`play` (`ROUND_SECONDS` 120) → score (pages turn themselves) → Idle.
Returning players start at `read`.

Defaults, no drop-ins needed any more: layout `split` (top-down left, arm cam
right, Oskar between), arm cam mirrored, round 120 s, `MARKER_HOLD` 1.0 s.
Toggles: `pnp-cam arm flip mirror|ud|180|off` (and `top`) flips a pane
live, no restart, kept in `flip.json` (display only, the overlay follows).
These restart the game: `pnp-layout split|top`, `pnp-time N`, `pnp-think N`.
The player number stands big on Bella's first screen.

## What the floor data said (29.9., 59 players, 25 finished rounds)

- Median ~72 s from Bella to the round start, 120 s round, 24 s on the score
  screen: ~3.5 min a player, at most ~16 an hour.
- 18 of 29 let the think time run out instead of pressing ▶.
- First treat after a median 29 s of the round; 5 of 29 rounds placed none,
  8 of 25 ended on an empty tray. 4 perfect, 9 within 10 ct.
- 4 practices ended at second 0-1 on a leftover blinking back in (fixed:
  `GameScene.seen`). Treats blinked out and back ~3× a round (hold 0.5 → 1.0).
- 18 of 43 rounds started with leftovers on the tray. Harmless: the target
  always needs adding, never removing.

Query: copy the DB with `sqlite3 backup` (the file is in WAL mode) and read
`events`; every scene switch, phase, tray change, hint, quit and end is there.

## Deploying (proven, now with the drop-ins)

Work in a worktree on a branch from `origin/expo`, then:

```sh
git push origin <branch>                                             # GitHub backup
git push pnp-messe:picknplay <branch>:refs/remotes/origin/pending    # onto the Pi, not active
# only after "jetzt":
ssh pnp-messe 'd=/etc/systemd/system/pnp-expo.service.d; b=~/dropins-$(date +%s); cd picknplay &&
  git merge -q --ff-only origin/pending && mkdir $b && sudo mv $d/*.conf $b/ 2>/dev/null;
  sudo systemctl daemon-reload && sudo systemctl restart pnp-expo && sleep 8 &&
  if [ "$(systemctl show -p NRestarts --value pnp-expo)" = 0 ] && systemctl is-active -q pnp-expo &&
     ! journalctl -u pnp-expo --since "-9s" -o cat | grep -q Traceback;
  then git update-ref refs/remotes/origin/expo HEAD; echo "OK $(git log --oneline -1)";
  else git reset -q --hard <LAST_GOOD>; sudo mv $b/*.conf $d/; sudo systemctl daemon-reload;
       sudo systemctl restart pnp-expo; echo ROLLED BACK; fi'
git push origin <branch>:expo                                        # after OK
```

## Tests before every deploy

From the worktree, with the main checkout's `.venv/bin/python`:

- In `game/`: `balance.py`, `db.py`, `hw.py`, `sprites.py`,
  `PNP_BUTTONS=0 scenes.py`, once more with `PNP_LAYOUT=top` and with
  `PNP_ASK_NAME=1`. Each prints `ok`.
- `tools/shots.py`, look at the changed PNGs, commit `docs/shots`.
- **Required: the real loop.** The layout test doesn't see scene switching
  (a crash loop got through on 29.9.). Idle only:
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PNP_CAMERA=0 PNP_BUTTONS=0 perl -e 'alarm 10; exec @ARGV' .venv/bin/python game/main.py`
  → exit 142. Whole flow: drive `app.run_game` with one ▶ and nothing else
  (short `PNP_ROUND_SECONDS`/`PNP_THINK_SECONDS`/`PNP_TUT_SECONDS`) and see
  it come back to `IdleScene`.

Never call a scene attribute `next` (that's the scene switch); `read`,
`plan`, `start`, `play` are GameScene methods, `think`/`go`/`tut` countdowns.

## Commands on the Pi (`source ~/picknplay/tools/pi_aliases.sh`)

`pnp-winners [n]` (prize: number, score, off, time left) · `pnp-events [n]` ·
`pnp-db-reset` (with backup) · `pnp-cam …` (exposure/snap) · the toggles
above. DB backups: `~/picknplay/scores.backup-*.db`.

## Open

- Bella's story is 3 pages (~24 s unattended). Shortest lever left on the
  queue, not touched: Vadim decides.
- The math (budget + think time) stays as is by decision of 29.9.; most
  people wait out the think time.
- A round can need 3 moves if a treat is occluded when the target is rolled.
- #5 (red round) never checked in the frame (`pnp-cam snap`).
- Every ▶ in idle creates a player (skip-name side effect).
- The idle parade still shows the retired treats (theme `SPRITES`).
- Harmless noise on every stop: `RuntimeError: cannot schedule new futures
  after shutdown` from the detector thread.
