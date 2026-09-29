import os
import signal
import subprocess

import cv2
import pygame
from config import (WIDTH, HEIGHT, FPS, FONT_PATH, FONT_SIZES, CAMERA, CAM_VIEWS, ARM_MIRROR, ARM_UD, ARM_PANE, TOP_CROP,
                    CAM_INDEXES, CAM_ZOOM, CAM_FLIP, DEMO_VIDEO, CV_THREADS, BUTTONS,
                    CAM_STALE, CAM_CTRLS, TRAY_ROI, MAC)
from app import Ctx, run_game
from db import DB
from hw import (ArucoDetector, Buttons, Camera, CameraView, FakeDetector,
                Leds, VideoView, notify)
from music import Music, SR, BUF
from scenes import IdleScene


class NoView:
    """pnp-layout solo: the arm pane draws nothing (scenes skip a None surface)."""
    det = None
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
    cams = {i: Camera(i, zoom=CAM_ZOOM if i == top else None, flip=CAM_FLIP and i == top)
            for i in set(CAM_INDEXES)} if CAMERA else {}
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
    det = ArucoDetector(cams[top]) if cams else FakeDetector()
    # Left is plain passthrough, right is the same image plus overlay. Only
    # the top-down pane gets the detector.
    ctx = Ctx(detector=det, db=DB(), fonts=fonts, music=Music(), leds=Leds(),
              views=(CameraView(cams[arm], size=CAM_VIEWS[0], mirror=ARM_MIRROR, ud=ARM_UD)
                     if ARM_PANE else NoView(),
                     CameraView(cams[top], det, size=CAM_VIEWS[1], crop=TOP_CROP)) if cams else (),
              demo=VideoView(DEMO_VIDEO) if DEMO_VIDEO else None,
              buttons=Buttons() if BUTTONS else None)
    # Expo mode (pi/setup.sh): systemd sets RUNTIME_DIRECTORY and NOTIFY_SOCKET.
    # The scene name goes to a file so the updater only restarts between
    # rounds; the watchdog ping only goes out while every camera delivers.
    run_dir = os.environ.get("RUNTIME_DIRECTORY")
    last = None

    def beat(scene):
        nonlocal last
        name = type(scene).__name__
        if run_dir and name != last:
            with open(os.path.join(run_dir, "state"), "w") as f:
                f.write(name)
            last = name
        if all(c.age() < CAM_STALE for c in cams.values()):
            notify("WATCHDOG=1")

    notify("READY=1")
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS, beat)
    ctx.leds.close()
    for c in cams.values():
        c.close()
    if ctx.buttons:
        ctx.buttons.close()
    if ctx.demo:
        ctx.demo.close()


if __name__ == "__main__":
    main()