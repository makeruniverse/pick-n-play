"""Pingt beide Servo-Busse durch und sagt, welche Motoren antworten.

Laeuft auf dem Pi im conda-Env der Teleop, nicht unter uv:
    ~/miniforge3/envs/lerobot/bin/python tools/scan_motors.py

Teleop muss dafuer gestoppt sein, sonst sind die Ports belegt.
Ein gesunder SO-101 meldet sechs Motoren, IDs 1-6, Modell 777 (STS3215).
Schweigt ein Bus komplett, obwohl der Adapter da ist, fehlt fast immer die
Servo-Stromversorgung -- der USB-Adapter haengt am Pi, die Motoren nicht.
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
