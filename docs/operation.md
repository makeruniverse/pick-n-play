# Operation

How to start the machine, check it, and keep it running. As of: 2026-09-09.

## What runs on the Pi

Two processes that know nothing about each other. **Teleop** reads the leader
arm and writes the joint angles to the follower, 60 Hz, as a systemd service
running continuously. **The game** reads the top-down camera, detects ArUco
markers, and renders. It never queries the arm state.

The two use separate Python environments and never touch each other:

| | Environment | Version |
|---|---|---|
| Teleop | conda, `~/miniforge3/envs/lerobot` | Python 3.10, LeRobot 0.4.2 |
| Game | uv, project `.venv` | Python 3.13, pygame-ce, OpenCV |

Hardware: Raspberry Pi 5 (8 GB) with Ubuntu 24.04, two SO-101 arms via CH343
adapters, two USB cameras, display on HDMI-A-1.

> The game has been installed on the Pi and starts since 2026-09-09. It is,
> however, **not accepted**: it doesn't reach the target frame rate and drives
> the Pi into throttling together with Teleop. See "Acceptance status".

## Getting in

```sh
ssh picknplay
```

The entry lives in `~/.ssh/config` and points to `ubuntu@172.22.1.2`. The Pi
is on the makerspace network over WiFi, `eth0` is dead. The IP comes via
DHCP, so it can change. If nothing works: ping it. If it answers a ping but
port 22 is closed, `sshd` isn't running, and you'll have to go to the
keyboard on the device.

## Starting and stopping Teleop

```sh
sudo systemctl start teleop.service
sudo systemctl stop  teleop.service
sudo systemctl restart teleop.service
```

The service is `enabled`, so it starts on its own at boot.

## Is it running?

```sh
systemctl is-active teleop.service
systemctl show teleop.service -p NRestarts -p SubState
vcgencmd measure_temp
vcgencmd get_throttled
```

Healthy looks like this: `active`, `SubState=running`, **`NRestarts=0`**,
around 55 to 65°C, `throttled=0x0`.

`NRestarts` is the number that matters most. If it climbs, the service is
crashing and restarting, and that's always a hardware problem: an arm without
power, a cable unplugged, an adapter not detected. Software bugs look
different.

In normal operation Teleop writes **nothing** to the journal. That's
intentional (see "Why the journal is quiet"). Silence means: it's running.
Errors still end up in the log:

```sh
journalctl -u teleop.service -b --no-pager | tail -30
```

### Reading `get_throttled`

The number is a bitmask. Four bits matter:

| Value | Meaning |
|---|---|
| `0x0` | everything fine |
| `0x1` | undervoltage **right now**, i.e. power supply or cable |
| `0x8` | temperature limit **right now**, it's throttling |
| `0x80000` | temperature limit has occurred at some point since boot |

`0x80008` accordingly means: throttling right now, and has done so before.
That starts at around 80°C.

## Checking motors

If Teleop crashes, the first question is: do the servos respond at all?
`tools/scan_motors.py` answers that. Teleop has to be stopped for this,
otherwise the ports are busy.

```sh
sudo systemctl stop teleop.service
~/miniforge3/envs/lerobot/bin/python ~/scan_motors.py
sudo systemctl start teleop.service
```

The script lives in the repo under `tools/scan_motors.py`, and as a copy
directly in `~` on the Pi, so it's on hand even without a checked-out repo.

Healthy:

```
/dev/ttyACM0 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
/dev/ttyACM1 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
```

Six motors per arm, IDs 1 to 6, model 777 (STS3215). Anything else is a
finding:

A port reports **no motors**, even though it shows up in the scan. Then the
servo power supply is missing, or the three-wire bus cable isn't plugged in.
The USB adapter draws its power from the Pi and shows up even without a servo
power supply, but the bus itself stays silent. Leader runs on 7.4 V, follower
on 12 V.

**Individual** motors are missing in the middle of the chain, say 2 and 4,
while 3, 5, and 6 respond. Then it's not the connecting cables but the servos
themselves: connector loose, or ID changed.

A port **doesn't show up at all**. Then a USB adapter has come loose, and
that's the dangerous case, see the next section.

### The case that looks like a servo fault and isn't

On 2026-09-09, motors dropped out over the course of hours, and they
alternated: first 2 and 4, then all six, then 4 and 6. The scan found all six
every time, but LeRobot failed anyway. The cause was the **power supply,
which was set to 5 V**.

Why this is so hard to spot: a ping draws almost no current, so under
undervoltage every motor dutifully answers in the scan. But as soon as
LeRobot enables torque, the two that draw the most drop out — on an SO-101
those are 4 (wrist flex) and 6 (gripper), because they work against gravity.
They fall off the bus, and the error message says "Missing motor IDs".

