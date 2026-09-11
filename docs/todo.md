# To-dos — Stand 11. September 2026

Reihenfolge nach dem Prinzip des Projekts: nach jedem Schritt läuft etwas.
Legende: ● fertig · ◐ angefangen · ○ offen · ✱ wartet auf eine Entscheidung

---

## 1 · Hardware-Anbindung

### ○ Geofencing der Arme
`run_teleop.sh` startet das nackte `lerobot-teleoperate`. `SO101FollowerConfig`
kennt nur `max_relative_target` — das begrenzt die **Schrittweite**, nicht die
**Lage**. Absolute Gelenkgrenzen gibt es in LeRobot nicht.

Also ein eigener Teleop-Loop (`teleop/run.py`, ~30 Zeilen): Leader lesen, jedes
Gelenk in ein Band klemmen, Follower schreiben. Die Grenzen kommen aus einer
Tabelle in derselben Datei und werden am Automaten eingefahren, nicht geraten.

Nebenwirkung, die für uns spricht: der Loop ist dann unsere Datei, und Idle-
Torque-Abschaltung, Parkpose und Watchdog haben später einen Ort.

### ● Buttons an GPIO
Pins **17 · 27 · 22 · 23** (Header 11 · 13 · 15 · 16), Taster gegen GND,
interner Pull-up. Begründung und Belegung: siehe `docs/betrieb.md`.
Abgefragt wird einmal pro Bild im Loop — kein Callback-Thread, keine Queue.

### ◐ LED-Streifen — SPI direkt am Pi
Entschieden am 10.9.2026, Code steht seit dem 11.9.: `hw.Leds`, ein
Worker-Thread mit Zustandsslot, schreibt direkt auf `/dev/spidev0.0` — ein
`ioctl` und ein `write`, deshalb ohne `rpi5-ws2812`/`Pi5Neo`. Vier Zustände
aus den Szenen: `idle` (laufende Zuckerstange), `game` (Restzeit als Balken),
`hurry` (rot, 2 Hz, ab `WARN_SECONDS`), `score` (Zuckerstange, schnell).
Ohne Gerät stumm, am Mac also einfach aus. Kodierung im Selbsttest von `hw.py`.

**Ungeprüft, weil der Streifen fehlt:** alles am echten Draht. Offen:
- Pegelwandler 3,3 → 5 V
- welcher Streifen: 3 Kontakte (adressierbar) oder 4 (nur eine Farbe)? 5 oder 24 V?
- `LED_COUNT` und `LED_ORDER` in `config.py` am Streifen abzählen/prüfen
- SPI am Pi einschalten und `spidev.bufsiz` hochsetzen, siehe `docs/betrieb.md`
- Last des Threads auf dem Pi messen (~15 ms Schreibzeit pro Bild, gibt das GIL frei)

---

## 2 · Datenhaltung und Bestenliste

### ● Jede Runde wird gespeichert, nicht nur der beste Lauf
Neue Tabelle `runs(ts, name, off, goal, total)`. Die Bestenliste ist eine
Abfrage darüber (`MIN(off) GROUP BY name`), keine zweite Tabelle. Damit fällt
„derselbe Name am nächsten Tag verbessert sich" ohne eine Zeile Sonderlogik
heraus, der alte Lauf bleibt stehen, und die Versuche sind vollständig da.
Die 16 Zeilen der alten `scores`-Tabelle wandern beim ersten Start mit.

### ○ Rückfrage bei bekanntem Namen
`db.best(name)` liefert den bisherigen Bestwert. Die Rückfrage gehört in die
neue Namenseingabe und kommt mit dem UI-Umbau.

---

## 3 · UI/UX-Umbau

Der große Posten. Ziel: jemand, der das Spiel nie gesehen hat, versteht es aus
3–8 m in wenigen gescannten Wörtern. Betrifft:

- **Erklärung/Onboarding** — drei Textzeilen erklären nichts. Braucht Bild
  oder Animation, nicht mehr Worte.
- ● **`OFF BY` und die Anordnung während der Runde** — ersetzt durch Balken
  plus Handlungsanweisung. Der Schirm sagt jetzt `ADD POINTS 60`, und der
  Balken zeigt Richtung und Abstand ohne Lesen. Skala des Balkens ist die
  Summe aller zehn Pucks, also über alle Runden dieselbe.
- ● **Vier Knöpfe in Grün, Rot, Blau, Gelb** — jeder Pfeil auf dem Schirm hat
  die Farbe seines Knopfes. Grün ▶, Rot ◀, Blau ▲, Gelb ▼.
- ✱ **Punktesystem** — wird komplett neu gedacht, eigene Session. Bis dahin
  bleiben `OFF BY` auf dem Score-Screen und die Zeilen „THE LOWER THE BETTER"
  / „LOWER MEANS BETTER" stehen: sie sind hässlich, aber solange die
  Bestenliste aufsteigend sortiert, wäre sie ohne sie falsch zu lesen.
- ○ **Erklärung/Onboarding** — drei Textzeilen erklären nichts.
- ○ **Leaderboard-Flow** — Score-Screen → Namenseingabe → Idle ist heute drei
  Seiten für ein Ergebnis. Hängt am Punktesystem, deshalb danach.
