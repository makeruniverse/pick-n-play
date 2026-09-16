"""8-bit music and sound effects, clearly noted.

A string per track. A token is a sixteenth:

f4 Note (name + optional # or b + octave)
.
- Break
f4/a4/c5 chord, issued as 45-Hz-Arpeggio (the NES trick: a channel
jumps so fast between the chordtoes that the ear
Accord hoert)
a#2^f2 Glide from the first to the second note
k s h Kick, Snare, Hi-Hat -- fixed short lange no matter how long the token

Print is per track in PIECES: Huell bend, Vibrato, Duty. It is rendered
once at the start, after that everything is in the mixer.

uv run game/music.py -> Self-test + WAV-Vorhoer nach /tmp
"""
import array
import math
import random

import pygame

from config import ROUND_SECONDS, WARN_SECONDS, DUCK, DUCK_RELEASE

SR   = 44100    # 22050 rounds F5 by 23 cents too deep -- the intervals sound sloping
BUF  = 512      # ~12 ms latency, short enough for button clips
DIV  = 4        # tokens per quarter note -> sixteenth notes
EDGE = 128      # ~3 ms ramp at each edge of the note, otherwise each flank cracks

ARP_HZ  = 45.0  # Accord switching rate. The NES did this once per image recovery
VIB_HZ  = 5.6
VIB_LAG = 0.13  # Vibrato starts later, short notes just stay

_PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

# Huellkurven, Argumente in Sekunden: (seit Notenbeginn, Notenlaenge).
# Without that, every note sounds like a test tone -- that's the whole difference
# between "computer-generated" and "played".
ENV = {
    "flat":  lambda s, d: 1.0,
    "pluck": lambda s, d: 0.22 + 0.78 * math.exp(-5.5 * s),   # Melodie: Anschlag, dann stehen
    "hit":   lambda s, d: math.exp(-13.0 * s),                # Blip, Drum, Fanfare
    "punch": lambda s, d: 0.45 + 0.55 * math.exp(-16.0 * s),  # Bass: Wumms, dann tragen
    "swell": lambda s, d: min(1.0, s * 12) * (0.55 + 0.45 * math.exp(-1.1 * s)),
}

DRUMS = {"k": 0.11, "s": 0.09, "h": 0.028}   # Token -> feste Laenge in Sekunden


# ── Synthese ──────────────────────────────────────────────────────────────

def _freq(tok):
    pc, i = _PC[tok[0]], 1
    if tok[1] in "#b":
        pc += 1 if tok[1] == "#" else -1
        i = 2
    return 440 * 2 ** ((pc + 12 * (int(tok[i:]) + 1) - 69) / 12)


