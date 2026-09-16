# PICK'N'PLAY

Arcade cabinet with a real robot arm. Visitors control an SO-101 follower arm via teleoperation and play a timed estimation game with a tray of pucks.
Built as commissioned work for a STEM fair.

Complete documentation (concept, game flow, layout, hardware, design decisions): **[`picknplay-overview.md`](picknplay-overview.md)**.
Startup, checks, and maintenance: **[`docs/betrieb.md`](docs/betrieb.md)**.

## Architecture

Two fully separate processes (see “Process Architecture” in the overview):

| Process | Responsibility | Stack |
|---|---|---|
| Teleop | Read leader → write follower, 60 Hz | LeRobot 0.4.x, Python 3.10 |
| Game | Camera → ArUco → state → rendering | OpenCV, pygame-ce, SQLite, Python 3.13 |

This repository contains the **game** process. `game/` is not a package; modules are imported flat via `sys.path[0]`.

## Start

```sh
uv run game/main.py
```

For development without hardware: set `CAMERA = False` in `game/config.py` to use `FakeDetector`, and set `FULLSCREEN = False` for windowed mode.

## Self-tests

Each module with non-trivial logic contains a self-test and prints `ok`:

```sh
uv run game/db.py        # Leaderboard: sorting and edge cases
uv run game/balance.py   # Target-value generation from tray contents
uv run game/music.py     # Notation and synthesis
uv run game/scenes.py    # Layout: bounds, SAFE_BOTTOM, overlap checks
```

The layout self-test intercepts every `draw()` call and verifies all scenes in all states. It protects against clipping/overlap bugs like the previous leaderboard overlay issue.

## Licenses

Font: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P), SIL Open Font License — see [`game/assets/OFL.txt`](game/assets/OFL.txt).
