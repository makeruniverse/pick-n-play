import math
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
    views: tuple = ()        # Kamera-Passthrough, leer = kein Bild
    demo: object = None      # VideoView der Zwischenszene, None = nur Text

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


def crt_overlay(w, h):
    """Scanlines + Vignette. Einmal gebaut, danach ein Blit pro Frame."""
    o = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, SCANLINE_STEP):
        o.fill((0, 0, 0, SCANLINE_ALPHA), (0, y, w, 1))
    # ponytail: 16x10-Alphagitter, hochskaliert = weicher Radialverlauf. Spart
    # die Distanzrechnung fuer 2,3 Mio Pixel, und weich ist es sowieso.
    v = pygame.Surface((16, 10), pygame.SRCALPHA)
    for y in range(10):
        for x in range(16):
            d = math.hypot(x / 15 - .5, y / 9 - .5) / .5
            v.set_at((x, y), (0, 0, 0, min(255, int(VIGNETTE_ALPHA * d * d))))
    # ADD statt normalem Blit: beide Ebenen sind reines Schwarz, nur das Alpha
    # addiert sich. Haengt an keiner pygame-Version.
    o.blit(pygame.transform.smoothscale(v, (w, h)), (0, 0),
           special_flags=pygame.BLEND_RGBA_ADD)
    return o


def barrel_maps(w, h, k):
    """Woelbung als Nachschlagetabelle: fuer jedes Zielpixel die Quellkoordinate."""
    y, x = np.indices((h, w), dtype=np.float32)
    nx = x / (w - 1) * 2 - 1
    ny = y / (h - 1) * 2 - 1
    f = 1 + k * (nx * nx + ny * ny)   # aussen weiter aussen greifen = Woelbung
    return cv2.convertMaps((nx * f + 1) / 2 * (w - 1),
                           (ny * f + 1) / 2 * (h - 1), cv2.CV_16SC2)


def px(s):
    """(h,w,4)-Sicht auf die Pixel einer 32-Bit-Surface, ohne Kopie.

    Nicht surfarray.pixels3d: das liefert RGB, pygame speichert BGRA, also hat
    die Sicht auf der Farbachse Schrittweite -1 und OpenCV kopiert erst — 8,3 ms
    statt 1,4. Die Farbreihenfolge ist egal, remap verschiebt nur Pixel.
    """
    return np.asarray(s.get_view("2")).T.view(np.uint8).reshape(
        s.get_height(), s.get_width(), 4)


def run_game(scene, width, height, fps):
    pygame.init()
    flags = pygame.SCALED | (pygame.FULLSCREEN if FULLSCREEN else 0)
    screen = pygame.display.set_mode((width, height), flags, vsync=1)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    pygame.key.set_repeat(*KEY_REPEAT)
    dt = 0.0

    # Der Loop traegt den CRT-Effekt, nicht die Szene: er liegt ueber allem,
    # also gehoert er an die eine Stelle, an der alles zusammenlaeuft.
    overlay = crt_overlay(width, height) if CRT else None
    maps    = barrel_maps(width, height, BARREL_K) if CRT and BARREL_K else None
    frame   = pygame.Surface((width, height)).convert(screen) if maps else screen

    while scene is not None:
        for e in pygame.event.get():
            action = action_of(e)
            if action == "quit":
                scene = None
                break
            if action:
                # Jeder Knopfdruck klingt: "ok" wenn die Szene ihn genommen hat,
                # sonst "nope". handle() gibt den Namen zurueck, None heisst nope.
                scene.ctx.music.sfx(scene.handle(action) or "nope")
        if scene is None:
            break

        scene.ctx.music.update()
        scene.update(dt)
        scene.render(frame)
        if maps:
            # Die px()-Sichten sperren ihre Surface. Als Argumente direkt im
            # Aufruf sterben sie mit der Zeile — sonst scheitert der Blit
            # darunter mit "Surfaces must not be locked during blit".
            # NEAREST, nicht LINEAR: schneller, und bilinear verwaschen waere
            # die Pixelfont.
            cv2.remap(px(frame), *maps, cv2.INTER_NEAREST, dst=px(screen))
        if overlay:
            screen.blit(overlay, (0, 0))
        pygame.display.flip()

        # Tickrate der Szene, die gerade lief — vor dem Wechsel, damit der
        # Uebergang nicht mit der Rate der naechsten Szene abgerechnet wird.
        dt = clock.tick(scene.TICK or fps) / 1000
        scene = scene.next

    pygame.quit()


