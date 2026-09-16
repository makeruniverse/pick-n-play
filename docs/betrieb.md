# Operations

How to start, check and keep running. Stand: 9 September 2026.

## What's on the Pi

Two processes that do not know each other. **Teleop** reads the Leader arm and
writes the joint angle on the follower, 60 Hz, as a systemd service in continuous running.
**The game** reads the top down camera, recognizes ArUco marker and renders. It asks
never cut off the arm state.

The two use separate Python environments and do not accept:

| | Environment | Version |
|---|---|---|
| Teleop | conda, `~/miniforge3/envs/lerobot` | Python 3.10, LeRobot 0.4.2 |
| Game | uv, project `.venv` | Python 3.13, pygame-ce, OpenCV |

Hardware: Raspberry Pi 5 (8 GB) with Ubuntu 24.04, two SO-101 arms via CH343 adapter,
two USB cameras, display on HDMI-A-1.

> The game has been installed on the Pi since the 9.9.2026 and starts. It is
> but ** not removed**: it does not reach the target image rate and drives the
> Pi together with the Teleop in the throttle. See 'As of acceptance'.

## Reinkommen

```sh
ssh picknplay
```

The entry is in`~/.ssh/config`and shows`ubuntu@172.22.1.2`. The Pi hangs
per WLAN am Makerspace-Netz, `eth0`is dead. The IP comes via DHCP, so it can
change. If nothing goes: pin. He responds to Ping, but Port 22 is closed, running
`sshd`not, and you have to go to the keyboard on the device.

## Start Teleop and Stop

```sh
sudo systemctl start teleop.service
sudo systemctl stop  teleop.service
sudo systemctl restart teleop.service
```

The service is`enabled`, startet also beim Booten von allein.

## Is it?

```sh
systemctl is-active teleop.service
systemctl show teleop.service -p NRestarts -p SubState
vcgencmd measure_temp
vcgencmd get_throttled
```

Healthy looks like this: `active`, `SubState=running`, **`NRestarts=0`**, around 55 to 65 °C,
`throttled=0x0`.

`NRestarts`is the most important number. rises, crashes the service and restarts, and
this is always a hardware problem: an arm without power, a cable off, an adapter not
recognized. Software failures look different.