**Rule of thumb: shifting motor IDs mean voltage, fixed ones mean hardware.**
If the same motor always drops out, it's the motor or its connector. If it
changes, measure the voltage first. Follower 12 V, leader 7.4 V.

### The first start attempt sometimes fails

Even with the correct voltage, the first connection attempt occasionally
fails and the second one succeeds. That's why `Restart=on-failure` is set in
the override, and why `NRestarts=1` after a start is no cause for concern.
Only a climbing number is.

## Which adapter is which arm

```sh
ls -l /dev/serial/by-id/
```

```
usb-1a86_USB_Single_Serial_5970072402-if00 -> ttyACM0    Leader
usb-1a86_USB_Single_Serial_5970073917-if00 -> ttyACM1    Follower
```

`run_teleop.sh` passes `ttyACM0` as the leader and `ttyACM1` as the follower.
The kernel assigns these numbers in the order the devices show up. If an
adapter isn't plugged in, everything behind it shifts up by one number:
`ttyACM1` becomes `ttyACM0`, and Teleop talks to the follower as if it were
the leader.

That's exactly what happened on September 9. The error shows up as "Missing
motor IDs" and looks like broken servos, even though only a cable was
missing. So the first move on this error is always `ls -l
/dev/serial/by-id/`, not the motor scan.

The serial numbers are fixed and never shift. The clean fix is to enter them
in `run_teleop.sh` instead of the `ttyACM*` numbers. Still outstanding.

## Buttons on the panel

Four buttons, nothing else. Each has one leg on its GPIO, the other on
ground. The pull-up lives in the chip, no resistor and no capacitor go into
the cable — debouncing happens in software (`bounce_time` in `hw.Buttons`).

| Function | Color | GPIO (BCM) | Header pin |
|---|---|---|---|
| up    | blue   | 25 | 22 |
| right | green  | 8  | 24 |
| left  | red    | 7  | 26 |
| down  | yellow | 1  | 28 |
| ground |       |    | 30 |

One row, shared ground at 30. Wired this way as of 2026-09-11.

**Two pins with history:** GPIO 7 and 8 are the chip selects of SPI0. SPI0
therefore has to be **off** (`dtparam=spi=on` commented out), otherwise the
kernel claims the pins and gpiozero reports "GPIO busy". GPIO 1 is ID_SC of
the HAT EEPROM and is only read at boot — don't hold the yellow button down
while powering on.

**The emergency stop isn't on GPIO.** It sits in the 12 V supply to the
servos and cuts it. An emergency stop that has to go through Python first
isn't one.

Install the software for this on the Pi:

```sh
uv sync --extra pi
```

`gpiozero` and `lgpio` are listed under the `pi` extra in `pyproject.toml`,
not among the regular dependencies: `lgpio` builds against Linux headers and
won't install on the development machine. On the Mac, `PNP_BUTTONS` is
therefore 0 by default (`config.MAC`), and the import is never run there.

## LED strip

WS2812, data on **GPIO 14 (header 8)**. Power comes from its own power
supply (5 V, 18 A), whose ground is tied to Pi ground (header 6). The Pi is
on its own USB-C power supply, **not** on the LED power supply via header pin
4: powered that way, it kept rebooting on 2026-09-11.

`hw.Leds` writes to `/dev/spidev5.0`. The RP1 on the Pi 5 brings the MOSI of
SPI5 out on GPIO 14; the overlay also claims 12 (CS), 13, and 15. If the
device is missing, the game keeps running with silent LEDs and prints `LEDs
aus: …` at startup.

GPIO 14 is UART0 by default, with kernel console and login prompt. Those have
to go, otherwise boot messages show up as colors on the strip. One-time setup
on the Pi:

```sh
cd /boot/firmware
sudo cp config.txt config.txt.pnp-bak && sudo cp cmdline.txt cmdline.txt.pnp-bak
sudo sed -i 's/^dtparam=spi=on/#dtparam=spi=on/' config.txt   # SPI0 off, GPIO 7/8 free
echo "dtparam=uart0=off"         | sudo tee -a config.txt      # GPIO 14/15 free
# enable_uart=1 turns UART0 back on regardless -- then the serial driver
# grabs GPIO 14 first and spidev5.0 never appears (dmesg: "pin gpio14
# already requested by ...serial")
sudo sed -i 's/^enable_uart=1/enable_uart=0/' config.txt
echo "dtoverlay=spi5-1cs-pi5"    | sudo tee -a config.txt      # SPI5 MOSI on GPIO 14
sudo sed -i 's/console=serial0,115200 //' cmdline.txt
# spidev otherwise only takes 4096 bytes per write; 800 LEDs are 19,500.
# Append to the end of the ONE line in cmdline.txt, no new line:
sudo sed -i 's/$/ spidev.bufsiz=65536/' cmdline.txt
sudo systemctl mask serial-getty@ttyAMA0.service
sudo reboot
```

