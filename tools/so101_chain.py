"""Print the LINKS table in game/arm.py, from the SO-101's own CAD.

    uv run tools/so101_chain.py            # fetches the CAD, prints the table

Run this when the arm's geometry changes -- a new SO-101 revision, or a
different view. Paste the output over LINKS in game/arm.py. It is not part
of the game and the game never calls it: 37 MB of STLs has no business in
the repo, and the numbers it makes have not changed since the arm was
built.

What it does, in one paragraph. TheRobotStudio publishes the arm as a URDF
plus one STL per part. The URDF is a tree of links joined by transforms, so
walking it at the zero pose gives every part's triangles in one shared
space. Project those onto the plane the side view looks at, and each link
becomes a blob of overlapping triangles; take the outer contour of that
blob and hand it to approxPolyDP, and the blob becomes eight or ten points.
Finally each link's points are written relative to its own joint, which is
what lets the game place a link by rotating it about that joint and nothing
else -- no frames, no matrices at runtime.

Two joints come out with spin 0: shoulder_pan and wrist_roll turn about an
axis that lies in the picture, so from the side they do nothing. `spin` is
just how much of a joint's axis points at the camera, rounded.
"""

import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

import cv2
import numpy as np

REPO = "https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/main/Simulation/SO101"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".so101")

# link -> (parent, the joint that moves it). Base first: the walk below
# needs the parent placed before the child.
CHAIN = [("base_link", None, None),
         ("shoulder_link", "base_link", "shoulder_pan"),
         ("upper_arm_link", "shoulder_link", "shoulder_lift"),
         ("lower_arm_link", "upper_arm_link", "elbow_flex"),
         ("wrist_link", "lower_arm_link", "wrist_flex"),
         ("gripper_link", "wrist_link", "wrist_roll"),
         ("moving_jaw_so101_v1_link", "gripper_link", "gripper")]
SHORT = dict(zip([c[0] for c in CHAIN],
                 ["base", "shoulder", "upper", "fore", "wrist", "grip", "jaw"]))
# The board holder is clutter at this size, and the base servo never shows:
# it sits inside its printed holder.
SKIP = ("waveshare_mounting_plate",)
HIDE_SERVO = ("base",)
# Their real profile has the motor holder's slots cut into it, and at four
# millimetres a pixel a slot stops reading as a slot.
HULL = ("base", "shoulder")


def fetch(name):
    path = os.path.join(CACHE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        print("fetching", name, file=sys.stderr)
        urllib.request.urlretrieve(f"{REPO}/{name}", path)
    return path


def stl(path):
    """(n, 3, 3) triangles from a binary STL. 84-byte header, 50 per facet."""
    raw = open(path, "rb").read()
    n = int(np.frombuffer(raw, "<u4", 1, 80)[0])
    rec = np.frombuffer(raw, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)),
                                       ("a", "<u2")]), n, 84)
    return rec["v"].astype(np.float64)


def rpy(r, p, y):
    """URDF fixed-axis roll-pitch-yaw -> rotation matrix."""
    cr, sr, cp, sp, cy, sy = (np.cos(r), np.sin(r), np.cos(p),
                              np.sin(p), np.cos(y), np.sin(y))
    return (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
            @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
            @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]]))


def T(el):
    m = np.eye(4)
    if el is not None:
        m[:3, :3] = rpy(*map(float, el.get("rpy", "0 0 0").split()))
        m[:3, 3] = list(map(float, el.get("xyz", "0 0 0").split()))
    return m


def world():
    """link -> 4x4 at the zero pose, and link -> [(stl path, 4x4)]."""
    root = ET.parse(fetch("so101_new_calib.urdf")).getroot()
    org = {j.find("child").get("link"): T(j.find("origin"))
           for j in root.findall("joint")}
    at = {"base_link": np.eye(4)}
    for link, parent, _ in CHAIN[1:]:
        at[link] = at[parent] @ org[link]
    vis = {}
    for L in root.findall("link"):
        out = []
        for v in L.findall("visual"):
            mesh = v.find("geometry/mesh")
            name = mesh is not None and os.path.basename(mesh.get("filename"))
            if name and not any(s in name for s in SKIP):
                out.append((fetch("assets/" + name), T(v.find("origin"))))
        vis[L.get("name")] = out
    return at, vis


