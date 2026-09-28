"""MLG mode: air horns, hitmarkers, a wobble drop, a deep-fried screen and
a rainbow strip. Staff easter egg, not part of the game.

    blue + yellow held for MLG_HOLD s   -> on, from any scene (Buttons.pump)
    red                                 -> off, back to the idle screen
    m on the keyboard                   -> on, for the Mac

The screen renders at 320 x 180, gets JPEG-crunched and blown up without
filtering: the low quality is the look, and it's cheaper than full HD.
With game/assets/mlg/video.mp4 present it plays under the text spam; its
sound comes from video.wav next to it (cv2 decodes no audio). Both are
downloaded by hand, see pnp-help. Without them the synth drop loops.

Sounds are synthesised like music.py, no samples, and in F major like the
soundtrack. Any assets/mlg/<sound>.wav (airhorn, hit, drop) replaces the
synth -- a real "OH BABY A TRIPLE" is a file copy, not a code change.

  uv run game/mlg.py    -> self-test + WAV previews into /tmp/picknplay-audio
"""
import functools
import math
import os
import random

import cv2
import numpy as np
import pygame

from app import SceneBase
from config import MLG_VIDEO, VOLUME
from hw import VideoView

ASSETS = os.path.dirname(MLG_VIDEO)
LOW    = (320, 180)    # render size: the "low quality"
JPEG   = 12            # 0..100, lower = more crunch

# ── Sound ─────────────────────────────────────────────────────────────────
# Float in -1..1 at sample rate sr; sounds() scales to int16 for the mixer.

HORN = (349.2, 440.0, 523.3)   # F major triad: the key of the game music
BPM  = 140


def _t(sec, sr):
    return np.arange(int(sec * sr)) / sr


def _env(t, attack, release):
    """Linear in, linear out -- without it every edge clicks."""
    return np.minimum(1, t / attack) * np.clip((t[-1] - t) / release, 0, 1)


def _saw(f, sr):
    """Saw from a per-sample frequency array: phase is summed, so a glide
    stays continuous instead of jumping at every sample."""
    return 2 * (np.cumsum(f) / sr % 1) - 1


def _blast(sec, sr):
    """One air-horn blast: six detuned saws that scoop up into pitch,
    overdriven -- the rasp IS the horn, a clean chord sounds like an organ."""
    t = _t(sec, sr)
    bend = 0.93 + 0.07 * (1 - np.exp(-t / 0.05))
    x = sum(_saw(np.full_like(t, f * d) * bend, sr) for f in HORN for d in (0.996, 1.004))
    return np.tanh(1.2 * x) * _env(t, 0.01, 0.04)


def airhorn(sr):
    """BWAA BWAA BWAAAAAA."""
    gap = np.zeros(int(0.06 * sr))
    return np.concatenate((_blast(0.16, sr), gap, _blast(0.16, sr), gap, _blast(0.9, sr)))


def hit(sr):
    """Hitmarker: two metallic partials and a click of noise, 70 ms."""
    t = _t(0.07, sr)
    ring = (np.sin(2 * np.pi * 2800 * t) + 0.6 * np.sin(2 * np.pi * 4100 * t)) * np.exp(-t / 0.012)
    click = np.random.default_rng(0).uniform(-1, 1, len(t)) * np.exp(-t / 0.003)
    return (ring + 0.5 * click) / 2.1 * _env(t, 0.0005, 0.005)