Check: `ls -l /dev/spidev5.0` (group `dialout`), no more `/dev/ttyAMA0`,
`cat /sys/module/spidev/parameters/bufsiz` → 65536.

First test on the strip, small and dim, without changing any file:

```sh
PNP_LED_COUNT=60 PNP_LED_BRIGHT=0.1 timeout -s KILL 20 .venv/bin/python -c "
import sys, time; sys.path.insert(0, 'game')
from hw import Leds
l = Leds()
for s in ('idle', 'game', 'hurry', 'score'):
    print(s); l.show(s, 0.5); time.sleep(4)
l.close()"
```

With the data line open, a few LEDs light up randomly at the start — that's
noise, not a defect. Colors wrong (red and green swapped)? `LED_ORDER` in
`config.py` — WS2812B is `GRB`, WS2811 strips (12/24 V) are often `RGB`. Only
part of it lights up? `LED_COUNT` or `PNP_LED_COUNT`.

Check whether a button registers, without starting the game:

```sh
timeout -s KILL 15 .venv/bin/python -c "
from gpiozero import Button
import time
b = {p: Button(p) for p in (25, 8, 7, 1)}
for _ in range(200):
    print({p: v.is_pressed for p, v in b.items()}, end='\r')
    time.sleep(0.05)"
```

All `False` at rest, exactly one `True` when pressed. If one stays `True`
permanently, the button is stuck to ground, or the pin is wired like a
normally-closed contact against 3.3 V — then the pull-up is the wrong way
around.

## Maintenance

Once a month, or when something looks off:

```sh
df -h /                    # keep under 85%
journalctl --disk-usage    # capped at 200 MB
vcgencmd measure_temp
systemctl show teleop.service -p NRestarts
```

If the disk does fill up, in this order:

```sh
sudo journalctl --rotate && sudo journalctl --vacuum-size=200M
sudo rm -f /var/log/syslog.1 /var/log/syslog.*.gz
rm -rf ~/.cache/pip ~/.cache/huggingface/hub ~/.cache/huggingface/xet
rm -rf ~/.vscode-server
```

**Don't** delete `~/.cache` entirely. The arm calibration lives in there:

```
~/.cache/huggingface/lerobot/calibration/robots/so101_follower/my_follower_arm.json
~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/my_leader_arm.json
```

Two files, under 2 KB together, dated March 31. If they're gone, calibration
has to happen again. A backup of them on the MacBook would be smart.

### Why the journal is quiet

Teleop used to print a line of loop time per loop iteration, so at 60 Hz
that's 60 lines a second. That was 99.7% of the entire journal, around 1 GB a
day, because journald and rsyslog were both writing out the same stream.
journald's built-in rate limit doesn't kick in at 60 lines per second — that's
below the threshold.

Two changes now keep that in check. `SystemMaxUse=200M` in
`/etc/systemd/journald.conf` caps the journal. And in
`/etc/systemd/system/teleop.service.d/override.conf`:

```ini
[Unit]
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Restart=on-failure
StandardOutput=null
```

`StandardOutput=null` swallows the debug print. The two `StartLimit` lines
are the heat protection: on a hardware fault, the service used to never stop
with `Restart=always` and would restart itself 153 times in 30 minutes, each
time fully loading torch again. The Pi hit 82°C and throttled. Now it stops
after five failed attempts within two minutes and reports that, instead of
heating up.

## When something doesn't work

| Symptom | First check | Usually the cause |
|---|---|---|
| `ssh` says Connection refused, ping works | go to the keyboard on the device, `df -h /` | disk full, `sshd` won't start |
| `ssh` says Timeout | `arp -n 172.22.1.2` | Pi is off, or has a new IP via DHCP |
| `NRestarts` is climbing | `journalctl -u teleop.service -b \| tail -30` | hardware, never software |
| "Missing motor IDs" | `ls -l /dev/serial/by-id/` | adapter disconnected, numbers shifted |
| One bus is completely silent | servo power supply and bus cable | power missing, not the servos |
| Individual motors go missing erratically, sometimes 2 and 4, sometimes 4 and 6 | **measure the voltage at the power supply** | undervoltage. See below |
| Over 80°C | `systemctl show teleop.service -p NRestarts` | crash loop is heating the Pi |
| Disk over 85% | `journalctl --disk-usage` | see "Maintenance" |
| `git` says "loose object is corrupt" | `git fsck` | Pi was hard-powered-off. See below |

### Broken git objects after a hard power-off

On 2026-09-10, six objects were broken, five of them **zero bytes long**.
That's the signature of a power cut: the file was created, but the content
never made it to the card. If `dmesg` shows no EXT4 or mmc messages, the card
is healthy and it was the power-off.

