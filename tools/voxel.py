"""Voxel treats in the style of the sprites from themes/sugar_rush.py.

    uv run tools/voxel.py [dir] [treat ...]      # default build/voxel, all

Writes one 3MF per treat (one object, one part per filament, colors and
extruders already assigned), plus preview.png.

Each treat is a stack of layers, one layer = one voxel height: a top-down
mask plus a color. Chunky and smooth like a 16x16 sprite, no sprinkles, no
highlights.

The ArUco marker (DICT_4X4_50) is projected onto the shape from above, in
1 mm cells independent of the voxel grid: as large as possible, but only as
large as OpenCV can still read it at camera resolution from above.
"""

import json
import os
import sys
import zipfile

import cv2
import numpy as np

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame                                                  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
from themes.sugar_rush import (APPLE, BG, CARAMEL, GREY, ICE,  # noqa: E402
                               IVORY, LATTE, LEMON, LILAC, SAKURA, SCARLET, TAN)

VOX = 5            # mm per voxel. 2.5 was too fiddly, 1.25 too filigree
N = 16             # base area 16 x 16 voxels = 80 x 80 mm, like a sprite

# Bambu PLA Matte. The names end up in the file names.
FIL = dict(ivory=IVORY, latte=LATTE, sakura=SAKURA, lemon=LEMON, ice=ICE, lilac=LILAC,
           tan=TAN, caramel=CARAMEL, scarlet=SCARLET, apple=APPLE,
           dark_chocolate=(77, 51, 36), charcoal=(0, 0, 0),
           plum=(149, 0, 81), dark_blue=(4, 47, 86))       # Plum, Dark Blue: marker cells only
# Cube faces: normal, four corners counter-clockwise as seen from outside.
FACES = (((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))),
         ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))),
         ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0))),
         ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
         ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))),
         ((0, 0, -1), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))))


def neighbour(m, n):
    """m read shifted by n cells, False outside."""
    k = max(map(abs, n))
    p = np.pad(m, k)
    x, y, z = m.shape
    return p[k + n[0]:k + n[0] + x, k + n[1]:k + n[1] + y, k + n[2]:k + n[2] + z]


def tops(solid):
    """Index of the topmost filled voxel per column, -1 if empty."""
    return np.where(solid.any(2), solid.shape[2] - 1 - np.argmax(solid[:, :, ::-1], 2), -1)




# Seen from above, in voxels, centered between the four middle cells
I, J = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
X, Y = I + 0.5 - N / 2, J + 0.5 - N / 2
RHO = np.hypot(X, Y)
# Long stripes: per side face they run across it, so they stay straight
STRIPE = np.where(np.abs(X) > np.abs(Y), J, I) % 2 == 0


def disc(r):
    return RHO <= r


def box(w, d):
    return (np.abs(X) < w / 2) & (np.abs(Y) < d / 2)


def stack(*layers):
    """Layers from the bottom: (mask, filament or array of filaments).
    A '*' before the filament means decoration: drops out where the marker goes."""
    g = np.full((N, N, len(layers)), "", "<U16")
    for k, (m, fil) in enumerate(layers):
        g[..., k][m] = np.broadcast_to(fil, (N, N))[m]
    return g


def cupcake(cup, rim, frost, top, cup_c, rim_c, frost_c):
    """Radii in voxels from the bottom; cup striped, rim overhangs."""
    return stack(*[(disc(r), np.where(STRIPE, *cup_c)) for r in cup],
                 (disc(rim), rim_c),
                 *[(disc(r), frost_c) for r in frost],
                 *[(disc(1), f"*{top}")] * 2 * bool(top))


def macaron(shell, fill):
    """Filling set slightly in: visible stripe instead of a deep seam in shadow."""
    return stack((disc(3.6), shell), (disc(4.2), shell), (disc(3.9), fill),
                 (disc(4.2), shell), (disc(3.6), shell))