def drop(sr):
    """Eight beats of wobble bass with a kick on every beat, loops seamlessly.

    The "filter" is a crossfade from a sine to an overdriven saw, driven by
    the LFO. ponytail: no real resonant low-pass, that's a per-sample
    recursion; a crossfade reads as wub from 3 m and costs one line.
    F2, not F1: the cabinet speakers don't go down to 44 Hz.
    """
    beat = 60 / BPM
    rates = (2, 2, 4, 4, 3, 3, 8, 1)          # wobbles per beat: wub wub, wubwub, triplets, buzz, one long
    t = _t(beat * len(rates), sr)
    per = np.repeat(rates, len(t) // len(rates) + 1)[:len(t)] / beat
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * np.cumsum(per) / sr)
    f = np.full_like(t, 87.3)
    bright = np.tanh(3 * (_saw(f, sr) + 0.7 * _saw(f * 2.006, sr)))
    wub = (np.sin(2 * np.pi * 87.3 * t) * (1 - lfo) + bright * lfo) * (0.6 + 0.4 * lfo)
    tb = t % beat                              # time since the last beat
    kick = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-tb / 0.03)) / sr) * np.exp(-tb / 0.12)
    return np.clip(0.7 * wub + 0.6 * kick, -1, 1) * _env(t, 0.005, 0.005)


#  sound -> (synth, level)
SOUNDS = {"airhorn": (airhorn, 1.0), "hit": (hit, 0.8), "drop": (drop, 0.9)}


@functools.cache
def sounds(sr=44100, peak=3800 * VOLUME):
    """name -> pygame Sound, built on first use. A WAV in assets/mlg/ wins."""
    out = {}
    for name, (fn, level) in SOUNDS.items():
        path = os.path.join(ASSETS, f"{name}.wav")
        if os.path.exists(path):
            out[name] = pygame.mixer.Sound(path)
        else:
            pcm = np.clip(fn(sr) * level * peak, -32768, 32767).astype(np.int16)
            out[name] = pygame.mixer.Sound(buffer=pcm.tobytes())
    return out


# ── Screen ────────────────────────────────────────────────────────────────

WORDS = ("MLG", "360 NOSCOPE", "WOW", "OH BABY A TRIPLE", "GET REKT", "#REKT",
         "DAMN SON", "SANIC", "ILLUMINATI CONFIRMED", "2SPOOKY", "WOMBO COMBO",
         "GIT GUD", "1V1 ME BRO", "M-M-M-MONSTER KILL", "HEADSHOT")


def rainbow(h):
    return pygame.Color.from_hsva(h % 1 * 360, 100, 100)


def fry(surf):
    """Deep-fry: JPEG at quality JPEG, colours pushed. Works on the 320 x 180
    canvas, so it costs well under a millisecond even on the Pi."""
    img = pygame.surfarray.array3d(surf).swapaxes(0, 1)
    _, jpg = cv2.imencode(".jpg", img, (cv2.IMWRITE_JPEG_QUALITY, JPEG))
    img = cv2.convertScaleAbs(cv2.imdecode(jpg, cv2.IMREAD_COLOR), alpha=1.35, beta=-20)
    return pygame.image.frombuffer(np.ascontiguousarray(img).tobytes(), LOW, "RGB")


def hitmarker(s, x, y, r=9):
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pygame.draw.line(s, (255, 255, 255), (x + dx * 3, y + dy * 3), (x + dx * r, y + dy * r), 2)


