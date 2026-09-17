"""ArUco markers as SVG in millimeters, for Bambu Studio and Fusion.

    uv run tools/marker_svg.py [edge_length_mm]      # default 30

Writes markers/aruco_marker_<id>.svg for each ID in VALUES. Only the
black cells, as squares -- the light area is the material around it, i.e.
the cupcake. The black border belongs to the marker, the light border
around it doesn't: the surface has to provide that (at least one cell
width).

The PNGs next to them stay: no slicer builds geometry from a pixel image.
"""

import os
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
from config import VALUES                                      # noqa: E402

D = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
OUT = os.path.join(os.path.dirname(__file__), "..", "markers")


def cells(i):
    """6 x 6 cells including border, True = black. One pixel per cell."""
    return cv2.aruco.generateImageMarker(D, i, 6) < 128


def svg(i, mm):
    c = mm / 6
    rects = "\n".join(f'  <rect x="{x * c:g}" y="{y * c:g}" width="{c:g}" height="{c:g}"/>'
                      for y, x in zip(*np.nonzero(cells(i))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm:g}mm" height="{mm:g}mm" '
            f'viewBox="0 0 {mm:g} {mm:g}">\n{rects}\n</svg>\n')


def check(text, mm, i):
    """Rasterize the SVG back into an image and let it be detected -- checks
    the file, not just the cells it was built from."""
    px = 10 / (mm / 6)                       # 10 px per cell
    img = np.full((80, 80), 255, np.uint8)   # 1 cell light border all around
    for x, y, w in re.findall(r'x="([\d.]+)" y="([\d.]+)" width="([\d.]+)"', text):
        x0, y0 = round(float(x) * px) + 10, round(float(y) * px) + 10
        img[y0:y0 + round(float(w) * px), x0:x0 + round(float(w) * px)] = 0
    _, ids, _ = cv2.aruco.ArucoDetector(D).detectMarkers(img)
    assert ids is not None and ids.ravel().tolist() == [i], f"{i}: detected {ids}"


if __name__ == "__main__":
    mm = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    for i in sorted(VALUES):
        text = svg(i, mm)
        check(text, mm, i)
        path = os.path.join(OUT, f"aruco_marker_{i}.svg")
        with open(path, "w") as f:
            f.write(text)
        print(path)
