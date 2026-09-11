import cv2
import numpy as np
import pygame
from dataclasses import dataclass
from config import *


@dataclass
class Ctx:
    detector: object
    db: object
    fonts: dict
    music: object
    leds: object             # immer da, ohne Streifen stumm -- wie music
    views: tuple = ()        # Kamera-Passthrough, leer = kein Bild
    demo: object = None      # VideoView der Zwischenszene, None = nur Text
    buttons: object = None   # GPIO-Taster, None = nur Tastatur

class SceneBase:
    MUSIC = "idle"       # None = die Szene regelt es selbst (GameScene)
    MUSIC_IN = (0.0, 0)  # (Pause in Sekunden, Einblendung in Millisekunden)
    TICK  = None         # abweichende Bildrate, None = FPS aus config

    def __init__(self, ctx):
        self.ctx = ctx
        self.next = self
        if self.MUSIC:
            ctx.music.play(self.MUSIC, *self.MUSIC_IN)

    def handle(self, action): pass
    def update(self, dt):     pass
    def render(self, screen): pass

    def switch_to(self, scene):
        self.next = scene

def action_of(e):
    if e.type == pygame.QUIT:
        return "quit"
    if e.type == pygame.KEYDOWN:
        return KEYMAP.get(e.key)
    return None


def crt_gain(w, h, k):
    """Scanlines + Vignette als Helligkeitsfaktor je Pixel. Einmal gebaut.

    Schwarz mit Alpha a ueberblenden ist algebraisch nichts als
    dst * (1 - a/255) -- eine Multiplikation, und die Karte dafuer steht beim
    Start. Zur Laufzeit bleibt ein cv2.multiply ueber das fertige Bild.

    **Die Woelbung steckt in dieser Karte, nicht im Bild.** Vorher warpte ein
    cv2.remap das ganze Bild. Gemessen am 10.9.2026 am Automaten kostete das
    25,0 ms pro Bild, die gewoelbte Karte kostet 11,1 -- also genau so viel
    wie gar keine Woelbung, weil sie beim Start gebaut wird und zur Laufzeit
    nichts mehr tut.

    Der zweite Grund ist wichtiger als die Millisekunden: remap tastet mit
    NEAREST ab, und ein 8x8-Glyphenraster auf nicht-ganzzahlige Positionen
    abgetastet franst aus. Die Woelbung zerlegte die Pixelschrift -- genau der
    Effekt, vor dem FONT_SIZES in config.py warnt, nur von der anderen Seite.
    Aus 3-8 m liest sich eine Roehre ohnehin an den Zeilen, nicht an der
    Geometrie.

    Die Scanlinephase kommt aus der *gewoelbten* Quellzeile: die Zeilen
    kruemmen sich wie auf einer Roehre und ruecken zum Bildrand hin zusammen.
    Als Deckungsgrad gerechnet, nicht abgetastet -- ein punktweise gewarptes
    3-px-Muster gibt sonst Moirestreifen am Rand.

    Woelbung *des Bildes* mit scharfer Schrift ginge als GLES-Fragmentshader
    auf dem VideoCore, mit korrekter Filterung und ohne Bildratenkosten.
    Bewusst nicht gebaut, siehe "CRT-Overlay" im Overview.

    Der vierte Kanal bleibt 255: das Alphabyte der Anzeigeflaeche wird nicht
    benutzt, also wird es auch nicht gedunkelt.
    """
    y, x = np.indices((h, w), dtype=np.float32)
    nx = x / (w - 1) * 2 - 1
    ny = y / (h - 1) * 2 - 1
    # Vignette aus dem *ungewoelbten* Radius, unveraendert gegenueber frueher:
    # einen weichen Radialverlauf um 10 % zu kruemmen sieht niemand, und so
    # bleibt die Abdunklung genau die, die in der Halle eingestellt wird.
    a = VIGNETTE_ALPHA * (nx * nx + ny * ny)          # Ecke = 2 x ALPHA
    f  = 1 + k * (nx * nx + ny * ny)   # aussen weiter aussen greifen = Woelbung
    sy = (ny * f + 1) / 2 * (h - 1)    # gewoelbte Quellzeile, gebrochen
    ph = np.mod(sy, SCANLINE_STEP)
    # Dreieckiger Deckungsgrad um die dunkle Zeile. Bei k = 0 faellt das auf
    # ein Bit genau auf "jede dritte Zeile ganz dunkel" zurueck, also auf das
    # Bisherige (nachgerechnet, groesste Abweichung 1 von 255).
    a += SCANLINE_ALPHA * (np.clip(1 - ph, 0, 1)
                           + np.clip(1 - (SCANLINE_STEP - ph), 0, 1))
    return cv2.cvtColor(np.clip(255 - a, 0, 255).astype(np.uint8),
                        cv2.COLOR_GRAY2BGRA)