def bar(wrap, choc):
    """Lying bar: chocolate chunks on the left, paper with label on the right."""
    body, left = box(14, 8), X < -2
    blocks = left & ((I - 1) % 3 < 2) & ((J - 4) % 3 < 2)
    label = (np.abs(X - 2.5) < 2) & (np.abs(Y) < 3)
    center = (np.abs(X - 2.5) < 1) & (np.abs(Y) < 1)
    return stack((body, np.where(left, choc, wrap)),
                 (body & (blocks | ~left), np.where(left, choc, wrap)),
                 (label, np.where(center, "*lemon", "*ivory")))


def petitfour(icing, band):
    flower = box(4, 4) & ~(box(4, 4) & (np.abs(X) > 1) & (np.abs(Y) > 1))
    return stack(*[(box(8, 8), f) for f in (icing, icing, band, icing, icing)],
                 (flower, np.where(box(2, 2), "*lemon", "*ivory")))


def berliner(dough, base):
    jam = (X > 4) & (np.abs(Y) < 1)
    return stack((disc(3.2), base), (disc(4.2), dough),
                 (disc(4.8), np.where(jam, "scarlet", dough)),
                 (disc(4.8), np.where(jam, "scarlet", dough)),
                 (disc(4.4), np.where(disc(3.2), "ivory", dough)),
                 (disc(3.4), "ivory"), (disc(2), "ivory"))


def slice_(frost, sponge, jam):
    """Cake slice, point facing forward (-y)."""
    wedge = (np.abs(Y) < 5) & (np.abs(X) <= (Y + 5) * 0.36 + 0.5)
    return stack(*[(wedge, f) for f in (sponge, sponge, jam, sponge, sponge, frost)])


def cake(frost, sponge, jam):
    """Whole cake: layers, icing with drips over the edge, candles at the rim
    (the center belongs to the marker)."""
    drip = ~disc(4.4) & STRIPE
    candle = ((np.abs(X) == 4.5) & (np.abs(Y) == 1.5)) | ((np.abs(X) == 1.5) & (np.abs(Y) == 4.5))
    return stack(*[(disc(5.2), f) for f in (sponge, jam, sponge, sponge, jam)],
                 (disc(5.2), np.where(drip, frost, sponge)),
                 (disc(5.2), frost), (candle, "*ivory"), (candle, "*ivory"), (candle, "*lemon"))


# Name -> build plan. Order like SPRITE in the theme: cheap/light first.
TREATS = {
    "macaron":      lambda: macaron("sakura", "ivory"),
    "riegel":       lambda: bar("scarlet", "dark_chocolate"),
    "petitfour":    lambda: petitfour("sakura", "ice"),
    "berliner":     lambda: berliner("caramel", "tan"),
    "cup_mini":     lambda: cupcake([3, 3.3, 3.6], 4.2, [3.8, 3, 1.6], None,
                                    ("lemon", "ivory"), "caramel", "sakura"),
    "cup_vanille":  lambda: cupcake([3.6, 4, 4.2, 4.6, 4.8], 5.2, [4.8, 4.2, 3.2, 2.2], "scarlet",
                                    ("sakura", "ivory"), "tan", "ivory"),
    "cup_blaubeer": lambda: cupcake([3.2, 3.4, 3.6, 3.8, 4, 4.2], 4.6, [4.2, 3.6, 2.6], "lilac",
                                    ("lilac", "ivory"), "tan", "ice"),
    "cup_erdbeer":  lambda: cupcake([4, 4.4, 4.8, 5.2], 5.8, [5.4, 4.8, 3.8, 2.4], "scarlet",
                                    ("ivory", "sakura"), "tan", "sakura"),
    "cup_schoko":   lambda: cupcake([3.6, 4, 4.2, 4.6, 4.8], 5.2, [4.6, 3.8, 3.8, 2.8, 2.8, 1.6], "scarlet",
                                    ("dark_chocolate", "caramel"), "caramel", "dark_chocolate"),
    "cup_luxus":    lambda: cupcake([3.8, 4.2, 4.4, 4.8, 5, 5.2], 5.6, [5.2, 4.6, 4, 3.2, 2.2], "lemon",
                                    ("charcoal", "tan"), "dark_chocolate", "tan"),
    "stueck_erdbeer": lambda: slice_("sakura", "tan", "scarlet"),
    "stueck_schoko":  lambda: slice_("dark_chocolate", "caramel", "latte"),
    "torte_schoko":   lambda: cake("dark_chocolate", "caramel", "latte"),
    "torte_erdbeer":  lambda: cake("sakura", "tan", "scarlet"),
}


