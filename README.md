# PICK'N'PLAY

Arcade-Automat mit echtem Roboterarm. Besucher steuern per Teleoperation einen
SO-101-Follower und schätzen gegen die Uhr den Wert eines Tabletts voller Pucks.
Auftragsarbeit für eine MINT-Messe.

Die vollständige Dokumentation (Konzept, Spielablauf, Layout, Hardware,
Entwurfsentscheidungen) steht in **[`picknplay-overview.md`](picknplay-overview.md)**.
Wie man den Automaten startet, prüft und wartet, steht in
**[`docs/betrieb.md`](docs/betrieb.md)**.

## Aufbau

Zwei Prozesse, die sich nichts teilen (siehe „Prozess-Architektur" im Overview):

| Prozess | Aufgabe | Stack |
|---|---|---|
| Teleop | Leader lesen → Follower schreiben, 60 Hz | LeRobot 0.4.x, Python 3.10 |
| Spiel  | Kamera → ArUco → Zustand → Rendern | OpenCV, pygame-ce, SQLite, Python 3.13 |

Dieses Repository enthält den **Spiel**-Prozess. `game/` ist kein Paket — die
Module finden sich flach über `sys.path[0]`.

## Starten

```sh
uv run game/main.py
```

Zum Entwickeln ohne Hardware: `CAMERA = False` in `game/config.py` schaltet auf
den `FakeDetector`, `FULLSCREEN = False` auf Fenster.

## Selbsttests

Jedes Modul mit nicht-trivialer Logik prüft sich selbst und druckt `ok`:

```sh
uv run game/db.py        # Bestenliste: Sortierung, Grenzfälle
uv run game/balance.py   # Zielwert-Findung aus dem Tablett
uv run game/music.py     # Notation und Synthese
uv run game/scenes.py    # Layout: Bildgrenzen, SAFE_BOTTOM, Überdeckung
```

Der Layout-Selbsttest fängt jeden `draw()`-Aufruf ab und prüft alle Szenen in
allen Zuständen — er ist die Absicherung gegen die Klasse von Klippfehlern, die
das Leaderboard-Overlay hatte.

## Lizenzen

Schrift: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P),
SIL Open Font License — siehe [`game/assets/OFL.txt`](game/assets/OFL.txt).
