import importlib
import os
import sys
import pygame

# ── Anzeige ───────────────────────────────────────────────────────────────
# Entwurfsaufloesung = Panelaufloesung des Asus MB169CK, nativ und ohne
# pygame.SCALED. Die Skalierung 1200 -> 1080 kostete gemessen rund 20 ms pro Bild,
# und sie legte die 8x8-Pixelschrift auf ein Raster mit Faktor 0,9 -- also auf
# ungleich grosse Glyphenpixel. Jede Koordinate in scenes.py ist eine absolute
# Zahl fuer dieses Raster; ein anderes Panel heisst Layout anfassen.
WIDTH, HEIGHT = 1920, 1080

# 30, nicht 60. Zwei Gruende, beide unabhaengig von der Rechenleistung:
#
# 1. 60/30 = 2, also steht jedes Bild exakt zwei Refreshes lang und die Kadenz
#    ist gleichmaessig. Bei 40 fps waere 60/40 = 1,5: abwechselnd ein und zwei
#    Refreshes, sichtbares Ruckeln bei *hoeherer* Bildrate. Unterhalb von 60
#    ist 30 auf einem 60-Hz-Panel die einzige gerade Zahl.
# 2. Die Kameras liefern 30 Bilder/s. Alles darueber zeigt in der Runde
#    dasselbe Kamerabild zweimal.
#
# Es gibt in diesem Spiel keine 60-Hz-Bewegung: Sekundenzaehler, Summe,
# blinkender Text, Kamerabild. Der Arcade-Look kommt aus Scanlines, Woelbung
# und harten Pixelkanten, nicht aus der Bildrate. Halbe Renderlast ist
# ausserdem halbe Waerme, und der Pi drosselt zusammen mit der Teleop.
FPS = 30
IDLE_FPS = int(os.environ.get("PNP_IDLE_FPS", "15"))
                     # die Haelfte von FPS, damit die Kadenz gerade bleibt.
                     # Der Idle-Screen aendert sich zweimal pro Sekunde -- mehr
                     # ist sechs Stunden Waerme fuer nichts.
                     # PNP_IDLE_FPS=30 laesst den Renderpfad unter Spielszenen-Last
                     # messen, ohne dass jemand einen Knopf druecken muss.
# Default ist der Automat. Zum Entwickeln und fuer Fernwartung ueber SSH lassen
# sich die drei per Umgebungsvariable umschalten, ohne die Datei zu aendern
# (sonst ueberschreibt das naechste git pull die lokale Anpassung):
#   PNP_FULLSCREEN=0  Fenster statt Vollbild
#   PNP_CAMERA=0      FakeDetector, kein Kamerazugriff
#   PNP_FPSLOG=1      Bildrate einmal pro Sekunde auf stdout
#   PNP_VSYNC=0       ohne Bildsynchronisation, kostet Tearing
#
# Am Mac sind die Defaults der Entwicklungsrechner: Fenster, keine GPIO-Knoepfe
# (Pfeiltasten), die eingebaute Webcam in beiden Panes. Kein eigener Branch --
# der liefe dem Automaten davon. Der Automat ist Linux, also aendert das dort nichts.
MAC        = sys.platform == "darwin"
FULLSCREEN = os.environ.get("PNP_FULLSCREEN", "0" if MAC else "1") != "0"
FPSLOG     = os.environ.get("PNP_FPSLOG") == "1"
# Kostete bei 60 Hz gemessen 12 bis 19 %. Bei 30 fps ist das Budget da, und
# Tearing quer durch eine Pixelschrift sieht man aus 8 m sofort. Bleibt an.
VSYNC      = os.environ.get("PNP_VSYNC", "1") != "0"

# OpenCV-Threads fuer remap und multiply im Renderpfad. Drei, nicht vier: der
# vierte Kern gehoert dem Teleop-Prozess (CPUAffinity=3 in seiner Unit). Ohne
# diese Zeile nimmt sich OpenCV alle Kerne und verdraengt genau den Loop, der
# als einziger terminkritisch ist.
CV_THREADS = int(os.environ.get("PNP_CV_THREADS", "3"))