# Name -> (marker ID from DICT_4X4_50, cell color, base color, search region).
# IDs 0..9 like SPRITE in the theme, 10..13 are new. Color pairs from
# docs/meshy-prompts.md; inverted on chocolate (light cells).
MARKERS = {
    "macaron":        (0, "plum", "sakura", None),
    "riegel":         (1, "charcoal", "ivory", X > -2),     # paper only
    "petitfour":      (2, "plum", "sakura", None),
    "berliner":       (3, "charcoal", "ivory", None),
    "cup_erdbeer":    (4, "plum", "sakura", None),
    "cup_vanille":    (5, "charcoal", "ivory", None),
    "stueck_erdbeer": (6, "plum", "sakura", None),
    "torte_schoko":   (7, "ivory", "dark_chocolate", None),
    "stueck_schoko":  (8, "ivory", "dark_chocolate", None),
    "torte_erdbeer":  (9, "plum", "sakura", None),
    "cup_mini":       (10, "plum", "sakura", None),
    "cup_blaubeer":   (11, "dark_blue", "ice", None),
    "cup_schoko":     (12, "ivory", "dark_chocolate", None),
    "cup_luxus":      (13, "charcoal", "tan", None),
}

SUB = 5                # fine grid for the marker: 5 cells per voxel = 1 mm
FINE = VOX / SUB
DEPTH = 2              # mm colored from the top; the camera only sees top faces
CAM = 1.2              # px per mm on the tray, camera looks straight down
TRAY = (110, 110, 110)
DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
_params = cv2.aruco.DetectorParameters()
_params.detectInvertedMarker = True    # like hw.ArucoDetector
DET = cv2.aruco.ArucoDetector(DICT, _params)


