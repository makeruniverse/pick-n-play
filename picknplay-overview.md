# PICK'N'PLAY — Project Overview

**Titel:** PICK'N'PLAY (vorher Arbeitstitel: TRAY RUNNER)
**Stand:** August 2026 · Konzept steht, Hardware im Bau, Software im Bau
**Plattform:** Raspberry Pi · Python · pygame

---

## Wertung (11. September 2026)

Das Punktesystem war seit dem 10.9. als Ganzes offen und ist es jetzt nicht mehr.

**Vorher:** `score = |Zielwert − Tablettsumme|`, klein ist gut, Bestenliste
aufsteigend — plus zwei Erklärzeilen (`THE LOWER THE BETTER`,
`LOWER MEANS BETTER`), ohne die man die Liste falsch herum liest. Dass die
Zahl eine Gebrauchsanweisung brauchte, war der Befund.

**Jetzt:** 0 bis 1000, hoch ist gut, aus zwei Teilen:

```
genauigkeit = 900 · (1 − off/distanz) ²      distanz = Abstand bei Rundenbeginn
zeit        = 100 · restzeit/(30 − 3)        ist nur ≠ 0, wenn perfekt
```

Drei Entscheidungen stecken darin:

**Gewertet wird der Anteil der geschlossenen Distanz, nicht der absolute
Fehler.** Eine absolute Skala braucht eine Konstante („so viele Punkte je 10
Cent"), die bei jeder Preisänderung neu geraten werden muss. Der Anteil
braucht keine. Nebenwirkung, die das Gleichstandsproblem fast alleine löst:
zwei Spieler, beide 0,30 € daneben, bekommen bei verschiedener Startdistanz
verschiedene Punkte.

**Der Zeitbonus ist nur für Perfekte zu holen — ohne Sonderzweig.** Die Runde
endet vorzeitig ausschließlich über `PERFECT_HOLD`, also ist Restzeit > 0
gleichbedeutend mit einem Treffer. Wer daneben liegt und nachdenkt statt zu
hetzen, verliert dadurch nichts, und das ist wichtig: der Skill des Spiels ist
das Schätzen.

**Die Datenbank speichert weiter die physische Wahrheit** (`off`, `dist`,
`secs`), nicht die Punktzahl. Eine geänderte Formel gilt damit rückwirkend
auch für alte Runden. Der Preis: die Bestenliste ist kein `ORDER BY` mehr,
weil die Punktzahl ein Verhältnis ist — `top()` liest alle Zeilen und rechnet
in Python. Ein Messetag sind ein paar hundert Zeilen.

**Preise statt Punkte.** Zehn Cupcakes zu 1,40 € bis 5,20 €. Gerechnet wird in
10-Cent-Einheiten, weil die Preise teilerfremd sein müssen — glatte Preise in
Cent hätten ggT 10, und damit wäre das Spiel wieder binär (Distanz durch den
Teiler teilbar → ein Griff genügt, sonst gar nicht erreichbar). Geteilt wird
genau einmal, in `euro()` in `scenes.py`.

**Rundenlänge und Schwierigkeit sind jetzt ein Modus.** `MODES` in
`config.py`, umschaltbar mit `PNP_MODE`, einzelne Werte mit
`PNP_ROUND_SECONDS=20` — die Zahlen werden noch viel durchprobiert und ein
Hard Mode ist ein weiterer Eintrag im Dict, keine Codeänderung.

**Zwei Folgebefunde, beide gemessen statt geraten:**

`GAP_MOVES` musste von 3 auf 2. Ein teleoperierter Pick dauert 10–20 s; bei 30
Sekunden Rundenzeit wären drei Züge ein Versprechen, das der Arm nicht hält —
und der alte Selbsttest zeigte, dass 113 von 200 Runden tatsächlich drei
gebraucht hätten.

Der Balken hatte die falsche Skala. Sie war die Summe aller zehn Cupcakes
(31,10 €), aber seit das Tablett leer startet, spielt sich alles unter
`GAP_MAX` (9,80 €) ab — Ziellinie und Füllung saßen im linken Viertel. Jetzt
ist `SCALE = GAP_MAX`.

**Offen und nur am Automaten zu klären:** ob `GAP_ONE_MAX = 25` die richtige
Vielfalt gibt. Am leeren Tablett ist die Menge möglicher Ziele endlich und
jeden Tag dieselbe — bei 15 wären es 14 Ziele, bei 25 sind es 21. Der
Selbsttest in `balance.py` gibt die Zahl bei jedem Lauf aus.

## Stand: 11. September 2026

**Das Spiel läuft am Mac**, ohne Branch: `config.MAC` setzt dort Fenster,
Pfeiltasten und die eingebaute Webcam in beiden Panes als Default. Der
Automat ist Linux, für ihn ändert sich nichts.

**Die Objekte sind Cupcakes, ihr Wert ist ihr Preis**, schwerer greifbar heißt
teurer. Marker als SVG (`tools/marker_svg.py`), Kegel-Topping mit von oben
hineinextrudiertem Marker, Schokokuchen invertiert (`detectInvertedMarker`).
Farbtest gegen die Bambu-PLA-Matte-Tabelle steht in `docs/todo.md`.

**Neuer Look „Sugar Rush"**: Schokoladengrund, Pink statt Gelb, Pixel-Sprites
in `game/sprites.py`, Laufbänder im Idle, Zuckerstangen-Balken, Streusel. Die
Layout-Koordinaten sind unverändert. **Auf dem Pi ungemessen** — das Zeichnen
war dort 1,5 ms pro Bild, die Sprites sind vorgerenderte Blits, aber es wurde
nicht nachgemessen.

**Das Thema ist austauschbar.** Farben, Texte, Sprites, LED-Farben und die
Zuordnung Marker → Sprite stehen in einer Datei, `game/themes/sugar_rush.py`.
`config.py` lädt sie über `PNP_THEME` und nennt in `THEME_KEYS`, was jedes
Thema liefern muss. Szenen nennen keinen Sprite-Namen, sie lesen `LADDER`
(die Objekte nach Preis). Ein zweites Thema (PCB-Bauteile) ist eine Kopie der
Datei. Bewusst nicht im Thema: HPI-Rot/-Orange, Knopffarben, `VALUES`, Titel,
Musik.

**LED-Modul geschrieben** (`hw.Leds`, SPI direkt), am Streifen ungeprüft.

---

## Stand: 10. September 2026

**Der Automat läuft mit stabilen 30 fps, mit Spiel und Teleop gleichzeitig.**
Das war seit dem 9.9. der offene Punkt, an dem die Abnahme hing. Gemessen am
Automaten, 45 Sekunden am Stück: 29,4 bis 30,3 fps, kein Abfall, dabei von
61,5 auf 75,7 °C.

Vier Änderungen, in der Reihenfolge ihres Ertrags:

1. **`pygame.SCALED` ist raus, gerendert wird nativ in 1920 × 1080.** Das war
   mit Abstand der größte Posten und der am schlechtesten geschätzte: die
   Vermutung lautete 8,5 ms, tatsächlich waren es rund 20. Die Szene selbst
   zeichnet in 1,4 bis 2,0 ms — die 25 ms, die vorher als „Szene + flip"
   verbucht waren, waren fast vollständig die Skalierung 1200 → 1080.
2. **Die Wölbung wölbt nicht mehr das Bild, sondern die Scanlines.** Sie steckt
   jetzt in der Verdunklungskarte, die beim Start einmal gebaut wird, und
   kostet zur Laufzeit nichts. Siehe „Messung auf dem Pi".
3. **Zielbildrate 30 statt 60**, Idle 15 statt 20. Begründung in `config.py`
   und unten.
4. **`cv2.setNumThreads(3)`** — OpenCV nimmt sich sonst alle vier Kerne und
   verdrängt genau den Teleop-Loop, der als einziger terminkritisch ist.

Das Layout ist dafür auf das 1080-Raster **neu gesetzt, nicht skaliert**: ein
reines ×0,9 hätte die Zeilenabstände relativ zur unveränderten Glyphenhöhe
zusammengezogen, und genau dort saß der Klippfehler vom 28. August. Der
Cursorbalken in `LeaderboardScene` ist dabei von einer Magic Number zu
`CURSOR_Y`/`CURSOR_H` geworden — er war ein `fill()` und damit für den
Layout-Selbsttest unsichtbar, also für die Fehlerklasse blind, gegen die der
Test gebaut wurde.

**Zwei Befunde nebenbei:**

Das Git-Repo auf dem Pi war kaputt — sechs Objekte, fünf davon null Byte lang.
Das ist die Signatur eines harten Ausschaltens, nicht einer sterbenden Karte:
`dmesg` zeigt keine einzige I/O- oder EXT4-Meldung. Repariert, indem die
kaputten Objekte beiseitegelegt und von origin neu geholt wurden.

Der Pi drosselt beim Messen auch mit *gestoppter* Teleop: von 63,7 auf 80,7 °C
in 25 Sekunden. Dasselbe `remap` kostete kalt 8,7 ms und warm 12,5 — 35 %
Unterschied allein aus der Temperatur. **Jede Messung ohne Lüfter misst auch
die Drosselung mit.** Aktive Kühlung ist damit keine Vorsichtsmaßnahme mehr,
sondern eine Voraussetzung für belastbare Zahlen.

---

## Stand: 28. August 2026

**UX-Pass über alle fünf Szenen.** Anlass war ein Klippfehler auf dem
Leaderboard: die fünfte Bestenlisten-Zeile und die Abbruch-Rückfrage
überdeckten sich um 528 × 30 px, sichtbar erst ab fünf Einträgen in der DB.
Der Fehler war kein Zahlendreher, sondern eine fehlende Invariante — eine
datenabhängig lange Liste und ein Overlay teilten sich denselben Raum ohne
Absprache.

Vier Änderungen, alle in „UI-Layout" ausgeschrieben:

1. **Footer-Band** (`FOOTER_Y`, `SAFE_BOTTOM`, `footer()`) — eine Zeile pro
   Szene an derselben Stelle für die vier Knöpfe. Die Rückfrage *ersetzt* sie,
   statt daneben zu stehen: damit kann die Fehlerklasse nicht wiederkommen.
2. **Preiszeile statt Preistabelle** in `DisplayScoreScene` — die ArUco-ID-Spalte
   ist raus, die Werte sind sortiert, und gelb sind die, die tatsächlich lagen.
3. **`BEST — LOWEST WINS`** über beiden Bestenlisten, und `TOP 10!` heißt jetzt
   `ENTER YOUR NAME` — die alte Überschrift versprach ein Gate, das es nicht gibt.
4. **`OFF BY` in der Runde** — die Differenz, die der Besucher vorher im Kopf
   bilden musste, steht jetzt groß da. `PERFECT n` erbt denselben Platz.

Dazu ein **Layout-Selbsttest** in `scenes.py` nach der Hauskonvention:
`uv run game/scenes.py` → `ok`. Er fängt jeden `draw()`-Aufruf ab und prüft
Bildgrenzen, `SAFE_BOTTOM` und Überdeckung über alle Szenen und Zustände.
Gegengeprüft, dass er scheitern kann.

---

## Stand: 27. August 2026

**Was läuft:** Das Skelett ist durchklickbar. Alle vier Szenen zeichnen nach dem
Layout unten, `FakeDetector` liefert wechselnde Zahlen, SQLite speichert und
sortiert richtig. Die sechs Befunde in `scenes.py` sind behoben (siehe unten).

Seit heute steht außerdem die Optik: **Press Start 2P** als Schrift, die
Farb-ID auf HPI-Rot und -Orange, und das **CRT-Overlay** mit Wölbung,
Scanlines und Vignette. Beides in eigenen Abschnitten weiter unten.

Quellcode liegt seit heute in `game/`. Kein Import ändert sich dadurch:
`uv run game/main.py` setzt `sys.path[0]` auf `game/`, also finden die Module
sich weiterhin flach. Der Ordner bildet die Prozessgrenze aus
„Prozess-Architektur" ab — ein späteres `teleop/` steht daneben, nicht darin.

| Datei | Zustand |
|---|---|
| `game/config.py` | fertig — Zeiten, Farben, Schrift, CRT, Keymap, Werte, Hardware-Konstanten |
| `game/app.py` | fertig — `Ctx`, `SceneBase`, `action_of`, `run_game`, CRT-Overlay |
| `game/assets/` | Press Start 2P (SIL OFL) + `OFL.txt` |
| `game/scenes.py` | **fünf** Szenen inkl. `render()`, `footer()`, Layout-Selbsttest (`uv run game/scenes.py` → `ok`) |
| `game/db.py` | fertig, mit `assert`-Selbsttest (`uv run game/db.py` → `ok`) |
| `game/hw.py` | `FakeDetector`, `Camera` (mit Warmup-Guard), `ArucoDetector`, `CameraView`, `VideoView` fertig; `Buttons` offen |
| `game/main.py` | fertig — Verdrahtung, vier Fontgrößen aus `FONT_SIZES` |
| `game/music.py` | fertig — Notation, Synthese, Ducking, `Ctx.music`, Selbsttest (`uv run game/music.py` → `ok`) |
| `game/balance.py` | fertig — Zielwert-Findung aus dem Tablett, Selbsttest (`uv run game/balance.py` → `ok`) |

### Befunde in `game/scenes.py` — erledigt

Die sechs Befunde vom 27. August (doppeltes `handle`, fehlendes `self.top`,
`tray_sum()` im falschen Block, `top(TOP_N)` statt `top(5)`, Magic Number
`3.0`, Sprachmix) stehen alle behoben im Code. Nachgeprüft am selben Tag,
headless durchgespielt: Idle → Runde → Score → Initialen → Idle, der Name
steht danach in der Bestenliste.

`scenes.py` und `app.py` mischten Tabs und Leerzeichen; alle Dateien in `game/`
stehen jetzt auf vier Leerzeichen (`expand -t4`). Die Mischung war keine
Kosmetikfrage, sondern eine Falle für jedes Werkzeug, das die Datei anfasst.

### Arbeitsweise in diesem Projekt

**Ablauf pro Feature — vier Schritte, in dieser Reihenfolge:**

1. **Vadim fragt nach einem Feature.**
2. **Der Assistent überlegt und präsentiert** — Lösungsweg, die Alternativen die
   er verworfen hat und warum, und den Code. Dazu eine *kurze* Erklärung der
   Stellen, an denen etwas Neues passiert. Kurz heißt kurz: wenn die Erklärung
   länger ist als der Code, stimmt etwas mit dem Code nicht.
3. **Vadim gibt Freigabe** — oder korrigiert die Richtung. Ohne Freigabe wird
   keine `.py`-Datei angefasst.
4. **Der Assistent implementiert** und sagt hinterher, was tatsächlich geprüft
   wurde und was nicht.

Der Punkt an Schritt 2 und 3 ist nicht die Genehmigung, sondern dass die
Entwurfsentscheidung einmal ausgesprochen wird, bevor sie im Code steht. Ein
Feature, das man nicht in fünf Sätzen erklären kann, ist zu groß geschnitten.

Für Vorschläge gilt die Reihenfolge aus dem Ladder-Prinzip: braucht es das
überhaupt → Standardbibliothek → natives Plattform-Feature → vorhandene
Abhängigkeit → eine Zeile → erst dann eigener Code.

Dieses Dokument pflegt der Assistent laufend mit. Es ist in Arbeitssprache
Deutsch geschrieben; **alles, was auf dem Bildschirm des Automaten steht, ist
Englisch** (siehe „Anzeigesprache").

### Reihenfolge ab hier

Regel: nach jedem Schritt läuft etwas, und jeder Schritt ist am Bildschirm zu
sehen. Schritt 1–3 sind heute machbar, 4–5 brauchen Hardware.

1. ~~Befunde 1–5 beheben~~ — erledigt, Meilenstein 1–4 steht.
2. ~~`music.py`~~ — erledigt, siehe „Sound". Offen bleibt das Abhören auf dem
   Automatenlautsprecher: Lautstärken sind am Kopfhörer gesetzt, die Halle ist
   lauter. Die Melodien stehen als Zeichenketten in `PIECES` — nachbessern ist
   eine Zeile ändern, kein Umbau.
3. ~~CRT-Overlay in `run_game`~~ — erledigt, inklusive Wölbung und Pixelfont.
   Die Bildrate ist seit dem 10.9.2026 abgenommen: 30 fps stabil mit laufender
   Teleop, siehe „Messung auf dem Pi". Offen bleibt die Einstellung in der
   Halle (`SCANLINE_ALPHA`, `VIGNETTE_ALPHA`).
4. ~~`Camera` + `ArucoDetector`~~ — erledigt, inkl. Passthrough-Inset. Offen
   bleibt die Erkennungsrate gegen die *gedruckten* Marker unter Hallenlicht.
5. Teleop-Prozess: Torque-Zustandsmaschine, Heartbeat-Empfänger, Weckrampe.
6. `Buttons` (GPIO), LEDs, systemd.

Nicht dazwischenschieben: `db.qualifies()` als Gate vor dem Leaderboard
(Balancing-Frage, siehe Offene Punkte). Der Demo-Clip hat seinen Platz
(`HowToScene`, `DEMO_VIDEO` in `config.py`) und wartet nur noch auf einen
Aufbau zum Filmen — bis dahin läuft die Szene als Textseite.

---

## Was

Ein Arcade-Automat mit echtem Roboterarm. Besucher steuern per Teleoperation einen SO-101-Follower-Arm und lösen ein Wertschätzungsspiel gegen die Uhr. Auftragsarbeit für eine MINT-Messe zur Anwerbung prospektiver HPI-Studierender.

Der Arcade-Rahmen ist keine Deko, sondern die Bedienungsanleitung: Jeder versteht einen Spielautomaten sofort. Kein Erklärtext, kein Personal nötig, um den Einstieg zu erklären.

## Spielmechanik

Adaptiert von Googles *Price-a-Tray* (GDC-Demo). Ablauf:

1. Das Tablett ist leer. Daneben liegt die Auslage: zehn Cupcakes, jeder mit einem verdeckten Preis.
2. Auf dem Display steht ein Zielpreis, z. B. `GOAL €6.30`.
3. 30 Sekunden: Cupcakes auf das Tablett legen (und wieder herunter, wer sich vertut).
4. Während der Runde steht **keine Punktzahl** auf dem Schirm, nur der Preis. Über und unter zählen gleich — es gibt kein Scheitern, nur eine Zahl. Stimmt die Summe `PERFECT_HOLD` Sekunden lang, endet die Runde vorzeitig — die Hände liegen am Leader-Arm, ein „Fertig"-Knopf wäre unerreichbar.
5. Danach dreht der Score-Screen die Punktzahl hoch, wie eine Boxmaschine. Siehe „Wertung".
6. Darunter: Reveal der gesamten Preistabelle. Lernmoment und zweite Belohnung.

Der Skill liegt im Rückschluss („was war das Ding wert?"), nicht in der Feinmotorik. Das ist bewusst so gewählt — der Arm hat zu viel Getriebespiel für ein Präzisionsspiel.

**Leeres Tablett und 30 Sekunden** sind die zentrale Anpassung gegenüber Google: teleoperierte Picks dauern 10–20 s statt 1–2 s mit der Hand, also sind zwei Züge eine volle Runde. Das Tablett wird nach jeder Runde geräumt — damit startet jeder bei demselben Zustand, und niemand erbt die Aufgabe seines Vorgängers.

Bis zum 11. September war es umgekehrt gedacht (vorbeladenes Tablett, tauschen statt aufbauen, 60 s). Das Räumen zwischen den Runden hat es gekippt: wer leer anfängt, kann nicht tauschen.

## Arcade-Framing

| Element | Umsetzung |
|---|---|
| Kabinett | Aluminium-Extrusion-Box (Follower innen), Leader-Arm davor auf Podest |
| Marquee | Beleuchtetes Schild oben, Spieltitel + HPI-Logo. Physisch, nicht auf dem Screen |
| Attract Mode | Bei Leerlauf: LED-Loop am Kabinett, Display zeigt High Scores im Wechsel mit Titel. **Der Arm bewegt sich nicht** — siehe „Idle, Cooldown, Strom" |
| Bedienung | **Vier Arcade-Buttons in Kreuzanordnung, sonst nichts.** Rechts = vorwärts/bestätigen, links = zurück/abbrechen, hoch/runter = auswählen. Dieselben vier Knöpfe starten das Spiel, brechen ab und tippen die Initialen. Keine Tastatur, kein Joystick, kein Extra-Startknopf. |
| Timer | Hintergrundfarbe: schwarz bei Start, ab 5 s Restzeit nach HPI-Rot laufend. Aus 8 m lesbar. |
| High Score | Top 10, drei Buchstaben Initialen, Eingabe über dieselben vier Buttons |
| Optik | **Press Start 2P** (Pixelfont, kein Antialiasing), Monospace, hoher Kontrast, schwarzer Grund. Darüber ein **CRT-Overlay** — Wölbung, Scanlines, Vignette, siehe eigener Abschnitt |
| Sound | **Low-Bit-Arcade-Musik**, deklarativ notiert und zur Laufzeit synthetisiert, siehe eigener Abschnitt. Messehalle ist laut — Sound ist Beiwerk, nie Informationsträger. |
| LED-Streifen | Adressierbar, Zustandsanzeige am Kabinett: Idle-Loop, Laufzeit, letzte 5 s, Score-Reveal |
| Not-Aus | Roter Pilzknopf. Funktional nötig, passt visuell perfekt. |

**Anzeigesprache: Englisch.** Entschieden am 27. August 2026. Arcade-Konvention — `PRESS`, `GOAL`, `TIME`, `TOP 10` liest jeder sofort als Automatensprache, auch elf Jahre alt. Deutsche Wörter sind zudem länger, und Breite ist bei Schriftgröße 200 die knappste Ressource auf dem Schirm. Dieses Dokument bleibt Deutsch, die Zeichenketten im Code sind Englisch.

**Lesbarkeit vor Effekt.** Die Zielgruppe steht 3–8 m entfernt in einer hellen Halle. Zielwert, aktuelle Summe und Restzeit sind die drei Zahlen, die immer groß und immer an derselben Stelle stehen. Alles andere ist Beiwerk.

## Hardware

- **Rechner: Raspberry Pi** (Modell noch festzulegen, siehe Offene Punkte)
- SO-101 Follower (12 V STS3215) in der Box, Leader (7,4 V) außen
- **Zwei Kameras:**
  - *Top-Down*, fest montiert, Autofokus und Belichtung fixiert — liefert die Marker-Erkennung
  - *Arm-Kamera*, reiner Passthrough auf dem Display, keine Auswertung — das
    gilt weiterhin, das Overlay liegt nur auf der Top-Down-Kamera
- **Display: Asus MB169CK, 15,6", 1920 × 1080 (16:9).** Am 9.9.2026 per EDID am Pi ausgelesen. **Korrektur:** hier stand vorher „1920 × 1200 (16:10)", das war falsch — die MB169-Reihe ist FHD. Seit dem 10.9.2026 ist die Entwurfsauflösung dieselbe Zahl und `pygame.SCALED` ist raus — die Skalierung mit Faktor 0,9 kostete rund 20 ms pro Bild und die Schärfe der Pixelfont, siehe „Auflösung und Vollbild". Zweites Display optional für Zuschauer
- **Vier Arcade-Buttons** (hoch/runter/links/rechts) an GPIO, plus Not-Aus. **Panel 3 mm** — Snap-in (Sanwa OBSF-30, spezifiziert für 2–4 mm) liegt im Bereich, aber bei Sperrholz sind Schraubtaster (Seimitsu PS-14-KN, OBSN-30) mit Mutter die haltbarere Wahl. Lochmaß 30 mm, Flachstecker 2,8 mm.
- WS2812B-Streifen. Auf Pi 5 funktioniert `rpi_ws281x` nicht (RP1); Optionen: PIOLib, SPI-Weg (`rpi5-ws2812`, `Pi5Neo`) oder Auslagerung auf einen ESP32 mit WLED via UDP/DDP. Letzteres nimmt Timing, Netzteil und Pegelwandlung aus dem Pi.
- 3D-gedruckte Pucks: flacher Boden, tiefer Schwerpunkt, einheitliche Greifrippe, ArUco-Marker plan oben
- Tablett mit Rand

**Kein Jetson.** Die einzige Rechtfertigung für einen Jetson wäre CUDA-Inferenz, und ML ist bewusst nicht im Spiel. Der vorhandene Jetson Nano hängt auf JetPack 4.6 / Ubuntu 18.04 / Python 3.6 fest, LeRobot verlangt Python ≥3.12. Alter Stack, ungenutzte GPU, keine Gegenleistung.

## Software

Python · OpenCV (ArUco) · pygame · SQLite

**ArUco statt Machine Learning.** Marker-IDs mappen deterministisch auf Werte. Kein Training, kein Datensatz, kein Beleuchtungsrisiko, Werte per Dictionary-Reload änderbar. Ersetzt Googles kompletten Vertex-AI-/GCS-Stack.

**pygame statt Browser-Frontend.** Ein Prozess, eine Sprache, kein Chromium, kein Webserver, kein JPEG-Encoding pro Frame. Vollbild direkt über KMSDRM ohne Desktop-Umgebung. Der Arcade-Button kommt als normales Event rein. Preis dafür: Layout ist Handarbeit in Koordinaten, kein CSS. Bei dieser Optik — Monospace, große Zahlen, schwarzer Grund — ist das kein Verlust.

Falls ML am Stand gezeigt werden soll: nur als paralleler Schauwert auf einem zweiten Monitor, **niemals im kritischen Pfad der Spiellogik.**

## Prozess-Architektur

**Zwei getrennte Prozesse. Sie reden nicht miteinander.**

| Prozess | Aufgabe | Abhängigkeiten |
|---|---|---|
| Teleop | Leader lesen → Follower schreiben, ~30–50 Hz konstant | LeRobot (oder Feetech-SDK direkt) |
| Spiel | Kamera → ArUco → Zustand → Rendern | OpenCV, pygame, SQLite |

Die Spiellogik braucht Kamerabild, Marker-IDs, Timer und Buttondruck. Sie braucht **nie** den Armzustand. Der Besucher schiebt Pucks, die Kamera sieht das Ergebnis — der Arm ist reine Eingabemethode.

Konsequenzen:

- Kein gemeinsamer Loop. Rendering darf die Armsteuerung nicht ins Stottern bringen.
- Kein Protokoll zwischen beiden. Nichts zu synchronisieren, nichts zu debuggen.
- Absturz des einen tötet nicht das andere.
- Notfalls laufen sie auf zwei Rechnern. Falls LeRobot auf dem Pi zickt: Teleop auf einem Laptop, Spiel auf dem Pi.

**Teleop läuft durchgehend, nicht pro Runde.** Kein Start von LeRobot aus der Spiellogik heraus. Motorinitialisierung und Kalibrierung bei jedem Besucher wären Sekunden Wartezeit plus ein Absturzrisiko, das mit jeder Runde neu gezogen wird.

**Kamera-Passthrough auf dem Spielbildschirm ist optional.** Der echte Arm ist im Kabinett sichtbar; ein Live-Bild ist aus 8 m Entfernung ohnehin unlesbar. Falls überhaupt, dann als kleines Inset („was die Maschine sieht") in niedriger Auflösung, nie als Hauptfläche.

**LeRobot-Installation:** Python-Version des Pi prüfen. Bookworm liefert 3.11, aktuelles LeRobot verlangt ≥3.12 — dann miniforge/pyenv, oder auf LeRobot 0.4.x pinnen (≥3.10). Auf ARM fällt LeRobot beim Video-Decoding automatisch von TorchCodec auf pyav zurück, das ist erwartet und kein Fehler.

Die Servo-Kalibrierung (Offsets, Drehrichtungen, Endanschläge) wird nicht selbst geschrieben. Genau die Sorte Bug, die stundenlang wie ein Verkabelungsfehler aussieht.

---

## Code-Struktur (Spielprozess)

```
picknplay/
  game/         # Spielprozess, gestartet mit: uv run game/main.py
    main.py     # Verdrahtung: Ctx bauen, Startszene bauen, run_game aufrufen
    config.py   # Konstanten: Zeiten, Farben, Schrift, CRT, Keymap, Werte, Pfade
    app.py      # Ctx, SceneBase, action_of, run_game, CRT-Overlay
    assets/     # PressStart2P-Regular.ttf, OFL.txt
    scenes.py   # IdleScene, GameScene, DisplayScoreScene, LeaderboardScene
    hw.py       # Kamera-Grabber, ArucoDetector, FakeDetector, Buttons, LEDs
    db.py       # SQLite Highscore
    music.py    # Notation -> Square-Wave-Synthese -> pygame.mixer.Sound
  markers/      # generierte ArUco-PNGs
  archive/      # Vorstufen, nicht importiert
  scores.db     # entsteht beim ersten Start, relativ zum Arbeitsverzeichnis
```

**Flach statt Pakete, aber in einem Unterordner.** Der ursprüngliche Plan sah `app/`, `scenes/`, `hw/`, `data/` als Pakete vor. Bei rund 500 Zeilen Gesamtcode kostet das nur `__init__.py`-Rauschen und lange Importpfade; sieben Dateien, die je auf einen Bildschirm passen, sind schneller zu überblicken. Aufteilen, sobald eine Datei das nicht mehr tut.

`game/` ist **kein Paket** — kein `__init__.py`, keine relativen Importe. Python setzt `sys.path[0]` auf das Verzeichnis der gestarteten Datei, also finden sich die Module gegenseitig flach wie vorher. Der Ordner trennt Quellcode von Markern, Archiv und Dokument und markiert die Prozessgrenze: ein späteres `teleop/` steht daneben, denn die beiden Prozesse teilen sich nichts.

**`scenes.py` importiert `hw.py` nie.** Nur `main.py` kennt beide Seiten und steckt sie zusammen. Ein falscher Import fällt damit sofort auf.

### Vier Prinzipien

**Der Loop besitzt die Zeit, die Szene besitzt nur Zustand.**
`clock.tick(fps)` liefert `dt` in Sekunden, der Loop reicht es durch. `update(dt)` rechnet, `render(screen)` zeichnet nur schon Berechnetes. Ein langsamer Frame darf die Spiellogik nicht driften lassen.

**`Ctx` ist eine Naht, kein Container.**
Szenen rufen `self.ctx.detector.tray_sum()` und wissen nie, ob dahinter OpenCV oder eine Attrappe steckt. Damit ist das gesamte Spiel ohne Arm, Kamera und LEDs schreib- und testbar; der Tausch auf echte Hardware ist eine Zeile in `main.py`. Duck Typing, kein Framework.

**Szenen kennen Aktionen, keine Tasten.**
`action_of(event)` übersetzt Pfeiltasten *und* GPIO zu vier Strings: `"up"`, `"down"`, `"left"`, `"right"`. Der Loop übersetzt einmal zentral und ruft `scene.handle(action)`; unbekannte Tasten werden vorher verworfen, damit keine Szene je einen Sonderfall prüfen muss. Tastatur beim Entwickeln, Arcade-Button auf der Messe, Szenen unverändert.

Bewusst *keine* semantischen Namen wie `"start"`/`"back"`. Bei genau vier Knöpfen ohne Beschriftung ist die Richtung die Bedeutung, und eine Zwischenschicht, die `"right"` in `"start"` übersetzt, wäre eine Abstraktion mit genau einer Implementierung. Die Konvention (rechts vorwärts, links zurück) lebt stattdessen in einem Kommentar in `config.py` und wird in jeder Szene gleich angewandt.

`pygame.key.set_repeat()` liefert die Wiederholung beim Halten — nötig, um durchs Alphabet zu scrollen. **Achtung bei der Integration:** GPIO-Callbacks haben keine Auto-Repeat, die muss `hw.py` selbst erzeugen.

**Kein `on_enter`/`on_exit`. Szenen sind Wegwerf-Objekte.**
Jeder Übergang baut eine neue Instanz (`self.switch_to(GameScene(self.ctx))`), also ist `__init__` der Eintrittspunkt und das Ende der Referenz ist der Austritt. Ein zweites Hook-Paar für denselben Moment wäre nur eine weitere Stelle, an der Zustand vergessen werden kann. Der einzige Preis: `__init__` läuft rund einen Frame vor der Aktivierung — bei 60-Sekunden-Runden irrelevant.

**Eine Zeitquelle pro Runde.**
Kein `set_timer` parallel zu einem `t_start`. Die Restzeit ist ein `float` in der Szene, den `update(dt)` runterzählt; aus derselben Zahl folgen Anzeige *und* Übergang. Zwei Uhren laufen auseinander, und das sieht auf einem Automaten mit Publikum nach einem Bug aus, weil es einer ist.

### Szenen und Übergänge

| Szene | Verlässt nach | Ziel |
|---|---|---|
| Idle | `right` | HowTo |
| HowTo | `right` | Game |
| HowTo | `left` oder Timeout | Idle |
| Game | 60 s abgelaufen | Score |
| Game | `left` zweimal innerhalb 3 s | Idle |
| Score | `right` | Leaderboard |
| Score | `left` | Idle |
| Leaderboard | `right` auf dem letzten Feld (speichert) | Idle |
| Leaderboard | `left` auf dem Zurück-Pfeil | Idle |

Die Leaderboard-Eingabe ist ein einzelner Cursor-Index: `0` = Zurück-Pfeil, `1..3` = die drei Buchstaben. `up`/`down` ändern den Buchstaben unter dem Cursor, `left`/`right` bewegen ihn. Dadurch braucht die Szene keinen Eingabemodus — Position *ist* der Modus.

**Jede Nicht-Idle-Szene hat einen Inaktivitäts-Timeout zurück auf Idle.** Besucher gehen mitten in der Eingabe weg; der Automat muss sich ohne Personal selbst zurücksetzen.

### Nebenläufigkeit im Spielprozess

- **Kamera-Grabber und Detection laufen als Threads, nicht als Prozesse.** `read()` und `detectMarkers()` sind C++-Code und geben das GIL frei — ein Thread liefert dort echte Parallelität. Shared Memory zwischen Prozessen wird erst nötig, wenn in Python selbst gerechnet wird.
- **Muster: Thread schreibt in ein Attribut (unter Lock), Loop liest.** Nie umgekehrt.
- **Der Grabber hält immer das neueste Bild**, nicht das älteste. Sonst liefert der V4L2-Puffer alte Frames und die Erkennung hinkt sichtbar hinterher.
- **GPIO-Callbacks laufen in einem fremden Thread.** Tastendruck in eine `queue.SimpleQueue` legen, einmal pro Frame im Loop leeren.
- **LEDs blockieren nie.** `set_state()` kommt sofort zurück — bei WLED ein `sendto`, bei lokalen LEDs ein Worker-Thread mit Zustandsslot.
- **Kern-Zuteilung passiert in der systemd-Unit (`CPUAffinity=`)** auf Prozessebene, nicht im Python-Code. Erst pinnen, wenn gemessen wurde, dass es stottert.

---

## Idle, Cooldown, Strom

Entschieden am 27. August 2026, nachdem die Hardware-Einbindung anstand.

**Im Idle ist der Follower stromlos.** Die STS3215 halten Position über
Dauerstrom gegen die Schwerkraft — das ist die Wärmequelle, und sie verschwindet
nur, wenn das Halten aufhört. Sechs Stunden Messe bei 100 % Einschaltdauer sind
der sichere Weg, den Gripper-Servo zu verlieren. Mit Abschaltung zwischen den
Runden werden aus 100 % rund 67 % (60 s Runde von 90 s pro Besucher), und die
Pausen sind gleichmäßig über den Tag verteilt.

**Preis dafür: der Arm fällt.** Es braucht eine Pose, in der er stromlos stabil
steht und nicht auf das Tablett kippt. Das ist ein Konstruktionsauftrag
(Anschlag oder Ablage), keine Software-Aufgabe, und es blockiert die
Torque-Abschaltung bis es gelöst ist.

**Die Attract-Mode-Armbewegung ist gestrichen.** Sie stand im Widerspruch zur
Zeile darüber: eine Idle-Bewegungsschleife ist 100 % Einschaltdauer in genau
den Phasen, in denen niemand spielt — der größte Wärme- und Verschleißposten
des Standes, für Publikum, das gerade nicht da ist. Die Bewegung im Attract
Mode machen die LEDs. Sie sind aus 8 m ohnehin besser sichtbar als ein Arm im
Kabinett.

**Aufwecken ist die gefährliche Stelle.** Follower stromlos, Besucher stellt den
Leader irgendwohin, Torque an — der Follower springt schlagartig auf die
Leader-Pose. Die Reihenfolge, die das verhindert: Goal-Position auf die
**Ist-Position** des Followers setzen, *dann* Torque einschalten, dann das Goal
über ~1,5 s zur Leader-Pose rampen. Ohne diese drei Schritte hat man
Servowärme gegen einen Ruck pro Besucher getauscht, 240-mal am Tag. Eine
EEPROM-Drehmomentgrenze hilft dagegen nicht — der Sprung passiert innerhalb des
erlaubten Moments.

**Die Prozessgrenze bekommt genau einen Kanal.** „Roboter im Idle aus" heißt,
dass das Spiel dem Teleop-Prozess seinen Zustand mitteilen muss. Gewählt: ein
UDP-Datagramm an localhost, ein paar Mal pro Sekunde, Inhalt ist der
Szenenname. Einseitig, verlustfest, ohne Verbindung und ohne Protokoll.

Die entscheidende Eigenschaft ist nicht der Mechanismus, sondern die Auslegung:
**kein Paket bedeutet „aus".** Stirbt der Spielprozess, hängt die Kamera, wird
ein Kabel gezogen — dann kühlt der Arm ab, statt unbeaufsichtigt durchzuheizen.
Ein Kanal, bei dem Stille als „letzter Zustand gilt weiter" gelesen wird,
verwandelt jeden Absturz in sechs Stunden Dauerlast. Teleop wartet nie auf das
Spiel; das wäre die Kopplung, die die Zwei-Prozess-Architektur vermeiden soll.

**Cooldown ist kein Spielmechanismus.** Die Servos führen ihre Temperatur in
einem Register; gelesen wird sie mit 1 Hz, nicht im Teleop-Takt — Temperatur
ändert sich über Zehner-Sekunden, und jeder Read kostet Buszeit im
30–50-Hz-Zyklus. Der Wert geht ins Log und auf die LED-Farbe. Erst an einer
harten Grenze schaltet der Teleop-Prozess das Drehmoment ab, unabhängig vom
Spielzustand. Bewusst *keine* Runden-Sperre: „bitte warten" ist am Messestand
mit Warteschlange ein sichtbarer Ausfall, und wenn die harte Grenze greift, ist
ohnehin etwas anderes kaputt.

**Kerne: nur Teleop wird gepinnt.** `CPUAffinity=3` und `Nice=-10` in der
Teleop-Unit, `CPUAffinity=0-2` für das Spiel. Der Teleop-Loop ist CPU-leicht —
er wartet auf dem seriellen Bus —, aber terminkritisch: verspätete Zyklen sieht
man als Ruckeln im Arm. Das sind zwei verschiedene Probleme; Affinität löst
„darf nicht verdrängt werden", Priorität löst „darf nicht zu spät kommen".
IRQ-Affinität bleibt liegen, bis gemessen ist, dass sie fehlt.

Was Pinning **nicht** trennt: Speicherbandbreite, den USB-Host-Controller und
das Wärmebudget. Throttelt der Pi, sinkt der Takt für alle vier Kerne
gleichzeitig — auch für den gepinnten Teleop-Loop.

**Not-Aus trennt die 12-V-Schiene physisch.** Ein Pilzknopf, den eine
Python-Schleife per GPIO abfragt, ist kein Not-Aus, sondern ein Knopf: wenn der
Prozess hängt — der Fall, gegen den man sich absichert — tut er nichts. Die
Software-Aufgabe daran ist nicht das Auslösen, sondern das saubere Hochfahren
danach, denn der Follower steht dann irgendwo (siehe Weckrampe).

**LEDs bleiben auf dem ESP32.** WLED über UDP nimmt Timing, Pegelwandlung und
das Netzteil aus dem Pi. Ein WS2812B-Strang ist bei Vollweiß mit ~60 mA pro LED
der größte Einzelverbraucher am Stand, deutlich vor dem Pi —
Helligkeitsbegrenzung ist damit Powermanagement und Wärmemanagement in einer
Zahl.

**Zwei Fehlerbilder, die am Messetag garantiert falsch diagnostiziert werden:**
Unterspannung am Pi zeigt sich als Drosselung *und* als USB-Aussetzer — „die
Kamera fällt sporadisch aus" ist meist die Stromversorgung, nicht der Code. Und
Einschaltstrom: alles gleichzeitig am selben Schalter kann Netzteile in die
Strombegrenzung treiben, dann startet der Automat „manchmal nicht", was nach
Software aussieht.

**Der Idle-Screen rendert mit 20 FPS statt 60** (`IDLE_FPS` in `config.py`,
`TICK` als Klassenattribut der Szene). Er zeigt einen Text, der zweimal pro
Sekunde blinkt, und eine Bestenliste, die sich gar nicht ändert — dafür 60-mal
pro Sekunde 2,3 Megapixel durch die Barrel-Distortion zu schieben ist sechs
Stunden Wärme in einem geschlossenen Alu-Kabinett, für ein Bild, das niemand
ansieht. Der unsichtbarste Hebel im ganzen Projekt und der billigste.

Aktive Kühlung und ein Luftweg im Kabinett bleiben trotzdem erste Ordnung; jede
Software-Sparmaßnahme ist zweite.

### Was gemessen werden muss

- Haltestrom und Servotemperatur des Followers in Arbeitspose, mit Puck im
  Gripper, über 10 Minuten
- Ob und wo der Arm stromlos stabil steht
- Beide Kameras gleichzeitig am realen Pi, in den Formaten, die gewählt werden
- Pi-Temperatur im geschlossenen Kabinett unter Volllast
- Teleop-Zykluszeit-Jitter, gemessen *während* das Spiel rendert — vorher ist
  jede Aussage über Kerne geraten

### Kamera und Passthrough (umgesetzt am 27. August)

`Camera` ist ein Grabber-Thread mit `BUFFERSIZE=1`, `ArucoDetector` ein zweiter
Thread mit `DETECT_HZ`. Zwei Threads statt einem, weil auf dem Entwicklungsrechner
*eine* Webcam beides bedient: liefe die Erkennung im Grabber-Thread, würde die
Bildrate des Passthrough an der Erkennungsdauer hängen.

**Format vor Auflösung.** `MJPG` wird gesetzt, bevor Breite und Höhe gesetzt
werden. Als YUYV kostet 720p ein Vielfaches an USB-Bandbreite, und genau daran
entscheidet sich, ob zwei Kameras an einem Controller laufen.

**`Camera` scheitert laut**, wenn sich das Gerät nicht öffnen lässt, statt
leise auf `FakeDetector` zurückzufallen. Erfundene Zahlen auf dem Automaten
wären am Messestand nicht als Fehler zu erkennen; ein Startabbruch ist es.

**Passthrough nur in der `GameScene`**, beide Bilder 800 × 450 nebeneinander.
Im Idle bleibt die USB-Bandbreite frei und der Pi kalt — dieselbe Regel wie bei
den Servos. Gemessen 1,5 ms pro Frame fuer die ganze Szene inklusive beider
Panes; `CameraView` konvertiert nur, wenn die Kamera wirklich ein neues Bild
geliefert hat (Sequenzzaehler in `Camera`). Seit die Zielbildrate auf 30 steht,
laufen Quelle und Rendern gleich schnell und der Zaehler spart selten etwas —
er bleibt trotzdem: er kostet einen Vergleich und deckt den Fall ab, dass eine
Kamera einbricht oder haengt.

**`CAM_INDEXES` ist ein Paar**, `(Arm, Top-Down)`. Stehen zweimal dieselbe 0
darin, oeffnet `main.py` das Geraet trotzdem nur einmal (`set()`) und speist
beide Panes aus einem Grabber — das ist der Layout-Mock mit einer Webcam.
Echte Hardware ist `(0, 1)`, eine Zahl. Der Detector haengt immer an der
zweiten, der Top-Down-Kamera. `pygame.image.frombuffer(..., "BGR")` spart das `cvtColor`,
pygame-ce nimmt OpenCVs Kanalreihenfolge direkt an.

### Befund: Race in `tray_sum()` (behoben)

`seen` wurde vom Detector-Thread beschrieben und vom Render-Loop ohne Lock
gelesen. Ein Update auf einen bestehenden Schlüssel ist harmlos, ein **neuer**
Schlüssel während der Iteration nicht: `RuntimeError: dictionary changed size
during iteration`. Reproduziert, nicht theoretisch. Der Moment, in dem es
zuschlägt, ist genau der, in dem ein Marker zum ersten Mal auftaucht — also
mitten in der Runde. Pro Runde unwahrscheinlich, über 240 Besucher nicht.
`fresh()` hält jetzt einen `threading.Lock`.

### Overlay auf der Top-Down-Kamera

**Nur das Top-Down-Pane bekommt einen Detector.** Die Arm-Kamera bleibt reiner
Passthrough — sie sieht das Tablett aus einem anderen Winkel, dort gälten die
Ecken nicht, und ein zweiter Detector kostete Rechenzeit für Dekoration.
`CameraView(cam, det=None)` trägt die Zuordnung: das Pane weiß, ob es etwas
einzublenden hat.

**Die Preise stehen seit dem 11. September nicht mehr im Bild.** Bis dahin
zeichnete das Overlay den Wert jedes erkannten Markers auf den Schwerpunkt
seiner vier Ecken. Das war ein Widerspruch zur Grundregel des Spiels: „EVERY
TREAT HAS A HIDDEN PRICE" — wer die Preise während der Runde ablesen kann,
rechnet, statt zu schätzen, und der Reveal am Ende verliert seinen
Lernmoment. Aus 8 m las das ohnehin niemand; am Automaten, wo die Hände am
Leader-Arm liegen und der Schirm eine Armlänge entfernt ist, schon.

Der Code steht auskommentiert in `GameScene.overlay`, weil er beim Einrichten
der Kamera das Einzige ist, was zeigt, *welchen* Marker die Erkennung sieht und
nicht nur, dass sie einen sieht. `MARK_FONT` in `config.py` existiert nur noch
dafür.

Übrig bleibt das Detektionsfenster — Chrome in `GREY`, kein Spielwert.

**Verdeckte Marker bleiben stehen**, exakt so lange wie in der Summe: `TOTAL`
und die Summe lesen dieselbe `MARKER_HOLD`-Frist aus derselben Momentaufnahme,
die `update()` einmal pro Frame zieht. Sie können gar nicht widersprechen.

### Detektionsfenster (`TRAY_ROI`)

Die Top-Down-Kamera ist Weitwinkel und sieht den halben Messestand mit.
`TRAY_ROI` begrenzt die Erkennung auf ein Rechteck in Bildanteilen.

**Umgesetzt als Zuschnitt, nicht als Filter.** Der Detector schneidet den
Ausschnitt aus dem Frame (eine numpy-Sicht, keine Kopie) und erkennt nur darin.
Das erledigt beides in einem Schritt und ist billiger: gemessen **1,21 ms statt
2,00 ms** pro Durchlauf bei 60 % × 70 %. Ein Marker am Bildrand verschwindet
dabei von selbst, statt erkannt und danach verworfen zu werden.

Die Ecken kommen anschließend zurück auf Anteile am *ganzen* Bild gerechnet,
damit die Szene nur mit dem Pane-Rechteck multiplizieren muss.

**Das Rechteck steht in `GREY` im Bild** — Chrome, kein Spielwert, deshalb nicht
Gelb. Es ist sichtbar, weil man `TRAY_ROI` beim Ausrichten der Kamera in der
Halle einstellt und sonst blind justieren müsste. Gleiche Regel wie
`SCANLINE_ALPHA`.

**Fremde Marker-IDs werden verworfen.** Was nicht in `VALUES` steht, gehört
nicht zum Spiel — ein ausgedruckter Testbogen auf dem Tisch kann damit keine
Punkte erzeugen.

### Ton bei neuer Erkennung

`"blip"` in `SFX`: eine einzelne hohe Note, `duty=0.125`, `vol=1200` gegen 2600
bei `"ok"`, 200 ms. Kein Recycling des Knopftons — sonst klingt ein Puck wie ein
Knopfdruck und der Signifier-Mechanismus verliert seine Eindeutigkeit.

Ausgelöst wird bei **neu erkannt**, nicht bei sichtbar, sonst feuert es
`DETECT_HZ`-mal pro Sekunde. Der Vergleich steht in `GameScene.update`, eine
Mengendifferenz gegen den letzten Frame. Damit fällt zweierlei von selbst
heraus: fünf Pucks gleichzeitig geben **einen** Ton, und ein kurz verdeckter
Marker piept nicht erneut, weil ihn die Hysterese gar nicht erst verlässt.

Die Logik steht in der Szene, nicht im Thread — `hw.py` importiert weiterhin
kein `music`, und „Thread schreibt, Loop liest" bleibt unverletzt.

**`INTER_LINEAR` statt `INTER_AREA`:** gemessen 0,17 ms statt 3,5 ms pro Frame.
AREA mittelt beim Verkleinern über alle Quellpixel und ist bei Faktor 3
zwanzigmal teurer. Hinter Scanlines sieht das niemand — 3,5 ms wären auf dem Pi
ein Fünftel des Frame-Budgets für ein Inset, das laut Layout-Prinzip Beiwerk
ist.

---

## UI-Layout

### Auflösung und Vollbild

**Entwurfsauflösung = Panelauflösung: 1920 × 1080, Asus MB169CK.**
Am 10. September 2026 dorthin umgezogen. Jede Koordinate in `scenes.py` ist eine
absolute Zahl für dieses Raster; auf dem Zielmonitor ist die Abbildung 1:1, es
wird nichts skaliert und nichts weichgezeichnet. Was man hinschreibt, steht da.

**`pygame.SCALED` ist raus.** Bis zum 9.9. stand die Entwurfsauflösung auf
1920 × 1200, also auf einem Panel, das es nicht gibt — die 16:10-Angabe war
falsch —, und `SCALED` rechnete jedes Bild auf 1080 herunter. Das kostete
gemessen rund 20 ms pro Bild, mehr als CRT und Wölbung zusammen, und es legte
die 8 × 8-Pixelschrift auf ein Raster mit Faktor 0,9: ungleich große
Glyphenpixel, also genau der Fehler, gegen den die Schriftgrößen alle durch 8
teilbar sind.

```python
flags = pygame.FULLSCREEN if FULLSCREEN else 0
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=VSYNC)
except pygame.error:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.mouse.set_visible(False)
```

Das `try` ist kein Zierrat: `vsync` ohne `SCALED` ist backendabhängig, und ein
Automat, der am Messetag mit einer Exception statt mit einem Bild startet, ist
schlechter als einer mit Tearing. `PNP_VSYNC=0` schaltet es zum Nachmessen ab.

`vsync` verhindert Tearing beim Farbverlauf des Timers, der einzigen Stelle, an
der sich pro Frame eine große Fläche ändert. Es kostete bei 60 Hz gemessen 12
bis 19 %; bei 30 fps ist das Budget da. `set_visible(False)` nimmt den
Mauszeiger weg, der im Vollbild sonst mitten im Bild stehen bleibt.

**`FULLSCREEN` ist ein Schalter in `config.py`**, kein fester Wert: beim
Entwickeln aus (Fenster, `q` beendet), am Automaten an. Ein Flag, zwei
Betriebsarten, keine zweite Codebasis.

**Konsequenz:** ein anderes Panel heißt jetzt Layout anfassen, nicht mehr Flag
setzen. Das ist der bewusst gezahlte Preis — die Rückfallebene kostete das
Vierfache dessen, wogegen sie versicherte, und der Monitor ist gesetzte
Hardware.

**Zielbildrate 30, nicht 60.** Zwei Gründe, beide unabhängig von der
Rechenleistung. Erstens teilt 30 die 60 Hz des Panels glatt: jedes Bild steht
exakt zwei Refreshes lang. Bei 40 fps wäre 60/40 = 1,5, also abwechselnd ein
und zwei Refreshes — sichtbares Ruckeln bei *höherer* Bildrate. Unterhalb von
60 ist 30 die einzige gerade Zahl. Zweitens liefern die Kameras 30 Bilder/s;
alles darüber zeigt in der Runde dasselbe Kamerabild zweimal. Es gibt in diesem
Spiel keine 60-Hz-Bewegung: Sekundenzähler, Summe, blinkender Text, Kamerabild.
Der Arcade-Look kommt aus Scanlines, Wölbung und harten Pixelkanten, nicht aus
der Bildrate. `IDLE_FPS` steht auf 15, der Hälfte davon, damit die Kadenz auch
im Idle gerade bleibt.

### Schriftgrößen

`big` 168, `mid` 88, `small` 48, `tiny` 32 — alle durch 8 teilbar, Begründung
im eigenen Abschnitt weiter unten.

### Koordinaten

Alle Koordinaten für **1920 × 1080**, Bildmitte x = 960. Zeichnen ist Handarbeit in Zahlen — das ist der bewusst gezahlte Preis für pygame statt CSS. Damit es nicht in Magic Numbers ausartet, gelten drei Regeln:

- **Ein Helfer, kein Layoutsystem.** `draw(screen, font, text, x, y, color)` zeichnet einen Text zentriert auf `(x, y)`. Zentriert, nicht linksbündig, weil Zahlen ihre Breite ändern (`9` → `10`) und ein linksbündiger Wert dann sichtbar springt.
- **`font.render(text, False, color)`** — der zweite Parameter ist Antialiasing, und der muss `False` sein. Ein Pixelfont mit Kantenglättung sieht aus 8 m matschig aus statt scharf.
- **Farbe trägt Bedeutung, nicht Dekoration.** Sechs Farben, eine Leiter von leise nach laut, jede mit genau einem Job. Solange das gilt, ist „welche Farbe nehme ich hier" keine Entscheidung mehr, sondern eine Nachschlagung.

> **Seit 11.9.2026 („Sugar Rush"):** `BLACK` heißt `BG` und ist `#28101E`
> (dunkle Schokolade), `YELLOW` heißt `ACCENT` und ist `#FF65BD` (Pink),
> `WHITE` ist `#FFECF6` (Sahne), `GREY` ist `#B0809E`. Die Jobs sind dieselben.
> Neu ist `CANDY` — Bonbonfarben für Titel und Streusel, nie für Spielwerte.
> Die Tabellen in diesem Abschnitt nennen noch die alten Namen.

| Farbe | Hex | Job |
|---|---|---|
| `BLACK` | `#000000` | Grund, immer |
| `GREY` | `#787878` | Beschriftungen (`GOAL`, `TOTAL`) |
| `WHITE` | `#F0F0F0` | neutrale Werte |
| `YELLOW` | `#FFC800` | was der Besucher *gerade* beeinflusst |
| `ORANGE` | `#DE6207` | Warnung — HPI-Orange |
| `RED` | `#B1073A` | die letzten Sekunden — HPI-Rot |

Rot und Orange sind aus dem HPI-Logo-SVG gezogen, nicht geschätzt. `YELLOW` ist heller als das HPI-Gelb `#F7A900`, weil auf Schwarz aus 8 m das hellere gewinnt und man den Unterschied neben dem Logo nicht sieht. `GREEN` und `DARKRED` sind entfallen: Grün ist nicht HPI, und ein grüner Grund widerspricht „schwarzer Grund". `ORANGE` hat noch keinen Ort im Code — die Abbruchwarnung in `GameScene` ist der offensichtliche.

### Schriftgrößen

`main.py` baut ein Dict und legt es in `Ctx.fonts`. Vier Größen reichen, mehr sind nur Entscheidungen ohne Nutzen.

| Schlüssel | Größe | Wofür |
|---|---|---|
| `big` | 168 | Die Zahlen, die aus 8 m lesbar sein müssen |
| `mid` | 88 | Restzeit, Überschriften |
| `small` | 48 | Beschriftungen, Bestenliste |
| `tiny` | 32 | Steuerungshinweise, Preistabelle |

**Die Schrift ist Press Start 2P** (SIL OFL, liegt in `game/assets/`) — die literale Arcade-Font, den NAMCO-Automaten der 80er nachgezeichnet. Ausgewählt am 27. August 2026 gegen VT323, Silkscreen und Silkscreen Bold. Kriterium war Breite pro Ziffernhöhe, weil Breite bei diesen Größen die knappste Ressource auf dem Schirm ist:

| Font | Größe für 200 px Ziffern | `"180"` | `"PICK'N'PLAY"` |
|---|---|---|---|
| **Press Start 2P** | 228 | 628 px | 2480 px |
| VT323 | 357 | 378 px | 1547 px |
| Silkscreen | 320 | 600 px | 2240 px |
| Silkscreen Bold | 320 | 720 px | 2680 px |

VT323 ist mit Abstand die schmalste und wäre die naheliegende Wahl gewesen — aber ihre Striche sind ein Designpixel dünn, und dünn verliert aus 8 m in heller Halle. Press Start 2P hat die dicksten Striche und wird nur beim Titel breit, und der Titel ist die eine Zeichenkette, die niemand unter Zeitdruck lesen muss.

**Warum diese vier Zahlen.** Press Start 2P hat ein **8 × 8-Raster**: Schriftgröße ÷ 8 ist die Kantenlänge eines Glyphenpixels. Nur Vielfache von 8 sind pixelgenau, alles andere macht die Pixel *innerhalb* einer Glyphe ungleich groß. `big 168` trifft die Ziffernhöhe des alten Platzhalters fast genau (147 px statt 154) und lässt `PICK'N'PLAY` 1848 px breit werden — 36 px Rand, für ein Marquee genau richtig.

Alle 17 Zeichenketten aus `scenes.py` sind gegen ihre verfügbare Breite geprüft, keine läuft über: **keine Koordinate ändert sich.** `main.py` baut das Dict jetzt in einer Zeile aus `FONT_SIZES`.

Die Pfeilzeichen `▶ ◀ ▲ ▼` existieren in der Font (nachgesehen, nicht vermutet), ebenso Umlaute und `€`. **Seit dem 27. August sind sie überall im Einsatz**, die ASCII-Behelfe `<`, `>`, `^v` sind raus. Die Glyphen sind gefüllte Dreiecke auf demselben 8 × 8-Raster wie alles andere — ein selbstgezeichnetes `pygame.draw.polygon` war zwischenzeitlich im Code und flog wieder raus: es bricht das Pixelraster, skaliert nicht mit der Schriftgröße und ist Code für etwas, das die Font schon kann.

**`pygame.font.Font(pfad, größe)` mit mitgelieferter TTF ist auf dem Pi robuster als `SysFont`** — kein fontconfig, keine Frage, welche Schriften auf dem Raspberry-OS-Image liegen. Das Repository wird 118 kB schwerer und ist dafür reproduzierbar. Der Pfad wird aus `__file__` gebaut, nicht relativ zum Arbeitsverzeichnis, sonst bricht der systemd-Start.

### Footer-Band (28. August)

Zwei Konstanten in `config.py` und ein siebenzeiliger Helfer in `scenes.py`:

```python
FOOTER_Y    = 1000   # die eine Zeile, die sagt was die Knoepfe tun
SAFE_BOTTOM =  920   # kein Szeneninhalt darunter. Nie.
```

**Der Anlass war ein echter Klippfehler.** Die fünfte Bestenlisten-Zeile lag
auf y 1096…1144, die Rückfrage `PRESS ◀ AGAIN TO DISCARD` auf 1114…1146 —
528 × 30 px Überdeckung. Sichtbar wurde sie erst, als die DB fünf Einträge
hatte, deshalb „klippt manchmal". Ursache war nicht die Zahl 1130, sondern
dass eine *datenabhängig lange* Liste und ein Overlay sich denselben Raum
ohne Absprache teilten.

**Die Rückfrage ersetzt die Hinweiszeile, statt daneben zu stehen.** Damit
kann nichts mehr kollidieren — nicht weil die Zahlen jetzt passen, sondern
weil es kein zweites Element gibt. Und es ist die bessere Rückmeldung: die
Antwort auf einen Knopfdruck erscheint dort, wo ohnehin steht, was der Knopf
tut. Vorher standen Cursor `◀` (510, 470) und seine Antwort 660 px auseinander.

Beide Zahlen sind **Abstände von der Unterkante**, nicht Anteile der Höhe: das
Band ist eine feste Zeile am Bildrand und skaliert nicht mit. Beim Umzug auf
1080 blieben sie deshalb bei 80 und 160 px vom Rand — verschoben hat sich nur
der Szeneninhalt darüber.

```python
footer(screen, f, left=None, right=None, note=None)
```

`note` gelb und zentriert, sonst `left` bei x = 600 und `right` bei x = 1320,
beide `tiny` / `GREY`. **Pfeil immer zuerst** (`◀ BACK`, `▶ NEXT`) — die
Richtung trägt die Position im Footer, nicht die Wortstellung. Vorher
spiegelte `◀ BACK  START ▶` und `▲▼ LETTER ◀▶ FIELD` spiegelte nicht.

| Szene | links | rechts | `note` |
|---|---|---|---|
| `HowToScene` | `◀ BACK` | `▶ START` | — |
| `GameScene` | `◀ QUIT` | — | `◀ AGAIN TO QUIT` |
| `DisplayScoreScene` | `◀ BACK` | `▶ NEXT` | — |
| `LeaderboardScene` | `▲▼ LETTER`, bei `cursor == 0`: `◀ DISCARD` | `▶ SAVE` bei `cursor == 3`, sonst `▶ NEXT` | `◀ AGAIN TO DISCARD` |

`IdleScene` hat keinen Footer — das blinkende `PRESS ▶` in `mid` ist dort der
Signifier, und ein zweiter grauer Hinweis darunter würde ihn nur schwächen.

**`◀ QUIT` steht in der Runde permanent da**, nicht erst nach dem ersten
Druck. Ein verstecktes Bedienelement ist keins; das Versehen fängt die
Doppelbestätigung ab, nicht die Unsichtbarkeit.

### Layout-Selbsttest (`uv run game/scenes.py` → `ok`)

Dieselbe Konvention wie `db.py`, `music.py`, `balance.py`. Der Test fängt
jeden `draw()`-Aufruf der *echten* `render()`-Methoden ab und prüft die
Rechtecke: Bildgrenzen, `SAFE_BOTTOM`, und paarweise Überdeckung — inklusive
der beiden Kamerapanes und des Cursorbalkens, die kein `draw()` sind. Der
Balken kam erst am 10.9. dazu: er war ein `fill()` mit einer Magic Number und
damit für den Test unsichtbar, also blind für genau die Fehlerklasse, gegen die
der Test gebaut wurde. Jetzt steht er als `CURSOR_Y`/`CURSOR_H` in der Klasse
und der Test liest ihn von dort. Durchgespielt werden alle
Szenen, `GameScene` in drei Zuständen und `LeaderboardScene` in acht
(vier Cursorpositionen × Rückfrage an/aus).

Kein Screenshot-Vergleich: ein Referenzbild müsste bei jeder Farbänderung
gepflegt werden und sagt trotzdem nicht, *welche* zwei Elemente sich
überdecken. Gegengeprüft, dass der Test scheitern kann — mit den alten
Koordinaten meldet er die Kollision, die es tatsächlich gab.

### IdleScene

**Stumm** (`MUSIC = None` plus `ctx.music.stop()` im Konstruktor). Sechs Stunden
Chiptune am Stück sind anstrengend — und sie markieren nichts. Erst mit stillem
Idle wird der Musikeinsatz in der `HowToScene` zum Signal „es geht los". `stop()`
räumt dabei auch die aufgeschobene Idle-Musik weg, die `DisplayScoreScene` per
`MUSIC_IN` eingeplant hat.

`▶` führt jetzt in die `HowToScene`, nicht mehr direkt ins Spiel, und gibt
dabei `"ok"` zurück statt `"start"` — die Startfanfare gehört an den
tatsächlichen Rundenbeginn.

| Element | Position | Font / Farbe |
|---|---|---|
| `PICK'N'PLAY` | 960, 260 | `big` / `YELLOW` |
| `PRESS ▶` — blinkt 1 Hz | 960, 560 | `mid` / `WHITE` |
| `BEST — LOWEST WINS` | 960, 690 | `tiny` / `GREY` |
| Top 5 aus `db.top(5)` | 960, 750 + i·66 | `small` / `WHITE` |

**`LOWEST WINS` ist Pflicht, nicht Deko.** Jede Bestenliste, die ein Kind
kennt, sortiert die größte Zahl nach oben. Hier gewinnt die kleinste, und
ohne diese Zeile liest man die Liste falsch herum. Dieselbe Zeile steht in
der `LeaderboardScene`.

Das Blinken braucht keinen Timer: `self.t += dt` in `update`, und `render` prüft `int(self.t * 2) % 2`. Eine Zeitquelle, wieder dieselbe Regel wie beim Rundentimer.

### GameScene

Die drei Zahlen aus dem Lesbarkeits-Prinzip. Zielwert und Tablettsumme stehen nebeneinander, damit das Auge sie direkt vergleicht — genau das ist die Denkaufgabe des Spiels.

Seit dem 27. August liegen **beide Kamerabilder gross nebeneinander** unter
einer dreispaltigen Kopfzeile. Die Spaltenmitten 490 / 960 / 1430 gelten fuer
Zahl *und* Bild, damit beides uebereinander steht.

| Element | Position | Font / Farbe |
|---|---|---|
| `GOAL` | 490, 70 | `small` / `GREY` |
| Zielwert | 490, 145 | `mid` / `WHITE` |
| `TIME` | 960, 70 | `small` / `GREY` |
| Restzeit, ganze Sekunden | 960, 145 | `mid` / `WHITE` |
| `TOTAL` | 1430, 70 | `small` / `GREY` |
| Tablettsumme | 1430, 145 | `mid` / `YELLOW` |
| `OFF BY`, bei Treffer `PERFECT` | 960, 265 | `small` / `GREY` |
| Differenz, bei Treffer der Countdown | 960, 380 | `big` / `YELLOW` |
| Arm-Kamera (Passthrough) | 880 × 495 um 490, 740 | Rahmen `GREY` |
| Top-Down-Kamera | 880 × 495 um 1430, 740 | Rahmen `GREY` |
| Detektionsfenster | `TRAY_ROI` im rechten Pane | `GREY`, `MARK_WIDTH` |
| Marker-Werte | Schwerpunkt der Marker-Ecken | `MARK_FONT` / `YELLOW` |
| `◀ QUIT` / Abbruchwarnung | Footer | siehe Footer-Band |

**`OFF BY` in der Runde (28. August).** Vorher standen `GOAL` und `TOTAL`
940 px auseinander und der Besucher musste die Differenz im Kopf bilden —
unter Zeitdruck, aus 8 m, in einer lauten Halle. Die Denkaufgabe des Spiels
ist Pucks schieben, nicht Kopfrechnen. `GOAL` und `TOTAL` sind dafür von
`big` auf `mid` heruntergestuft; die Differenz bekommt `big`.

Es ist **dasselbe Wort wie auf dem Score-Screen** — einmal gelernt, zweimal
benutzt. Der Score-Screen ist damit „dein letzter Stand", kein neuer Begriff.

**`PERFECT n` erbt genau diesen Platz.** Steht die Summe auf dem Ziel, wird
das große gelbe Feld zum Countdown. Damit gibt es keine zweite Stelle mehr,
an der Countdown und Abbruchwarnung sich um dieselbe Zeile streiten — vorher
lagen beide auf 960, 1120 und ein `elif` deckte das zu.

Beide `YELLOW`: `TOTAL` und die Differenz sind dasselbe — was der Besucher
beeinflusst, einmal als Wert und einmal als Rest. `GOAL` und `TIME` sind das
Gegebene. Die Größe trennt sie (168 gegen 88), nicht die Farbe.

Die Kamerapanes rücken von 690 auf 740, damit unter der Differenz Luft
bleibt. Nachgerechnet im Selbsttest, nicht geschätzt.

`CAM_VIEW` ist 16:9 wie `CAM_SIZE`. Eine andere Ratio verzerrt das Bild, weil
`CameraView` stur auf die Zielgroesse skaliert statt zu beschneiden. Ein
Letterbox-Zweig waere Code fuer ein Problem, das zwei Zahlen in `config.py`
gar nicht erst entstehen lassen.

**Entwickler-Abkuerzung (`CHEAT_TAPS`, 27. August).** Fuenfmal `>` hintereinander
setzt `self.left = 0.0` — die Runde endet damit ueber ihren normalen Weg in
`update()`, inklusive Finish-Sound und Musikstufe. Ein `switch_to()` direkt aus
`handle()` waere ein zweiter Rundenschluss neben dem echten; genau den will man
beim Testen nicht abkuerzen. Jede andere Aktion setzt den Zaehler zurueck, und
`CHEAT_TAPS = 0` in `config.py` schaltet das Ganze am Automaten ab.

Nebeneffekt aus `KEY_REPEAT`: die Taste gedrueckt *halten* feuert die fuenf
Wiederholungen in ~0,6 s. Auf GPIO gibt es keine Repeat-Logik, dort sind es
fuenf echte Druecke — egal, weil der Cheat dort ohnehin aus ist.

**Vorzeitiges Ende bei `OFF BY 0`.** Steht die Summe `PERFECT_HOLD` Sekunden
lang exakt auf dem Ziel, endet die Runde — über denselben Weg wie der Ablauf
der Uhr, also inklusive Fertigsound und Szenenwechsel. Die Hysterese in
`fresh()` fängt das Flackern ab, die fünf Sekunden fangen die Absicht. Der
Countdown auf dem Schirm ist Pflicht: ein Abbruch ohne Vorwarnung sieht am
Automaten nach Absturz aus. Bleiben weniger als `PERFECT_HOLD` Sekunden, läuft
der Zähler nicht voll und die Runde endet normal — „kurz vor Schluss" braucht
keinen Sonderfall, weil es nur eine Zeitquelle gibt.

**Der Zielwert kommt aus `balance.gap()`**, gerechnet gegen das Tablett, wie es
zu Rundenbeginn tatsächlich liegt. `__init__` liest dafür einmal `fresh()` —
Nebeneffekt: der Blip-Ton feuert nicht mehr für die fünf Pucks, die beim Start
schon dalagen.

**Restzeit anzeigen:** `int(self.left) + 1`. Ohne das `+ 1` zeigt der Automat in der ersten Sekunde bereits `59` und in der letzten `0`, während die Runde noch läuft.

**Hintergrund als Timer.** Kein zusätzliches Element, die Fläche selbst ist die Anzeige:

```
k  = 0.0, solange left > WARN_SECONDS, sonst linear bis 1.0 bei left == 0
bg = BLACK + (RED - BLACK) * k         komponentenweise
```

Von Schwarz nach HPI-Rot statt von Grün nach Dunkelrot. Der Start ist damit derselbe schwarze Grund wie überall sonst, und die letzten fünf Sekunden färben den ganzen Schirm — das ist das Signal, das aus 8 m ankommt. Weiße Schrift auf `#B1073A` bleibt lesbar; die grauen Beschriftungen verlieren in diesen fünf Sekunden Kontrast, was hinnehmbar ist, weil `GOAL` und `TOTAL` da längst bekannt sind.

### HowToScene

Neu am 27. August. Erklärung, Demo-Clip, und **hier fängt die Musik an**
(`MUSIC_IN = (0.0, 800)` — 0,8 s Einblendung, statt aus der Stille zu knallen).

| Element | Position | Font / Farbe |
|---|---|---|
| `HOW TO PLAY` | 960, 110 | `mid` / `YELLOW` |
| Demo-Clip, nur wenn `DEMO_VIDEO` gesetzt | `DEMO_SIZE` um 960, 500 | Rahmen `GREY` |
| Drei Zeilen aus `HOWTO` | 960, 900 + i·60 (ohne Clip: 500 + i·60) | `tiny` / `WHITE` |
| `◀ BACK` / `▶ START` | Footer | siehe Footer-Band |

**Ohne Clip rückt der Text in die Mitte.** `DEMO_VIDEO = None` ist der
Auslieferungszustand, nicht der Ausnahmefall — den Film gibt es erst, wenn es
einen Aufbau zum Filmen gibt, und bis dahin darf das Feature weder blockiert
sein noch nach halbfertig aussehen.

**`VideoView` ist `CameraView` mit einer Uhr.** pygame kann kein Video, aber
`cv2.VideoCapture` nimmt eine Datei genauso wie ein Gerät — der Player ist
dieselbe Klasse wie der Passthrough, dieselbe `frombuffer(..., "BGR")`-Zeile,
keine neue Abhängigkeit. Der einzige echte Unterschied: eine Kamera *drückt*
Bilder (Grabber-Thread, Sequenzzähler), eine Datei wird *gezogen* (`dt`). Wer
das verwechselt, baut einen Thread zu viel oder einen zu wenig.

**Der Clip ist stumm.** Keine Tonspur, keine Synchronisation, kein zweiter
Audiopfad — die Musik trägt die Szene. Eine Erklärstimme über Chiptune in einer
lauten Halle wäre genau die Reizüberflutung, die der stille Idle wegnimmt.

**Preis: rund 5–8 s pro Besucher**, bei 240 Besuchern etwa 25 Minuten
Warteschlange über den Messetag. Dagegen steht, dass es keine Mindestdauer
gibt: wer die Erklärung kennt, tippt einmal `▶` durch.

### DisplayScoreScene

| Element | Position | Font / Farbe |
|---|---|---|
| `OFF BY` | 960, 150 | `small` / `GREY` |
| `self.score` | 960, 380 | `big` / `YELLOW` |
| `GOAL` | 660, 600 | `small` / `GREY` |
| Zielwert | 660, 690 | `mid` / `WHITE` |
| `TOTAL` | 1260, 600 | `small` / `GREY` |
| Tablettsumme | 1260, 690 | `mid` / `WHITE` |
| `PRICES` | 960, 860 | `tiny` / `GREY` |
| Preiszeile, 10 Werte | x = 204 + i·168, y = 940 | `small` / `YELLOW` wenn auf dem Tablett, sonst `WHITE` |
| `◀ BACK` / `▶ NEXT` | Footer | siehe Footer-Band |

**Die Preistabelle ist eine Preis*zeile* (28. August).** Vorher stand hier
`0 = 4`, `1 = 7`, … in fünf Spalten. Die linke Spalte war die ArUco-ID — und
die steht auf keinem Puck als Ziffer, der Besucher hat nur ein
Schwarz-Weiß-Muster gesehen. Der halbe Tabelleninhalt verlangte eine
Zuordnung, deren Schlüssel niemand besitzt. Genau das machte sie
unübersichtlich: sie sah nach Information aus und war Rauschen.

Jetzt: nur die Werte, **aufsteigend sortiert**, und **gelb die, die am
Rundenende tatsächlich auf dem Tablett lagen**. Damit ist es keine
Nachschlagetabelle mehr, sondern ein Bild der Runde — der Preiskatalog und
was man davon hatte. Die Farbe folgt der bestehenden Leiter, kein neues
Vokabular.

Der Reveal bleibt der Lernmoment aus der Spielmechanik, und er läuft weiter
über `sorted(VALUES.values())`, nicht über eine zweite Liste — sonst driften
Anzeige und Wertung auseinander, sobald jemand einen Wert ändert. Alle zehn
Werte bleiben stehen, nicht nur die eigenen: der volle Katalog ist genau das
Wissen, das die zweite Runde besser macht als die erste.

**Der Konstruktor nimmt `marks` statt `total`.** Die Summe steckt darin, und
die Preiszeile braucht ohnehin, *welche* Werte lagen. Ein Marker pro Puck und
lauter verschiedene Werte, also ist `{VALUES[i] for i in marks}` verlustfrei.

`GOAL` und `TOTAL` stehen als zwei Spalten mit Label darüber — dieselbe
Anordnung wie in der Kopfzeile der Runde, die der Besucher gerade 60 s lang
gelesen hat. Vorher war es eine gequetschte Zeile `GOAL 180    TOTAL 165`.

### LeaderboardScene

Cursor-Modell, wie unter „Szenen und Übergänge" beschrieben. Der Marker ist ein Rechteck oder Unterstrich unter dem Feld mit `self.cursor`.

| Element | Position | Font / Farbe |
|---|---|---|
| `ENTER YOUR NAME` | 960, 130 | `mid` / `YELLOW` |
| `◀` (Zurück-Feld, `cursor == 0`) | 510, 470 | `big` / `WHITE` |
| Buchstabe 1..3 | 840 / 1050 / 1260, 470 | `big` / `WHITE`, aktives Feld `YELLOW` |
| Cursorbalken | `COLS[cursor] − 68`, 580, 135 × 9 | `YELLOW` |
| `BEST — LOWEST WINS` | 960, 660 | `tiny` / `GREY` |
| Top 5 aus `db.top(5)` | 960, 720 + i·64 | `small` / `WHITE` |
| Knopfhinweise / Rückfrage | Footer | siehe Footer-Band |

**`TOP 10!` war eine Lüge (28. August).** `db.qualifies()` wird nirgends
aufgerufen, hier landet jeder — auch mit `OFF BY` 200. Die Überschrift
versprach etwas, das der Code nicht prüft, und zeigte fünf Zeilen statt zehn.
Der Screen ist eine Eingabe, also heißt er wie eine: `ENTER YOUR NAME`. Das
`qualifies()`-Gate bleibt davon unberührt und weiter offen (Balancing-Frage,
siehe Offene Punkte) — die ehrliche Überschrift nimmt der Entscheidung nichts
vorweg.

**Die Liste rückt von 860/65 auf 720/64.** Vorher lag die fünfte Zeile auf
1096…1144 und kollidierte mit der Rückfrage; jetzt endet sie bei 1004, unter
`SAFE_BOTTOM`.

**`▶ SAVE` im letzten Feld.** Dass Rechts aus dem dritten Buchstaben heraus
speichert, stand vorher nirgends — man musste es finden. Der Footer sagt,
was `▶` *jetzt* tut.

**Rueckfrage beim Verwerfen (27. August).** `◀` im Feld `cursor == 0` verwirft
den gerade gespielten Score. Das passiert versehentlich, wenn man einmal zu oft
nach links tippt, deshalb dieselbe Doppelbestaetigung wie beim Rundenabbruch:
erster Druck setzt `self.confirm = CONFIRM_SECONDS`, zweiter innerhalb des
Fensters geht ins Idle. Kein Dialogzustand, kein zweiter Screen — ein Float in
`update()` traegt beide Zustaende und laeuft von allein ab.

Die Feldfarbe kommt aus `self.cursor`, nicht aus einem zweiten Flag. Wenn `render` ein eigenes „welches Feld ist aktiv"-Attribut bräuchte, wäre der Zustand an zwei Stellen und könnte auseinanderlaufen.

### CRT-Overlay

Der Automat soll nach Röhre aussehen, nicht nach LCD. Drei Ebenen, alle in
`run_game`, zwischen `scene.render(...)` und `pygame.display.flip()`:
**Wölbung**, **Scanlines**, **Vignette**. Umgesetzt am 27. August 2026.

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

**Der Loop trägt den Effekt, nicht die Szene.** Er liegt über allem, also
gehört er an die eine Stelle, an der alles zusammenläuft. Keine Szene kennt
ihn, keine Szene kann ihn vergessen, und Abschalten ist ein Flag in
`config.py` statt vier Änderungen in `scenes.py`.

**Einmal bauen, nicht pro Frame rechnen.** Scanlines, Vignette und die
Wölbungstabelle entstehen beim Start. Pro Frame bleiben ein `remap` und ein
Blit — beides C, beides konstant. Dieselbe Regel wie bei `db.top()` im
`render`: was sich nicht ändert, wird nicht neu berechnet.

**Die Vignette ist ein 16 × 10-Alphagitter, hochskaliert.** Ein weicher
Radialverlauf kostet nichts, wenn man ihn winzig rechnet und den bilinearen
Filter von `smoothscale` die Arbeit machen lässt — 160 Pixel statt 2,3
Millionen. Draufgelegt wird sie mit `BLEND_RGBA_ADD`: beide Ebenen sind reines
Schwarz, nur das Alpha addiert sich, und das hängt an keiner pygame-Version.

**Barrel Distortion: doch, und sie kostet wenig.** Der frühere Eintrag hier
sagte „braucht einen Shader, also zu teuer". Das war falsch — `cv2.remap` ist
längst eine Abhängigkeit, weil ArUco OpenCV mitbringt. Für jedes Zielpixel wird
einmal die Quellkoordinate ausgerechnet und als Festkomma-Tabelle abgelegt
(`cv2.convertMaps`, `CV_16SC2`); pro Frame ist es ein einziger C-Aufruf.

```python
f = 1 + k * (nx² + ny²)      # aussen weiter aussen greifen = Woelbung
```

`BARREL_K = 0.05` ist sichtbar, ohne albern zu sein. `0` schaltet nur die
Wölbung ab und behält Scanlines und Vignette — das ist der Notausgang, falls
der Pi nicht mitkommt.

**`INTER_NEAREST`, nicht `INTER_LINEAR`.** Nicht nur schneller: bilineare
Filterung verwischt die Pixelfont, und „kein Antialiasing" ist die Regel eine
Ebene weiter oben. Der Preis sind leicht ausgefranste Glyphenkanten am Rand,
was auf einer Röhre nicht falsch aussieht.

**Das Overlay kommt nach der Wölbung, nicht davor.** Mitgewölbte Scanlines
wären authentischer, aber 1-px-Linien durch ein Nearest-Resampling geben
Moiré. Gerade Scanlines auf gewölbtem Bild kosten nichts und bleiben sauber.
Die Vignette deckt nebenbei die schwarzen Ecken ab, die die Wölbung erzeugt.

**Zwei Fallen im Speicherlayout**, beide teuer erkauft und deshalb hier notiert:

1. Der naheliegende Weg `pygame.surfarray.pixels3d` kostete **8,3 ms**, der
   gewählte **1,4 ms**. Grund: `pixels3d` liefert RGB, pygame speichert BGRA —
   die Sicht hat auf der Farbachse Schrittweite **−1**, und über ein rückwärts
   laufendes Array kann OpenCV nicht scannen, es kopiert erst. `get_view("2")`
   gibt die 32-Bit-Pixel wie sie liegen, `.T` dreht die pygame-Achsenreihenfolge
   `(w, h)` auf die Bildkonvention `(h, w)` und macht sie damit zusammenhängend.
   Die Farbreihenfolge ist egal, weil `remap` Pixel nur verschiebt.
2. Eine gehaltene numpy-Sicht **sperrt** ihre Surface, und der Blit darunter
   scheitert dann mit „Surfaces must not be locked during blit". Deshalb stehen
   die `px(...)` als Argumente direkt im Aufruf: die Sichten sterben mit der
   Zeile, die Sperre fällt.

**Gemessen** (Mac, headless, 1920 × 1200, echte Szenen):

| | ms/Frame |
|---|---|
| nur Szene + `flip` | 2,5 |
| **+ Wölbung + Scanlines + Vignette** | **5,8** |
| Budget bei 60 FPS | 16,7 |

Der CRT-Anteil sind rund **3,3 ms**. Auf dem Pi ist das der Posten, der als
erstes kippt — dort ist zu messen, nicht zu schätzen.

#### Messung auf dem Pi, 9. September 2026

Gemessen am Automaten: Pi 5 (8 GB), Ubuntu 24.04, KMSDRM-Vollbild, beide Kameras
aktiv, Teleop gestoppt. Der Idle-Screen wurde über `PNP_IDLE_FPS=60` auf
Spielszenen-Last getrieben, weil über SSH bei KMSDRM keine Taste ankommt und die
Spielszene sonst nicht erreichbar ist.

| Ziel 60 fps | CPU | erreicht |
|---|---|---|
| alles an | 268 % | **19,6** |
| ohne Wölbung (`BARREL_K = 0`) | 195 % | **26,5** |
| ohne CRT | 189 % | **36,6** |
| ohne CRT, ohne Kameras | 92 % | **40,0** |

**60 fps sind auf diesem Pi nicht erreichbar.** Auch nicht entkernt. Die letzte
Zeile ist der eigentliche Befund: 40 fps bei 92 % CPU heißt, dass da nichts mehr
zu parallelisieren ist, der Pfad hängt an einem Thread.

Drei Hypothesen wurden geprüft, zwei davon widerlegt:

**Textrendering war es nicht.** `font.render()` lief für jede Zeichenkette in
jedem Bild neu, Press Start 2P in bis zu 168 px. Ein `lru_cache` darauf brachte
in einer Variante 10 %, sonst nichts. Der Cache bleibt drin, er kostet nichts
und schadet nicht, aber er war nicht die Ursache.

**`vsync=1` kostet 12 bis 19 %**, erkauft sich das aber mit Tearing und bringt
die 60 trotzdem nicht. Bleibt drin.

**Native 1080 statt herunterskalierter 1200 bringt am meisten**, in der Variante
ohne Wölbung 26,5 → 34,2 fps. Das ist der Grund, warum die Auflösungsfrage oben
unter „Offene Punkte" steht.

Dazu ein Wärmebefund, unabhängig von der Bildrate: mit Spiel **und** Teleop
gleichzeitig läuft der Pi in unter einer Minute auf 83 °C und drosselt
(`throttled=0xe0008`), die Bildrate fällt dabei weiter. Ohne aktive Kühlung ist
der Dauerbetrieb am Messetag so nicht zu halten.

#### Entschieden am 10. September 2026: alle drei, plus eine vierte

Gemessen wurde am selben Automaten, nativ in 1920 × 1080, beide Kameras aktiv.

| Ziel unbegrenzt | 9.9. (1200, `SCALED`) | 10.9. (1080 nativ) |
|---|---|---|
| alles an | 19,6 | **28,5 kalt → 26 warm** |
| ohne Wölbung | 26,5 | **42** |
| ohne CRT | 36,6 | **61** |

Stufen des Renderpfads einzeln, am kalten Pi: Szene zeichnen 1,4–2,0 ms,
`remap` 8,7 ms, Scanlines 7,0 ms. Zum Vergleich die Untergrenze — eine reine
Kopie derselben Datenmenge kostet 1,83 ms. `remap` liegt also beim Fünffachen
davon: der Gather ist rechengebunden, nicht bandbreitengebunden, und mit
OpenCV ist dort nichts mehr zu holen. Vier Varianten wurden gegeneinander
gemessen (4 × uint8, 1 × int32, `BORDER_REPLICATE`), alle innerhalb von 2 %.

**Zwei Hypothesen von vorher haben sich nicht bestätigt.** Erstens: die 25 ms
für „Szene + flip" waren fast vollständig die `SCALED`-Skalierung, nicht das
Zeichnen — die Szene selbst kostet 1,5 ms. Zweitens: das Overlay von pygames
Alpha-Blit auf `cv2.multiply` umzustellen sollte 6 ms bringen und brachte
nichts. Auf dem Pi kostet die Multiplikation 7,2 ms und der Blit 6,4; im
ganzen Renderpfad 21,4 gegen 21,5 ms, also Gleichstand. Die Multiplikation ist
trotzdem geblieben — halb so viel Code, exakte statt genäherter Vignette, und
der ganze Nachbearbeitungspfad hängt damit an einer Thread-Einstellung statt
an zweien. Als Beschleunigung war sie ein Fehlschluss.

**Die vierte Stellschraube stand nicht auf der Liste und schlägt alle drei
anderen: die Wölbung wandert vom Bild in die Verdunklungskarte.** Statt jedes
Bild durch ein `cv2.remap` zu schicken, bekommt die statische Scanline- und
Vignettenkarte die Wölbung eingebaut — die Zeilen krümmen sich wie auf einer
Röhre und rücken zum Bildrand hin zusammen, das Bild selbst bleibt geometrisch
flach. Die Karte wird beim Start gebaut, zur Laufzeit kostet die Krümmung
nichts.

| Variante | ms/Bild | Decke |
|---|---|---|
| Wölbung im Bild (bis 9.9.) | 24,95 | 40 fps |
| **gewölbte Scanlines, Bild flach** | **11,12** | **90 fps** |
| ohne Wölbung | 11,65 | 86 fps |

Die gewölbten Scanlines kosten also genau so viel wie *gar keine* Wölbung.

**Der zweite Grund wiegt schwerer als die Millisekunden: die Wölbung zerlegte
die Pixelschrift.** `remap` tastet mit `INTER_NEAREST` ab, und ein
8 × 8-Glyphenraster auf nicht-ganzzahlige Positionen abgetastet franst aus —
Buchstabenkanten werden stufig, Glyphenpixel ungleich groß. Das ist derselbe
Fehler, gegen den alle Schriftgrößen durch 8 teilbar sind, nur von der anderen
Seite. Aus 3–8 m liest sich eine Röhre ohnehin an den Zeilen, nicht an der
Geometrie — dasselbe Argument, mit dem die Chromatic Aberration draußen
geblieben ist.

Die Scanlinephase kommt aus der gewölbten Quellzeile und wird als
**Deckungsgrad gerechnet, nicht abgetastet**. Ein punktweise gewarptes
3-px-Muster gäbe sonst Moirestreifen am Bildrand — das war der Grund, warum
die naheliegendere Variante (Scanlines vor die Wölbung legen) verworfen wurde,
bevor sie Code war. Bei `BARREL_K = 0` fällt die Karte auf ein Bit genau auf
das alte flache Muster zurück.

**Ergebnis: 30 fps, 45 Sekunden am Stück, mit laufender Teleop.** 29,4 bis
30,3, kein Abfall, dabei von 61,5 auf 75,7 °C.

**Offen bleibt der GPU-Shader.** Wölbung *des Bildes* mit scharfer Schrift ginge
als GLES-Fragmentshader auf dem VideoCore, mit korrekter Filterung und ohne
Bildratenkosten. Bewusst nicht gebaut: neue Abhängigkeit, GLES-Kontext unter
KMSDRM, Texturupload pro Bild, und der Layout-Selbsttest liefe nicht mehr
headless. Der Code für die Bildwölbung (`barrel_maps`, `cv2.remap` im Loop)
steht in der Historie bis einschließlich `6ed2b4a`, falls die Option gezogen
wird.

**Der Zielkonflikt gehört benannt:** Scanlines nehmen Helligkeit weg, und
Lesbarkeit aus 8 m in einer hellen Halle ist das oberste Prinzip dieses
Projekts. `SCANLINE_ALPHA` steht deshalb in `config.py` und wird **in der Halle**
eingestellt, nicht am Schreibtisch. Im Zweifel gewinnt die Lesbarkeit.

**Keine Chromatic Aberration.** Die bräuchte drei Remaps statt einem, und aus
3–8 m ist sie nicht als Effekt lesbar, sondern nur als Unschärfe.

### Sound: Low-Bit-Arcade-Musik, deklarativ notiert

Musik wird **als Daten geschrieben, nicht als Code**: eine Zeichenkette pro
Stück, die `music.py` zur Laufzeit in einen Ton wandelt. Keine Audiodateien im
Repository, keine Abhängigkeit, kein Lizenzthema — und Ändern einer Melodie ist
Ändern einer Zeile.

```python
# game/music.py
ATTRACT = "c4 e4 g4 c5 - g4 e4 c4 -"     # Notenname + Oktave, "-" ist Pause
```

Wie das funktioniert, in vier Schritten:

1. **Notenname → Frequenz** ist eine Zeile: `440 * 2 ** ((halbton - 69) / 12)`.
   Das ist die MIDI-Formel, 69 ist das Kammerton-A.
2. **Frequenz → Samples** ist eine Rechteckschwingung: abwechselnd `+A` und
   `-A` umschalten. Genau diese Kurvenform *ist* der Chiptune-Klang — sie
   entsteht, weil ein NES oder ein C64 nichts anderes konnte als einen Pegel
   an- und auszuschalten. „Low bit" ist hier keine Nachbildung, sondern der
   direkte Weg.
3. **Samples → `Sound`** über `pygame.mixer.Sound(buffer=...)` mit dem
   stdlib-Modul `array`. **Kein numpy** — `pygame.sndarray` bräuchte es, der
   `buffer`-Weg nicht, und numpy steht nicht in den Abhängigkeiten.
4. **Das ganze Stück wird einmal beim Start gerendert** und mit `play(loops=-1)`
   geschleift. Kein Scheduler, kein Timer-Thread, keine Note-für-Note-Ausgabe.
   Eine Schleife, die im Audiotreiber läuft, driftet nicht — dieselbe
   Überlegung wie „eine Zeitquelle pro Runde", nur für Audio.

`pygame.mixer.pre_init(...)` muss **vor** `pygame.init()` laufen, sonst steht
die Puffergröße schon fest und man hört Latenz.

Angebunden wird es wie der Detector: `Ctx` bekommt ein `music`-Feld, Szenen
rufen `self.ctx.music.play("attract")` und wissen nie, was dahinter steckt.
Damit gibt es eine stumme Attrappe für Tests ohne Audiogerät, und der
Kopfhörer-Test auf dem Laptop ist dieselbe Codebasis wie die Messe.

**Sound bleibt Beiwerk.** Die Halle ist laut; nichts im Spiel darf davon
abhängen, dass jemand etwas hört. Das Stück läuft im Attract Mode, ein kurzer
Beep bestätigt Knopfdrücke, ein Jingle den Score. Mehr nicht.

#### Umgesetzt am 27. August

Sechs Token in der Notation, ein Token ist ein Sechzehntel: `f4` Note, `.`
hält, `-` Pause, `f4/a4/c5` Akkord, `a#2^f2` Glide, `k s h` Kick/Snare/Hat.
Zwei Datentabellen am Kopf der Datei — `PIECES` und `SFX` —, darunter nur noch
Anbindung.

**Die Schleife läuft pro Schwingung, nicht pro Sample.** Das ist die
Entscheidung, aus der alles andere folgt. Eine Rechteckperiode ist 30 bis 500
Samples lang; wer Lautstärke und Frequenz einmal je Periode neu berechnet,
macht hundertmal weniger Arbeit als pro Sample — und hört keinen Unterschied,
weil sich innerhalb einer Periode ohnehin nichts ändern kann. In dieser einen
Schleife stecken deshalb **Hüllkurve, Vibrato, Glide, Arpeggio und die
Kickdrum**, jedes als zwei Zeilen. Alle Stücke und Effekte rendern in 0,12 s.

**Ohne Hüllkurve klingt jede Note wie ein Testton.** `ENV` hält fünf Kurven
(`pluck`, `hit`, `punch`, `swell`, `flat`), Argument sind Sekunden seit
Notenbeginn. Das war der eigentliche Grund, warum die erste Fassung
„computergeneriert" klang — nicht die Melodie.

**Stimmung: die Periode wird nicht gerundet, nur ihr Ende.** Eine gerundete
Periode zieht hohe Noten daneben — F5 bei 44100 Hz landet 12 Cent zu tief, F6
sogar 23 — und weil jede Note anders rundet, stimmen die *Intervalle* nicht.
Genau das hört man als „schief". Mit gebrochener Position stimmt die mittlere
Frequenz exakt, der Rest ist ein halbes Sample Jitter. Der Selbsttest zählt
über den ganzen Tonumfang die Nulldurchgänge einer Sekunde Ton und verlangt
±1 Hz.

**Mischen macht der Mixer.** Ein Stück hat bis zu vier Spuren, jede liegt auf
einem eigenen Kanal (`set_reserved(4)` von zwölf, acht bleiben den Effekten).
Alle Spuren eines Stücks sind gleich lang, also laufen sie geschleift für immer
synchron. Es gibt keine Additionsschleife in Python.

**Intensität ist keine Automation, sondern vier Stücke.** `round0`–`round3`,
dasselbe Riff in F-Dur bei 118 / 132 / 148 / 158 BPM, das Schlagzeug wird von
Halbe-Backbeat bis Sechzehntel-Hats dichter. Dur, nicht Moll: die Spannung
kommt aus Tempo und Schlagzeug, nicht aus Traurigkeit. Stufe 3, die letzten
fünf Sekunden, legt eine tickende Uhr auf jede Viertel — die Melodie läuft
weiter. Eine frühere Fassung ersetzte sie durch einen Alarm über
Sechzehntel-Bassdrum; das war Hardcore-Techno und für das Publikum am
Messestand deutlich zu viel. **Panik entsteht aus dem Ticken, nicht aus mehr
Bassdrum.**
`GameScene.update` ruft `music.stage(self.left)` pro Frame, gewechselt wird nur
bei Stufenwechsel. Gemessen: 60 → 40 → 20 → 5 Restsekunden; Stufe 3 setzt mit
`WARN_SECONDS` ein, also im selben Frame, in dem der Bildschirm rot wird.

**Nach dem Fertigsound kommt Stille.** `SceneBase.MUSIC_IN` ist ein Paar
`(Pause in Sekunden, Einblendung in Millisekunden)`, `DisplayScoreScene` setzt
`(2.2, 1500)`: die Rundenmusik hört sofort auf, die Fanfare klingt frei aus,
zwei Sekunden passiert nichts, dann blendet die Idle-Musik ein. Die Stille ist
der Effekt. Das Einblenden macht `Channel.play(..., fade_ms=...)`, das Warten
`Music.update()` — aufgerufen in `run_game`, wo ohnehin jeden Frame etwas
passiert. Kein Timer-Thread, keine zweite Zeitquelle.

**Szenenwechsel ist Musikwechsel, deklarativ.** `SceneBase.MUSIC` ist ein
Klassenattribut, `SceneBase.__init__` spielt es ab. Jede Szene sagt einmal,
was bei ihr läuft; `GameScene` setzt `MUSIC = None`, weil ihre Stufe an der
Restzeit hängt. Damit kann keine künftige Szene vergessen, die Rundenmusik
abzustellen — Idle, Score und Leaderboard erben `"idle"` und schalten von
allein zurück.

**Der Fehlton kostet eine Zeile.** `handle()` gibt den Namen des Sounds zurück,
`None` heißt „nicht genommen". In `run_game` steht deshalb:

```python
scene.ctx.music.sfx(scene.handle(action) or "nope")
```

Damit klingt *jeder* Knopfdruck, ohne dass eine Szene daran denken muss — im
Spiel `>` drücken brummt, im Leaderboard `^` auf dem `<`-Feld brummt. Die
Zeile ist der ganze Signifier-Mechanismus.

`Music.REPEAT_MS = 90` verschluckt denselben Effekt kurz hintereinander. Ohne
das feuert `KEY_REPEAT` beim Buchstabenscrollen 16 Blips pro Sekunde.

**Ohne Audiogerät ist `Music` stumm statt kaputt.** `pygame.mixer.get_init()`
muss exakt `(44100, -16, 1)` liefern, sonst rendert der Konstruktor nichts und
jede Methode kehrt sofort zurück. Keine zweite Attrappenklasse. `pre_init`
steht als erste Zeile in `main()` — nach `pygame.init()` ist die Puffergröße
fest.

`uv run game/music.py` prüft Taktlängen, Stimmung und Spurlängen und schreibt
WAV-Dateien nach `/tmp/picknplay-audio`, darunter `session.wav`: Idle,
Startfanfare, 60 Sekunden Steigerung, Fertigsound am Stück. Hören geht ohne
das Spiel zu starten.

#### Woher die Töne kommen

`Dream_Sound.mp3` (101 s) wurde per FFT analysiert, nicht abgeschrieben:
Tempo ≈ 85 BPM, Tonart F-Dur, Bass wandert F2 – Bb2 – C3 – A2/D2, die Melodie
sitzt zwischen F4 und A5. Genau das ist die Idle-Musik geworden — 84 BPM,
F – Dm – Bb – C, weite Halbe im Bass, dünner Puls (Duty 0.125) für die
Arpeggien. Die Runde nimmt dieselben Töne in d-Moll: verwandt genug, dass der
Wechsel nicht wie ein anderes Spiel klingt.

Übernommen wurde also die *Beschreibung* des Stücks, keine Note. Kein Sample,
keine Datei im Repository, kein Lizenzthema.

---

## Schnittstellen der noch leeren Dateien

Kein `abc`, kein `Protocol`, keine Basisklasse. Ein Detector ist alles, was `tray_sum()` hat — mehr Vertrag braucht es nicht, und der Tausch Attrappe ↔ Hardware bleibt eine Zeile in `main.py`.

### `db.py`

```python
class DB:
    def __init__(self, path=DB_PATH)      # CREATE TABLE IF NOT EXISTS
    def top(self, n=TOP_N)  -> list[tuple[str, int]]
    def qualifies(self, score) -> bool
    def add(self, initials, score) -> None
```

**`ORDER BY score ASC`.** Der Score ist der *Abstand* zum Zielwert, `0` ist perfekt. Auf `DESC` gestellt ist die Bestenliste lautlos falsch herum und niemand merkt es am Messestand. Ein `rowid ASC` als Tiebreak hält die Reihenfolge bei Gleichstand stabil.

`qualifies(score)` ist `len(top) < TOP_N or score < top[-1][1]`.

Diese Datei bekommt einen `if __name__ == "__main__":`-Block mit `assert`s — Einfügen, Sortierrichtung, Verdrängung bei vollen Top 10. Die einzige Stelle im Projekt mit nicht-trivialer Vergleichslogik, und die einzige, deren Fehler man am Messetag nicht sieht.

### `hw.py`

```python
class FakeDetector:                       # zuerst bauen, ohne Kamera
    def tray_sum(self) -> int

class Camera:                             # Grabber-Thread
    def __init__(self, index=CAM_INDEX, size=CAM_SIZE)
    def read(self)      -> frame | None   # immer das NEUESTE Bild
    def close(self)     -> None

class ArucoDetector:
    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI)
    def fresh(self) -> dict[int, quad]    # gleiche Signatur wie FakeDetector

class CameraView:                         # ein Pane
    def __init__(self, cam, det=None, size=CAM_VIEW)
    def surface(self) -> pygame.Surface | None
```

**Der Vertrag ist seit dem 27. August `fresh()`, nicht mehr `tray_sum()`.**
Ein Detector ist alles, was `fresh()` hat: ein Dict von Marker-ID auf ein
Viereck, beides braucht die Szene ohnehin. Summiert wird in der Szene, denn
`VALUES` ist Spielregel, kein Sensorwissen — ein Detector, der Punkte kennt,
wäre ein Sensor mit Meinung. `tray_sum()` ist ersatzlos entfallen, es hatte
genau einen Aufrufer.

`uv run game/hw.py` prüft ohne Kamera gegen ein synthetisch gezeichnetes
Tablett: dass `DICT_4X4_50` zu `markers/` passt, dass die Vierecke dort liegen,
wo die Marker gezeichnet wurden (±3 px), dass `TRAY_ROI` aussortiert, was
draußen liegt, dass die Hysterese erst hält und dann abbaut, und dass
`FakeDetector` dieselbe Schnittstelle hat.

**`FakeDetector` zuerst.** Die Attrappe soll ihre Summe von selbst ändern (etwa alle 3 s neu würfeln), sonst steht die Tablettzahl während der ganzen Runde still und du siehst nicht, ob die Anzeige überhaupt aktualisiert.

**`Camera` als Thread, nicht als Prozess.** `cap.read()` ist C++-Code und gibt das GIL frei. Der Thread schreibt das Bild unter Lock in ein Attribut, der Loop liest — nie umgekehrt. `CAP_PROP_BUFFERSIZE = 1`, sonst liefert der V4L2-Puffer alte Frames und die Erkennung hinkt sichtbar hinterher.

**Hysterese in `ArucoDetector`:** ein Dictionary `marker_id -> Zeitpunkt der letzten Sichtung`. `tray_sum()` summiert alles, was jünger als `MARKER_HOLD` ist. Das ist die Lösung für die Hand über dem Tablett, nicht für Pucks, die wirklich verschwinden — dafür bräuchte es Positions-Tracking, und das ist bewusst nicht im Scope.

`detectMarkers()` bei `DETECT_HZ` laufen zu lassen statt bei 60 FPS: die Erkennung ist teuer und das Spiel braucht sie nicht öfter als der Besucher Pucks bewegt.

### `Buttons` (später, Meilenstein 10)

gpiozero-Callbacks laufen in einem fremden Thread. Der Tastendruck geht in eine `queue.SimpleQueue`, `run_game` leert sie einmal pro Frame und schiebt die Aktionen durch dieselbe Stelle wie `action_of`. Damit ändert sich in `scenes.py` keine Zeile.

**Achtung:** `pygame.key.set_repeat()` gilt nur für die Tastatur. Das Durchscrollen der Buchstaben beim Halten muss `Buttons` selbst erzeugen — sonst funktioniert die Initialen-Eingabe auf der Messe anders als beim Entwickeln.

### `main.py`

```python
def main():
    pygame.init()
    fonts = {"big": ..., "mid": ..., "small": ..., "tiny": ...}
    ctx = Ctx(detector=FakeDetector(), db=DB(), fonts=fonts)
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS)
```

Die einzige Datei, die `scenes` **und** `hw` importiert. Der Umstieg auf echte Hardware ist genau eine Zeile: `FakeDetector()` → `ArucoDetector(Camera())`.


---

## Randbedingungen

- **Durchsatz:** ~90 s pro Person inkl. Wechsel. 6 h Messe ≈ 240 Besucher.
- **Toleranz:** Jede geforderte Ablagegenauigkeit ≥ 1 cm. Backlash und Totzone der Servos lassen nichts Feineres zu.
- **Servoschutz:** Torque- und Overload-Register konservativ im EEPROM, Software-Joint-Limits, Watchdog auf Last und Temperatur.
- **Verschleiß:** Gripper-Servo stirbt zuerst. Ersatzservos, gedruckte Ersatzteile, idealerweise kompletter Zweitarm als Hot Spare.
- **USB-Bandbreite:** Zwei UVC-Kameras an einem Bus überallozieren Bandbreite („No space left on device"). Vor Aufbau testen, ggf. getrennte Busse oder Auflösung senken.
- **Ergonomie:** Podest für kleinere Besucher. Desinfektionsmittel am Leader.
- **DSGVO:** Bei Erfassung von Kontaktdaten überwiegend Minderjährige. Vorab klären.
- **Autostart:** Beide Prozesse als systemd-Services. Der Automat muss nach Stromausfall ohne Tastatur hochkommen.

## Balancing: Preise und Zielwert

Entschieden am 27. August 2026, überarbeitet am 11. September mit der Wertung.

**Der Zielwert wird nicht frei gewürfelt.** `randrange(50, 300, 5)` neben einer
Tablettsumme hieß: der Zufall entscheidet, ob jemand 0,30 € oder 20 € zu
überbrücken hat. Das war die eigentliche Unfairness — nicht die Werte, sondern
die fehlende Kopplung. `balance.gap()` liest deshalb das echte Tablett und
wählt die *Distanz*:

1. in `GAP_MOVES` (2) Zügen exakt schließbar — keine Runde ist unmöglich
2. der beste einzelne Zug landet zwischen `GAP_ONE_MISS` (2) und
   `GAP_ONE_MAX` (25) daneben, also 0,20 € bis 2,50 €

Die Untergrenze verhindert den Glücksgriff, der direkt auf null führt. Die
Obergrenze verhindert das Gegenteil: eine Runde, die nach dem besten Einzelzug
noch 6,70 € offen lässt, ist in der Rundenzeit nicht zu holen.

**Das Tablett startet leer, und das macht die Zielmenge endlich.** Weil jede
Runde beim selben Zustand anfängt, ist auch die Menge zulässiger Ziele jede
Runde dieselbe — mit dem aktuellen Preissatz sind es 21, und sie sind der
ganze Vorrat an Aufgaben für einen Messetag. Der bindende Regler dafür ist
`GAP_ONE_MAX`: bei 15 wären es 14 Ziele, bei 25 sind es 21. Das Band
`GAP_MIN`/`GAP_MAX` ist es *nicht* — es schneidet nichts weg, was die
Einzelzug-Bedingung nicht ohnehin schon wegnimmt.

`gap()` liest trotzdem das echte Tablett statt eine Konstante zu benutzen: ein
liegengebliebener Cupcake ändert die Aufgabe dann mit, statt sie
kaputtzumachen.

**Die Preise haben keinen gemeinsamen Teiler.** Gerechnet wird in
10-Cent-Einheiten — `{14, 17, 21, 24, 28, 32, 36, 41, 46, 52}`, angezeigt als
1,40 € bis 5,20 €. Wären es glatte Preise in Cent, wäre der ggT 10 und das
Spiel binär: Distanz durch den Teiler teilbar, dann genügt ein Griff, sonst
ist sie *überhaupt nicht* erreichbar. Erst Teilerfremdheit gibt „knapp
daneben" — und damit eine Bestenliste mit Auflösung statt einer Liste aus
Nullen und Unmöglichkeiten.

**Ein Marker pro physischem Cupcake, zehn Stück.** `ArucoDetector.marks` ist
ein Dict mit der ID als Schlüssel: zwei Cupcakes mit demselben Marker zählen
einmal. Duplikate zu drucken wäre ein stiller Wertungsfehler, der am Messetag
wie ein Erkennungsproblem aussieht. Zehn passt außerdem zum Raster der
Preistabelle im Score-Screen.

## Preise

Drei Stufen, alle erreichbar — jeder gewinnt etwas:

- **Teilnahme** — Sticker oder 3D-gedruckter Keychain
- **Score-Band** — besserer Preis, nach Genauigkeit gestaffelt
- **Tagesbestenliste** — Hauptpreis am Ende des Messetags

Die Bandgrenzen sind noch nicht gesetzt. Sie gehören an `off` und nicht an die
Punktzahl, weil `off` die physische Wahrheit der Runde ist: Vorschlag `0` /
`≤ 5` (also bis 0,50 € daneben) / Rest, zu bestätigen, sobald jemand einen
Nachmittag lang echte Ergebnisse gesehen hat.

## MVP-Meilensteine

Reihenfolge nach dem Prinzip: nach jedem Schritt läuft etwas. Die Software wird gegen Attrappen fertiggestellt, bevor Hardware angeschlossen wird.

**Software (ohne Hardware)**

1. ● Skelett läuft — Szenenlogik, Übergänge, `main.py`/`db.py`/`hw.py` stehen, durchklickbar
2. ◐ Lesbarkeit — Layout gezeichnet, Farbtimer steht; aus 8 m noch nicht geprüft
3. ◐ Spiellogik — `FakeDetector` liefert Zahlen; `tray_sum()` steht im falschen Zweig (Befund 3)
4. ◐ High Score — Cursor-Modell und SQLite stehen, `handle` doppelt (Befund 1)
5. ◐ Attract Mode — Timeouts und Titelbild stehen, Demo-Video fehlt
5a. ● CRT-Overlay — Wölbung, Scanlines, Vignette in `run_game`; Press Start 2P als Schrift. Stärke in der Halle einstellen, Kosten auf dem Pi messen
5b. ● Musik — `music.py`, deklarative Notation, Square-Wave-Synthese, Ducking
5d. ● Balancing — `balance.py`, Zielwert aus dem Tablett, Werte ohne
    gemeinsamen Teiler; `GAP_MOVES` bleibt geraten bis jemand misst
5c. ● Vollbild — nativ 1920 × 1080 ohne `SCALED`, `FULLSCREEN`-Schalter in
    `config.py`, 30 fps am Automaten abgenommen (10.9.)

Legende: ● fertig · ◐ angefangen · ○ offen

**Hardware**

6. Arm läuft — Teleop 10 min ohne Fehler
7. Greifen klappt — 9 von 10 Pucks ohne Kippen
8. ◐ Marker werden erkannt — Code steht und läuft gegen die Webcam; gegen die
   gedruckten Marker unter Hallenlicht ungeprüft
9. ◐ Tablett wird gelesen — Hysterese steht (`MARKER_HOLD`), real ungeprüft

**Integration**

10. ● `FakeDetector` → `ArucoDetector` erledigt (`CAMERA` in `config.py`);
    `FakeButtons` → `Buttons` offen
11. LED-Zustände, systemd-Autostart beider Prozesse, UDP-Heartbeat

Meilensteine 1–5 brauchen weder Arm noch Kamera und laufen parallel zur Hardware. Ein Integrationsschritt entfällt: beide Prozesse werden nur nebeneinander gestartet.

## Nicht im Scope

Jetson, Browser-Frontend, WebSocket, Flask, Kubernetes, ConfigSync, GCS, Vertex-Pipelines, trainierte CV-Modelle, autonomer Betrieb ohne Teleop, FPV als eigenes Spiel (nur als optionaler Hard-Mode-Schalter). Videodekodierung im **Attract Mode** bleibt draußen — der Demo-Clip läuft in der `HowToScene`, ein paar Sekunden pro Besucher statt sechs Stunden im geschlossenen Kabinett.

## Offene Punkte

- Welcher Pi (Modell und RAM)
- **Stromlose Parkpose des Followers** — blockiert die Torque-Abschaltung im Idle
- Python-Version des Pi-Images, daraus folgt LeRobot-Version
- Anzahl verfügbarer Arme
- Messedauer und Standbesetzung
- ArUco-Erkennungsrate unter Hallenlicht (nicht im Studio testen)
- Reale Aktionszahl Ungeübter in 60 s — steckt jetzt als `GAP_MOVES = 3` in
  `config.py`. Der Mechanismus stimmt bei jedem Wert, nur die Konstante ist
  geraten; sobald jemand es misst, ist es eine Zeile
- Ob die Zwischenszene eigene, dünnere Musik bekommt statt des Idle-Loops —
  eine Zeichenkette in `PIECES`, keine Codeänderung
- `up` läuft in der Namenseingabe rückwärts durchs Alphabet (A → Z). Mit
  echten Pfeilen statt `^v` fällt das jetzt eher auf; eine Zeile in
  `LeaderboardScene.handle`, falls es umgedreht werden soll
- `TRAY_ROI` am aufgebauten Automaten einstellen — hängt an Kamerahöhe und Tablettgröße
- CRT-Scanline-Stärke unter Hallenlicht: ab wann kostet der Effekt mehr Lesbarkeit als er Optik bringt (`SCANLINE_ALPHA`, `VIGNETTE_ALPHA`)
- ~~Ob der Pi die 3,3 ms für die Wölbung übrig hat~~ — erledigt am 10.9.2026. Die Wölbung sitzt jetzt in der statischen Verdunklungskarte und kostet zur Laufzeit nichts
- **Aktive Kühlung.** Ohne Lüfter drosselt der Pi unter Doppellast und verfälscht jede Messung um bis zu 35 %. Erste Ordnung, blockiert den Dauerbetrieb am Messetag
- Ob der GPU-Shader gebaut wird (Wölbung des Bildes mit scharfer Schrift). Optional, nicht blockierend
- ~~Ob `cv2` neben `pygame` auf dem Pi sauber lädt~~ — erledigt am 9.9.2026. Auf Ubuntu 24.04 laden OpenCV 5.0.0 und pygame-ce 2.5.8 unter Python 3.13 ohne Symbolkonflikt
- Audioausgabe am Pi (Klinke, HDMI oder USB) und ob am Stand überhaupt etwas hörbar ist
- ~~Ob die 60-px-Balken oben/unten hinter der Kabinettblende verschwinden~~ — hinfällig, das Panel ist 16:9 und es wird nativ gerendert
- ~~Ob bei 1920 × 1080 nativ gerendert wird statt bei 1200 herunterskaliert~~ — erledigt am 10.9.2026, Layout ist umgezogen
- Stromversorgung des Pi beim Ausschalten: ein harter Schnitt hat am 9.9. das Git-Repo zerlegt (fünf Objekte null Byte). Am Messetag ist das die SD-Karte des Automaten
- Snap-in vs. Schraubtaster bei 3 mm Sperrholz — Ausrissverhalten testen
- Zwei Kameras gleichzeitig: Bandbreite am realen Pi verifizieren (Index der Arm-Kamera steht noch nicht fest, `CAM_INDEX` ist einer)
- FPV-Latenz, falls Hard Mode kommt

## Arbeitsweise

Ursprünglich: das MVP bewusst ohne KI-Assistenz. Primärquellen, Versuch vor Nachschlagen, bei Blockade nach zwei Stunden Kollegen fragen statt Werkzeug. Zeitbudget entsprechend zwei- bis dreifach angesetzt.

**Angepasst (August 2026):** Der Assistent wird als Prüfer und Erklärer genutzt — er liest Code, benennt Fehler mit Datei und Zeile, erklärt Entwurfsfragen und pflegt dieses Dokument. Geschrieben wurde zunächst alles von Hand: der Lerneffekt hängt daran, dass die Tastenanschläge selbst passieren.

**Angepasst (27. August 2026):** Das Skelett steht und ist verstanden — Szenenmodell, Loop, `Ctx`-Naht, Layout-Koordinaten sind von Hand entstanden und damit durchdrungen. Ab hier schreibt der Assistent den Code, aber erst nach dem Vier-Schritte-Ablauf oben. Das Verständnis wandert damit von „ich habe es getippt" zu „ich habe die Entscheidung getroffen und könnte sie verteidigen" — und Letzteres ist das, was am Messestand um 9 Uhr morgens beim Reparieren zählt. Der Ablauf ist die Bedingung dafür: ohne Schritt 2 und 3 wäre es nur noch Diktat.