# Die eine Zeile, die sagt was die vier Knoepfe tun -- in jeder Szene an
# derselben Stelle. Szeneninhalt endet ueber SAFE_BOTTOM, damit eine
# wachsende Liste (Bestenliste aus der DB) nie in den Footer hineinlaeuft.
# Abstand von der Unterkante, nicht Anteil der Hoehe: das Band ist eine feste
# Zeile am Bildrand, es skaliert nicht mit. 80 und 160 wie vorher bei 1200.
FOOTER_Y    = 1000
SAFE_BOTTOM = 920

# ── Zeiten (Sekunden) ─────────────────────────────────────────────────────
ROUND_SECONDS = 60
WARN_SECONDS  = 5     # ab hier faerbt sich der Bildschirm
IDLE_TIMEOUT  = 20    # Nicht-Idle-Szenen fallen von allein zurueck
CONFIRM_SECONDS = 3   # Fenster fuer die Abbruch-Doppelbestaetigung
PERFECT_HOLD  = 5.0   # so lange muss OFF BY 0 stehen, dann ist die Runde vorbei

# ponytail: >-Taps in der Runde, die sie sofort beenden. 0 = aus (Automat)
CHEAT_TAPS = 5

# ── Thema ─────────────────────────────────────────────────────────────────
# Farben, Texte, Sprites, LED-Farben und welches Sprite zu welchem Marker
# gehoert, stehen in EINER Datei: themes/<name>.py. Umschalten ohne Codeaenderung:
#   PNP_THEME=pcb uv run game/main.py
# Die Namen unten sind der Vertrag -- jedes Thema liefert genau diese, und
# `uv run game/sprites.py` prueft das fuer alle Dateien in themes/.
# Neues Thema: sugar_rush.py kopieren, der Kopf der Datei sagt, was zu tun ist.
THEME = os.environ.get("PNP_THEME", "sugar_rush")
THEME_KEYS = ("BG", "GREY", "WHITE", "ACCENT", "CANDY", "HOWTO",
              "LED_A", "LED_B", "BASE", "SHAPES", "SPRITES", "SPRITE")
_theme = importlib.import_module(f"themes.{THEME}")
(BG, GREY, WHITE, ACCENT, CANDY, HOWTO,
 LED_A, LED_B, BASE, SHAPES, SPRITES, SPRITE) = (getattr(_theme, k) for k in THEME_KEYS)

# ── Farben ────────────────────────────────────────────────────────────────
# Sechs Farben als Leiter von leise nach laut, jede mit genau einem Job:
#   BG Grund · GREY Beschriftung · WHITE neutrale Werte · ACCENT was der
#   Besucher beeinflusst (alle vier aus dem Thema) · ORANGE Warnung · RED die
#   letzten Sekunden. Die beiden bleiben HPI, egal welches Thema:
ORANGE = (222, 98, 7)       # HPI #DE6207
RED    = (177, 7, 58)       # HPI #B1073A

# Die Farben der vier Arcade-Knoepfe. Eigene Leiter, absichtlich neben der
# obigen: sie sagen nichts ueber den Spielstand, sondern welcher *physische*
# Knopf gemeint ist. Deshalb kommen sie an genau einer Stelle vor -- im
# Footer-Band, der einzigen Zeile, in der nie ein Spielwert steht. Damit bleibt
# die Regel "eine Farbe, ein Job" heil. Seit ACCENT pink ist, kommt Gelb
# ueberhaupt nur noch am Knopf vor.
BTN_GREEN  = (0, 208, 96)     # rechts -- vorwaerts, bestaetigen
BTN_RED    = (255, 72, 72)    # links  -- zurueck, abbrechen
BTN_BLUE   = (64, 156, 255)   # hoch
BTN_YELLOW = (255, 200, 0)    # runter
# BTN_RED ist deutlich heller als RED, und das ist kein Geschmack: in den
# letzten fuenf Sekunden faerbt sich der Grund nach RED, und ein Glyph im
# selben Ton waere dann genau dort weg, wo "ABBRECHEN" am ehesten gebraucht
# wird.