The working tree isn't affected, only the object database. Repair, as long
as everything is on origin:

```sh
git fsck --no-progress            # names the broken objects
mkdir -p /tmp/git-kaputt
mv .git/objects/XX/YYYY… /tmp/git-kaputt/    # for each broken object, don't delete
git fetch origin && git reset --hard origin/main
git fsck --no-progress            # should now be silent
```

Set aside rather than delete: if the fetch goes wrong, you still have them.
As a precaution, the Pi should be shut down rather than switched off — on the
trade-show day the whole machine runs off it.

## Starting the game

```sh
cd ~/picknplay
.venv/bin/python game/main.py
```

Runs over KMSDRM in full screen, with no desktop. **Note:** over SSH there's
no keyboard input in this — SDL reads from `/dev/input` under KMSDRM. Running
it requires a USB keyboard plugged into the Pi; press `q` to quit.

If you start it from an SSH session, always put a `timeout` in front of it.
Otherwise it keeps running if the session drops, and a fully loaded Pi won't
accept a new login anymore:

```sh
timeout -s KILL 30 .venv/bin/python game/main.py
```

### Shortcuts

`tools/pi_aliases.sh` wraps the commands in this document, each game start
with a timeout. Set up once on the Pi:

```sh
echo 'source ~/picknplay/tools/pi_aliases.sh' >> ~/.bash_aliases
```

`pnp-help` lists them: `pnp-start [s]`, `pnp-stop`, `pnp-log`,
`pnp-status`, `pnp-fps`, `pnp-fake`, `pnp-leds [brightness]`,
`pnp-leds-off`, `pnp-buttons`, `pnp-update`. The game runs detached
(`setsid`) and logs to `/tmp/pnp.log`; the switches below pass through,
e.g. `PNP_CRT=0 pnp-start 120`.

### Switches for measuring and developing

All via environment variable, the default is always the machine setup. You
don't need to touch the file for this, which matters because the next `git
pull` would wipe out local changes.

| Variable | Effect |
|---|---|
| `PNP_FULLSCREEN=0` | windowed instead of full screen |
| `PNP_CAMERA=0` | `FakeDetector`, no camera access |
| `PNP_FPSLOG=1` | frame rate and scene, once a second to stdout |
| `PNP_CRT=0` | CRT overlay fully off |
| `PNP_BARREL=0` | only the curvature off, scanlines stay |
| `PNP_IDLE_FPS=30` | idle screen at game-scene load, for measurements without a keyboard |
| `PNP_VSYNC=0` | without frame sync, costs tearing |
| `PNP_CV_THREADS=n` | OpenCV threads in the render path, default 3 (the fourth core belongs to Teleop) |
| `PNP_THEME=name` | theme from `game/themes/name.py`, default `sugar_rush` |

To find the ceiling instead of the target rate, set `PNP_IDLE_FPS=999
PNP_VSYNC=0` — otherwise you're measuring the frame clock, not the render
path.

## Acceptance status

Installed and checked: `uv`, Python 3.13, OpenCV 5.0, pygame-ce 2.5.8, all
four self-tests green, both cameras deliver a picture, KMSDRM starts
natively at 1920 × 1080, audio over HDMI present.

**The frame rate has been accepted since 2026-09-10.** Target is 30 fps,
measured 45 seconds straight at 29.4 to 30.3 — with full CRT, both cameras
**and Teleop running**, over which it went from 61.5 to 75.7°C. The reasoning
for 30 instead of 60, and the numbers behind it, are in the Overview under
"Measurement on the Pi".

Still open is **cooling**: without a fan the Pi goes over 80°C under load and
throttles, and throttling costs up to 35% of compute performance. Continuous
operation over six trade-show hours isn't accepted this way, even though the
frame rate is.

## Open

1. **Active cooling.** Without a fan, the Pi throttles under double load.
   First priority — it blocks continuous operation and skews every further
   measurement.
2. Listen to the audio on the machine's speaker. There's only HDMI audio, no
   USB sound card. ALSA underruns occurred during the test run.
3. ArUco detection rate against the printed markers. During the test run
   none were on the tray.
4. Write `picknplay.service`, with `After=teleop.service` but without
   `Requires` — the game should also start without the arms. Along with
   `CPUAffinity=0-2` for the game and `CPUAffinity=3` plus `Nice=-10` for
   Teleop; the three in `PNP_CV_THREADS` already assumes this.
5. The arm camera is mounted rotated 90°. The passthrough is sideways as a
   result.

Plus the two stability rework items: serial numbers instead of `ttyACM*` in
`run_teleop.sh`, and cameras via `/dev/v4l/by-path/` instead of by index.
Both cameras report the same USB serial, so `by-id` doesn't tell them apart —
only the physical port does.
