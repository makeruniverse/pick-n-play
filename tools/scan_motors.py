"""Pings both servo buses and reports which motors respond.

Run this on the Pi in Teleop's conda environment, not via uv:
~/miniforge3/envs/lerobot/bin/python tools/scan_motors.py

Teleop must be stopped first, otherwise the ports are occupied.
A healthy SO-101 reports six motors, IDs 1-6, model 777 (STS3215).
If a bus is completely silent while the adapter exists, the servo power
supply is usually missing: the USB adapter is powered by the Pi, but the
motors are not.
"""

from scservo_sdk import PacketHandler, PortHandler

PORTS = ("/dev/ttyACM0", "/dev/ttyACM1")
BAUD = 1_000_000

for port in PORTS:
    ph = PortHandler(port)
    if not (ph.openPort() and ph.setBaudRate(BAUD)):
        print(f"{port} -> Port laesst sich nicht oeffnen (Adapter ab? Teleop laeuft noch?)")
        continue
    pk = PacketHandler(0)
    found = []
    for motor_id in range(1, 10):
        model, result, _ = pk.ping(ph, motor_id)
        if result == 0:
            found.append(f"{motor_id}(m{model})")
    ph.closePort()
    print(f"{port} -> {', '.join(found) if found else 'KEINE Motoren'}")