# ── Schrift ───────────────────────────────────────────────────────────────
# Press Start 2P (SIL OFL, liegt in assets/). 8x8-Raster: Groesse / 8 ist die
# Kantenlaenge eines Glyphenpixels, deshalb sind alle Groessen durch 8 teilbar
# — sonst werden die Pixel innerhalb einer Glyphe ungleich gross.
# Pfad aus __file__, nicht relativ zum cwd: der systemd-Start hat ein anderes.
FONT_PATH  = os.path.join(os.path.dirname(__file__), "assets",
                          "PressStart2P-Regular.ttf")
FONT_SIZES = {"big": 168, "mid": 88, "small": 48, "tiny": 32}

# ── CRT-Overlay ───────────────────────────────────────────────────────────
# PNP_CRT=0 und PNP_BARREL=0 schalten die beiden zum Messen ab, ohne die Datei
# anzufassen. Gedacht fuer A/B-Laeufe auf dem Pi, der Automat nimmt die Defaults.
CRT            = os.environ.get("PNP_CRT", "1") != "0"
SCANLINE_STEP  = 3     # jede dritte Zeile abdunkeln
SCANLINE_ALPHA = 60    # in der Halle einstellen, im Zweifel runter
VIGNETTE_ALPHA = 90    # Abdunklung in den Ecken
BARREL_K       = float(os.environ.get("PNP_BARREL", "0.05"))
                       # Woelbung der Scanlines und nichts weiter: sie kruemmen
                       # sich damit wie auf einer Roehre und ruecken zum Rand
                       # hin zusammen. Kostet zur Laufzeit nichts, die Karte
                       # steht beim Start. 0 = waagerechte Zeilen.
                       # Das Bild selbst wird nicht mehr gewoelbt, siehe
                       # crt_gain() in app.py

# ── Sound ─────────────────────────────────────────────────────────────────
# Die Musik geht unter jedem Effekt kurz zurueck. Auf echter Arcade-Hardware
# passierte das von selbst: NES und C64 hatten vier bis fuenf Stimmen, und ein
# Effekt hat sich eine davon genommen. Hier ist es ein Kanalvolumen, weicher.
DUCK         = 0.55   # Musikpegel waehrend eines Effekts (~-5 dB)
DUCK_RELEASE = 0.35   # Sekunden zurueck auf voll

# ── Spielwerte ────────────────────────────────────────────────────────────
# marker_id -> Punktwert. Aenderbar ohne Codeaenderung, das ist der ganze
# Grund fuer ArUco statt eines trainierten Modells.
#
# Genau ein Marker pro physischem Puck. ArucoDetector.marks ist ein Dict mit
# der ID als Schluessel -- zwei Pucks mit demselben Marker zaehlen einmal, und
# das waere ein stiller Wertungsfehler, der wie ein Erkennungsproblem aussieht.
#
# Werte ohne gemeinsamen Teiler (ggT 1). Waren sie wie frueher alle durch 5
# teilbar, war das Spiel binaer: Distanz durch 5 teilbar -> ein Puck genuegt,
# sonst gar nicht erreichbar. Gemessen ueber die Distanzen 30..120 waren von
# 76 Distanzen, die kein einzelner Zug schafft, nur 4 in zwei Zuegen loesbar.
# Mit diesem Satz sind es 71 von 74 -- erst damit gibt es "knapp daneben".
VALUES = {0: 4, 1: 7, 2: 12, 3: 18, 4: 23,
          5: 29, 6: 36, 7: 44, 8: 53, 9: 67}