def _edge(buf):
    e = min(EDGE, len(buf) // 2)
    for i in range(e):
        k = i / e
        buf[i] = int(buf[i] * k)
        buf[-1 - i] = int(buf[-1 - i] * k)
    return buf


def _tone(n, freqs, vol, duty, env, vib=0.0, glide=False):
    """A note. The loop releases per vibration, not per sample --
100x cheaper, and a rectangle sounded the same. Huell curve,
Vibrato, Glide and Arpeggio all fall out of this one loop."""
    out = array.array("h")
    d, pos = n / SR, 0.0
    while int(pos) < n:
        i = int(pos)
        s = i / SR
        if glide:
            f = freqs[0] * (freqs[-1] / freqs[0]) ** (i / n)
        else:
            f = freqs[int(s * ARP_HZ) % len(freqs)]
        if vib:
            f *= 1 + vib * math.sin(2 * math.pi * VIB_HZ * s) * min(1.0, max(0.0, (s - VIB_LAG) * 6))
        # pos is broken: the period is not rounded, only its end. The
        # corrects the average frequency exactly -- rounded periods draw high
        # Notes up to 23 cents, and the intervals sound oblique.
        pos += SR / f
        p = max(2, int(pos) - i)
        a = int(vol * env(s, d) * min(1.0, (d - s) * 60))   # Release, sonst schneidet es ab
        hi = min(p - 1, max(1, round(p * duty)))
        out += array.array("h", [a] * hi + [-a] * (p - hi))
    return _edge(out[:n])


def _noise(n, vol, env):
    return _edge(array.array("h", (int(random.randint(-vol, vol) * env(i / SR, n / SR))
                                   for i in range(n))))


def _drum(tok, n, vol):
    """Kick is a glide from 160 to 45 Hz -- therefore the anger. Snare and
Hi-Hat are noise, only different lengths."""
    hit = int(min(n, DRUMS[tok] * SR))
    if tok == "k":
        buf = _tone(hit, [160.0, 45.0], vol, 0.5, ENV["hit"], glide=True)
    else:
        buf = _noise(hit, vol if tok == "s" else vol // 2, ENV["hit"])
    buf.frombytes(bytes(2 * (n - len(buf))))
    return buf


def _render(pat, bpm, vol=3000, duty=0.5, env="flat", vib=0.0):
    step = int(SR * 60 / bpm / DIV)
    toks, out, i = pat.split(), array.array("h"), 0
    while i < len(toks):
        j = i + 1
        while j < len(toks) and toks[j] == ".":
            j += 1
        n, t = (j - i) * step, toks[i]
        if t == "-":
            out += array.array("h", bytes(2 * n))
        elif t in DRUMS:
            out += _drum(t, n, vol)
        elif "^" in t:
            out += _tone(n, [_freq(x) for x in t.split("^")], vol, duty, ENV[env], glide=True)
        else:
            out += _tone(n, [_freq(x) for x in t.split("/")], vol, duty, ENV[env], vib)
        i = j
    return out


def _build(bpm, specs):
    """Traces of a mare, all taken on the same lange."""
    tracks = [_render(bpm=bpm, **t) for t in specs]
    n = max(len(t) for t in tracks)
    for t in tracks:
        t.frombytes(bytes(2 * (n - len(t))))
    return tracks


# ── Noten ─────────────────────────────────────────────────────────────────
# All in F major: F - Dm - Bb - C im Idle, F - C in the round. Dur, not Moll --
# the tension finally comes from speed and percussion, not from sadness.
# Only level 3, the last five seconds, goes out with a little sexte.

IDLE_LEAD = ("-  -  c5 .  f5 .  a5 .  c6 .  .  .  a5 .  g5 . "
             "f5 .  .  .  a5 .  f5 .  d5 .  .  .  .  .  -  - "
             "-  -  d5 .  f5 .  a5 .  a#5 . .  .  a5 .  f5 . "
             "g5 .  .  .  e5 .  g5 .  c6 .  .  .  .  .  .  . ")

IDLE_ARP  = ("f4/a4/c5   . . . . . . . . . . . . . . . "
             "d4/f4/a4   . . . . . . . . . . . . . . . "
             "a#3/d4/f4  . . . . . . . . . . . . . . . "
             "c4/e4/g4   . . . . . . . . . . . . . . . ")

IDLE_BASS = ("f2  . f2  . f2  . a2 . c3 . c3 . a2 . f2  . "
             "d2  . d2  . d2  . f2 . a2 . a2 . f2 . d2  . "
             "a#1 . a#1 . a#1 . d2 . f2 . f2 . d2 . a#1 . "
             "c2  . c2  . c2  . e2 . g2 . g2 . e2 . c2  . ")

IDLE_DRUM = ("k - h - -  - h - k - h - -  - h - "
             "k - h - s  - h - k - h - -  - h - ") * 2

RIFF_LEAD = ("f5 . f5 . a5 . f5 . c6 . a5 . f5 . e5 . "
             "d5 . d5 . f5 . a5 . g5 . e5 . c5 . -  - ")

RIFF_BASS = ("f2 . f2 . f2 . f2 . f2 . f2 . a2 . a#2 . "
             "c2 . c2 . c2 . c2 . g2 . g2 . e2 . f2  . ")

DRUM_CALM  = "k - - - s - - - k - - - s - - - " * 2
DRUM_MID   = "k - h - s - h - k - h - s - h - " * 2
DRUM_BUSY  = "k - h h s - h h k h h h s - h h " * 2
DRUM_DRIVE = "k - h h s - h h k h h h s h k h " * 2

# Last five seconds: the clock ticks on every quarter. This is
# Signifier -- Panik emerges from the tick, not from more bass drum.
TICK = "c6 - - - c6 - - - c6 - - - c6 - - - " * 2

#  name -> (bpm, Kanallautstaerke, Spuren)
PIECES = {
    "idle":   (104, 0.42, [
        dict(pat=IDLE_BASS, vol=3000, duty=0.50, env="punch"),
        dict(pat=IDLE_ARP,  vol=1500, duty=0.125, env="pluck"),
        dict(pat=IDLE_LEAD, vol=2500, duty=0.25, env="pluck", vib=0.010),
        dict(pat=IDLE_DRUM, vol=2000, env="hit")]),
    "round0": (118, 0.60, [
        dict(pat=RIFF_BASS, vol=3400, duty=0.50, env="punch"),
        dict(pat=RIFF_LEAD, vol=2700, duty=0.25, env="pluck", vib=0.008),
        dict(pat=DRUM_CALM, vol=2400, env="hit")]),
    "round1": (132, 0.70, [
        dict(pat=RIFF_BASS, vol=3400, duty=0.50, env="punch"),
        dict(pat=RIFF_LEAD, vol=3000, duty=0.25, env="pluck", vib=0.010),
        dict(pat=DRUM_MID,  vol=2700, env="hit")]),
    "round2": (148, 0.80, [
        dict(pat=RIFF_BASS, vol=3600, duty=0.50, env="punch"),
        dict(pat=RIFF_LEAD, vol=3300, duty=0.50, env="pluck", vib=0.014),
        dict(pat=DRUM_BUSY, vol=3000, env="hit")]),
    "round3": (158, 0.88, [
        dict(pat=RIFF_BASS,  vol=3600, duty=0.50, env="punch"),
        dict(pat=RIFF_LEAD,  vol=3300, duty=0.25, env="pluck", vib=0.016),
        dict(pat=TICK,       vol=2100, duty=0.125, env="hit"),
        dict(pat=DRUM_DRIVE, vol=3000, env="hit")]),
}

#  name -> (bpm, tracks) -- same form, only without loop
SFX = {
    "start":  (150, [
        dict(pat="f4 a4 c5 f5 a5 c6 f6 . .", vol=3800, duty=0.25, env="hit"),
        dict(pat="-  -  -  -  -  -  f3/a3/c4 . .", vol=2600, duty=0.125, env="pluck"),
        dict(pat="k - - - - - k . .", vol=3400, env="hit")]),
    "ok":     (240, [
        dict(pat="a5^c6 .", vol=2600, duty=0.25, env="hit")]),
    # Marker newly recognized. In short, duenn (duty 0.125) and half as loud as "ok":
    # it should be best, not interrupt — during a round it fades
    # 10 times, a button at the place would disintegrate the music.
    "blip":   (300, [
        dict(pat="e6 .", vol=1200, duty=0.125, env="hit")]),
    "nope":   (200, [
        dict(pat="a#2^d#2 . .", vol=3400, duty=0.50, env="hit"),
        dict(pat="s . .",       vol=1800, env="hit")]),
    "finish": (160, [
        dict(pat="c5 . e5 . g5 . c6 . . - d6 e6 f5/a5/f6 . . . . . . .",
             vol=3600, duty=0.25, env="hit", vib=0.012),
        dict(pat="f2 . f2 . f2 . f2 . . -  f2 f2 f2 . . . . . . .",
             vol=3200, duty=0.50, env="punch"),
        dict(pat="k - s - k - k - . -  s  k  k . . . . . . .",
             vol=3200, env="hit")]),
}

# From how much residual seconds that level is running. Read descending.
STAGES = [(ROUND_SECONDS * 2 / 3, "round0"),
          (ROUND_SECONDS / 3,     "round1"),
          (WARN_SECONDS,          "round2"),
          (0.0,                   "round3")]


# ── Anbindung ─────────────────────────────────────────────────────────────

class Music:
    """Stumm, if there's no audio germ -- scenes don't notice."""

    REPEAT_MS = 90   # the same SFX is swallowed faster

    def __init__(self):
        self.on = pygame.mixer.get_init() == (SR, -16, 1)
        self.now = None
        self._pending = None
        self._last = (None, 0)
        self.duck = 1.0   # Musikpegel-Faktor, 1.0 = voll. Siehe sfx()/update()
        if not self.on:
            return
        self.reserved = max(len(p[2]) for p in PIECES.values())
        pygame.mixer.set_num_channels(self.reserved + 8)
        pygame.mixer.set_reserved(self.reserved)   # Kanaele 0..n-1 listened to music
        self.pieces = {k: (vol, [pygame.mixer.Sound(buffer=t) for t in _build(bpm, tr)])
                       for k, (bpm, vol, tr) in PIECES.items()}
        self.sfx_ = {k: [pygame.mixer.Sound(buffer=t) for t in _build(bpm, tr)]
                     for k, (bpm, tr) in SFX.items()}

    def _volumes(self):
        """Write current levels on the musical canals.

All traces of a stuck are divided by a loudspeaker (vol from PIECES),
a factor instead of a level table is sufficient. set reserved() haelt
the canals 0..n-1 free from the effects -- the loop can never
accidentally turn a SFX quieter.
"""
        v = self.pieces[self.now][0] * self.duck if self.now else 0.0
        for i in range(self.reserved):
            pygame.mixer.Channel(i).set_volume(v)

    def play(self, name, delay=0.0, fade=0):
        """delay in Sekunden Stille davor, fade in Millisekunden Einblendung."""
        if not self.on or name == self.now:
            return
        self.now = name
        if delay:
            for i in range(self.reserved):
                pygame.mixer.Channel(i).stop()
            self._pending = (name, pygame.time.get_ticks() + int(delay * 1000), fade)
            return
        self._start(name, fade)

    def _start(self, name, fade=0):
        vol, tracks = self.pieces[name]
        for i in range(self.reserved):
            ch = pygame.mixer.Channel(i)
            if i >= len(tracks):
                ch.stop()
            else:
                ch.set_volume(vol * self.duck)   # ein Stufenwechsel mitten im
                ch.play(tracks[i], loops=-1, fade_ms=fade)   # Duck bleibt leise

    def update(self):
        """Starts pushed music and sweeps the ducking back.

No timer thread, run game calls that any frame -- one line
instead of a second time source. The ramp calculates  last[1], the
timestamp, the sfx() for the repetition lock already leads: no
second state for the same watch.
"""
        if not self.on:
            return
        t = pygame.time.get_ticks()
        if self._pending and t >= self._pending[1]:
            name, _, fade = self._pending
            self._pending = None
            self._start(name, fade)
        if self.duck < 1.0:
            self.duck = min(1.0, DUCK + (1 - DUCK) *
                            (t - self._last[1]) / (DUCK_RELEASE * 1000))
            self._volumes()

    def stage(self, left):
        """Selects the stage of intensification at the remaining time. Changes only if necessary."""
        for limit, name in STAGES:
            if left > limit:
                return self.play(name)
        self.play(STAGES[-1][1])

    def sfx(self, name):
        if not self.on:
            return
        t = pygame.time.get_ticks()
        if self._last[0] == name and t - self._last[1] < self.REPEAT_MS:
            return
        self._last = (name, t)
        # down immediately, then over DUCK RELEASE: fast use,
        # slow release. In other respects, the ducking itself is honed.
        self.duck = DUCK
        self._volumes()
        for s in self.sfx_[name]:
            s.play()

    def stop(self):
        if self.on:
            pygame.mixer.stop()
            self.now = self._pending = None
            self.duck = 1.0


if __name__ == "__main__":
    import os
    import time
    import wave

    for name, (bpm, _, specs) in PIECES.items():
        for t in specs:
            assert len(t["pat"].split()) % (4 * DIV) == 0, (name, len(t["pat"].split()))
        assert len(set(len(t) for t in _build(bpm, specs))) == 1, ("Spuren ungleich lang", name)
    assert round(_freq("a4")) == 440 and round(_freq("a#2")) == 117 and round(_freq("f2")) == 87
    # Mood: one second tone must have f zero crossing up, above
    # all the tone. The MIDI 78 fails with a rounded period.
    for m in range(29, 97):
        f = 440 * 2 ** ((m - 69) / 12)
        buf = _tone(SR, [f], 9000, 0.5, ENV["flat"])
        cyc = sum(1 for i in range(1, SR) if buf[i - 1] < 0 <= buf[i])
        assert abs(cyc - f) <= 1, (m, cyc, round(f, 1))

    t0 = time.time()

    def flat(tracks, n=None):
        n = n or max(len(t) for t in tracks)
        mix = array.array("h", bytes(2 * n))
        for t in tracks:
            for i in range(n):                      # Loop wiederholen bis n
                v = mix[i] + t[i % len(t)]
                mix[i] = -32768 if v < -32768 else 32767 if v > 32767 else v
        return mix

    def wav(path, data):
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(data.tobytes())

    out = "/tmp/picknplay-audio"
    os.makedirs(out, exist_ok=True)
    for name, (bpm, _, specs) in PIECES.items():
        wav(f"{out}/{name}.wav", flat(_build(bpm, specs)))
    for name, (bpm, specs) in SFX.items():
        wav(f"{out}/sfx-{name}.wav", flat(_build(bpm, specs)))

    # A file that counts the whole round: idle, start, 60 s increase, finished.
    session = flat(_build(PIECES["idle"][0], PIECES["idle"][2]), n=SR * 12)
    session += flat(_build(SFX["start"][0], SFX["start"][1]))
    left = float(ROUND_SECONDS)
    for limit, name in STAGES:
        bpm, _, specs = PIECES[name]
        session += flat(_build(bpm, specs), n=int(SR * (left - limit)))
        left = limit
    session += flat(_build(SFX["finish"][0], SFX["finish"][1]))
    # Break and stop as in the game: MUSIC IN from DisplayScoreScene.
    pause, fade = 2.2, 1500
    session += array.array("h", bytes(2 * int(SR * pause)))
    tail = flat(_build(PIECES["idle"][0], PIECES["idle"][2]), n=SR * 10)
    for i in range(int(SR * fade / 1000)):
        tail[i] = int(tail[i] * i / (SR * fade / 1000))
    session += tail
    wav(f"{out}/session.wav", session)
    print(f"ok -> {out}  session {len(session)/SR:.0f}s  ({time.time()-t0:.1f}s inkl. WAV-Mix)")
