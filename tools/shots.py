"""Screenshots of all scenes, no cabinet, no camera, no window.

    uv run tools/shots.py [target_dir]      # default: docs/shots

For the build log. Run once after every UI change, then the current state
sits as a PNG in the repo and `git diff --stat docs/shots` shows which scenes
changed.

Same trick as the layout self-test at the end of `scenes.py`: SDL on the
dummy driver, a stub ctx instead of music, database and detector, then
`scene.render()` onto its own surface. No cabinet, no reference image,
nothing to maintain. The difference from the self-test is one line -- instead
of checking the rectangles, the surface gets saved.

The CRT overlay is included: the image should show what the cabinet looks
like, and without scanlines it looks like a different game.
"""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import cv2                                                      # noqa: E402
import pygame                                                   # noqa: E402
from app import Ctx, crt_gain, px                               # noqa: E402
from config import (WIDTH, HEIGHT, FONT_PATH, FONT_SIZES, CRT,  # noqa: E402
                    BARREL_K, CAM_VIEW, GREY, BG, WARN_SECONDS, ROUND_SECONDS)
import scenes                                                   # noqa: E402


class Stub:
    """Music, database and detector all in one -- they all do nothing here."""

    def __getattr__(self, _):    return lambda *a, **k: None
    # Scores, descending -- since the scoring session, high is good, and a
    # dummy with single-digit numbers would show a game in the build log that
    # no longer exists. Four digits at the top: that's a perfect round.
    def top(self, n=5):          return [("VAD", 1000), ("MAX", 948), ("ANN", 871),
                                         ("LEO", 795), ("KIM", 640)][:n]
    # Empty, like the cabinet at the start of a round -- only this way does
    # GameScene get a distance that matches a real round. What's shown on the
    # tray in the image is set by the plan below via `total`.
    def fresh(self):             return {}


class StubView:
    """Camera pane as a placeholder.

    Without this the round screen in the build log would have two black holes
    in the most noticeable spot -- an image that says something wrong about
    the state. A labeled box says "this is the camera," and that's true.
    """

    det = None

    def __init__(self, label, font):
        self.surf = pygame.Surface(CAM_VIEW)
        self.surf.fill((28, 28, 28))
        pygame.draw.rect(self.surf, GREY, self.surf.get_rect(), 2)
        t = font.render(label, False, GREY)
        self.surf.blit(t, t.get_rect(center=self.surf.get_rect().center))

    def surface(self):
        return self.surf


def burst(x, y, t):
    """Sprinkle pop, already t seconds in -- at t = 0 it is a single clump."""
    fx = scenes.Sprinkles(x, y)
    for _ in range(round(t * 30)):
        fx.update(1 / 30)
    return fx


def shots(out):
    pygame.init()
    fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    stub = Stub()
    ctx = Ctx(detector=stub, db=stub, fonts=fonts, music=stub, leds=stub,
              views=(StubView("ARM CAM", fonts["tiny"]),
                     StubView("TOP-DOWN CAM", fonts["tiny"])))

    random.seed(0)    # balance.gap() rolls the target, otherwise 3-6 drifts each run
    game = scenes.GameScene(ctx)
    # A round that landed just off: EUR 0.30 short at EUR 5.00 distance, time
    # ran out. Gives a score with three digits instead of a round number that
    # wouldn't let you judge the count-up.
    done = scenes.Result(target=67, total=64, dist=50, left=0.0,
                         marks={0: 1, 3: 1, 7: 1, 9: 1})
    board = scenes.LeaderboardScene(ctx, done)
    # (filename, scene, state). The state gets written into __dict__ -- same
    # technique as in the self-test, so the in-between states that are hard to
    # hit by hand also make it into the image (final seconds, PERFECT).
    plan = [
        ("1-idle",         scenes.IdleScene(ctx),                     {}),
        ("2-howto",        scenes.HowToScene(ctx),                    {}),
        ("3-game-add",     game, dict(left=ROUND_SECONDS * 0.7, hit=0.0,
                                      confirm=0.0, total=game.target - 32)),
        ("4-game-remove",  game, dict(total=game.target + 17)),
        ("5-game-warning", game, dict(left=WARN_SECONDS * 0.4)),
        ("6-game-perfect", game, dict(left=ROUND_SECONDS * 0.7,
                                      total=game.target, hit=1.0,
                                      fx=burst(960, 178, 0.25))),
        # done=True: the screenshot shows the final state, not the first
        # tenth of a second of the count-up.
        ("7-score",        scenes.DisplayScoreScene(ctx, done),
                           dict(shown=done.score, done=True, t=2.5,
                                fx=burst(960, 300, 2.5))),
        ("8-name",         board, dict(cursor=2)),
    ]

    gain = crt_gain(WIDTH, HEIGHT, BARREL_K) if CRT else None
    os.makedirs(out, exist_ok=True)
    for name, scene, state in plan:
        scene.__dict__.update(state)
        # 32 bit, otherwise get_view("2") in px() doesn't have the shape cv2 wants.
        surf = pygame.Surface((WIDTH, HEIGHT), depth=32)
        surf.fill(BG)
        scene.render(surf)
        if gain is not None:
            cv2.multiply(px(surf), gain, px(surf), 1 / 255)
        path = os.path.join(out, f"{name}.png")
        pygame.image.save(surf, path)
        print(path)
    pygame.quit()


if __name__ == "__main__":
    shots(sys.argv[1] if len(sys.argv) > 1
          else os.path.join(os.path.dirname(__file__), "..", "docs", "shots"))