def place(g, name, cell, margin):
    """Place the marker with `cell` mm cells as centered as possible on the
    top-down view. None if it doesn't fit fully on the treat anywhere, margin
    of `margin` mm included."""
    mid, ink, paper, region = MARKERS[name]
    t = 6 * cell + 2 * margin
    sil = (g != "").any(2)
    if region is not None:
        sil &= region.repeat(SUB, 0).repeat(SUB, 1)
    c = np.pad(sil.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    full = (c[t:, t:] - c[:-t, t:] - c[t:, :-t] + c[:-t, :-t]) == t * t
    if not full.any():
        return None
    pos = np.argwhere(full)
    # Field center vs. area center, both computed in cell edges
    x0, y0 = pos[np.argmin(((pos + t / 2 - np.argwhere(sil).mean(0) - 0.5) ** 2).sum(1))]
    g = g.copy()
    win = np.zeros(sil.shape, bool)
    win[x0:x0 + t, y0:y0 + t] = True
    g[np.char.startswith(g, "*") & win[:, :, None]] = ""     # decoration in the field: out
    bits = cv2.aruco.generateImageMarker(DICT, mid, 6)    # 6x6 including border, 0 = dark
    top = tops(g != "")
    for i, j in np.argwhere(win):
        u, v = (i - x0 - margin) // cell, (j - y0 - margin) // cell
        dark = 0 <= u < 6 and 0 <= v < 6 and bits[5 - v, u] == 0   # image row runs against y
        z = np.arange(max(0, top[i, j] - DEPTH + 1), top[i, j] + 1)
        g[i, j, z] = np.where(g[i, j, z] != "", ink if dark else paper, "")
    return g


def view(g):
    """Camera image: straight down, topmost voxel per column."""
    top = tops(g != "")
    col = np.where((top >= 0)[..., None],
                   np.take_along_axis(rgb(g), np.maximum(top, 0)[..., None, None], 2)[:, :, 0], TRAY)
    img = np.pad(col, ((8, 8), (8, 8), (0, 0)), constant_values=TRAY[0])
    img = img[:, ::-1].transpose(1, 0, 2).astype(np.uint8)       # rows = -y
    return cv2.resize(img, None, fx=CAM * FINE, fy=CAM * FINE, interpolation=cv2.INTER_AREA)


def found(g, mid):
    _, ids, _ = DET.detectMarkers(cv2.cvtColor(view(g), cv2.COLOR_RGB2GRAY))
    return ids is not None and mid in ids


def marked(name):
    """Fine grid with the largest marker the camera can still read."""
    g = TREATS[name]()
    g = g.repeat(SUB, 0).repeat(SUB, 1).repeat(SUB, 2)
    for cell in range(12, 2, -1):
        # without margin only if it doesn't fit with one: then the tray is the margin
        for margin in (-(-cell // 2), 0):
            m = place(g, name, cell, margin)
            if m is not None and found(np.char.lstrip(m, "*"), MARKERS[name][0]):
                return np.char.lstrip(m, "*"), cell
    raise SystemExit(f"{name}: no readable marker")


def rgb(g):
    names, inv = np.unique(g, return_inverse=True)
    return np.array([FIL.get(n, BG) for n in names], np.uint8)[inv].reshape(g.shape + (3,))


def mesh(m):
    """Closed shell: every cube face that borders something else."""
    tris, norms = [], []
    for n, quad in FACES:
        idx = np.argwhere(m & ~neighbour(m, n))
        q = idx[:, None, :] + np.array(quad)
        tris.append(q[:, [0, 1, 2, 0, 2, 3]].reshape(-1, 3, 3))
        norms.append(np.repeat([n], 2 * len(idx), axis=0))
    tris = np.concatenate(tris) * FINE
    # Signed volume == voxel volume: shell closed, normals point outward
    vol = np.einsum("ij,ij->", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])) / 6
    assert np.isclose(vol, m.sum() * FINE ** 3), (vol, m.sum() * FINE ** 3)
    return tris, np.concatenate(norms)


def hexcol(fil):
    return "#%02X%02X%02X" % tuple(FIL[fil])


def write_3mf(path, name, parts):
    """One object, one part per filament, extruders 1..n in part order.
    Bambu Studio reads model_settings.config (part -> extruder) and
    project_settings.config (filament colors); other slicers read the
    basematerials."""
    n = len(parts)
    objs = []
    for k, (fil, tris) in enumerate(parts, 1):
        v, idx = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
        v -= [N * VOX / 2, N * VOX / 2, 0]
        vs = "".join(f'<vertex x="{a:g}" y="{b:g}" z="{c:g}"/>' for a, b, c in v)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in idx.reshape(-1, 3))
        objs.append(f'<object id="{k}" type="model" pid="{n + 2}" pindex="{k - 1}">'
                    f'<mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
    mats = "".join(f'<base name="{f}" displaycolor="{hexcol(f)}"/>' for f, _ in parts)
    comps = "".join(f'<component objectid="{k}"/>' for k in range(1, n + 1))
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">\n'
        '<metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
        f'<metadata name="Title">{name}</metadata>\n'
        f'<resources><basematerials id="{n + 2}">{mats}</basematerials>{"".join(objs)}'
        f'<object id="{n + 1}" type="model"><components>{comps}</components></object></resources>\n'
        f'<build><item objectid="{n + 1}" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/></build>\n'
        '</model>\n')
    unit = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
    part_cfg = "".join(
        f'<part id="{k}" subtype="normal_part"><metadata key="name" value="{fil}"/>'
        f'<metadata key="matrix" value="{unit}"/><metadata key="extruder" value="{k}"/></part>\n'
        for k, (fil, _) in enumerate(parts, 1))
    settings = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
        f'<object id="{n + 1}"><metadata key="name" value="{name}"/>'
        '<metadata key="extruder" value="1"/>\n' + part_cfg + '</object>\n'
        '<plate><metadata key="plater_id" value="1"/><metadata key="locked" value="false"/>'
        f'<model_instance><metadata key="object_id" value="{n + 1}"/>'
        '<metadata key="instance_id" value="0"/></model_instance></plate>\n</config>\n')
    project = json.dumps({"filament_colour": [hexcol(f) for f, _ in parts],
                          "filament_settings_id": ["Bambu PLA Matte @BBL X1C"] * n,
                          "filament_type": ["PLA"] * n, "version": "02.07.01.62"}, indent=4)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                   '<Default Extension="config" ContentType="text/xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
                   'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config", project)


