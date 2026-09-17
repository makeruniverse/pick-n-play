"""Pixel sprites from text grids -- like the music in music.py.

The grids and palettes belong to the theme (themes/<name>.py, via config).
This module only handles turning text into a surface: 16 x 16, scaled with
NEAREST in whole factors, so the pixels stay as hard-edged as the font's.
"""

from functools import lru_cache

import pygame

from config import BASE, SHAPES, SPRITES


@lru_cache(maxsize=128)
def sprite(name, scale):
    """Finished surface, memoized: each size is built exactly once."""
    shape, colors = SPRITES[name]
    pal = {**BASE, **colors}
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, row in enumerate(SHAPES[shape]):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), pal[ch])
    return pygame.transform.scale(surf, (16 * scale, 16 * scale))


if __name__ == "__main__":
    # Checks EVERY theme in themes/, not just the active one: otherwise a
    # typo in the second theme only surfaces when someone switches at the show.
    #   uv run game/sprites.py [sheet.png]   -> ok, optional sheet of the active theme
    import glob
    import importlib
    import os
    import sys
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    from config import VALUES
    import config
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(os.path.join(here, "themes", "*.py"))):
        t = importlib.import_module("themes." + os.path.basename(path)[:-3])
        for key in config.THEME_KEYS:
            assert hasattr(t, key), f"{path}: {key} missing"
        for name, rows in t.SHAPES.items():
            assert len(rows) == 16 and all(len(r) == 16 for r in rows), (path, name)
        for name, (shape, colors) in t.SPRITES.items():
            used = set("".join(t.SHAPES[shape])) - {"."}
            missing = used - {**t.BASE, **colors}.keys()
            assert not missing, (path, name, missing)
        # Every marker needs a sprite, otherwise the price reveal dies
        assert set(t.SPRITE) == set(VALUES), (path, set(VALUES) ^ set(t.SPRITE))
        assert set(t.SPRITE.values()) <= t.SPRITES.keys(), path
    assert sprite(next(iter(SPRITES)), 2).get_size() == (32, 32)
    if len(sys.argv) > 1:
        sheet = pygame.Surface((len(SPRITES) * 136 + 8, 144))
        sheet.fill(config.BG)
        for i, name in enumerate(SPRITES):
            sheet.blit(sprite(name, 8), (8 + i * 136, 8))
        pygame.image.save(sheet, sys.argv[1])
    print("ok")
