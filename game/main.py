import pygame
from config import (WIDTH, HEIGHT, FPS, FONT_PATH, FONT_SIZES, CAMERA,
                    CAM_INDEXES, DEMO_VIDEO)
from app import Ctx, run_game
from db import DB
from hw import ArucoDetector, Camera, CameraView, FakeDetector, VideoView
from music import Music, SR, BUF
from scenes import IdleScene


def main():
    pygame.mixer.pre_init(SR, -16, 1, BUF)   # must stand before pygame.init(),
    pygame.init()                            # then the buffer size is fixed
    fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    # One Camera object per physical index: if CAM_INDEXES contains the same
    # index twice (e.g. 0 and 0), the device is opened only once and shared.
    cams = {i: Camera(i) for i in set(CAM_INDEXES)} if CAMERA else {}
    arm, top = CAM_INDEXES
    det = ArucoDetector(cams[top]) if cams else FakeDetector()
    # Left pure passthrough, right the same picture plus overlay. Only
    # Top-down banana gets the Detector.
    ctx = Ctx(detector=det, db=DB(), fonts=fonts, music=Music(),
              views=(CameraView(cams[arm]), CameraView(cams[top], det)) if cams else (),
              demo=VideoView(DEMO_VIDEO) if DEMO_VIDEO else None)
    run_game(IdleScene(ctx), WIDTH, HEIGHT, FPS)
    for c in cams.values():
        c.close()
    if ctx.demo:
        ctx.demo.close()


if __name__ == "__main__":
    main()