def outline(tri, eps=0.012, res=1600):
    """Outer contour of projected triangles, simplified to a few points."""
    flat = tri.reshape(-1, 2)
    lo, hi = flat.min(0), flat.max(0)
    s = res / max(hi - lo)
    w, h = (np.ceil((hi - lo) * s) + 8).astype(int)
    img = np.zeros((h, w), np.uint8)
    q = ((tri - lo) * s + 4).astype(np.int32)
    q[:, :, 1] = h - 1 - q[:, :, 1]
    cv2.fillPoly(img, q, 1)
    # Close first: a part built from several meshes can have hairline gaps
    # between them, and findContours would walk into every one of them.
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cnts, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, eps * cv2.arcLength(c, True), True)[:, 0]
    p = c.astype(np.float64)
    p[:, 1] = h - 1 - p[:, 1]
    return (p - 4) / s + lo


def wrap(pts, indent=6):
    if pts is None:
        return "None"
    out, line = [], ""
    for x, y in pts:
        t = f"({round(x * 1000)}, {round(y * 1000)}), "
        if len(line) + len(t) > 66:
            out.append(line.rstrip())
            line = ""
        line += t
    out.append(line.rstrip().rstrip(","))
    return "(" + ("\n" + " " * indent).join(out) + ")"


def main():
    at, vis = world()
    print("LINKS = (")
    for link, parent, joint in CHAIN:
        M = at[link]
        pivot = np.array([M[0, 3], M[2, 3]])          # world xz = the side view
        parts = {}
        for path, vt in vis[link]:
            W = M @ vt
            v = stl(path)
            kind = "servo" if "sts3215" in os.path.basename(path) else "body"
            parts.setdefault(kind, []).append(v @ W[:3, :3].T + W[:3, 3])
        name = SHORT[link]
        polys = {}
        for kind, tris in parts.items():
            p = outline(np.concatenate(tris)[:, :, [0, 2]]) - pivot
            if name in HULL:
                p = cv2.convexHull(p.astype(np.float32))[:, 0].astype(np.float64)
            polys[kind] = p
        if name in HIDE_SERVO:
            polys.pop("servo", None)
        print(f'    ("{name}", {SHORT.get(parent)!r}, {joint!r}, '
              f"({round(pivot[0] * 1000)}, {round(pivot[1] * 1000)}), "
              f"{int(round(-M[1, 2])):+d},")
        print(f"     {wrap(polys.get('body'))},")
        print(f"     {wrap(polys.get('servo'))}),")
    print(")")

    # The constants solve() needs, measured off the same zero pose.
    P = lambda k: np.array([at[k][0, 3], at[k][2, 3]])
    S, E, Wp = P("upper_arm_link"), P("lower_arm_link"), P("wrist_link")
    ang = lambda v: np.degrees(np.arctan2(v[1], v[0]))
    print(f"\n# L1, L2 = {np.linalg.norm(E - S) * 1000:.1f}, "
          f"{np.linalg.norm(Wp - E) * 1000:.1f}")
    print(f"# UPPER_REST, FORE_REST = {ang(E - S):.2f}, {ang(Wp - E):.2f}")
    print(f"# SHOULDER = ({round(S[0] * 1000)}, {round(S[1] * 1000)})")
    # The gripper tip -- how far the fingers reach past the wrist, which
    # is the ceiling on arm.TCP.
    root = ET.parse(fetch("so101_new_calib.urdf")).getroot()
    tip = at["gripper_link"] @ next(T(j.find("origin")) for j in root.findall("joint")
                                    if j.get("name") == "gripper_frame_joint")
    g = np.array([tip[0, 3], tip[2, 3]]) - Wp
    print(f"# wrist -> gripper tip: {np.linalg.norm(g) * 1000:.1f} mm "
          f"at {ang(g):.2f} deg  (arm.TCP holds a treat short of it)")


if __name__ == "__main__":
    main()
