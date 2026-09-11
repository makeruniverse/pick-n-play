"""ArUco-Marker als SVG in Millimetern, fuer Bambu Studio und Fusion.

    uv run tools/marker_svg.py [kantenlaenge_mm]      # Vorgabe 30

Schreibt markers/aruco_marker_<id>.svg fuer jede ID aus VALUES. Nur die
schwarzen Zellen, als Quadrate -- das Helle ist das Material drumherum, also
der Cupcake. Der schwarze Rand gehoert zum Marker, der helle Rand darum nicht:
den muss die Oberflaeche liefern (mindestens eine Zellbreite).

Die PNGs daneben bleiben: aus einem Pixelbild baut kein Slicer Geometrie.
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
    """6 x 6 Zellen inklusive Rand, True = schwarz. Ein Pixel pro Zelle."""
    return cv2.aruco.generateImageMarker(D, i, 6) < 128


def svg(i, mm):
    c = mm / 6
    rects = "\n".join(f'  <rect x="{x * c:g}" y="{y * c:g}" width="{c:g}" height="{c:g}"/>'
                      for y, x in zip(*np.nonzero(cells(i))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm:g}mm" height="{mm:g}mm" '
            f'viewBox="0 0 {mm:g} {mm:g}">\n{rects}\n</svg>\n')


def check(text, mm, i):
    """Die SVG zurueck ins Bild rastern und erkennen lassen -- prueft die Datei,
    nicht nur die Zellen, aus denen sie entstanden ist."""
    px = 10 / (mm / 6)                       # 10 px pro Zelle
    img = np.full((80, 80), 255, np.uint8)   # 1 Zelle heller Rand ringsum
    for x, y, w in re.findall(r'x="([\d.]+)" y="([\d.]+)" width="([\d.]+)"', text):
        x0, y0 = round(float(x) * px) + 10, round(float(y) * px) + 10
        img[y0:y0 + round(float(w) * px), x0:x0 + round(float(w) * px)] = 0
    _, ids, _ = cv2.aruco.ArucoDetector(D).detectMarkers(img)
    assert ids is not None and ids.ravel().tolist() == [i], f"{i}: erkannt {ids}"


if __name__ == "__main__":
    mm = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    for i in sorted(VALUES):
        text = svg(i, mm)
        check(text, mm, i)
        path = os.path.join(OUT, f"aruco_marker_{i}.svg")
        with open(path, "w") as f:
            f.write(text)
        print(path)
