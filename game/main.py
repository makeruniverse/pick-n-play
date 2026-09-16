import cv2
import pygame
from config import (WIDTH, HEIGHT, FPS, FONT_PATH, FONT_SIZES, CAMERA,
                    CAM_INDEXES, DEMO_VIDEO, CV_THREADS, BUTTONS)
from app import Ctx, run_game
from db import DB
from hw import (ArucoDetector, Buttons, Camera, CameraView, FakeDetector,
                Leds, VideoView)
from music import Music, SR, BUF
from scenes import IdleScene


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
    cams = {i: Camera(i) for i in set(CAM_INDEXES)} if CAMERA else {}
    arm, top = CAM_INDEXES
    det = ArucoDetector(cams[top]) if cams else FakeDetector()
    # Left is plain passthrough, right is the same image plus overlay. Only
    # the top-down pane gets the detector.
    ctx = Ctx(detector=det, db=DB(), fonts=fonts, music=Music(), leds=Leds(),
              views=(CameraView(cams[arm]), CameraView(cams[top], det)) if cams else (),
              demo=VideoView(DEMO_VIDEO) if DEMO_VIDEO else None,
              buttons=Buttons() if BUTTONS else None)
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS)
    ctx.leds.close()
    for c in cams.values():
        c.close()
    if ctx.buttons:
        ctx.buttons.close()
    if ctx.demo:
        ctx.demo.close()


if __name__ == "__main__":
    main()