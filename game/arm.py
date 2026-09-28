"""The SO-101 on screen: real geometry, real kinematics, pixel output.

The old arm was two 32 x 32 grids and `demo()` slid the whole picture from
frame to frame. That is why it read as a crane hook: on a real arm the base
stands still and only the angles change. Drawing more detail would not have
fixed that -- the eye recognises a robot arm by its joint chain, not by its
surface.

So the shape is not drawn by hand here. It is measured off the machine that
stands next to the cabinet. TheRobotStudio publishes the SO-101 as CAD:

    https://github.com/TheRobotStudio/SO-ARM100
    Simulation/SO101/so101_new_calib.urdf + assets/*.stl

`tools/so101_chain.py` takes those, projects every link's meshes onto the
side view, reduces each silhouette to a handful of points, and prints the
`LINKS` table below -- run it and it prints what is written here. 37 MB of
triangles come out as seventy numbers, and those seventy numbers are the
real arm, not an impression of it.

What that buys, beyond looking right:

  * The link lengths are the machine's own -- upper arm 116 mm, forearm
    135 mm, wrist to gripper tip 159 mm. Nothing here is eyeballed.
  * `solve()` is ordinary two-link inverse kinematics, so the gripper gets
    to a point the way the follower would, elbow up and wrist hanging
    straight down. The grip from above that the story screen shows is a
    constraint now, not a pose somebody drew.
  * `LIMITS` is straight out of the URDF, so a pose the sprite takes is a
    pose the real servos could hold. A demo the machine cannot copy would
    be a small lie standing right next to the machine.

Not modelled: `shoulder_pan` and `wrist_roll`. Both turn about an axis that
lies in the picture plane, so from the side there is nothing to see -- the
side view is what makes the other four joints legible, and this is the
price. The arm reaches out and back instead of swinging around its base,
which is also the shorter motion for a four-second loop.
"""

import math
from functools import lru_cache

import pygame

from config import ARM, BASE

# ── The chain, measured off the CAD ───────────────────────────────────────
# (name, parent, joint, pivot, spin, printed part, servo)
#
# Millimetres, and the pivot is where that link's joint sits at the zero
# pose. `spin` is which way a positive joint angle turns on screen: it is
# how much of the joint's axis points at the camera, so the two joints you
# cannot see turn from the side carry a 0 and never move.
#
# The polygons are already world-oriented at the zero pose and relative to
# their own pivot, which is what makes the runtime a rotate-and-add and
# nothing more. Two of them per link, because the real arm is two-tone:
# printed plate and black servo, and the servo block at every joint is what
# says "this is a servo arm" from three metres away.
LINKS = (
    # Base and shoulder are the convex hull of their profile, everything
    # above them is the profile itself. Their real outline has the motor
    # holder's slots cut into it, and at four millimetres a pixel those
    # stop reading as slots and start reading as holes in the machine.
    ("base", None, None, (0, 0), 0,
     ((-27, 67), (-22, -2), (64, -2), (63, 15), (52, 56), (24, 70)),
     None),      # the base servo sits inside its holder, so nothing shows
    ("shoulder", "base", "shoulder_pan", (39, 62), 0,
     ((50, 38), (16, 38), (-12, 9), (-12, -36), (-11, -46), (35, -46),
      (47, -35)),
     ((21, 64), (18, 61), (18, 20), (42, 19), (43, 61), (40, 64))),
    ("upper", "shoulder", "shoulder_lift", (69, 117), -1,
     ((11, 130), (-12, 129), (-12, -2), (-1, -12), (12, -2)),
     ((-7, 124), (-6, 100), (35, 100), (38, 103), (38, 122), (35, 125))),
    ("fore", "upper", "elbow_flex", (97, 229), -1,
     ((119, 22), (92, 22), (91, 12), (-2, 12), (-12, -3), (-1, -12), (118, -15)),
     ((100, 16), (101, -7), (142, -7), (145, -4), (145, 15), (142, 18))),
    ("wrist", "fore", "wrist_flex", (232, 234), -1,
     ((66, 15), (39, 20), (38, 15), (24, 12), (-3, 12), (-10, 6), (-12, -3),
      (-2, -12), (61, -15)),
     ((23, 9), (23, -9), (26, -9), (26, -12), (58, -12), (58, -7), (61, -10),
      (63, 2), (61, 10), (58, 7), (58, 12), (26, 12), (26, 9))),
    ("grip", "wrist", "wrist_roll", (293, 234), 0,
     ((-1, 12), (7, -36), (43, -36), (105, -11), (37, -14), (37, 3), (11, 16),
      (9, 31), (5, 12)),
     ((14, 31), (11, 28), (11, -14), (35, -16), (36, 28), (33, 31))),
    ("jaw", "grip", "gripper", (317, 255), 1,
     ((-10, 2), (-9, -7), (-2, -12), (62, -10), (82, -12), (80, -7), (59, 3),
      (-1, 10)),
     None),
)

