"""Teleop: read leader -> write follower, servo overload guard on every start.

Replaces the plain `lerobot-teleoperate`. The geofence sits behind --fence
and is only on in pnp-arm-test / pnp-arm-limits while it's being tested, the
service runs with the overload guard alone. LeRobot's `max_relative_target`
limits the step size, not the position, so the fence does it here:
  - every joint clamped into its band from LIMITS. At the edge only that
    joint stops, the others keep following: the arm stays playable
  - FLOOR, the table as a plane: shoulder_lift gets raised just enough that
    the gripper slides over the table instead of pressing into it
  - RAMP: after a start the follower glides to the leader instead of jumping

Runs in the conda env `lerobot` (Python 3.10), not in the game's .venv:

  python teleop/run.py                 teleop loop (teleop.service)
  python teleop/run.py --fence         the same, geofenced (pnp-arm-test)
  python teleop/run.py --show --fence  plus live min/max per joint, Enter
                                       marks a table point, Ctrl-C prints
                                       LIMITS and FLOOR (pnp-arm-help)
  python teleop/run.py --test          self-test, no hardware
"""
import os
import shutil
import socket
import sys
import threading
import time

FPS      = 60     # same as lerobot-teleoperate
FOLLOWER = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5970073917-if00"
LEADER   = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5970072402-if00"

# Calibrated LeRobot units: body joints -100..100, gripper 0..100.
# Full range until dialed in on the machine with --show -- not guessed.
LIMITS = {
    "shoulder_pan":  (-100, 100),
    "shoulder_lift": (-100, 100),
    "elbow_flex":    (-100, 100),
    "wrist_flex":    (-100, 100),
    "wrist_roll":    (-100, 100),
    "gripper":       (0, 100),
}
SHORT = {"shoulder_pan": "pan", "shoulder_lift": "lift", "elbow_flex": "elbow",
         "wrist_flex": "wrist", "wrist_roll": "roll", "gripper": "grip"}   # --show line

# The table, measured with --show: where shoulder_lift = a*elbow_flex +
# b*wrist_flex + c the gripper touches it, `side` (+1/-1) is the side lift
# has to stay on. None until measured.
# ponytail: a plane in joint space = linearized kinematics. Good near the
# measured points, off far away from them -- real FK with link lengths and
# use_degrees if the edge shows up in the wrong place.
FLOOR = None

RAMP = 1.0   # s, after a start the follower glides from where it stands


# Servo firmware overload guard: above Overload_Torque (80 %) for longer
# than Protection_Time, the servo drops to Protective_Torque (20 %). Factory
# time is 2 s -- long enough to grind into the table. Normal play peaks at
# 77 % only for short bursts (21.9.), pressing into the table holds 100 %.
# Gripper keeps LeRobot's own settings, wrist_roll is left alone for now.
GUARD      = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex")
GUARD_TIME = 50   # x 10 ms = 0.5 s


def guard(follow):
    """Written on every start, so a swapped servo gets it too (EEPROM)."""
    with follow.bus.torque_disabled():
        for m in GUARD:
            follow.bus.write("Protection_Time", m, GUARD_TIME)


def clamp(action):
    """{"elbow_flex.pos": v, ...} -> same dict, every known joint inside its band."""
    out = {}
    for k, v in action.items():
        lo, hi = LIMITS.get(k.split(".")[0], (v, v))   # unknown key: passes as is
        out[k] = min(hi, max(lo, v))
    return out


def fence(action):
    """Bands, then the table plane on the clamped pose (that's where the
    follower goes), then bands again: the band is the hard limit."""
    out = clamp(action)
    if FLOOR:
        a, b, c, side = FLOOR
        edge = a * out["elbow_flex.pos"] + b * out["wrist_flex.pos"] + c
        if side * (out["shoulder_lift.pos"] - edge) < 0:
            out["shoulder_lift.pos"] = edge
    return clamp(out)


def floor(marks, trail):
    """Table points [(lift, elbow, wrist), ...] -> FLOOR, least squares.
    The safe side is where the arm spent most of the session, it only
    touches the table for the marks.
    ponytail: majority vote, wrong only if most of the session was spent
    below the table plane -- which the table doesn't allow."""
    import numpy as np
    m = np.array(marks, float)
    a, b, c = np.linalg.lstsq(np.c_[m[:, 1:], np.ones(len(m))], m[:, 0], rcond=None)[0]
    t = np.array(trail, float)
    side = 1 if 2 * np.sum(t[:, 0] > a * t[:, 1] + b * t[:, 2] + c) > len(t) else -1
    return float(a), float(b), float(c), side


