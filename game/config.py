import os
import pygame

# ── Anzeige ───────────────────────────────────────────────────────────────
# Entwurfsaufloesung = Panelaufloesung des Asus 15" (16:10). Jede Koordinate
# in scenes.py ist eine absolute Zahl fuer dieses Raster. pygame.SCALED faengt
# ein abweichendes Panel ab, ohne dass hier etwas geaendert werden muss.
WIDTH, HEIGHT = 1920, 1200
FPS = 60
IDLE_FPS = 20        # der Idle-Screen aendert sich zweimal pro Sekunde. 60 Hz
                     # dafuer sind sechs Stunden Waerme fuer nichts.
# Default ist der Automat. Zum Entwickeln und fuer Fernwartung ueber SSH lassen
# sich die drei per Umgebungsvariable umschalten, ohne die Datei zu aendern
# (sonst ueberschreibt das naechste git pull die lokale Anpassung):
#   PNP_FULLSCREEN=0  Fenster statt Vollbild
#   PNP_CAMERA=0      FakeDetector, kein Kamerazugriff
#   PNP_FPSLOG=1      Bildrate einmal pro Sekunde auf stdout
FULLSCREEN = os.environ.get("PNP_FULLSCREEN", "1") != "0"
FPSLOG     = os.environ.get("PNP_FPSLOG") == "1"

# Die eine Zeile, die sagt was die vier Knoepfe tun -- in jeder Szene an
# derselben Stelle. Szeneninhalt endet ueber SAFE_BOTTOM, damit eine
# wachsende Liste (Bestenliste aus der DB) nie in den Footer hineinlaeuft.
FOOTER_Y    = 1120
SAFE_BOTTOM = 1040

# ── Zeiten (Sekunden) ─────────────────────────────────────────────────────
ROUND_SECONDS = 60
WARN_SECONDS  = 5     # ab hier faerbt sich der Bildschirm
IDLE_TIMEOUT  = 20    # Nicht-Idle-Szenen fallen von allein zurueck
CONFIRM_SECONDS = 3   # Fenster fuer die Abbruch-Doppelbestaetigung
PERFECT_HOLD  = 5.0   # so lange muss OFF BY 0 stehen, dann ist die Runde vorbei

# ponytail: >-Taps in der Runde, die sie sofort beenden. 0 = aus (Automat)
CHEAT_TAPS = 5

# ── Farben ────────────────────────────────────────────────────────────────
# Schwarzer Grund, hoher Kontrast, HPI-Rot und -Orange direkt aus dem Logo.
# Sechs Farben als Leiter von leise nach laut, jede mit genau einem Job:
BLACK  = (0, 0, 0)          # Grund, immer
GREY   = (120, 120, 120)    # Beschriftungen
WHITE  = (240, 240, 240)    # neutrale Werte
YELLOW = (255, 200, 0)      # was der Besucher gerade beeinflusst
ORANGE = (222, 98, 7)       # Warnung          (HPI #DE6207)
RED    = (177, 7, 58)       # die letzten Sekunden (HPI #B1073A)
# YELLOW ist heller als das HPI-Gelb #F7A900 — auf Schwarz gewinnt aus 8 m
# das hellere, und im Vergleich mit dem Logo sieht man den Unterschied nicht.

# ── Schrift ───────────────────────────────────────────────────────────────
# Press Start 2P (SIL OFL, liegt in assets/). 8x8-Raster: Groesse / 8 ist die
# Kantenlaenge eines Glyphenpixels, deshalb sind alle Groessen durch 8 teilbar
# — sonst werden die Pixel innerhalb einer Glyphe ungleich gross.
# Pfad aus __file__, nicht relativ zum cwd: der systemd-Start hat ein anderes.
FONT_PATH  = os.path.join(os.path.dirname(__file__), "assets",
                          "PressStart2P-Regular.ttf")
FONT_SIZES = {"big": 168, "mid": 88, "small": 48, "tiny": 32}

# ── CRT-Overlay ───────────────────────────────────────────────────────────
CRT            = True
SCANLINE_STEP  = 3     # jede dritte Zeile abdunkeln
SCANLINE_ALPHA = 60    # in der Halle einstellen, im Zweifel runter
VIGNETTE_ALPHA = 90    # Abdunklung in den Ecken
BARREL_K       = 0.05  # Woelbung. 0 schaltet nur sie ab, Scanlines bleiben —
                       # das ist der teure Posten, falls der Pi nicht mitkommt

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
DEMO_SIZE  = (1120, 630)     # 16:9 -- andere Ratio verzerrt, wie bei CAM_VIEW
HOWTO = ("EVERY PUCK HAS A HIDDEN PRICE",
         "MOVE THEM UNTIL TOTAL MEETS GOAL",
         "60 SECONDS. CLOSEST WINS.")

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
CAM_INDEXES   = (0, 2)
CAM_SIZE      = (1280, 720)
CAM_VIEW      = (880, 495)     # 16:9 wie CAM_SIZE — andere Ratio verzerrt
CAM_POS       = ((490, 740), (1430, 740))   # Mittelpunkte, links Arm
MARKER_HOLD   = 0.5    # Hysterese: Marker zaehlt weiter, solange kuerzer verdeckt
DETECT_HZ     = 15     # Erkennungsrate, entkoppelt von den 60 FPS
# Detektionsfenster der Top-Down-Kamera, als Anteile (x, y, breite, hoehe).
# Die Weitwinkellinse sieht sonst den halben Messestand mit; erkannt wird nur,
# was hier drin liegt. Das Rechteck wird ins Bild gezeichnet, also stellt man
# es in der Halle beim Ausrichten der Kamera ein und sieht sofort das Ergebnis.
TRAY_ROI      = (0.20, 0.15, 0.60, 0.70)
MARK_FONT     = "small"   # Schriftgroesse der eingeblendeten Werte
MARK_WIDTH    = 5         # Strichstaerke des Detektionsfensters
BUTTON_PINS   = {17: "up", 27: "down", 22: "left", 23: "right"}