# Degrees, from the URDF's <limit> blocks. Every pose runs through these.
LIMITS = {"shoulder_pan": (-110, 110), "shoulder_lift": (-100, 100),
          "elbow_flex": (-97, 97), "wrist_flex": (-95, 95),
          "wrist_roll": (-157, 163), "gripper": (-10, 100)}

# Also measured, not chosen: the upper arm leaves the shoulder at 76.03°
# and the forearm leaves the elbow at 2.21° in the zero pose, so a joint
# angle of 0 has to mean exactly those directions.
L1, L2 = 116.0, 135.0                   # shoulder->elbow, elbow->wrist
UPPER_REST, FORE_REST = 76.03, 2.21
SHOULDER = (69, 117)                    # where the arm's own pivot sits
DOWN = -90.0            # wrist angle at which the jaws hang straight down

MM = 4                  # millimetres per drawn pixel

# ── The grip ──────────────────────────────────────────────────────────────
# The jaws do not close parallel: one finger is fixed to the gripper body,
# the other swings, so the opening is a wedge -- narrow at its root, wide at
# the tips. That one fact decides everything below.
#
# TREAT is how wide a treat may be, and it is a ceiling, not a taste: a
# 64 mm treat (what the demo used to draw) does not fit between these two
# fingers at ANY jaw angle. Open far enough for its middle and the wedge's
# root has already cut through its shoulders; the old picture solved that
# by drawing the arm on top, which is exactly the clipping this replaces.
#
# SHUT and TCP are the answer to one question asked of the drawn pixels, not
# of the geometry: which jaw angle and which hold point put a treat between
# the fingers, close enough to touch both, without sharing a pixel with
# either? Searched once over the rendered masks. scenes.py's self-test asks
# it again every run, so a new treat sprite or a different scale fails there
# instead of quietly going back to clipping.
TREAT = 16 * 5 * MM / 6         # 53.3 mm -- a 16 px sprite at scale 5
SHUT, OPEN = 30, 45             # jaw angle carrying a treat, and empty
TCP = (169.0, 21.0)             # the treat's centre in the wrist's frame
# A treat standing on something has its centre half its height up, and the
# tray's floor sits this far above the counter.
REST, TRAY, LIFT = TREAT / 2, 18.0, 55.0
JOINTS = ("shoulder_lift", "elbow_flex", "wrist_flex", "gripper")


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def solve(x, y, shut=True):
    """Joint angles (degrees) that hold a treat at (x, y) mm, jaws down.

    Two-link inverse kinematics, elbow up. The wrist is not free: it is
    whatever keeps the gripper pointing straight down, which is the whole
    reason the picture reads as picking a treat off a table.
    """
    # Wrist first: with the gripper vertical the treat sits at a fixed
    # offset from it, so the wrist position follows from the target without
    # any search. TCP is not straight down -- the wedge holds a treat off to
    # the fixed finger's side -- hence the two different components.
    wx, wy = x - TCP[1], y + TCP[0]
    dx, dy = wx - SHOULDER[0], wy - SHOULDER[1]
    d = clamp(math.hypot(dx, dy), abs(L1 - L2) + 1, L1 + L2 - 1)
    a = math.degrees(math.atan2(dy, dx))
    beta = math.degrees(math.acos((d * d + L1 * L1 - L2 * L2) / (2 * L1 * d)))
    upper = a + beta                                   # elbow up
    ex = SHOULDER[0] + L1 * math.cos(math.radians(upper))
    ey = SHOULDER[1] + L1 * math.sin(math.radians(upper))
    fore = math.degrees(math.atan2(wy - ey, wx - ex))
    # Frame rotations, then back to joint angles through `spin` (all -1 on
    # this side of the arm, hence the minus signs).
    phi_u, phi_f = upper - UPPER_REST, fore - FORE_REST
    return {"shoulder_lift": clamp(-phi_u, *LIMITS["shoulder_lift"]),
            "elbow_flex": clamp(-(phi_f - phi_u), *LIMITS["elbow_flex"]),
            "wrist_flex": clamp(-(DOWN - phi_f), *LIMITS["wrist_flex"]),
            "gripper": SHUT if shut else OPEN}


