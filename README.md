# PICK'N'PLAY

Arcade machine with a real robot arm. Visitors teleoperate an SO-101 follower
and, against the clock, estimate the value of a tray full of pucks.
Commissioned for a STEM fair.

The full documentation (concept, game flow, layout, hardware, design
decisions) is in **[`picknplay-overview.md`](picknplay-overview.md)**.
How to start, check and maintain the machine is in
**[`docs/operation.md`](docs/operation.md)**.

## Structure

Two processes that share nothing (see "Process architecture" in the overview):

| Process | Job | Stack |
|---|---|---|
| Teleop | read leader → write follower, 60 Hz | LeRobot 0.4.x, Python 3.10 |
| Game   | camera → ArUco → state → render | OpenCV, pygame-ce, SQLite, Python 3.13 |

This repository contains the **game** process. `game/` is not a package — the
modules find each other flat via `sys.path[0]`.

## Running

```sh
uv run game/main.py
```

To develop without hardware: `CAMERA = False` in `game/config.py` switches to
the `FakeDetector`, `FULLSCREEN = False` to a window.

## Self-tests

Every module with non-trivial logic checks itself and prints `ok`:

```sh
uv run game/db.py        # leaderboard: sorting, edge cases
uv run game/balance.py   # picking a target from the tray
uv run game/music.py     # notation and synthesis
uv run game/scenes.py    # layout: screen bounds, SAFE_BOTTOM, overlap
```

The layout self-test intercepts every `draw()` call and checks all scenes in
all states — it guards against the class of clipping bugs the leaderboard
overlay used to have.

`uv run tools/shots.py` renders every scene to `docs/shots/` without machine,
camera or window.

## Licenses

Font: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P),
SIL Open Font License — see [`game/assets/OFL.txt`](game/assets/OFL.txt).