# Der Zielwert wird nicht mehr frei gewuerfelt, sondern als Distanz zur
# tatsaechlichen Tablettsumme gewaehlt (siehe balance.py). Sonst entscheidet
# der Zufall, ob jemand 3 oder 200 Punkte zu ueberbruecken hat, und die
# Bestenliste vergleicht Runden, die nichts miteinander zu tun haben.
GAP_MIN, GAP_MAX = 25, 130
GAP_MOVES    = 3   # so viele Zuege darf die perfekte Loesung kosten
GAP_ONE_MISS = 2   # so weit muss ein einzelner Zug mindestens danebenliegen
GAP_ONE_MAX  = 15  # ... und so weit hoechstens. Beidseitig, sonst laesst eine
                   # Runde nach dem besten Einzelzug 2 offen und die naechste
                   # 67 -- dieselbe Unfairness, nur eine Ebene tiefer

# ── Zwischenszene ─────────────────────────────────────────────────────────
# Der Idle-Screen ist stumm, die Musik faengt hier an. Sechs Stunden Chiptune
# als Dauerteppich sind anstrengend -- und sie markieren nichts. Mit stillem
# Idle wird der Musikeinsatz zum Signal "es geht los".
DEMO_VIDEO = None            # Pfad zum Clip. None = nur Text, Szene laeuft trotzdem
DEMO_SIZE  = (1024, 576)     # 16:9 -- andere Ratio verzerrt, wie bei CAM_VIEW
# HOWTO steht im Thema.

# ── Persistenz ────────────────────────────────────────────────────────────
DB_PATH = "scores.db"
TOP_N   = 10

# ── Eingabe ───────────────────────────────────────────────────────────────
# Vier Arcade-Knoepfe, sonst nichts. Konvention im ganzen Spiel:
#   right   = vorwaerts / bestaetigen
#   left    = zurueck / abbrechen
#   up/down = auswaehlen
KEYMAP = {
    pygame.K_UP:   "up",   pygame.K_DOWN:  "down",
    pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    pygame.K_q:    "quit",   # ponytail: nur Entwicklung, am Automaten gibt es das nicht
}

# Der physische Knopf hinter jeder Richtung, als Farbe und als Glyph. Die
# Hinweiszeile faerbt jeden Pfeil damit ein, und das ist die ganze
# Bedienungsanleitung: der Besucher sucht die Farbe, nicht die Richtung.
# Gruen = los, Rot = zurueck sind die einzigen zwei Farbbedeutungen, die jeder
# mitbringt; Blau und Gelb sind frei und deshalb einfach oben und unten.
BUTTON_COLORS = {"up": BTN_BLUE, "down": BTN_YELLOW,
                 "left": BTN_RED, "right": BTN_GREEN}
ARROWS = {"▲": "up", "▼": "down", "◀": "left", "▶": "right"}

# Halten scrollt durch die Buchstaben: (Verzoegerung, Wiederholrate) in ms
KEY_REPEAT = (400, 60)

# ── Hardware ──────────────────────────────────────────────────────────────
CAMERA        = os.environ.get("PNP_CAMERA", "1") != "0"   # 0 = FakeDetector
# (Arm-Kamera, Top-Down). Zweimal derselbe Index = eine Webcam in beiden
# Panes, das ist der Layout-Mock.
# Der Detector haengt immer an der zweiten, der Top-Down-Kamera.
#
# Am Automaten (9.9.2026 am Bild geprueft, nicht geraten): video0 steht seitlich
# und um 90 Grad gedreht am Arm, video2 schaut senkrecht auf das Tablett.
# NICHT (0, 1): video1 und video3 sind Metadata-Nodes und liefern kein Bild.
CAM_INDEXES   = (0, 0) if MAC else (0, 2)
CAM_SIZE      = (1280, 720)
# 544 x 306 ist exakt 16:9 (544 * 9/16 = 306) — andere Ratio verzerrt.
# Kleiner als die frueheren 800 x 450: der Balken und die Handlungsanweisung
# liegen jetzt darueber und brauchen den Platz. Die Panes sind Kontrolle, kein
# Spielinhalt; aus 8 m liest ohnehin niemand ein Kamerabild.
CAM_VIEW      = (544, 306)
CAM_POS       = ((490, 757), (1430, 757))   # Mittelpunkte, links Arm
MARKER_HOLD   = 0.5    # Hysterese: Marker zaehlt weiter, solange kuerzer verdeckt
DETECT_HZ     = 15     # Erkennungsrate, entkoppelt von den 60 FPS
# Detektionsfenster der Top-Down-Kamera, als Anteile (x, y, breite, hoehe).
# Die Weitwinkellinse sieht sonst den halben Messestand mit; erkannt wird nur,
# was hier drin liegt. Das Rechteck wird ins Bild gezeichnet, also stellt man
# es in der Halle beim Ausrichten der Kamera ein und sieht sofort das Ergebnis.
TRAY_ROI      = (0.20, 0.15, 0.60, 0.70)
MARK_FONT     = "tiny"    # Schriftgroesse der eingeblendeten Werte.
                          # Mit dem Pane von 800 auf 544 mitgegangen,
                          # sonst deckt die Zahl den Puck zu.