def iso(g, px):
    """Isometric preview, view from (+x, +y, above), back painted first."""
    X, Y, Z = g.shape
    a, b, c = px, px / 2, px * 1.15
    surf = pygame.Surface(((X + Y) * a, (X + Y) * b + Z * c), pygame.SRCALPHA)
    col = rgb(g)

    def pt(x, y, z):
        return ((y - x + X) * a, (x + y) * b + (Z - z) * c)

    full = g != ""
    shade = {(0, 0, 1): 1.0, (1, 0, 0): 0.78, (0, 1, 0): 0.6}
    open_ = {n: ~neighbour(full, n) for n in shade}
    # Just for the image: ambient occlusion per face -- the more voxels stand
    # directly in front of a face, the darker it gets. Otherwise grooves and
    # steps disappear.
    light = {}
    for n in shade:
        u, v = [e for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if e != n]
        light[n] = 1 - 0.07 * sum(neighbour(full, tuple(np.add(n, np.add(np.multiply(u, i), np.multiply(v, j))))).astype(float)
                                  for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    vis = full & (open_[0, 0, 1] | open_[1, 0, 0] | open_[0, 1, 0])
    for x, y, z in sorted(map(tuple, np.argwhere(vis)), key=sum):
        for n, quad in FACES:
            if n in shade and open_[n][x, y, z]:
                pygame.draw.polygon(surf, [int(v * shade[n] * light[n][x, y, z]) for v in col[x, y, z]],
                                    [pt(x + qx, y + qy, z + qz) for qx, qy, qz in quad])
    return surf


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "build", "voxel")
    only = sys.argv[2:] or list(TREATS)
    os.makedirs(out, exist_ok=True)
    pygame.font.init()
    font = pygame.font.Font(None, 22)
    cols, tw = 5, 360
    grids, isos, infos = {}, {}, {}
    used = set()
    for name in only:
        g, cell = marked(name)
        fils = sorted(set(g[g != ""]))
        used |= set(fils)
        write_3mf(os.path.join(out, f"{name}.3mf"), name, [(f, mesh(g == f)[0]) for f in fils])
        full = g != ""
        w, h = full.any(axis=(1, 2)).sum() * FINE, g.shape[2] * FINE
        cm3 = full.sum() * FINE ** 3 / 1000
        img = iso(g, 8 / SUB)
        isos[name] = img.subsurface(img.get_bounding_rect())
        infos[name] = f"{name}  #{MARKERS[name][0]}  {6 * cell} mm  {cm3:.0f} cm3"
        print(f"{name:15} {w:.0f}x{h:.0f} mm  {cm3:4.0f} cm3  Marker #{MARKERS[name][0]:<2} "
              f"{6 * cell} mm  {', '.join(fils)}")
    th = max(s.get_height() for s in isos.values()) + 60
    sheet = pygame.Surface((cols * tw, -(-len(only) // cols) * th))
    sheet.fill(BG)
    for i, name in enumerate(only):
        ox, oy, img = (i % cols) * tw, (i // cols) * th, isos[name]
        sheet.blit(img, (ox + (tw - img.get_width()) // 2, oy + th - 40 - img.get_height()))
        sheet.blit(font.render(infos[name], True, GREY), (ox + 12, oy + th - 30))
    pygame.image.save(sheet, os.path.join(out, "preview.png"))
    print(f"{len(used)} filaments total: {', '.join(sorted(used))}")
