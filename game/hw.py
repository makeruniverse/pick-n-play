import random
import threading
import time

import cv2
import pygame

from config import (VALUES, CAM_SIZE, CAM_VIEW, MARKER_HOLD, DETECT_HZ,
                    TRAY_ROI, DEMO_SIZE)


def _quad(cx, cy, r=0.06):
    """Rectangular around a center, in image parts. Only for FakeDetector."""
    return ((cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r))


class FakeDetector:
    # ponytail: periodically refreshes so that you can see that the ad lives.
    # Replaced by ArucoDetector(Camera()), one line in main.py.
    def __init__(self, period=3.0):
        self.period = period
        self.t = 0.0
        self.marks = {}

    def fresh(self):
        now = time.monotonic()
        if now - self.t > self.period:
            self.t = now
            self.marks = {i: _quad(0.3 + n % 3 * 0.2, 0.35 + n // 3 * 0.25)
                          for n, i in enumerate(random.sample(sorted(VALUES), 5))}
        return self.marks


class Camera:
    """Grabber-Thread. read() always provides the NEW picture, never an old one.

cap.read() is C++ code and releases the GIL, so a thread is here
real parallelity. BUFFERSIZE=1, otherwise V4L2 extends old frames
the detection is visible behind.
"""

    def __init__(self, index, size=CAM_SIZE, warmup=3.0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            # After failing, do not fall silently on attraction: invented
            # Numbers on the vending machine cannot be seen on the trade fair day.
            raise RuntimeError(f"Kamera {index} laesst sich nicht oeffnen")
        # Put MJPG in front of the big: as YUYV costs 720p a multiple
        # USB bandwidth, and it depends on whether two cameras go on a bus.
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.lock = threading.Lock()
        self.frame = None
        self.seq = 0          # counts new frames so CameraView can cache
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        # isOpened() only confirms that the device opened; it does not confirm
        # that frames arrive. If the camera is busy (second game start, other
        # process), macOS can return an open handle while read() stays False.
        # Without this loop, both panes stay black while the game keeps running.
        # This costs startup time only, not runtime performance.
        t0 = time.monotonic()
        while self.frame is None and time.monotonic() - t0 < warmup:
            time.sleep(0.05)
        if self.frame is None:
            self.close()
            raise RuntimeError(f"Kamera {index} liefert kein Bild "
                               f"(belegt? Kamerarechte?)")

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                # Camera disconnected or hung: do not busy-loop. The last frame
                # remains, the hysteresis releases, tray sum() goes to 0.
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame
                self.seq += 1

    def read(self):
        with self.lock:
            return self.seq, self.frame

    def close(self):
        self.running = False
        self.cap.release()


class ArucoDetector:
    """Marker -> {id: Viereck}. Same signature as FakeDetector.

Own thread with DETECT HZ instead of 60 Hz: detectMarkers is expensive, and
Nobody pushes Pucks 60 times a second.

The squares emerge as shares in the whole picture (0...1), not as
Pixel. Otherwise the scene must know the camera opening — and the
is no longer true at the moment when a UVC-Geraet the requested
Don't deliver. That they do, and the mistake would be
Overlay, which is systematically out of line.
"""

    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI):
        self.cam = cam
        self.hold = hold
        self.roi = roi
        self.lock = threading.Lock()
        self.marks = {}         # marker_id -> (timestamp, quad in 0..1)
        self.det = cv2.aruco.ArucoDetector(
            cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50),
            cv2.aruco.DetectorParameters())
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        rx, ry, rw, rh = self.roi
        while True:
            _, frame = self.cam.read()
            if frame is not None:
                h, w = frame.shape[:2]
                x0, y0 = int(rx * w), int(ry * h)
                x1, y1 = x0 + int(rw * w), y0 + int(rh * h)
                # Crop first instead of filtering later: one step does both,
                # and detection only pays for the ROI area.
                # Measured 1.21 ms instead of 2.00 ms at 60% x 70%.
                # The slice is a NumPy view, not a copy.
                gray = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
                corners, ids, _ = self.det.detectMarkers(gray)
                now = time.monotonic()
                found = {}
                for c, i in zip(corners, ids.flatten() if ids is not None else ()):
                    if int(i) not in VALUES:
                        continue    # foreign marker, not to the game
                    # Map window coordinates back to image fractions so the
                    # scene only needs to multiply by the pane rectangle.
                    q = c.reshape(4, 2) / (x1 - x0, y1 - y0) * (rw, rh) + (rx, ry)
                    found[int(i)] = (now, tuple(map(tuple, q)))
                with self.lock:
                    self.marks.update(found)
            time.sleep(1 / DETECT_HZ)

    def fresh(self):
        # Hysteresis: a marker stays active while hidden for less than hold.
        # is covered. This is the solution for the hand above the tray,
        # not for pucks that are really taken away.
        # The lock is mandatory: without it, iteration can throw RuntimeError
        # when the thread inserts a new ID concurrently.
        now = time.monotonic()
        with self.lock:
            return {i: q for i, (t, q) in self.marks.items() if now - t < self.hold}


