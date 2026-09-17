"""Pings both servo buses and reports which motors respond.

Runs on the Pi in the teleop's conda env, not under uv:
    ~/miniforge3/envs/lerobot/bin/python tools/scan_motors.py

Teleop must be stopped for this, otherwise the ports are taken.
A healthy SO-101 reports six motors, IDs 1-6, model 777 (STS3215).
If a bus stays silent entirely even though the adapter is there, it's almost
always missing servo power -- the USB adapter is connected to the Pi, the
motors aren't.
"""

from scservo_sdk import PacketHandler, PortHandler

PORTS = ("/dev/ttyACM0", "/dev/ttyACM1")
BAUD = 1_000_000

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