- ○ **Der große `◀` in der Namenseingabe** — trägt noch nicht die Rotfärbung
  seines Knopfes, weil dort Gelb schon „ausgewählt" bedeutet. Fällt mit dem
  Leaderboard-Flow.
- ● **„Sugar Rush"-Look** (11.9.) — Schokoladengrund, Pink statt Gelb, Sahne
  statt Weiß (`config.BG/ACCENT/WHITE`). 16 Pixel-Sprites in `game/sprites.py`
  als Text notiert, Farben aus der Bambu-Matte-Tabelle. Idle: gegenläufige
  Laufbänder und Wellentitel. Runde: Zuckerstangen-Balken, Streusel bei PERFECT,
  in den letzten 5 s Sahne statt Pink (Pink auf Rot hat nur 2,7 : 1).
  Preisreveal: jedes Teil als Sprite, die gelegten hüpfen, Streuselschauer.
  Layout unverändert, Selbsttest prüft die Sprites mit. **Auf dem Pi ungemessen.**
- ● **Thema austauschbar** (11.9.) — alles Themenhafte (Farben, Texte, Sprites,
  LED-Farben, Marker→Sprite) steht in `game/themes/sugar_rush.py`. Neues Thema =
  Datei kopieren, `PNP_THEME=name`. `uv run game/sprites.py` prüft jedes Thema in
  `themes/` gegen den Vertrag in `config.THEME_KEYS`. Kein Szenencode nennt ein Sprite.
- ○ **Sprite-Zuordnung** — `SPRITE` im Thema ist ein Platzhalter, billig → teuer.
  Neu belegen, sobald die gedruckten Objekte feststehen. Mehr als zehn Objekte
  heißt mehr Einträge in `VALUES` — das gehört in die Wertungssitzung.
- ○ **Demo-Video** — `DEMO_VIDEO = None`, es gibt noch keinen Aufbau zum Filmen.

---

## 4 · Build-Log

### ● Screenshots aller Szenen ohne Automat
`uv run tools/shots.py` → `docs/shots/*.png`. Läuft headless, ohne Kamera,
ohne Fenster, mit CRT-Overlay wie am Automaten.

### ● Auslöser
Entschieden am 11.9.2026: vor jedem Commit, den der Assistent macht, läuft
`uv run tools/shots.py`, und `docs/shots` geht in denselben Commit. Kein Hook,
kein Cron. Die Bilder sind deterministisch (Streusel mit festem Seed) — ändert
sich ein PNG ohne UI-Änderung, ist das ein Befund.

---

## 5 · Objekte: Cupcakes

Entschieden am 11.9.2026: Cupcakes, Wert = Preis, schwerer zu greifen = teurer.
Kegelförmiges Topping bleibt, der Marker wird von oben ein Stück hineinextrudiert
(senkrechte Projektion), nicht flach aufgesetzt. Die Preise selbst gehören in die
Wertungssitzung.

### ● Marker als SVG
`uv run tools/marker_svg.py [mm]` → `markers/aruco_marker_<id>.svg`, 30 mm
Vorgabe, nur die schwarzen Zellen. Jede Datei wird zurückgerastert und erkannt,
bevor sie geschrieben wird.

### ○ Marker als kleine STL/3MF zum Skalieren in Bambu Studio
Für den Workflow gebraucht: pro ID ein Körper, der sich in Bambu wie jedes
andere Teil mit dem Skalierwerkzeug auf Maß ziehen und in den Cupcake schieben
lässt. SVG-Import in Bambu hat eine eigene Größenlogik, das ist der Umweg.

### ● Meshy-Prompts für alle Sorten
`docs/meshy-prompts.md`: 24 fertige Prompts mit Tail, dazu Farbpaare (Bambu Matte
und CMYK) und Hinweise für den H2C mit Vortek.

### ○ Testplättchen pro Farbpaar drucken
Erster CMYK-Druck auf dem H2C. Farbmischung nur an senkrechten Wänden, Topping und
Marker immer aus einem ungemischten Filament. Plättchen vor die Mac-Webcam halten,
das Spiel zeigt die Erkennung live.

### ○ Kegel-Grenze am echten Aufbau prüfen
Simuliert (11.9.): über der Markerfläche höchstens ~5 mm Höhenunterschied
(~10°) geht überall auf dem Tablett, 10–15 mm nur in der Mitte. Am Automaten
mit einem Testdruck gegenprüfen, sobald Kamerahöhe und Tablett stehen.

---

## Entscheidungen

Gefallen am 10.9.2026:

- Knopffarben: **Grün ▶, Rot ◀, Blau ▲, Gelb ▼**
- Rundenbildschirm: **Balken plus Handlungsanweisung**
- LEDs: **SPI direkt am Pi**, eigenes Netzteil vorhanden

Gefallen am 11.9.2026:

- Objekte: **Cupcakes, Wert = Preis**, später Kuchenstücke und weitere Sorten
- Marker: **Kegel-Topping, von oben hineinextrudiert**; Schokokuchen invertiert
  (`detectInvertedMarker` ist an)
- UI: **Variante B, „Sugar Rush"**
- Build-Log: **Screenshots vor jedem Commit**

Offen:

- **Punktesystem** — eigene Session, das ganze System wird überarbeitet
- Leaderboard-Flow und Onboarding, beide hängen daran
