"""Screenshots aller Szenen, ohne Automat, ohne Kamera, ohne Fenster.

    uv run tools/shots.py [zielordner]      # Vorgabe: docs/shots

Fuer das Build-Log. Nach jeder UI-Aenderung einmal laufen lassen, dann liegt
der Stand als PNG im Repo und `git diff --stat docs/shots` sagt, welche Szenen
sich geaendert haben.

Derselbe Trick wie der Layout-Selbsttest am Ende von `scenes.py`: SDL auf den
Dummy-Treiber, ein Stub-Ctx statt Musik, Datenbank und Detector, dann
`scene.render()` auf eine eigene Flaeche. Kein Automat, kein Vergleichsbild,
nichts zu pflegen. Der Unterschied zum Selbsttest ist eine Zeile -- statt die
Rechtecke zu pruefen, wird die Flaeche gespeichert.

Das CRT-Overlay liegt mit drauf: das Bild soll zeigen, wie der Automat
aussieht, und ohne Scanlines sieht es aus wie ein anderes Spiel.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import cv2                                                      # noqa: E402
import pygame                                                   # noqa: E402
from app import Ctx, crt_gain, px                               # noqa: E402
from config import (WIDTH, HEIGHT, FONT_PATH, FONT_SIZES, CRT,  # noqa: E402
                    BARREL_K, CAM_VIEW, GREY, BG, WARN_SECONDS)
import scenes                                                   # noqa: E402


class Stub:
    """Musik, Datenbank und Detector auf einmal -- sie tun hier alle nichts."""

    def __getattr__(self, _):    return lambda *a, **k: None
    def top(self, n=5):          return [("VAD", 3), ("MAX", 8), ("ANN", 12),
                                         ("LEO", 19), ("KIM", 26)][:n]
    def fresh(self):             return {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}


class StubView:
    """Kamera-Pane als Platzhalter.

    Ohne das haette der Rundenbildschirm im Build-Log zwei schwarze Loecher an
    der auffaelligsten Stelle -- ein Bild, das etwas Falsches ueber den Stand
    sagt. Ein beschrifteter Kasten sagt „hier ist die Kamera", und das stimmt.
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


def shots(out):
    pygame.init()
    fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    stub = Stub()
    ctx = Ctx(detector=stub, db=stub, fonts=fonts, music=stub, leds=stub,
              views=(StubView("ARM CAM", fonts["tiny"]),
                     StubView("TOP-DOWN CAM", fonts["tiny"])))

    game = scenes.GameScene(ctx)
    board = scenes.LeaderboardScene(ctx, 3)
    # (Dateiname, Szene, Zustand). Der Zustand wird ins __dict__ geschrieben --
    # dieselbe Technik wie im Selbsttest, damit auch die Zwischenstaende ins
    # Bild kommen, die man von Hand kaum trifft (letzte Sekunden, PERFECT).
    plan = [
        ("1-idle",         scenes.IdleScene(ctx),                     {}),
        ("2-howto",        scenes.HowToScene(ctx),                    {}),
        ("3-game-add",     game, dict(left=42.0, hit=0.0, confirm=0.0,
                                      total=game.target - 60)),
        ("4-game-remove",  game, dict(total=game.target + 23)),
        ("5-game-warning", game, dict(left=WARN_SECONDS * 0.4)),
        ("6-game-perfect", game, dict(left=42.0, total=game.target, hit=1.0,
                                      fx=scenes.Sprinkles())),
        ("7-score",        scenes.DisplayScoreScene(ctx, 180,
                                                    {0: 1, 3: 1, 7: 1, 9: 1}), {}),
        ("8-name",         board, dict(cursor=2)),
    ]

    gain = crt_gain(WIDTH, HEIGHT, BARREL_K) if CRT else None
    os.makedirs(out, exist_ok=True)
    for name, scene, state in plan:
        scene.__dict__.update(state)
        # 32 Bit, sonst hat get_view("2") in px() nicht die Form, die cv2 will.
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
