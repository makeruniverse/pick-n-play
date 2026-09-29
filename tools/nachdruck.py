"""Reprint plate 2026-09-28: six treats, one filament each plus marker cells.

    uv run tools/nachdruck.py build/voxel/nachdruck_h2c.3mf h2c      # or x1c_pink, x1c_red

One 3MF per printer, extruders by AMS slot (PRINTERS). Writes a preview PNG next to it."""
import json, sys, zipfile
import numpy as np
sys.path.insert(0, "tools")
import voxel as v
from voxel import solid, cupcake, macaron, berliner, marked, mesh, hexcol, found, N, VOX, FINE, box, stack, disc, I, J, X, Y, STRIPE


def bar_big(wrap, choc):
    """riegel one size up: 80 x 50, a layer taller, chunks on the left."""
    body, left = box(16, 10), X < -3
    blocks = left & ((I - 0) % 3 < 2) & ((J - 3) % 3 < 2)
    return stack((body, np.where(left, choc, wrap)), (body, np.where(left, choc, wrap)),
                 (body & (blocks | ~left), np.where(left, choc, wrap)))


def bonbon(wrap):
    """Lying bonbon like the sprite: flat round middle (the marker's), a
    twisted fan of wrapper on either side, one layer lower."""
    fan = (np.abs(X) > 3.5) & (np.abs(X) < 7.5) & (np.abs(Y) <= np.abs(X) - 3)
    return stack((disc(3.6) | fan, wrap), (disc(3.6) | fan, wrap), (disc(3.6), wrap))


def cake_big(frost, sponge, jam):
    """Two tiers on the torte's 50 mm footprint (the gripper wedge caps the
    width, so bigger has to go up). No candles: in one filament they fill the
    ledge and the tiers stop reading as tiers."""
    drip = ~disc(4.4) & STRIPE
    return stack(*[(disc(5.2), f) for f in (sponge, jam, sponge, sponge, jam)],
                 (disc(5.2), np.where(drip, frost, sponge)), (disc(5.2), frost),
                 *[(disc(3.6), f) for f in (sponge, jam, sponge, frost)])

# name -> (plan, body, marker cells, id, plate). One body colour each. A
# spool can only sit in one printer and there is one black spool. Plates with
# two colours go to the X1Cs; the one with more goes to the H2C, whose tool
# changer swaps without purging. Macaron and torte share Hot Pink: one plate,
# two colours.
SET = {
    "macaron":      (lambda: macaron("a", "a"), "hot_pink", "ivory", 0, "x1c_pink"),
    "torte_gross":  (lambda: cake_big("a", "a", "a"), "hot_pink", "ivory", 8, "x1c_pink"),
    "cup_vanille":  (v.TREATS["cup_vanille"], "scarlet", "ivory", 5, "x1c_red"),
    "cup_mini":     (v.TREATS["cup_mini"], "yellow", "charcoal", 10, "h2c"),
    "riegel_gross": (lambda: bar_big("a", "a"), "blue", "charcoal", 7, "h2c"),
    "bonbon":       (lambda: bonbon("a"), "grass_green", "charcoal", 4, "h2c"),
}
# Search region: the marker must stay on one level, not spill down a cone or
# off the top tier onto the ledge 20 mm below.
REGION = {"riegel_gross": X > -3, "torte_gross": disc(3.6), "cup_vanille": disc(3.6)}


def register():
    """SET into voxel's TREATS/MARKERS, so marked() builds each as printed.
    tools/treat_pics.py needs the same, which is why this isn't script code."""
    for name, (plan, body, cell, mid, _) in SET.items():
        v.TREATS[name] = lambda plan=plan, body=body: solid(plan(), body)
        v.MARKERS[name] = (mid, cell, body, REGION.get(
            name, v.MARKERS[name][3] if name in v.MARKERS else None))


# AMS slot order per plate
PRINTERS = {"x1c_pink": ["hot_pink", "ivory"],
            "x1c_red": ["scarlet", "ivory"],
            "h2c": ["charcoal", "yellow", "blue", "grass_green"]}


