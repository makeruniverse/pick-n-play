"""Teleop with geofencing: read leader -> clamp every joint -> write follower.

Replaces the plain `lerobot-teleoperate`. LeRobot's `max_relative_target`
limits the step size, not the position -- so every joint gets clamped into
a band here. At the edge only that joint stops, the others keep following:
the arm stays playable instead of looking broken.

Runs in the conda env `lerobot` (Python 3.10), not in the game's .venv:

  python teleop/run.py          teleop loop (teleop.service)
  python teleop/run.py --show   the same loop, plus live min/max per joint
                                and a LIMITS block on Ctrl-C (pnp-arm-help)
  python teleop/run.py --test   self-test, no hardware
"""
import os
import socket
import sys
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


def clamp(action):
    """{"elbow_flex.pos": v, ...} -> same dict, every known joint inside its band."""
    out = {}
    for k, v in action.items():
        lo, hi = LIMITS.get(k.split(".")[0], (v, v))   # unknown key: passes as is
        out[k] = min(hi, max(lo, v))
    return out


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


def main(watch=False):
    """Teleop loop. `watch` additionally tracks min/max per joint.

    Watching drives the follower like any other run -- limits are dialed in
    by watching where the arm actually gets close to the table, not by
    reading numbers with a dead follower. Recorded are the *leader's* raw
    values, before the clamp, because that's what belongs in LIMITS. A band
    that's already in LIMITS stays in effect meanwhile: the printed value
    keeps rising while the follower has long since stopped.
    """
    from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
    lead = leader()
    follow = SO101Follower(SO101FollowerConfig(port=FOLLOWER, id="my_follower_arm"))
    follow.connect()
    notify("READY=1")
    seen, n = {}, 0
    try:
        while True:
            t = time.perf_counter()
            action = lead.get_action()
            follow.send_action(clamp(action))
            # A hung serial bus stops this line -> systemd's watchdog restarts us.
            notify("WATCHDOG=1")
            if watch:
                for k, v in action.items():
                    j = k.split(".")[0]
                    lo, hi = seen.get(j, (v, v))
                    seen[j] = (min(lo, v), max(hi, v))
                n += 1
                if n % 6 == 0:     # 10 lines a second, nobody reads 60
                    print("  ".join(f"{j} {lo:6.1f}..{hi:6.1f}"
                                    for j, (lo, hi) in seen.items()),
                          end="\r", flush=True)
            time.sleep(max(0.0, 1 / FPS - (time.perf_counter() - t)))
    except KeyboardInterrupt:
        print("\nLIMITS = {")
        for j, (lo, hi) in seen.items():
            print(f'    "{j}": ({lo:.0f}, {hi:.0f}),')
        print("}")
    finally:
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
        print("ok")
    else:
        main(watch="--show" in sys.argv)
