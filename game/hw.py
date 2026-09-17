import fcntl
import os
import random
import socket
import struct
import threading
import time

import cv2
import numpy as np
import pygame

from config import (VALUES, CAM_SIZE, CAM_VIEW, MARKER_HOLD, DETECT_HZ,
                    TRAY_ROI, DEMO_SIZE, BUTTON_PINS, KEY_REPEAT, HOLD_QUIT,
                    LED_DEV, LED_COUNT, LED_ORDER, LED_BRIGHT, LED_FPS,
                    LED_STRIPES, LED_A, LED_B, LED_RED)


def notify(msg):
    """sd_notify without the dependency: one datagram to systemd. No-op
    outside a Type=notify unit (Mac, pnp-start)."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.connect("\0" + addr[1:] if addr[0] == "@" else addr)   # @ = abstract socket
        s.sendall(msg.encode())


def _quad(cx, cy, r=0.06):
    """Quad around a center point, in image fractions. Only for FakeDetector."""
    return ((cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r))


class FakeDetector:
    """Stand-in: an empty tray that fills up bit by bit.

    ponytail: adds one piece every `period` seconds and clears out once
    nobody has asked for a while. Replaced by ArucoDetector(Camera()),
    one line in main.py.

    Why not five randomly rolled markers at once anymore: that was the game
    from before the scoring session, where the tray started pre-loaded and
    got rearranged. Today it's cleared and built up after every round --
    a stand-in that doesn't start that way would have every local round
    begin from a different task than at the machine, and that's exactly
    what it must not do.

    Clearing happens via the gap between two queries: only the round
    queries the detector, not the idle screen. A long pause therefore means
    "no round was running", and that's when someone clears the tray at the
    machine. The stand-in needs no knowledge of scenes for that.
    """

    def __init__(self, period=3.0):
        self.period = period
        self.t = self.seen = 0.0
        self.marks = {}
        self.rest = []

    def fresh(self):
        now = time.monotonic()
        if now - self.seen > self.period * 3:      # pause = someone cleared it
            self.marks, self.rest = {}, random.sample(sorted(VALUES), len(VALUES))
            self.t = now
        self.seen = now
        if self.rest and now - self.t > self.period:
            self.t = now
            n = len(self.marks)
            self.marks[self.rest.pop()] = _quad(0.25 + n % 4 * 0.17,
                                                0.35 + n // 4 * 0.25)
        return self.marks


class Camera:
    """Grabber thread. read() always returns the NEWEST frame, never a stale one.

    cap.read() is C++ code and releases the GIL, so a thread here is real
    parallelism. BUFFERSIZE=1, otherwise V4L2 queues up stale frames and
    detection visibly lags behind.
    """

    def __init__(self, index, size=CAM_SIZE, warmup=3.0, zoom=None):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            # Fail loudly, don't silently fall back to a stand-in: made-up
            # numbers on the machine wouldn't be noticed on show day.
            raise RuntimeError(f"Camera {index} won't open")
        # Set MJPG before the size: as YUYV, 720p costs a multiple of the USB
        # bandwidth, and that decides whether two cameras fit on one bus.
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if zoom is not None:
            self.cap.set(cv2.CAP_PROP_ZOOM, zoom)
        self.lock = threading.Lock()
        self.frame = None
        self.seq = 0          # counts new frames so CameraView can cache
        self.t = time.monotonic()   # last new frame, see age()
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        # isOpened() only says the device let itself be opened -- whether
        # frames actually arrive, only a frame can say. If the camera is busy
        # (second game start, another program), macOS returns an open handle
        # and read() then returns False forever. Without this loop, both
        # panes just stay black and the game keeps running: exactly the
        # silent failure the raise above was meant to prevent. Costs startup
        # time, no runtime cost.
        t0 = time.monotonic()
        while self.frame is None and time.monotonic() - t0 < warmup:
            time.sleep(0.05)
        if self.frame is None:
            self.close()
            raise RuntimeError(f"Camera {index} delivers no image "
                               f"(in use? camera permissions?)")

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                # Camera gone or hung: don't busy-loop. The last frame
                # stays as-is, hysteresis runs out, tray_sum() goes to 0.
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame
                self.seq += 1
                self.t = time.monotonic()

    def age(self):
        """Seconds since the last new frame. A dead or hung camera only shows
        up here: read() keeps returning the last frame."""
        return time.monotonic() - self.t

    def read(self):
        with self.lock:
            return self.seq, self.frame

    def close(self):
        self.running = False
        self.cap.release()


class ArucoDetector:
    """Markers -> {id: quad}. Same signature as FakeDetector.

    Own thread at DETECT_HZ instead of 60 Hz: detectMarkers is expensive,
    and nobody pushes pucks around 60 times a second.

    The quads come out as fractions of the whole image (0..1), not pixels.
    Otherwise the scene would need to know the camera resolution -- and that
    stops being true the moment a UVC device doesn't deliver the requested
    size. They do that regularly, and the bug would be an overlay that's
    systematically off.
    """

    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI):
        self.cam = cam
        self.hold = hold
        self.roi = roi
        self.lock = threading.Lock()
        self.marks = {}         # marker_id -> (timestamp, quad in 0..1)
        # Also bright cells on a dark background: chocolate cupcakes carry the
        # marker inverted. It still finds normal markers, it tries both.
        params = cv2.aruco.DetectorParameters()
        params.detectInvertedMarker = True
        # Larger threshold windows: the pink macaron carries a purple marker,
        # little contrast in gray. Measured 2026-09-16 at zoom 40: 84 instead
        # of 68 of 90 frames, 9 instead of 4 ms -- plenty at DETECT_HZ.
        params.adaptiveThreshWinSizeMax = 53
        params.adaptiveThreshWinSizeStep = 6
        self.det = cv2.aruco.ArucoDetector(
            cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), params)
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        rx, ry, rw, rh = self.roi
        while True:
            _, frame = self.cam.read()
            if frame is not None:
                h, w = frame.shape[:2]
                x0, y0 = int(rx * w), int(ry * h)
                x1, y1 = x0 + int(rw * w), y0 + int(rh * h)
                # Crop instead of filtering afterward: does both in one step,
                # and detection only costs as much as the window is big.
                # Measured 1.21 instead of 2.00 ms at 60% x 70%.
                # The crop is a numpy view, not a copy.
                gray = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
                corners, ids, _ = self.det.detectMarkers(gray)
                now = time.monotonic()
                found = {}
                for c, i in zip(corners, ids.flatten() if ids is not None else ()):
                    if int(i) not in VALUES:
                        continue    # foreign marker, not part of the game
                    # Window fraction back to image fraction, so the scene only
                    # has to multiply by the pane rectangle.
                    q = c.reshape(4, 2) / (x1 - x0, y1 - y0) * (rw, rh) + (rx, ry)
                    found[int(i)] = (now, tuple(map(tuple, q)))
                with self.lock:
                    self.marks.update(found)
            time.sleep(1 / DETECT_HZ)

    def fresh(self):
        # Hysteresis: a marker keeps counting as long as it's covered for
        # less than hold. That's the fix for a hand over the tray, not for
        # pucks that are actually removed.
        # The lock is mandatory, not caution: without it, iteration throws
        # RuntimeError the moment the thread inserts a new ID meanwhile.
        now = time.monotonic()
        with self.lock:
            return {i: q for i, (t, q) in self.marks.items() if now - t < self.hold}


class Buttons:
    """Four arcade buttons on GPIO. Polled once per frame, not via callback.

    The overview envisioned gpiozero callbacks into a `queue.SimpleQueue`
    that the loop drains. That's one more line of code in three places: a
    foreign thread, a queue, and -- because `pygame.key.set_repeat()` only
    applies to the keyboard -- a second clock for repeat-while-held.

    Polled instead: a button press lasts 80 to 200 ms, a frame 33. There's
    nothing to miss. That means the same rule applies here as everywhere
    else in the game -- the loop owns time, `pump(dt)` gets it passed through,
    and the repeat calculates with the same `dt` as the round timer. No lock,
    no thread, no second time source.

    `KEY_REPEAT` applies to both paths: what happens at the machine when you
    hold the button is the same as when developing on the keyboard. That's
    exactly what the overview warns against, and it's the spot where things
    would otherwise diverge.
    """

    def __init__(self, pins=BUTTON_PINS, repeat=KEY_REPEAT):
        # Import only here: gpiozero and lgpio only exist on the Pi
        # (pyproject extra `pi`). On the dev machine the game runs with
        # PNP_BUTTONS=0 and this line never executes.
        from gpiozero import Button
        self.delay, self.rate = (ms / 1000 for ms in repeat)
        # bounce_time debounces in gpiozero, so there's no capacitor sitting
        # in the wiring harness that nobody would resolder on show day.
        self.btns = {a: Button(p, pull_up=True, bounce_time=0.02)
                     for p, a in pins.items()}
        self.wait = {}     # action -> seconds until the next repeat
        self.held = 0.0    # all four pressed for this long, see pump()

    def pump(self, dt):
        """Actions that have fired since the last frame."""
        # Staff escape hatch: all four held for HOLD_QUIT seconds -> "quit".
        # In expo mode systemd starts the game again, so this is a restart.
        pressed = [b.is_pressed for b in self.btns.values()]
        self.held = self.held + dt if all(pressed) else 0.0
        if self.held >= HOLD_QUIT:
            self.held = 0.0
            return ["quit"]
        out = []
        for a, b in self.btns.items():
            if not b.is_pressed:
                self.wait.pop(a, None)     # released: fresh start next time
                continue
            w = self.wait.get(a)
            if w is None:
                out.append(a)              # edge: immediately, not only after delay
                self.wait[a] = self.delay
                continue
            w -= dt
            # while, not if: a long frame has several repeats due, and += rate
            # keeps the cadence, while = rate would drift.
            while w <= 0:
                out.append(a)
                w += self.rate
            self.wait[a] = w
        return out

    def close(self):
        for b in self.btns.values():
            b.close()


class VideoView:
    """Clip from a file, looped. Same conversion as CameraView.

    pygame can't do video, but cv2.VideoCapture takes a file just like a
    device -- so the player is the same class as the passthrough, just with
    a clock instead of a grabber. A camera *pushes* frames (hence a thread and
    a sequence counter there), a file gets *pulled* (hence dt here).

    ponytail: decodes in the render thread. At 1120x630 that's a few
    milliseconds, 25 times a second, and only while the scene is showing. If
    it gets tight on the Pi: same grabber thread as in Camera, the shape
    already fits.
    """

    def __init__(self, path, size=DEMO_SIZE):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Demo clip {path} won't open")
        self.size = size
        self.step = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 25)
        self.t = self.step      # first frame immediately, not only after step
        self.surf = None

    def surface(self, dt):
        self.t += dt
        if self.t < self.step:
            return self.surf    # clip runs at 25 Hz, rendering at 60
        self.t = 0.0
        ok, frame = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # restart at the end
            ok, frame = self.cap.read()
        if ok:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
        return self.surf

    def close(self):
        self.cap.release()


class CameraView:
    """Passthrough: newest camera frame as a pygame surface at inset size.

    Downscale first, then copy -- conversion cost is proportional to pixel
    count, and 400x300 is a twentieth of 1280x720. frombuffer with "BGR"
    skips the cvtColor: pygame-ce accepts OpenCV's channel order directly.

    INTER_LINEAR, not INTER_AREA: measured 0.17 ms instead of 3.5 ms per
    frame. AREA averages over all source pixels when downscaling and is
    twenty times more expensive at factor 3 -- for an inset behind scanlines
    nobody sees that, but 3.5 ms would be a fifth of the frame budget on
    the Pi.
    """

    def __init__(self, cam, det=None, size=CAM_VIEW):
        self.cam = cam
        self.det = det      # only the top-down pane has one: the arm image is
        self.size = size    # a pure passthrough, there'd be nothing to show
        self.seq = -1
        self.surf = None

    def surface(self):
        seq, frame = self.cam.read()
        # The camera delivers 30 frames/s, rendering happens at 60: without
        # this comparison, every frame gets converted twice, for nothing.
        if seq != self.seq and frame is not None:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
            self.seq = seq
        return self.surf


# WS2812 over SPI: every data bit becomes one SPI byte. At 6.5 MHz, one byte
# takes 1.23 us, matching the strip's 800 kHz timing. 0b11000000 holds the
# line high for 0.3 us (a 0), 0b11111100 for 0.9 us (a 1). Pattern and clock
# match rpi5-ws2812, which is how it runs on the Pi 5 -- here without the
# dependency, because it's just one ioctl and one write.
SPI_HZ     = 6_500_000
BIT0, BIT1 = 0b11000000, 0b11111100
SPI_IOC_WR_MAX_SPEED_HZ = 0x40046B04   # _IOW('k', 4, u32) from linux/spi/spidev.h
# 300 zero bytes = 370 us low before every frame: latch for the previous
# one, even for the newer WS2812B, which only takes over after 280 us.
RESET = bytes(300)


def led_encode(rgb, order=LED_ORDER):
    """(n, 3) uint8 in RGB -> SPI bytes, one per data bit, reset before."""
    idx = ["RGB".index(c) for c in order]
    bits = np.unpackbits(np.ascontiguousarray(rgb[:, idx], np.uint8).ravel())
    return RESET + np.where(bits, BIT1, BIT0).astype(np.uint8).tobytes()


def led_frame(state, k, t, n):
    """One frame of the strip as (n, 3) RGB. Pure function of state and time.

    idle   candy cane, runs slowly -- attract mode, visible from 8 m
    game   time left as a bar: k = fraction of the round still remaining
    hurry  final seconds, red at 2 Hz, in sync with the red screen
    score  same candy cane, four times as fast
    """
    i = np.arange(n)
    if state == "game":
        return np.where((i < k * n)[:, None], LED_A, np.multiply(LED_A, 0.08))
    if state == "hurry":
        return np.tile(LED_RED if int(t * 4) % 2 == 0 else (0, 0, 0), (n, 1))
    w = max(1, n // LED_STRIPES)
    shift = int(t * (4 if state == "score" else 1) * 2 * w)   # two stripes per second
    return np.where((((i + shift) // w) % 2 == 0)[:, None], LED_A, LED_B)


class Leds:
    """WS2812 strip on SPI0, one worker thread with a state slot.

    `show()` only sets the slot and returns immediately -- LEDs never block
    the render loop. Without a device (Mac, SPI off), everything stays
    silent, like Music without audio: scenes notice nothing and need no
    None check.
    """

    def __init__(self, dev=LED_DEV, n=LED_COUNT):
        self.slot = ("idle", 1.0)
        self.n = n
        self.run = False
        try:
            self.fd = os.open(dev, os.O_WRONLY)
        except OSError as e:
            print(f"LEDs off: {e}")
            return
        fcntl.ioctl(self.fd, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("I", SPI_HZ))
        # spidev takes at most bufsiz bytes per write(), default 4096 -- one
        # frame with 480 LEDs is 11,820. Multiple writes have gaps between
        # them, and an older WS2812B already latches after 50 us, i.e. mid-
        # frame. The fix belongs in the kernel (spidev.bufsiz, docs/operation.md).
        with open("/sys/module/spidev/parameters/bufsiz") as f:
            self.chunk = int(f.read())
        if len(RESET) + n * 24 > self.chunk:
            print(f"LEDs: frame {len(RESET) + n * 24} B > spidev.bufsiz {self.chunk}, "
                  "getting chunked -- may flicker")
        self.run = True
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def show(self, state, k=1.0):
        self.slot = (state, k)    # assigning a tuple is atomic, no lock needed

    def _loop(self):
        t0 = time.monotonic()
        while self.run:
            state, k = self.slot
            self._write(led_frame(state, k, time.monotonic() - t0, self.n))
            time.sleep(1 / LED_FPS)   # ponytail: plus write time (~15 ms), so ~20 frames/s

    def _write(self, rgb):
        data = led_encode(np.clip(np.multiply(rgb, LED_BRIGHT), 0, 255).astype(np.uint8))
        for o in range(0, len(data), self.chunk):
            os.write(self.fd, data[o:o + self.chunk])

    def close(self, rgb=(0, 0, 0)):
        """Off, don't stay stuck on the last frame. The expo unit passes
        LED_DOWN here when the game crashed (pi/setup.sh, ExecStopPost)."""
        if not self.run:
            return
        self.run = False
        self.th.join()
        self._write(np.tile(rgb, (self.n, 1)))
        os.close(self.fd)


if __name__ == "__main__":
    # Self-test without a camera: synthetic tray. Checks that dictionary
    # and markers/ match up, that the quads sit where the markers were
    # drawn, that the window filters correctly, and that hysteresis holds
    # first and then decays. uv run game/hw.py -> ok
    import numpy as np

    W, H, MS = 640, 480, 90

    class _Still:
        def __init__(self, frame): self.frame = frame
        def read(self): return 1, self.frame

    def _tray(spots):
        """spots: {marker_id: (x, y) top-left corner in pixels}"""
        frame = np.full((H, W, 3), 255, np.uint8)   # white = rest zone
        for i, (x, y) in spots.items():
            m = np.zeros((MS, MS), np.uint8)
            cv2.aruco.generateImageMarker(
                cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50),
                i, MS, m)
            frame[y:y + MS, x:x + MS] = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
        return frame

    def _settle(det):
        time.sleep(4 / DETECT_HZ)
        return det.fresh()

    # 1 · Detection, values, and position of the quads with an open window
    spots = {0: (60, 60), 4: (260, 60), 9: (460, 260)}
    still = _Still(_tray(spots))
    det_open = ArucoDetector(still, roi=(0, 0, 1, 1))
    marks = _settle(det_open)
    assert sorted(marks) == sorted(spots), marks
    assert sum(VALUES[i] for i in marks) == sum(VALUES[i] for i in spots)
    for i, (x, y) in spots.items():
        cx = sum(p[0] for p in marks[i]) / 4 * W
        cy = sum(p[1] for p in marks[i]) / 4 * H
        assert abs(cx - (x + MS / 2)) < 3 and abs(cy - (y + MS / 2)) < 3, (i, cx, cy)

    # 1b · Inverted marker (chocolate cupcake) is detected the same way
    det_inv = ArucoDetector(_Still(255 - _tray({5: (260, 160)})), roi=(0, 0, 1, 1))
    assert sorted(_settle(det_inv)) == [5], det_inv.fresh()

    # 2 · Window filters out what lies outside
    det_roi = ArucoDetector(_Still(_tray(spots)), roi=(0.0, 0.0, 0.6, 0.5))
    assert sorted(_settle(det_roi)) == [0, 4], det_roi.fresh()   # 9 lies outside

    # 3 · Hysteresis holds briefly and then decays
    still.frame = _tray({})                 # tray cleared out
    time.sleep(MARKER_HOLD / 2)
    assert len(_ := det_open.fresh()) == 3, ("hysteresis doesn't hold", _)
    time.sleep(MARKER_HOLD * 2)
    assert det_open.fresh() == {}, "hysteresis doesn't decay"

    # 4 · Repeat-while-held, without GPIO. Powers of two as times: they
    #     are binary-exact, otherwise 4 x 0.1 of 0.4 leaves a remainder of
    #     5e-17 and the test wobbles on rounding instead of logic.
    class _Pin:
        is_pressed = False
    btn = Buttons.__new__(Buttons)
    btn.delay, btn.rate = 0.5, 0.25
    btn.btns, btn.wait, btn.held = {"up": _Pin()}, {}, 0.0
    assert btn.pump(0.125) == []                        # not pressed
    btn.btns["up"].is_pressed = True
    assert btn.pump(0.125) == ["up"], "edge doesn't fire immediately"
    assert [btn.pump(0.125) for _ in range(3)] == [[], [], []], "fires too early"
    assert btn.pump(0.125) == ["up"], "repeat doesn't kick in"   # 0.5 s elapsed
    assert [btn.pump(0.125) for _ in range(2)] == [[], ["up"]], "rate is wrong"
    # A long frame catches up on due repeats instead of swallowing them
    assert btn.pump(0.75) == ["up"] * 3, "long frames swallow repeats"
    btn.btns["up"].is_pressed = False
    assert btn.pump(0.125) == [] and btn.wait == {}, "release not forgotten"
    # All buttons held for HOLD_QUIT -> quit, once
    btn.btns["up"].is_pressed = True
    btn.pump(HOLD_QUIT / 2)
    assert btn.pump(HOLD_QUIT / 2) == ["quit"] and btn.held == 0.0

    # 5 · FakeDetector has the same interface: starts empty, adds over time
    fk = FakeDetector(period=0.05)
    assert fk.fresh() == {}, "stand-in doesn't start empty"
    time.sleep(0.08)                  # > period, < 3 x period (otherwise it clears)
    f = fk.fresh()
    assert len(f) == 1 and all(len(q) == 4 for q in f.values())

    # 6 · LED encoding: GRB order, MSB first, one SPI byte per bit.
    #     This is the part that can't be checked without a physical strip.
    enc = led_encode(np.array([[0x80, 0x01, 0x00]]))          # R=0x80 G=0x01 B=0
    assert enc[:len(RESET)] == RESET and len(enc) == len(RESET) + 24
    g, r, b = (enc[len(RESET) + 8 * j:len(RESET) + 8 * j + 8] for j in range(3))
    assert g == bytes([BIT0] * 7 + [BIT1]), "G not first, or not MSB first"
    assert r == bytes([BIT1] + [BIT0] * 7) and b == bytes([BIT0] * 8)
    # Time-left bar: half a round = half the strip lit
    fr = led_frame("game", 0.5, 0.0, 100)
    assert (fr[:50] == LED_A).all() and not (fr[50:] == LED_A).all()
    # Without a device, silent instead of crashing -- that's how the game runs on the Mac
    q = Leds(dev="/nonexistent")
    q.show("game", 0.3)
    q.close()
    print("ok")
