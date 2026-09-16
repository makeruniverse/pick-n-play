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
    views: tuple = ()        # Camera passthrough, blank = no image
    demo: object = None      # VideoView of the Intermediate Scene, None = only text

class SceneBase:
    MUSIC = "idle"       # None = the scene regulates it itself (GameScene)
    MUSIC_IN = (0.0, 0)  # (delay in seconds, fade-in in milliseconds)
    TICK  = None         # custom frame rate, None = FPS from config

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
    """Scanlines + Vignette. Once built, then a Blit per frame."""
    o = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, SCANLINE_STEP):
        o.fill((0, 0, 0, SCANLINE_ALPHA), (0, y, w, 1))
    # ponytail: 16x10-Alphagitter, hochskaliert = weicher Radialverlauf. Spart
    # the distance calculation for 2.3 million pixels, and soft is anyway.
    v = pygame.Surface((16, 10), pygame.SRCALPHA)
    for y in range(10):
        for x in range(16):
            d = math.hypot(x / 15 - .5, y / 9 - .5) / .5
            v.set_at((x, y), (0, 0, 0, min(255, int(VIGNETTE_ALPHA * d * d))))
    # ADD instead of normal Blit: both levels are pure black, only the alpha
    # adds up. No pygame version.
    o.blit(pygame.transform.smoothscale(v, (w, h)), (0, 0),
           special_flags=pygame.BLEND_RGBA_ADD)
    return o


def barrel_maps(w, h, k):
    """Wooling as a reference table: for each target pixel the source coordinate."""
    y, x = np.indices((h, w), dtype=np.float32)
    nx = x / (w - 1) * 2 - 1
    ny = y / (h - 1) * 2 - 1
    f = 1 + k * (nx * nx + ny * ny)   # aussen weiter aussen greifen = Woelbung
    return cv2.convertMaps((nx * f + 1) / 2 * (w - 1),
                           (ny * f + 1) / 2 * (h - 1), cv2.CV_16SC2)


def px(s):
    """(h,w,4) view on the pixels of a 32-bit interface, without copy.

Not surfarray.pixels3d: that supplies RGB, pygame stores BGRA, so has
the view on the color axis step width -1 and OpenCV copied only — 8.3 ms
instead of 1.4. The color order is no matter, remap only shifts pixels.
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

    # The loop carries the CRT effect, not the scene: it lies above all,
    # So he puts the one place where everything goes together.
    overlay = crt_overlay(width, height) if CRT else None
    maps    = barrel_maps(width, height, BARREL_K) if CRT and BARREL_K else None
    frame   = pygame.Surface((width, height)).convert(screen) if maps else screen
    ticks   = 0

    while scene is not None:
        for e in pygame.event.get():
            action = action_of(e)
            if action == "quit":
                scene = None
                break
            if action:
                # Every push of a button sounds: "ok" when the scene took it,
                # otherwise "nope". handle() gives the name back, None heisst nope.
                scene.ctx.music.sfx(scene.handle(action) or "nope")
        if scene is None:
            break

        scene.ctx.music.update()
        scene.update(dt)
        scene.render(frame)
        if maps:
            # The px() lines lock their surface. As arguments directly in
            # Call them to the line — otherwise the Blit fails
            # "Surfaces must not be locked during blit".
            # NEAREST, not LINEAR: faster, and bilinear washed waere
            # the Pixelfont.
            cv2.remap(px(frame), *maps, cv2.INTER_NEAREST, dst=px(screen))
        if overlay:
            screen.blit(overlay, (0, 0))
        pygame.display.flip()

        # Tickrate of the scene that just ran — before the change so that the
        # transition is not calculated with the rate of the next scene.
        dt = clock.tick(scene.TICK or fps) / 1000
        # Without output, a measurement on the Pi is blind: there is no
        # Developer on the screen, but an SSH session on the stdout.
        ticks += 1
        if FPSLOG and ticks % 60 == 0:
            print(f"{clock.get_fps():5.1f} fps  {type(scene).__name__}", flush=True)
        scene = scene.next

    pygame.quit()