class VideoView:
    """Clip from a file, in loop. Same conversion as CameraView.

pygame can't be a video, but cv2.VideoCapture takes a file as well as
a Geraet -- the player is the same class as the passthrough, only
with a clock instead of a gravel. A camera *drueckt* pictures (thousand
there a thread and a sequence counter), a file is *drawn* (thus
here dt).

ponytail: decoded in the renderthread. At 1120x630 are the few
Milliseconds, 25 times a second, and only as long as the scene stands. Will it
close to the Pi: the same tombber thread as in Camera, the shape already fits.
"""

    def __init__(self, path, size=DEMO_SIZE):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Demo-Clip {path} laesst sich nicht oeffnen")
        self.size = size
        self.step = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 25)
        self.t = self.step      # first picture immediately, not only after step
        self.surf = None

    def surface(self, dt):
        self.t += dt
        if self.t < self.step:
            return self.surf    # Clip with 25 Hz, rendered with 60
        self.t = 0.0
        ok, frame = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # am Ende von vorn
            ok, frame = self.cap.read()
        if ok:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
        return self.surf

    def close(self):
        self.cap.release()


class CameraView:
    """Passthrough: latest camera image as pygame interface in Insetgroesse.

First reduce, then copy — the conversion costs proportional
to the pixel number, and 400x300 are a twentieth of 1280x720.
frombuffer with "BGR" saves the cvtColor: pygame-ce takes OpenCVs
channel order directly.

INTER LINEAR, not INTER AREA: measured 0.17 ms instead of 3.5 ms per frame.
AREA averages all source pixels during comminution and is at factor 3
twenty times more expensive — for an inset behind scanlines nobody sees that
but 3.5 ms waer a fuenftel of the frame budget on the Pi.
"""

    def __init__(self, cam, det=None, size=CAM_VIEW):
        self.cam = cam
        self.det = det      # only the top down pin has one: the arm image is
        self.size = size    # pure passthrough, there be nothing to show
        self.seq = -1
        self.surf = None

    def surface(self):
        seq, frame = self.cam.read()
        # The camera delivers 30 pictures/s, renders with 60: without this
        # Comparison is converted twice, for nothing.
        if seq != self.seq and frame is not None:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
            self.seq = seq
        return self.surf


if __name__ == "__main__":
    # Self-test without camera: synthetic tablet. Prueft, that Dictionary
    # and markers/ match that the squares lie where the markers
    # that the window was sorted out and that the hysteresis
    # and then it's down. uv run game/hw.py -> ok
    import numpy as np

    W, H, MS = 640, 480, 90

    class _Still:
        def __init__(self, frame): self.frame = frame
        def read(self): return 1, self.frame

    def _tray(spots):
        """spots: {marker_id: (x, y) linke obere Ecke in Pixeln}"""
        frame = np.full((H, W, 3), 255, np.uint8)   # weiss = Ruhezone
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

    # 1 · Recognition, values and position of the quadrangle in open window
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

    # 2 · Fenster sortiert aus, was ausserhalb liegt
    det_roi = ArucoDetector(_Still(_tray(spots)), roi=(0.0, 0.0, 0.6, 0.5))
    assert sorted(_settle(det_roi)) == [0, 4], det_roi.fresh()   # 9 liegt draussen

    # 3 · Hysteresis swoops short and then expands
    still.frame = _tray({})                 # Tablett leer geraeumt
    time.sleep(MARKER_HOLD / 2)
    assert len(_ := det_open.fresh()) == 3, ("Hysterese haelt nicht", _)
    time.sleep(MARKER_HOLD * 2)
    assert det_open.fresh() == {}, "Hysterese baut nicht ab"

    # 4 · FakeDetector hat dieselbe Schnittstelle
    f = FakeDetector().fresh()
    assert len(f) == 5 and all(len(q) == 4 for q in f.values())
    print("ok")