def notify(msg):
    """sd_notify without the dependency. No-op outside systemd.
    ponytail: same 6 lines as game/hw.py -- two envs, no shared package."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.connect("\0" + addr[1:] if addr[0] == "@" else addr)
        s.sendall(msg.encode())


def leader():
    from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
    arm = SO101Leader(SO101LeaderConfig(port=LEADER, id="my_leader_arm"))
    arm.connect()
    return arm


def main(watch=False, fenced=False):
    """Teleop loop. `fenced` switches the geofence on, `watch` additionally
    tracks min/max per joint and takes a table point on every Enter.

    Watching drives the follower like any other run -- limits are dialed in
    by watching where the arm actually gets close to the table, not by
    reading numbers with a dead follower. Recorded are the *leader's* raw
    values, before the fence, because that's what belongs in LIMITS and
    FLOOR. A band that's already in LIMITS stays in effect meanwhile: the
    printed value keeps rising while the follower has long since stopped.
    """
    from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
    lead = leader()
    follow = SO101Follower(SO101FollowerConfig(port=FOLLOWER, id="my_follower_arm"))
    follow.connect()
    guard(follow)
    start = ({k: v for k, v in follow.get_observation().items() if k.endswith(".pos")}
             if fenced else {})
    notify("READY=1")
    seen, n, marks, trail, pose = {}, 0, [], [], None
    t0 = time.perf_counter()

    def mark():    # Enter in the terminal: the leader's pose is a table point
        for _ in sys.stdin:
            if pose:
                marks.append(pose)
                print(f"\n  table point {len(marks)}: lift/elbow/wrist "
                      + " ".join(f"{v:.1f}" for v in pose))
    if watch:
        threading.Thread(target=mark, daemon=True).start()
    try:
        while True:
            t = time.perf_counter()
            action = lead.get_action()
            target = fence(action) if fenced else action
            k = (t - t0) / RAMP
            if fenced and k < 1:
                target = {j: start.get(j, v) + k * (v - start.get(j, v))
                          for j, v in target.items()}
            follow.send_action(target)
            # A hung serial bus stops this line -> systemd's watchdog restarts us.
            notify("WATCHDOG=1")
            if watch:
                for key, v in action.items():
                    j = key.split(".")[0]
                    lo, hi = seen.get(j, (v, v))
                    seen[j] = (min(lo, v), max(hi, v))
                pose = tuple(action[f"{j}.pos"]
                             for j in ("shoulder_lift", "elbow_flex", "wrist_flex"))
                trail.append(pose)   # ponytail: ~40k tuples per 10 min, fine
                n += 1
                if n % 6 == 0:     # 10 lines a second, nobody reads 60
                    # One line that fits: a wrapped line breaks the \r, and
                    # the terminal fills with copies (28.9.).
                    line = "  ".join(f"{SHORT.get(j, j)} {lo:.0f}..{hi:.0f}"
                                     for j, (lo, hi) in seen.items())
                    cols = shutil.get_terminal_size().columns
                    print(line[:cols - 1].ljust(cols - 1), end="\r", flush=True)
            time.sleep(max(0.0, 1 / FPS - (time.perf_counter() - t)))
    except KeyboardInterrupt:
        pass
    finally:
        # Also when the bus dies mid-run: what was measured so far is printed.
        if watch:
            print("\nLIMITS = {")
            for j, (lo, hi) in seen.items():
                print(f'    "{j}": ({lo:.0f}, {hi:.0f}),')
            print("}")
            if len(marks) >= 3:
                a, b, c, side = floor(marks, trail)
                print(f"FLOOR = ({a:.3f}, {b:.3f}, {c:.1f}, {side})")
            else:
                print(f"# no FLOOR: needs 3+ table points, got {len(marks)}")
        lead.disconnect()
        follow.disconnect()


if __name__ == "__main__":
    if "--test" in sys.argv:
        a = clamp({"shoulder_pan.pos": -150.0, "gripper.pos": 50.0, "x.pos": 999})
        assert a == {"shoulder_pan.pos": -100, "gripper.pos": 50.0, "x.pos": 999}, a
        LIMITS["elbow_flex"] = (-20, 30)
        assert clamp({"elbow_flex.pos": 31})["elbow_flex.pos"] == 30
        assert clamp({"elbow_flex.pos": -21})["elbow_flex.pos"] == -20
        assert clamp({"elbow_flex.pos": 0})["elbow_flex.pos"] == 0
        # table at lift = 0.5*elbow - 0.2*wrist + 10, the arm mostly above it
        pts = [(0.5 * e - 0.2 * w + 10, e, w) for e, w in [(0, 0), (20, 5), (-10, 30), (5, -20)]]
        a, b, c, side = floor(pts, [(90, 0, 0)] * 9 + [(-90, 0, 0)])
        assert (round(a, 3), round(b, 3), round(c, 3), side) == (0.5, -0.2, 10, 1)
        assert floor(pts, [(-90, 0, 0)] * 9 + [(90, 0, 0)])[3] == -1
        FLOOR = (0.5, -0.2, 10, 1)
        pose = {"shoulder_lift.pos": 0, "elbow_flex.pos": 20, "wrist_flex.pos": 0}
        assert fence(pose)["shoulder_lift.pos"] == 20                 # raised onto the plane
        assert fence({**pose, "shoulder_lift.pos": 50})["shoulder_lift.pos"] == 50   # above: untouched
        f = fence({**pose, "elbow_flex.pos": 90})
        assert f["elbow_flex.pos"] == 30 and f["shoulder_lift.pos"] == 25, f  # plane on the clamped elbow
        print("ok")
    else:
        main(watch="--show" in sys.argv, fenced="--fence" in sys.argv)
