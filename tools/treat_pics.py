"""The printed treats as pictures for the price ladder, strip and pop-up.

    uv run tools/treat_pics.py          # -> game/assets/treats/<marker id>.png

The sprites were a drawing of the treat, and the visitor had to match the
drawing to the object in their hand -- one layer too many. These are the
objects themselves: the same voxel plans the printers got (tools/voxel.py,
tools/nachdruck.py), marker included, because the white or black field on
top is what tells the red bar from the red cupcake.

All pictures share one scale (PX per voxel), so a bigger print is a bigger
picture: heavier is dearer stays visible. The game scales them all by one
factor. Takes a minute (marked() searches the largest readable marker), so
it runs here and the PNGs go into git.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pygame                       # noqa: E402  voxel sets the dummy driver
import voxel as v                   # noqa: E402
import nachdruck                    # noqa: E402

# Marker id -> the plan it was printed from. Everything in the theme's SPRITE,
# including the retired ones, so switching one back on needs no new picture.
PRINTED = {1: "riegel", 0: "macaron", 6: "stueck_erdbeer", 2: "petitfour",
           7: "riegel_gross", 5: "cup_vanille", 9: "torte_erdbeer", 8: "torte_gross",
           4: "bonbon", 10: "cup_mini", 11: "cup_blaubeer"}
PX = 2      # px per 1 mm cell, 10 per voxel: the game only ever scales down

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "game", "assets", "treats")
    os.makedirs(out, exist_ok=True)
    nachdruck.register()
    for mid, name in PRINTED.items():
        g, _ = v.marked(name)
        assert v.MARKERS[name][0] == mid, (name, v.MARKERS[name][0], mid)
        img = v.iso(g, PX)
        img = img.subsurface(img.get_bounding_rect())
        pygame.image.save(img, os.path.join(out, f"{mid}.png"))
        print(f"#{mid:<2} {name:15} {img.get_width()}x{img.get_height()}")
