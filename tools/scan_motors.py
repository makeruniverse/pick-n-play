"""Pings both servo buses and reports which motors respond.

Runs on the Pi in the teleop's conda env, not under uv:
    ~/miniforge3/envs/lerobot/bin/python tools/scan_motors.py
    ~/miniforge3/envs/lerobot/bin/python tools/scan_motors.py --watch [s]

Teleop must be stopped for this, otherwise the ports are taken.
A healthy SO-101 reports six motors, IDs 1-6, model 777 (STS3215).
If a bus stays silent entirely even though the adapter is there, it's almost
always missing servo power -- the USB adapter is connected to the Pi, the
motors aren't.

--watch (pnp-arm-bus): voltage of every motor on both buses, live, a line
marked DROP the moment one goes missing. Move the leader and wiggle cables
and plugs meanwhile -- the whole bus dropping means power or bus cable,
single shifting IDs mean undervoltage (docs/operation.md).
"""

import sys
import time

from scservo_sdk import PacketHandler, PortHandler

PORTS = ("/dev/ttyACM0", "/dev/ttyACM1")
BAUD = 1_000_000
S = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_"
BUSES = {"follower": S + "5970073917-if00", "leader": S + "5970072402-if00"}


def watch(secs):
    pk = PacketHandler(0)
    ports = {}
    for name, dev in BUSES.items():
        ports[name] = ph = PortHandler(dev)
        if not (ph.openPort() and ph.setBaudRate(BAUD)):
            print(f"{name} -> port won't open (adapter unplugged? teleop still running?)")
    last, shown, end = None, 0.0, time.time() + secs
    while time.time() < end:
        # Present_Voltage, address 62, in 0.1 V. "!" = the servo reports an error.
        row = {n: [pk.read1ByteTxRx(ph, i, 62) for i in range(1, 7)] for n, ph in ports.items()}
        missing = {n: [i for i, (_, res, _) in enumerate(r, 1) if res != 0] for n, r in row.items()}
        # A line on every change of who's missing, else once a second.
        if missing != last or time.time() - shown > 1:
            print(time.strftime("%H:%M:%S"), "   ".join(
                f"{n[:4]} " + " ".join(f"{v / 10:4.1f}{'!' if err else ' '}" if res == 0 else "  -- "
                                        for v, res, err in r)
                for n, r in row.items()), " DROP" if any(missing.values()) else "", flush=True)
            last, shown = missing, time.time()
        time.sleep(0.1)


if "--watch" in sys.argv:
    try:
        watch(float(sys.argv[-1]) if sys.argv[-1] != "--watch" else 60)
    except KeyboardInterrupt:   # Ctrl-C ends it cleanly, so pnp-arm-bus restarts teleop
        pass
else:
    for port in PORTS:
        ph = PortHandler(port)
        if not (ph.openPort() and ph.setBaudRate(BAUD)):
            print(f"{port} -> port won't open (adapter unplugged? teleop still running?)")
            continue
        pk = PacketHandler(0)
        found = []
        for motor_id in range(1, 10):
            model, result, _ = pk.ping(ph, motor_id)
            if result == 0:
                found.append(f"{motor_id}(m{model})")
        ph.closePort()
        print(f"{port} -> {', '.join(found) if found else 'NO motors'}")