class MlgScene(SceneBase):
    MUSIC = None
    POP   = 0.45   # seconds between text pops

    def __init__(self, ctx):
        super().__init__(ctx)
        ctx.music.stop()
        ctx.leds.show("mlg")
        self.snd = sounds() if ctx.music.on else {}
        self.video = VideoView(MLG_VIDEO, size=LOW) if os.path.exists(MLG_VIDEO) else None
        self.frame = None
        wav = MLG_VIDEO.rsplit(".", 1)[0] + ".wav"
        if self.snd:
            loop = pygame.mixer.Sound(wav) if os.path.exists(wav) else self.snd["drop"]
            loop.play(loops=-1)
            self.snd["airhorn"].play()
        self.low = pygame.Surface(LOW)
        self.font = pygame.font.Font(None, 30)   # pygame's default font: exactly as cheap as it should look
        self.now = self.next_pop = 0.0
        self.shake = 0.0
        self.pops = []      # [surface, x, y, born]
        self.hits = []      # [x, y, born]

    def _sfx(self, name):
        if name in self.snd:
            self.snd[name].play()

    def _pop(self):
        word = random.choice(WORDS)
        s = self.font.render(word, False, rainbow(random.random()), (0, 0, 0) if random.random() < .3 else None)
        s = pygame.transform.rotozoom(s, random.uniform(-30, 30), random.uniform(0.6, 1.6))
        self.pops.append([s, random.randrange(LOW[0]), random.randrange(LOW[1]), self.now])
        self.hits.append([random.randrange(LOW[0]), random.randrange(LOW[1]), self.now])
        self._sfx("hit")

    def handle(self, action):
        if action == "left":       # the red button: back to the real game
            if self.video:
                self.video.close()
            self.ctx.music.stop()  # mixer.stop() also ends our loop
            from scenes import IdleScene     # scenes imports app like this file does
            self.switch_to(IdleScene(self.ctx))
            return "ok"
        if action == "right":      # green: more horn
            self._sfx("airhorn")
            self.shake = 0.6
        else:                      # blue, yellow: more text
            self._pop()
        return "blip"

    def update(self, dt):
        self.now += dt
        self.shake = max(0.0, self.shake - dt)
        if self.now >= self.next_pop:
            self.next_pop = self.now + self.POP * random.uniform(0.5, 1.5)
            self._pop()
            if random.random() < 0.08:
                self._sfx("airhorn")
                self.shake = 0.6
        self.pops = [p for p in self.pops if self.now - p[3] < 1.2]
        self.hits = [h for h in self.hits if self.now - h[2] < 0.25]
        if self.video:
            self.frame = self.video.surface(dt)

    def render(self, screen):
        s = self.low
        s.fill(rainbow(self.now * 0.3))
        if self.video and self.frame:
            s.blit(self.frame, (0, 0))
        else:
            big = pygame.transform.rotozoom(self.font.render("MLG", False, (255, 255, 255)),
                                            math.sin(self.now * 3) * 15, 3 + math.sin(self.now * 8) * 0.4)
            s.blit(big, big.get_rect(center=(LOW[0] // 2, LOW[1] // 2)))
        for surf, x, y, _ in self.pops:
            s.blit(surf, surf.get_rect(center=(x, y)))
        for x, y, _ in self.hits:
            hitmarker(s, x, y)
        j = int(self.shake * 60)
        off = (random.randint(-j, j), random.randint(-j, j)) if j else (0, 0)
        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(fry(s), screen.get_size()), off)


if __name__ == "__main__":
    import wave

    SR = 44100
    assert rainbow(0)[:3] == (255, 0, 0) and rainbow(1 / 3)[:3] == (0, 255, 0)
    out = "/tmp/picknplay-audio"
    os.makedirs(out, exist_ok=True)
    for name, (fn, _) in SOUNDS.items():
        x = fn(SR)
        assert np.isfinite(x).all() and np.abs(x).max() <= 1.0 + 1e-9, name
        assert abs(x[0]) < 0.05 and abs(x[-1]) < 0.05, (name, "edge clicks")
        with wave.open(f"{out}/mlg-{name}.wav", "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((x * 12000).astype(np.int16).tobytes())
    assert len(hit(SR)) < 0.1 * SR and abs(len(drop(SR)) / SR - 8 * 60 / BPM) < 0.01

    # The scene, headless: enter, run 10 s of frames, every button, leave.
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    class _Stub:
        on = False
        def __getattr__(self, _): return lambda *a, **k: None
    from app import Ctx
    ctx = Ctx(detector=None, db=_Stub(), fonts={}, music=_Stub(), leds=_Stub())
    sc = MlgScene(ctx)
    screen = pygame.Surface((1920, 1080))
    for i in range(300):
        sc.update(1 / 30)
        sc.render(screen)
    for a in ("up", "down", "right"):
        assert sc.handle(a) == "blip"
    sc.render(screen)
    assert len({screen.get_at((x, 540))[:3] for x in range(0, 1920, 40)}) > 3, "screen is flat"
    fried = fry(sc.low)
    assert fried.get_size() == LOW
    assert sc.handle("left") == "ok" and type(sc.next).__name__ == "IdleScene"
    print(f"ok -> {out}/mlg-*.wav")