def main():
    register()
    out, printer = sys.argv[1], sys.argv[2]
    EXT = PRINTERS[printer]
    plate = {k: t for k, t in SET.items() if t[4] == printer}
    objs, items, cfg, oid, grids = [], [], [], 0, {}
    for i, (name, (plan, body, cell, mid, _)) in enumerate(plate.items()):
        px, py = 128 + (i - (len(plate) - 1) / 2) * 90, 128     # one row, 90 mm apart
        g, c = marked(name)
        assert found(g, mid), name
        full = g != ""
        print(f"{name:12} #{mid:<2} {body:8}/{cell:8} marker {6*c} mm  "
              f"{full.any(axis=(1,2)).sum()*FINE:.0f}x{full.any(axis=(0,2)).sum()*FINE:.0f}x{g.shape[2]*FINE:.0f} mm  "
              f"{full.sum()*FINE**3/1000:.0f} cm3")
        grids[name] = g
        parts = []
        for fil in sorted(set(g[full])):
            oid += 1
            tris = mesh(g == fil)[0]
            vv, idx = __import__("numpy").unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
            vv -= [N * VOX / 2, N * VOX / 2, 0]
            objs.append(f'<object id="{oid}" type="model"><mesh><vertices>'
                        + "".join(f'<vertex x="{a:g}" y="{b:g}" z="{c_:g}"/>' for a, b, c_ in vv)
                        + "</vertices><triangles>"
                        + "".join(f'<triangle v1="{a}" v2="{b}" v3="{c_}"/>' for a, b, c_ in idx.reshape(-1, 3))
                        + "</triangles></mesh></object>")
            parts.append((oid, fil))
        oid += 1
        objs.append(f'<object id="{oid}" type="model"><components>'
                    + "".join(f'<component objectid="{k}"/>' for k, _ in parts) + "</components></object>")
        items.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {px} {py} 0" printable="1"/>')
        unit = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
        cfg.append(f'<object id="{oid}"><metadata key="name" value="{name}_{mid}"/><metadata key="extruder" value="1"/>\n'
                   + "".join(f'<part id="{k}" subtype="normal_part"><metadata key="name" value="{f}"/>'
                             f'<metadata key="matrix" value="{unit}"/><metadata key="extruder" value="{EXT.index(f) + 1}"/></part>\n'
                             for k, f in parts) + "</object>\n")
        cfg_ids = [int(o.split('"')[1]) for o in cfg]

    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">\n'
             '<metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
             '<metadata name="Title">nachdruck</metadata>\n'
             f'<resources>{"".join(objs)}</resources>\n<build>{"".join(items)}</build>\n</model>\n')
    settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(cfg)
                + '<plate><metadata key="plater_id" value="1"/><metadata key="locked" value="false"/>'
                + "".join(f'<model_instance><metadata key="object_id" value="{i}"/><metadata key="instance_id" value="0"/></model_instance>'
                          for i in cfg_ids) + '</plate>\n</config>\n')
    project = json.dumps({"filament_colour": [hexcol(f) for f in EXT],
                          "filament_settings_id": ["Bambu PLA Matte @BBL X1C"] * len(EXT),
                          "filament_type": ["PLA"] * len(EXT), "version": "02.07.01.62"}, indent=4)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
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
    print("wrote", out)

    import pygame                                            # preview next to the 3MF
    tiles = [v.iso(g, 8 / v.SUB) for g in grids.values()]
    tiles = [t.subsurface(t.get_bounding_rect()) for t in tiles]
    sheet = pygame.Surface((sum(t.get_width() for t in tiles) + 40 * len(tiles), max(t.get_height() for t in tiles) + 40))
    sheet.fill(v.BG); x = 20
    for t in tiles:
        sheet.blit(t, (x, sheet.get_height() - 20 - t.get_height())); x += t.get_width() + 40
    pygame.image.save(sheet, out.replace(".3mf", ".png"))

    # Height spread of the marker cells. The cupcake cones reach 10-15 mm, which
    # the 2026-09-11 simulation allows in the tray's middle (todo.md, cone limit).
    for name, g in grids.items():
        z = np.argwhere(g == plate[name][2])[:, 2] * FINE
        print(f"{name:12} marker cells span {z.max() - z.min():.0f} mm in height")

    # Colour changes: layers (0.2 mm) that need more than one filament, and how
    # many filaments each of those has. The slicer changes k-1 times per layer.
    layers = {}
    for g in grids.values():
        for z in range(g.shape[2]):
            layers.setdefault(z, set()).update(set(g[:, :, z][g[:, :, z] != ""]))
    changes = sum(max(len(f) - 1, 0) for f in layers.values()) * round(FINE / 0.2)
    print(f"{printer}: {changes} filament changes at 0.2 mm layers")


if __name__ == "__main__":
    main()
