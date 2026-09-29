import os
import signal
import subprocess
import time

import settings
settings.boot()     # before config: rolls back a settings change that keeps crashing

import cv2
import pygame
from config import (WIDTH, HEIGHT, FPS, FONT_PATH, FONT_SIZES, CAMERA, CAM_VIEWS,
                    CAM_INDEXES, CAM_ZOOM, CAM_FLIP, DEMO_VIDEO, CV_THREADS, BUTTONS,
                    CAM_STALE, CAM_CTRLS, TRAY_ROI, MAC, DB_PATH)
from app import Ctx, run_game
from db import DB
from hw import (ArucoDetector, Buttons, Camera, CameraView, FakeDetector,
                Leds, VideoView, notify, read_flips)
from music import Music, SR, BUF
from scenes import IdleScene, PauseScene


class NoView:
    """Arm camera missing: the pane draws nothing (scenes skip a None surface)."""
    det, mirror, ud = None, False, False
    def surface(self): return None


def main():
    # remap and multiply in the render path spread out over three cores
    # instead of all four -- the fourth belongs to the teleop process.
    cv2.setNumThreads(CV_THREADS)
    pygame.mixer.pre_init(SR, -16, 1, BUF)   # must come before pygame.init(),
    pygame.init()                            # after that the buffer size is fixed
    fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    # One Camera object per physical index: if CAM_INDEXES has the same 0
    # twice, the device is not opened twice (that fails), instead one
    # grabber feeds both panes.
    arm, top = CAM_INDEXES
    # A camera that won't open used to crash the start: a black restart loop
    # every 3 s. Now the arm camera is simply left out, and without the top
    # camera (no scoring possible) the screen says "technical pause" and the
    # start is retried in PAUSE_SECONDS.
    cams = {}
    for i in set(CAM_INDEXES) if CAMERA else ():
        try:
            cams[i] = Camera(i, zoom=CAM_ZOOM if i == top else None, flip=CAM_FLIP and i == top)
        except RuntimeError as e:
            print(e, flush=True)
    paused = CAMERA and top not in cams
    # Exposure etc. from config + cam.json (pnp-cam). auto_exposure comes
    # first in each dict: exposure_time is refused until it's manual.
    for role, i in zip(("arm", "top"), CAM_INDEXES if cams and not MAC else ()):
        for k, v in CAM_CTRLS[role].items():
            subprocess.run(["v4l2-ctl", "-d", f"/dev/video{i}", "-c", f"{k}={v}"])

    def snap(*_):
        """pnp-cam snap: the frames as they come in, the top one with the
        detection box, next to the scene state (or /tmp under pnp-start)."""
        for role, i in zip(("arm", "top"), CAM_INDEXES):
            f = cams[i].read()[1]
            if f is None:
                continue
            if role == "top":
                h, w = f.shape[:2]
                rx, ry, rw, rh = TRAY_ROI
                f = cv2.rectangle(f.copy(), (int(rx * w), int(ry * h)),
                                  (int((rx + rw) * w), int((ry + rh) * h)), (0, 255, 0), 3)
            cv2.imwrite(os.path.join(os.environ.get("RUNTIME_DIRECTORY", "/tmp"),
                                     f"cam-{role}.jpg"), f)
    if cams:
        signal.signal(signal.SIGUSR1, snap)
    det = ArucoDetector(cams[top]) if top in cams else FakeDetector()
    # Left is plain passthrough, right is the same image plus overlay. Only
    # the top-down pane gets the detector.
    ctx = Ctx(detector=det, db=DB(), fonts=fonts, music=Music(), leds=Leds(),
              views=(CameraView(cams[arm], size=CAM_VIEWS[0]) if arm in cams else NoView(),
                     CameraView(cams[top], det, size=CAM_VIEWS[1])) if top in cams else (),
              demo=VideoView(DEMO_VIDEO) if DEMO_VIDEO else None,
              buttons=Buttons() if BUTTONS else None)
    # Expo mode (pi/setup.sh): systemd sets RUNTIME_DIRECTORY and NOTIFY_SOCKET.
    # The scene name goes to a file so the updater only restarts between
    # rounds; the watchdog ping only goes out while every camera delivers.
    run_dir = os.environ.get("RUNTIME_DIRECTORY")
    last, polled, t0, saved = None, 0.0, time.monotonic(), time.monotonic()

    def beat(scene):
        nonlocal last, polled, t0, saved
        now = time.monotonic()
        if t0 and now - t0 > settings.TRIAL_OK:
            settings.ok()      # ran long enough: a settings change sticks
            t0 = None
        # Hourly copy of the scores, only between rounds (it blocks a moment).
        # One file per hour of the day, so there are never more than 24.
        if now - saved > 3600 and type(scene).__name__ == "IdleScene":
            saved = now
            ctx.db.backup(DB_PATH.replace(".db", "") + time.strftime(".backup-auto-%H.db"))
        # pnp-cam <role> flip ...: re-read once a second, no restart
        if ctx.views and time.monotonic() - polled > 1.0:
            polled = time.monotonic()
            flips = read_flips()
            for role, view in zip(("arm", "top"), ctx.views):
                view.mirror, view.ud = flips[role]
        name = type(scene).__name__
        if run_dir and name != last:
            with open(os.path.join(run_dir, "state"), "w") as f:
                f.write(name)
            last = name
        if all(c.age() < CAM_STALE for c in cams.values()):
            notify("WATCHDOG=1")

    notify("READY=1")
    run_game(PauseScene(ctx) if paused else IdleScene(ctx), WIDTH, HEIGHT, FPS, beat,
             home=IdleScene)
    ctx.leds.close()
    for c in cams.values():
        c.close()
    if ctx.buttons:
        ctx.buttons.close()
    if ctx.demo:
        ctx.demo.close()


if __name__ == "__main__":
    main()