In normal operation, Teleop **nots** writes to the journal. This is intentional (see “Why
the journal is still"). Stille means it's running. Errors continue to land in the log:

```sh
journalctl -u teleop.service -b --no-pager | tail -30
```

### `get_throttled` lesen

The number is a bit mask. Four bits are important:

|Value| Bedeutung |
|---|---|
| `0x0` | alles in Ordnung |
| `0x1` |Undervoltage **now**, so power supply or cable|
| `0x8` | Temperature limit **now**, he just shoots |
| `0x80000` |Temperature limit has occurred since the boat|

`0x80008`says accordingly: just shoots and has done it before. About
80 °C starts this.

test engines

If Teleop crashes, is the first question: answer servos at all? The answer
`tools/scan_motors.py`. Teleop has to stand for it, otherwise the ports are occupied.

```sh
sudo systemctl stop teleop.service
~/miniforge3/envs/lerobot/bin/python ~/scan_motors.py
sudo systemctl start teleop.service
```

The script is under the repo`tools/scan_motors.py`and as a copy directly into`~`on
Pi, so it's handy even without checked-out repo.

Gesund:

```
/dev/ttyACM0 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
/dev/ttyACM1 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
```

Six engines per arm, IDs 1 to 6, model 777 (STS3215). Everything else is a finding:

A port reports **no engines**, although it appears in the scan. Then missing
Servo power supply or the three-wire bus cable is not in place. The USB adapter pulls
its current from the Pi and also reports without a power supply, but the bus remains
Quiet. Leader runs to 7.4 V, followers to 12 V.

There are ** single engines in the middle of the chain, about 2 and 4, while 3, 5 and 6
answer. Then it is not the connecting cables, but the servos themselves: plugs
set loose or ID.

A port ** doesn't appear at all**. Then a USB adapter is off, and this is the
dangerous case, see next section.

### The case that looks like a servo defect and nobody is

On 9.9.2026, engines fell out over hours, alternatingly: only 2 and 4,
then all six, then 4 and 6. The scan found every time every six, LeRobot
still failed. The cause was the **network that stood at 5 V**.

The reason why this is so difficult to see: a ping almost does not draw electricity,
therefore all the motors brav in the scan respond to undervoltage. As soon as LeRobot
but Torque enabled, break the two that pull the most — in one
SO-101 are the 4 (Wrist-Flex) and 6 (Greifer) because the
work. They fall off the bus and the error message says "Missing motor IDs".

**Merk rule: changing engine IDs mean voltage, fixed mean hardware. **
If the same motor always fails, it is the motor or its plug. Change it,
first measure the voltage. Followers 12 V, Leader 7,4 V.

### The first start attempt sometimes fails

Even with correct voltage, the first connection attempt occasionally strikes
and the second runs. That is why`Restart=on-failure`in the override, and
therefore,`NRestarts=1`no need to worry after a start. First of all
increasing number is one.

## Which adapter is which arm

```sh
ls -l /dev/serial/by-id/
```

```
usb-1a86_USB_Single_Serial_5970072402-if00 -> ttyACM0    Leader
usb-1a86_USB_Single_Serial_5970073917-if00 -> ttyACM1    Follower
```

`run teleop.sh`transferring`ttyACM0`as Leader and`ttyACM1` as followers. These numbers
assigns the kernel in the order in which the devices appear. Plugs an adapter
not, all of them slip up a number: out`ttyACM1`the`ttyACM0`and Teleop
talks to the follower as if he were the leader.

That's exactly what happened on September 9th. The error is reported as “Missing motor IDs”
and looks like broken servos, although only one cable was missing. First action
this error is always`ls -l /dev/serial/by-id/`Not the motor scan.

The serial numbers are fixed and never slip. The clean reconstruction is, it is in
`run_teleop.sh`to be entered instead of`ttyACM*`- Numbers. Stand still.

= Maintenance

Once a month or if something is weird:

```sh
df -h / # keep below 85%
journalctl --disk-usage # capped to 200 MB
vcgencmd measure_temp
systemctl show teleop.service -p NRestarts
```

If the plate is running, in this order:

```sh
sudo journalctl --rotate && sudo journalctl --vacuum-size=200M
sudo rm -f /var/log/syslog.1 /var/log/syslog.*.gz
rm -rf ~/.cache/pip ~/.cache/huggingface/hub ~/.cache/huggingface/xet
rm -rf ~/.vscode-server
```

**Not* *`~/.cache`completely delete. The arm calibration is in there:

```
~/.cache/huggingface/lerobot/calibration/robots/so101_follower/my_follower_arm.json
~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/my_leader_arm.json
```

Two files, together not 2 KB, from March 31. If they are gone, have to be recalibrated
,. A backup of it on the MacBook would be smart.

### Why the journal is still

Teleop printed one line of loop time per loop, i.e. 60 lines per 60 Hz
Just a second. These were 99,7 % of the entire journal and around 1 GB per day, because journald and
rsyslog the same current twice. Journald's built-in rate limit applies
Not 60 lines per second, that's below the threshold.

Two changes are now in check.`SystemMaxUse=200M` in
`/etc/systemd/journald.conf`covers the journal. And
`/etc/systemd/system/teleop.service.d/override.conf`:

```ini
[Unit]
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Restart=on-failure
StandardOutput=null
```

`StandardOutput=null`swallows the Debug print. The two`StartLimit`-Crows are the
Heat protection: in the case of a hardware error, the service hero with`Restart=always` never an
and restarted in 30 minutes 153 times, each time with full loading of torch.
The Pi came to 82°C and throttled. Now he remains in two after five failures
Minutes stand and reports that instead of heating.

# If something doesn't go

| Symptom |First examination|Mostly the cause|
|---|---|---|
| `ssh` sagt Connection refused, Ping geht |to the keyboard on the device,`df -h /` | Platte voll, `sshd`does not start|
| `ssh` sagt Timeout | `arp -n 172.22.1.2` |Pi off, or new IP via DHCP|
| `NRestarts` rises | `journalctl -u teleop.service -b \| tail -30` | Hardware, never software |
|"Missing motor IDs"| `ls -l /dev/serial/by-id/` ` Adapter off, numbers slipped |
| One bus is completely silent |Servo power supply and bus cable|lack of power, not the servos|
|Individual motors are missing abruptly, sometimes 2 and 4, times 4 and 6| ** Measuring voltage at the power supply** | See below
|Over 80 °C| `systemctl show teleop.service -p NRestarts` | Crash-Loop heizt den Pi |
|Plate over 85%| `journalctl --disk-usage` |see "Maintenance"|

## Start the game

```sh
cd ~/picknplay
.venv/bin/python game/main.py
```

Runs over KMSDRM in full screen, without desktop. **Attention
no keyboard input, SDL reads from KMSDRM`/dev/input`. To operate
belongs a USB keyboard to the Pi, to the end`q`.

Start it from an SSH session, always hang a`timeout` davor. Sonst
it continues when the session breaks, and a loaded Pi leaves no
new registration more for:

```sh
timeout -s KILL 30 .venv/bin/python game/main.py
```

### Switch for measuring and developing

All by environment variable, Default is always the machine. The file must be
do not touch what is important because the next`git pull` lokale
Changes taken in.

| Variable | Wirkung |
|---|---|
| `PNP_FULLSCREEN=0` | Fenster statt Vollbild |
| `PNP_CAMERA=0` | `FakeDetector`, no camera access|
| `PNP_FPSLOG=1` |Image rate and scene, once per second on stdout|
| `PNP_CRT=0` | Disable the CRT overlay completely |
| `PNP_BARREL=0` |only the curvature, scanlines stay|
| `PNP_IDLE_FPS=60` |Idle screen on game scene load, for measurements without keyboard|

## Stand of acceptance

Installed and tested:`uv`, Python 3.13, OpenCV 5.0, pygame-ce 2.5.8, all
four self-tests green, both cameras supply picture, KMSDRM starts sound over
HDMI vorhanden.

Not taken: **the image rate.** Objective are 60 fps, measured 19.6 with
full CRT and 40 in the sterilized state. Play and Teleop at the same time
the Pi in under one minute to 83°C and drosselts. The figures and the three
Set screws are shown in the Overview under "Measurement on the Pi".

**Until this is decided not to let both run permanently at the same time. **

Open

1. Image rate decision: Remove curvature, move to 1920 × 1080 natively,
or lower target image rate to 30. Design question, no configuration question.
Two. Active cooling. Without a fan, the Pi is under double load.
3. Layout to 1080, if point 1 starts.`FOOTER_Y = 1120` otherwise lies
outside the picture.
4. Listen to the automatic loudspeaker. There is only HDMI audio, no USB card.
ALSA-Underruns occurred during the test run.
Five. ArUco detection rate against the printed markers. No tests were carried out
on the tray.
6. write `picknplay.service` with `After=teleop.service`, but without
   `Requires`— the game should start without arms.
7. The arm camera is rotated by 90°. The passthrough is crossed.

To this end, the two stability modifications: serial numbers instead`ttyACM*` in
`run_teleop.sh`and cameras`/dev/v4l/by-path/`instead of indices. Both
Kameras melden denselben USB-Serial, `by-id`so it does not differ, only
the physical port does.
