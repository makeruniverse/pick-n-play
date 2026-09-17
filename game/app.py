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
    leds: object             # always there, silent without a strip -- like music
    views: tuple = ()        # camera passthrough, empty = no image
    demo: object = None      # VideoView of the intermission scene, None = text only
    buttons: object = None   # GPIO buttons, None = keyboard only

class SceneBase:
    MUSIC = "idle"       # None = the scene handles it itself (GameScene)
    MUSIC_IN = (0.0, 0)  # (pause in seconds, fade-in in milliseconds)
    TICK  = None         # deviating frame rate, None = FPS from config

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
    """Scanlines as a per-pixel brightness factor. Built once.

    Blending black with alpha a is algebraically nothing but
    dst * (1 - a/255) -- a multiplication, and the map for that is ready at
    startup. At runtime only a cv2.multiply over the finished image remains.

    **The barrel distortion lives in this map, not in the image.** Previously
    a cv2.remap warped the whole image. Measured on the cabinet on 2026-09-10,
    that cost 25.0 ms per frame; the warped map costs 11.1 -- exactly as much
    as no distortion at all, because it's built at startup and does nothing
    more at runtime.

    The second reason matters more than the milliseconds: remap samples with
    NEAREST, and an 8x8 glyph grid sampled at non-integer positions frays.
    The distortion broke up the pixel font -- exactly the effect FONT_SIZES
    in config.py warns about, just from the other side. From 3-8 m a tube
    reads from its scanlines anyway, not from its geometry.

    The scanline phase comes from the *warped* source row: the lines curve as
    if on a tube and draw together toward the edge of the image. Computed as
    coverage, not sampled -- a point-wise warped 3-px pattern would otherwise
    give moire stripes at the edge.

    Warping *the image itself* with sharp text would work as a GLES fragment
    shader on the VideoCore, with correct filtering and no frame-rate cost.
    Deliberately not built, see "CRT overlay" in the overview.

    The fourth channel stays 255: the alpha byte of the display surface is
    not used, so it isn't darkened either.
    """
    y, x = np.indices((h, w), dtype=np.float32)
    nx = x / (w - 1) * 2 - 1
    ny = y / (h - 1) * 2 - 1
    # No vignette since 2026-09-16: the panel's poor viewing angles already
    # darken the edges, the dark corners made that worse.
    f  = 1 + k * (nx * nx + ny * ny)   # reach further out the further out = distortion
    sy = (ny * f + 1) / 2 * (h - 1)    # warped source row, fractional
    ph = np.mod(sy, SCANLINE_STEP)
    # Triangular coverage around the dark row. At k = 0 this falls back, to
    # within a bit, to "every third row fully dark", i.e. to the previous
    # behavior (verified by calculation, largest deviation 1 of 255).
    a = SCANLINE_ALPHA * (np.clip(1 - ph, 0, 1)
                           + np.clip(1 - (SCANLINE_STEP - ph), 0, 1))
    return cv2.cvtColor(np.clip(255 - a, 0, 255).astype(np.uint8),
                        cv2.COLOR_GRAY2BGRA)


def px(s):
    """(h,w,4) view onto the pixels of a 32-bit surface, without copying.

    Not surfarray.pixels3d: that returns RGB, pygame stores BGRA, so the view
    would have stride -1 on the color axis and OpenCV would copy first — 8.3 ms
    instead of 1.4. The color order doesn't matter: the darkening map is gray,
    all three color channels get the same factor.
    """
    return np.asarray(s.get_view("2")).T.view(np.uint8).reshape(
        s.get_height(), s.get_width(), 4)


def run_game(scene, width, height, fps, beat=None):
    pygame.init()
    # No more pygame.SCALED: the design resolution *is* the panel resolution,
    # there's nothing to scale. vsync without SCALED is backend-dependent --
    # if set_mode fails on that, tearing is better than no image at all, and
    # the switch for re-measuring is in config.py.
    # Scaled in windowed mode: 1920 x 1080 doesn't fit the MacBook display
    # (1728 points wide). The cabinet runs fullscreen, so this never kicks in there.
    flags = pygame.FULLSCREEN if FULLSCREEN else pygame.SCALED | pygame.RESIZABLE
    try:
        screen = pygame.display.set_mode((width, height), flags, vsync=VSYNC)
    except pygame.error:
        screen = pygame.display.set_mode((width, height), flags)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    pygame.key.set_repeat(*KEY_REPEAT)
    dt = 0.0

    # The loop carries the CRT effect, not the scene: it sits over
    # everything, so it belongs at the one place where everything converges.
    gain  = crt_gain(width, height, BARREL_K) if CRT else None
    ticks = 0

    while scene is not None:
        # Keyboard and GPIO come together at exactly one place. After that
        # the scene only sees four strings and can't know where they came
        # from -- that's why wiring up the buttons in scenes.py never
        # changes a line here. dt is that of the last frame: the same number
        # the round counts down with, so also for key repeat.
        actions = [a for e in pygame.event.get() if (a := action_of(e))]
        if scene.ctx.buttons:
            actions += scene.ctx.buttons.pump(dt)
        for action in actions:
            if action == "quit":
                scene = None
                break
            # Every button press makes a sound: "ok" if the scene took it,
            # otherwise "nope". handle() returns the name, None means nope.
            scene.ctx.music.sfx(scene.handle(action) or "nope")
        if scene is None:
            break

        scene.ctx.music.update()
        if beat:
            beat(scene)    # expo heartbeat, see main.py
        scene.update(dt)
        scene.render(screen)
        if gain is not None:
            # The px() views lock their surface. As arguments directly in the
            # call they die with the line -- otherwise the flip below would
            # fail on a locked surface.
            cv2.multiply(px(screen), gain, px(screen), 1 / 255)
        pygame.display.flip()

        # Tick rate of the scene that just ran — before the switch, so the
        # transition isn't clocked at the next scene's rate.
        dt = clock.tick(scene.TICK or fps) / 1000
        # Without output, a measurement on the Pi is blind: no developer is
        # watching a screen there, just an SSH session on stdout.
        ticks += 1
        if FPSLOG and ticks % fps == 0:
            print(f"{clock.get_fps():5.1f} fps  {type(scene).__name__}", flush=True)
        scene = scene.next

    pygame.quit()