def frames(pose):
    """name -> (x, y, angle) in millimetres and radians. Forward kinematics.

    Six lines of it, because the table above already did the hard part: a
    link's polygon is stored world-oriented at the zero pose, so a link is
    placed by rotating it about its own pivot and carrying that pivot along
    on the parent's rotation. No matrices, no frame conventions to get
    backwards.
    """
    out = {None: (0.0, 0.0, 0.0)}
    pivots = {None: (0, 0)}
    for name, parent, joint, pivot, spin, _, _ in LINKS:
        ppx, ppy, pa = out[parent]
        c, s = math.cos(pa), math.sin(pa)
        ox, oy = pivot[0] - pivots[parent][0], pivot[1] - pivots[parent][1]
        out[name] = (ppx + c * ox - s * oy, ppy + s * ox + c * oy,
                     pa + math.radians(spin * pose.get(joint, 0.0)))
        pivots[name] = pivot
    return out


def place(pose):
    """name -> (printed polygon, servo polygon) in millimetres."""
    at = frames(pose)
    out = {}
    for name, _, _, _, _, body, servo in LINKS:
        px, py, a = at[name]
        c, s = math.cos(a), math.sin(a)
        out[name] = tuple(None if p is None else
                          [(px + c * qx - s * qy, py + s * qx + c * qy)
                           for qx, qy in p]
                          for p in (body, servo))
    return out


def hold(pose):
    """Where a treat sits between the jaws, in millimetres.

    The scene does not place the treat -- it asks the arm. That is the
    whole point of doing the kinematics: the treat cannot drift out of the
    gripper, because there is no second copy of the gripper's position to
    drift from.
    """
    x, y, a = frames(pose)["wrist"]
    c, s = math.cos(a), math.sin(a)
    return x + c * TCP[0] - s * TCP[1], y + s * TCP[0] + c * TCP[1]