MARK_WIDTH    = 5         # Strichstaerke des Detektionsfensters
# ── Knoepfe ───────────────────────────────────────────────────────────────
# BCM-Nummern, nicht Header-Pins. 17 · 27 · 22 · 23 sind Header 11 · 13 · 15 · 16,
# also vier benachbarte Loecher mit Masse bei 9, 14 und 20 gleich daneben --
# ein Pfostenstecker, keine Springerei ueber das Board.
#
# Warum nicht irgendwelche: der Header ist zur Haelfte schon vergeben und die
# Kollisionen fallen erst auf, wenn das Kabel dran ist.
#   0, 1       ID-EEPROM des HAT-Steckplatzes
#   2, 3       I2C, haben feste 1,8-kOhm-Pull-ups auf dem Board
#   4          1-Wire, Standardpin
#   7..11      SPI0 -- bleibt frei, da haengt der LED-Streifen dran, falls er
#              nicht an einen ESP32 geht. GPIO 10 (MOSI) ist der Datenpin.
#   12, 13     Hardware-PWM
#   14, 15     serielle Konsole
#   18..21     PCM/I2S, falls Ton ueber ein Audio-HAT geht
# Uebrig bleiben 5, 6, 16, 17, 22, 23, 24, 25, 26, 27. Vier davon, benachbart.
#
# Taster gegen GND, interner Pull-up, gedrueckt = LOW. Kein Widerstand,
# kein Kondensator: das Entprellen macht gpiozero.
#
# Der Not-Aus ist NICHT hier. Er sitzt in der Servo-Stromversorgung und trennt
# 12 V. Ein Not-Aus, der erst durch Python muss, ist keiner.
BUTTON_PINS   = {17: "up", 27: "down", 22: "left", 23: "right"}
# Wie CAMERA: Default ist der Automat, PNP_BUTTONS=0 zum Entwickeln ohne GPIO.
BUTTONS       = os.environ.get("PNP_BUTTONS", "0" if MAC else "1") != "0"

# ── LED-Streifen ──────────────────────────────────────────────────────────
# WS2812-Protokoll ueber SPI0, Daten auf GPIO 10 (Header 19), Pegelwandler
# 3,3 -> 5 V dazwischen. Kein Umschalter noetig: fehlt das Geraet (Mac, SPI
# nicht aktiviert), bleiben die LEDs stumm -- wie Music ohne Audiogeraet.
LED_DEV     = "/dev/spidev0.0"
LED_COUNT   = 480     # ponytail: geraten, 3 m x 160/m. Zaehlt, sobald der Streifen da ist
LED_ORDER   = "GRB"   # WS2812B. WS2811-Streifen (12/24 V) sind oft RGB -- am Streifen pruefen
LED_BRIGHT  = 0.3     # Strombudget: 3 m FCOB bei Vollweiss ~8,5 A an 5 V. Das ist
                      # Netzteil- und Waermefrage in einer Zahl, nicht Geschmack
LED_FPS     = 30
LED_STRIPES = 24      # Zuckerstangen-Streifen ueber die ganze Laenge, dichteunabhaengig
# LED_A / LED_B (Zuckerstange, Balken) kommen aus dem Thema; Rot bleibt HPI:
LED_RED     = (255, 0, 20)