def px(s):
    """(h,w,4)-Sicht auf die Pixel einer 32-Bit-Surface, ohne Kopie.

    Nicht surfarray.pixels3d: das liefert RGB, pygame speichert BGRA, also hat
    die Sicht auf der Farbachse Schrittweite -1 und OpenCV kopiert erst — 8,3 ms
    statt 1,4. Die Farbreihenfolge ist egal: die Verdunklungskarte ist grau,
    alle drei Farbkanaele bekommen denselben Faktor.
    """
    return np.asarray(s.get_view("2")).T.view(np.uint8).reshape(
        s.get_height(), s.get_width(), 4)


def run_game(scene, width, height, fps):
    pygame.init()
    # Kein pygame.SCALED mehr: die Entwurfsaufloesung *ist* die
    # Panelaufloesung, es gibt nichts zu skalieren. vsync ohne SCALED ist
    # backendabhaengig -- scheitert set_mode daran, ist Tearing besser als
    # gar kein Bild, und der Schalter zum Nachmessen steht in config.py.
    # Im Fenster skaliert: 1920 x 1080 passt nicht auf das MacBook-Display
    # (1728 Punkte breit). Am Automaten laeuft Vollbild, dort greift das nie.
    flags = pygame.FULLSCREEN if FULLSCREEN else pygame.SCALED | pygame.RESIZABLE
    try:
        screen = pygame.display.set_mode((width, height), flags, vsync=VSYNC)
    except pygame.error:
        screen = pygame.display.set_mode((width, height), flags)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    pygame.key.set_repeat(*KEY_REPEAT)
    dt = 0.0

    # Der Loop traegt den CRT-Effekt, nicht die Szene: er liegt ueber allem,
    # also gehoert er an die eine Stelle, an der alles zusammenlaeuft.
    gain  = crt_gain(width, height, BARREL_K) if CRT else None
    ticks = 0

    while scene is not None:
        # Tastatur und GPIO laufen an genau einer Stelle zusammen. Die Szene
        # sieht danach nur noch vier Strings und kann nicht wissen, woher sie
        # kommen -- deshalb aendert der Anschluss der Knoepfe in scenes.py
        # keine Zeile. dt ist das des letzten Bildes: dieselbe Zahl, mit der
        # die Runde runterzaehlt, also auch fuer die Tastenwiederholung.
        actions = [a for e in pygame.event.get() if (a := action_of(e))]
        if scene.ctx.buttons:
            actions += scene.ctx.buttons.pump(dt)
        for action in actions:
            if action == "quit":
                scene = None
                break
            # Jeder Knopfdruck klingt: "ok" wenn die Szene ihn genommen hat,
            # sonst "nope". handle() gibt den Namen zurueck, None heisst nope.
            scene.ctx.music.sfx(scene.handle(action) or "nope")
        if scene is None:
            break

        scene.ctx.music.update()
        scene.update(dt)
        scene.render(screen)
        if gain is not None:
            # Die px()-Sichten sperren ihre Surface. Als Argumente direkt im
            # Aufruf sterben sie mit der Zeile — sonst scheitert das Flip
            # darunter an einer gesperrten Flaeche.
            cv2.multiply(px(screen), gain, px(screen), 1 / 255)
        pygame.display.flip()

        # Tickrate der Szene, die gerade lief — vor dem Wechsel, damit der
        # Uebergang nicht mit der Rate der naechsten Szene abgerechnet wird.
        dt = clock.tick(scene.TICK or fps) / 1000
        # Ohne Ausgabe ist eine Messung auf dem Pi blind: dort haengt kein
        # Entwickler am Bildschirm, sondern eine SSH-Sitzung am stdout.
        ticks += 1
        if FPSLOG and ticks % fps == 0:
            print(f"{clock.get_fps():5.1f} fps  {type(scene).__name__}", flush=True)
        scene = scene.next

    pygame.quit()