# The drawing box, in millimetres around the base pivot. Fixed, not fitted
# per pose: the surface has to land in the same place every frame, otherwise
# the arm shivers as the silhouette grows and shrinks. The self-test below
# checks that every pose of the demo actually fits inside it.
BOX = (-36, -8, 372, 264)
W = (BOX[2] - BOX[0]) // MM + 2
H = (BOX[3] - BOX[1]) // MM + 2
ORIGIN = (1 - BOX[0] // MM, H - 2 + BOX[1] // MM)     # the base pivot, in pixels


@lru_cache(maxsize=64)
def surface(key, scale):
    """One pose, drawn small and scaled up whole -- same hard pixels as the
    sprites. `key` is the pose as a tuple of whole degrees, which is also
    what keeps the cache small: a loop of two dozen poses builds two dozen
    surfaces on the first pass and none after. 13 ms for the whole loop on
    the Mac, 0.15 ms a frame once it is warm.

    ponytail: the scaled surfaces are kept, about 25 MB for the loop. Cache
    the small ones and scale on each blit if that ever matters -- it is a
    thousandth of the size and costs a scale per frame.
    """
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    ink, bone, steel = BASE["k"], ARM[0], ARM[1]
    px = lambda poly: [(ORIGIN[0] + round(qx / MM), ORIGIN[1] - round(qy / MM))
                       for qx, qy in poly]
    for body, servo in place(dict(zip(JOINTS, key))).values():
        parts = [px(p) for p in (body, servo) if p]
        # One pixel of ink around each link, by stamping its silhouette nine
        # times. A border drawn inside would eat a link that is four pixels
        # wide, and drawing it per link instead of once around the whole arm
        # keeps the seams between the links visible.
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for p in parts:
                    pygame.draw.polygon(s, ink, [(x + dx, y + dy) for x, y in p])
        pygame.draw.polygon(s, bone, px(body))
        if servo:
            pygame.draw.polygon(s, steel, px(servo))
    return pygame.transform.scale(s, (W * scale, H * scale))


def to_screen(base, scale, p):
    """Arm millimetres -> screen pixels, for a base pivot at `base`."""
    return (round(base[0] + p[0] * scale / MM), round(base[1] - p[1] * scale / MM))


def draw(screen, base, scale, pose):
    screen.blit(surface(tuple(round(pose[k]) for k in JOINTS), scale),
                (base[0] - ORIGIN[0] * scale, base[1] - ORIGIN[1] * scale))


# ── The pick-and-place loop ───────────────────────────────────────────────
# Where the treat is, in millimetres, and whether the jaws are shut. The
# points are not free: two-link arms can only reach so far, and the wrist
# runs out of travel before the shoulder does, so the band in which this
# arm can hold something with the jaws truly vertical is roughly x 90..310,
# y 0..120. Every key below sits inside it -- reach past it and `solve`
# clamps to the servo limits instead, which looks exactly like what it is,
# a robot straining at a shelf it cannot get to. The heights are not free
# either: a treat lies on the counter or in the tray, so the arm has to aim
# at wherever its middle ends up when it does.
KEYS = ((185, LIFT, 0), (185, REST, 0), (185, REST, 1), (185, LIFT, 1),
        (290, LIFT, 1), (290, REST + TRAY, 1), (290, REST + TRAY, 0),
        (290, LIFT, 0))
CARRY = (2, 3, 4)       # segments during which the treat rides in the jaws
STEPS = 3               # poses per segment
HZ = 6                  # pose changes per second -- 4 s for the full loop


@lru_cache(maxsize=1)
def loop():
    """The whole cycle as [(pose, treat position)], built once.

    Interpolated between the keys in JOINT space, not in picture space.
    That one word is most of what makes it read as an arm: joints turning
    at a steady rate sweep the gripper along arcs, and the straight lines
    that picture-space tweening would give are exactly what no arm does.
    """
    out = []
    # Off the jaws the treat lies still, on the table before the pick and on
    # the tray after the drop. Those two spots are the keys where the jaws
    # close and open, so the treat never jumps at the handover.
    pick, drop = KEYS[1][:2], KEYS[5][:2]
    for i, key in enumerate(KEYS):
        a, b = solve(*key), solve(*KEYS[(i + 1) % len(KEYS)])
        for s in range(STEPS):
            f = s / STEPS
            # Whole degrees, because that is what surface() draws. Asking
            # hold() for the pose that actually reaches the screen is the
            # difference between the jaws holding the treat and holding it
            # to within a rounding error, which at four millimetres a pixel
            # is the treat's own edge.
            pose = {j: float(round(a[j] + (b[j] - a[j]) * f)) for j in JOINTS}
            out.append((pose, hold(pose) if i in CARRY
                        else drop if i > max(CARRY) else pick))
    return out


def cycle(t):
    """Pose and treat position at time t. Discrete steps, like hop(): a
    tweened arm next to 8-bit sprites reads as a different game."""
    steps = loop()
    return steps[int(t * HZ) % len(steps)]


if __name__ == "__main__":
    # uv run game/arm.py [sheet.png]   -> ok, optional sheet of the poses
    import os
    import sys
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()

    # The chain has to be a chain: every parent named has to exist already.
    seen = {None}
    for name, parent, joint, *_ in LINKS:
        assert parent in seen, (name, parent)
        assert joint is None or joint in LIMITS, (name, joint)
        seen.add(name)

    # solve() has to be the inverse of hold(): aim at a point, run the
    # kinematics forward, land back on it. Without this check the arm still
    # looks like an arm and quietly holds the treat beside the gripper.
    for key in KEYS:
        p = solve(*key)
        got = hold(p)
        assert math.dist(got, key[:2]) < 1.0, (key, got)
        for k, (lo, hi) in LIMITS.items():
            assert lo < p.get(k, 0) < hi, f"{key}: {k} at its limit ({p[k]:.1f})"

    # Out of reach must fall short, not raise and not flip the elbow over.
    for x, y in ((900, 40), (0, 0), (-200, 300)):
        assert all(LIMITS[k][0] <= v <= LIMITS[k][1]
                   for k, v in solve(x, y).items()), (x, y)

    # Every pose of the loop inside BOX, or the arm gets its fingertips
    # clipped off in the one frame nobody looked at.
    for pose, treat in loop():
        for body, servo in place(pose).values():
            for p in (body, servo):
                for qx, qy in p or ():
                    assert BOX[0] <= qx <= BOX[2] and BOX[1] <= qy <= BOX[3], \
                        (round(qx), round(qy), BOX)
        assert BOX[0] < treat[0] < BOX[2] and BOX[1] < treat[1] < BOX[3], treat

    # Inside one run of the loop the treat never jumps: from step to step it
    # moves less than its own width, carried or lying still. The one jump
    # that is allowed is the restart, where the treat is back on the table
    # and the tray is empty again -- and that one lands under the open
    # gripper, so it reads as the next treat arriving.
    xs = [t for _, t in loop()]
    for a, b in zip(xs, xs[1:]):
        assert math.dist(a, b) < 60, (a, b)

    if len(sys.argv) > 1:
        from config import BG
        steps = loop()
        sheet = pygame.Surface((W * 3 * len(steps), H * 3))
        sheet.fill(BG)
        for i, (pose, _) in enumerate(steps):
            draw(sheet, (i * W * 3 + ORIGIN[0] * 3, ORIGIN[1] * 3), 3, pose)
        pygame.image.save(sheet, sys.argv[1])
    print("ok")
