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
                    BARREL_K, CAM_VIEW, GREY, BG, ROUND_SECONDS, FUSE_PULSE)
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
    # GameScene start with the practice. The plan below sets `tray`.
    tray = {}
    def fresh(self):             return self.tray
    def rank(self, player):      return 4, 23
    def new_player(self, name):  return 42


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

    # The top-down pane gets the overlay, so the marker frames show up.
    ctx.views[1].det = True
    random.seed(0)    # balance.gap() rolls the target, otherwise the shots drift each run
    quad = lambda x: [(x, .5), (x + .06, .5), (x + .06, .6), (x, .6)]

    def typed(d, page=0):
        """A dialog on `page`, fully typed out -- the state a reader sees."""
        d.i, d.n, d.t = page, 1e9, 0.4
        return d

    story = scenes.StoryScene(ctx, 42, "MAX", new=True)
    tut = scenes.GameScene(ctx, 42, "MAX")
    typed(tut.dialog)
    # The practice treat lands: the scene goes through the same update()
    # as on the cabinet, so pop-up, sprinkles and Bella's line are real.
    done_tut = scenes.GameScene(ctx, 42, "MAX")
    stub.tray = {5: quad(.45)}
    done_tut.update(0.3)
    typed(done_tut.dialog)
    game = scenes.GameScene(ctx, 42, "MAX")
    typed(game.dialog)
    order = scenes.GameScene(ctx, 42, "MAX")
    typed(order.dialog, 1)
    # A round that landed just off: EUR 0.30 short at EUR 6.70, time ran
    # out. Gives a score with three digits and two stars.
    done = scenes.Result(target=67, total=64, dist=67, left=0.0,
                         marks={0: 1, 3: 1, 7: 1, 9: 1})
    score = scenes.DisplayScoreScene(ctx, done, 42)
    typed(score.dialog)
    play = dict(phase="play", dialog=None, pop=None, hit=0.0, confirm=0.0)
    # (filename, scene, state). The state gets written into __dict__ -- same
    # technique as in the self-test, so the in-between states that are hard to
    # hit by hand also make it into the image (hint, PERFECT, over budget).
    plan = [
        ("1-idle",         scenes.IdleScene(ctx),                     {}),
        ("2-name",         scenes.EntryScene(ctx),       dict(cursor=1, slots=[12, 0, 23])),
        ("3-story",        story, dict(dialog=typed(story.dialog, 1))),
        ("4-tutorial",     tut,                                       {}),
        ("5-tutorial-done", done_tut,                                 {}),
        ("6-order",        order,                                     {}),
        ("7-game-add",     game, dict(play, left=ROUND_SECONDS * 0.7, clock=0.3,
                                      marks={5: quad(.45)}, total=32, target=67,
                                      pop=["cupcake_lemon", "+3,20", 0.4])),
        ("8-game-hint",    game, dict(pop=None, still=99.0, left=FUSE_PULSE * 0.6,
                                      clock=0.3)),
        ("9-game-over",    game, dict(still=0.0, left=ROUND_SECONDS * 0.4,
                                      marks={5: quad(.35), 9: quad(.55)}, total=84)),
        ("10-game-perfect", game, dict(left=ROUND_SECONDS * 0.3, total=67, hit=1.0,
                                       marks={5: quad(.35), 2: quad(.55)},
                                       fx=burst(960, 196, 0.25))),
        # done=True: the screenshot shows the final state, not the first
        # tenth of a second of the count-up.
        ("11-score",       score, dict(shown=done.score, done=True, now=2.5,
                                       fx=burst(960, 300, 2.5))),
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
