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
    # remap und multiply im Renderpfad verteilen sich damit ueber drei Kerne
    # statt ueber alle vier -- der vierte gehoert dem Teleop-Prozess.
    cv2.setNumThreads(CV_THREADS)
    pygame.mixer.pre_init(SR, -16, 1, BUF)   # muss vor pygame.init() stehen,
    pygame.init()                            # danach ist die Puffergroesse fix
    fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    # Ein Camera-Objekt je physischem Index: stehen in CAM_INDEXES zweimal
    # dieselbe 0, wird das Geraet nicht zweimal geoeffnet (das schlaegt fehl),
    # sondern ein Grabber speist beide Panes.
    cams = {i: Camera(i) for i in set(CAM_INDEXES)} if CAMERA else {}
    arm, top = CAM_INDEXES
    det = ArucoDetector(cams[top]) if cams else FakeDetector()
    # Links reiner Passthrough, rechts dasselbe Bild plus Overlay. Nur das
    # Top-Down-Pane bekommt den Detector mit.
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