# Expo mode — plan

Agreed on 2026-09-16. Goal: the cabinet runs unattended for several fair days.
Nobody technical is on site. The person at the booth can do exactly one thing:
pull the plug and plug it back in. That must always be enough.

Decisions: notifications **email only** (via healthchecks.io, no SMTP on the
Pi), **Tailscale** for remote SSH, auto-update pulls **branch `expo`** only,
fair network **unknown** (everything must keep working offline).

## Status (2026-09-17)

Built: layers 1, 2, 4, 5 (`pi/setup.sh`, `pi/update.sh`, `pi/leds.py`,
`teleop/run.py`, `docs/expo-card.md`). Layer 3 (healthchecks) is postponed,
so the card leaves "we get a message" out for now. Extra: sshd waited 2 min
at boot for eth0 (no cable), now wait-online gives up after 15 s; apt and
snap auto-updates are off.

## Facts found on the Pi (2026-09-16)

- `kernel.panic = 0`: a kernel panic hangs forever
- `/dev/watchdog` exists, `RuntimeWatchdogSec` is off
- no Tailscale; `curl` is installed
- systemd 255: `RestartSteps` / `RestartMaxDelaySec` available
- EEPROM: the Pi 5 boots by itself when power returns
- teleop.service override: `StartLimitBurst=5` in 120 s, then it stays dead

## Layer 1 — game service `pnp-expo.service`

- `User=ubuntu`, runs `game/main.py` from the project `.venv`, starts on boot
- `Restart=always`, `RestartSec=3`, `RestartSteps` up to 2 min, never gives up
  (`StartLimitIntervalSec=0`)
- `Type=notify` + `WatchdogSec=15`; `app.py` sends `WATCHDOG=1` per frame via
  `NOTIFY_SOCKET` (stdlib socket, ~5 lines, no-op when the variable is unset)
- camera loss while running: no new frame for 5 s → exit non-zero, systemd
  restarts and reopens the camera (today `hw.py` silently keeps the last frame)
- `Nice=5`, `CPUWeight=50` so sshd and teleop always win (replaces the
  `timeout` of `pnp-start`, which stays unchanged for testing)
- `ExecStopPost` switches the LED strip off
- teleop gets the same never-give-up backoff instead of `StartLimitBurst=5`

## Layer 2 — the Pi itself

- `RuntimeWatchdogSec=30` in systemd (hardware watchdog → reboot on hang)
- `kernel.panic=10` via sysctl.d
- logind `HandlePowerKey=reboot`
- journald `SystemMaxUse=200M`
- highscore SQLite in WAL mode

## Layer 3 — notifications (healthchecks.io → email)

- checks: `alive`, `game`, `teleop`, `power-heat`, `update`
- `alive`: pinged every minute **only** if game + teleop are active and the
  camera delivers frames; 5 min grace → email "Pi silent"
- events: `/fail` ping with the last log lines as body → email with log;
  success ping when healthy again. healthchecks mails only on state change,
  so a restart loop doesn't spam
- triggers: game/teleop restart (`OnFailure=` or NRestarts delta), throttling
  or undervoltage (`vcgencmd get_throttled`), temperature > 80 °C, update
  applied / rolled back, boot
- offline: failed pings are queued in a file and sent when the net returns
- API key lives in `/etc/pnp-expo.env` (root 600), never in the repo; checks are
  created via the Management API with that key

## Layer 4 — remote updates

- timer every 5 min: `git fetch origin expo`; if new: pull, `uv sync` if the
  lock changed, restart the game **only between rounds** (game writes its scene
  state to a file, e.g. `/run/pnp/state`)
- rollback: game fails within 2 min after an update → reset to the previous
  commit, restart, notify
- `git fsck` fails → re-clone
- all network calls with timeouts

## Layer 5 — for the person at the booth

- hold all four buttons 5 s → game exits, systemd restarts it
- game down → the watchdog/update service shows a calm orange on the strip
- `docs/expo-card.md`: printable card: 1. hold buttons, 2. unplug 10 s, wait
  2 min, 3. arm acting strange: emergency stop, call <number>. "We already got
  a notification."

## Aliases (tools/pi_aliases.sh)

`pnp-expo`, `pnp-expo-stop`, `pnp-expo-log`, `pnp-expo-on` / `pnp-expo-off`
(autostart), `pnp-notify-test`, `pnp-wifi-add SSID PASS`; `pnp-status` shows
all services and NRestarts.

## Rejected

- read-only root (overlayfs): best plug-pull protection, but highscores and
  updates need to write; too much rework before the fair
- pulling `main`: half-done commits would go live
- Home Assistant as notifier: not reachable from the fair
- ntfy / Telegram: Vadim wants email only
- nightly reboot: halls usually cut power at night anyway, cold boot is the
  test that matters

## Needs Vadim

1. healthchecks.io account, email channel, read-write API key
2. Tailscale login link (click once)
3. OK for one reboot (watchdog + cold boot test)
4. creating/pushing branch `expo`
