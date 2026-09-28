# Shortcuts for the Pi. Loaded from ~/.bash_aliases:
#     echo 'source ~/picknplay/tools/pi_aliases.sh' >> ~/.bash_aliases
# `pnp-help` lists them. Every game start carries a timeout: a fully loaded
# Pi stops accepting SSH logins, and the timeout is the only way back.

PNP=~/picknplay
PNP_LOG=/tmp/pnp.log
PNP_PY=$PNP/.venv/bin/python

# Start the game detached from this shell (KMSDRM grabs the terminal), log
# to $PNP_LOG. Env switches pass through: PNP_CAMERA=0 pnp-start 120
pnp-start() {
    systemctl is-active -q pnp-expo && { echo "expo mode is running, pnp-expo-stop first"; return 1; }
    pnp-running && { echo "already running, pnp-stop first"; return 1; }
    (cd $PNP && PYTHONUNBUFFERED=1 setsid timeout -s KILL "${1:-900}" $PNP_PY game/main.py > $PNP_LOG 2>&1 < /dev/null &)
    sleep 1; echo "started for ${1:-900} s, log: pnp-log"
}

# Stop the game, then switch the strip off (KILL skips Leds.close()).
# Stops expo mode as well: otherwise systemd puts the game back after 3 s,
# and pnp-leds / pnp-buttons keep answering "game is running, pnp-stop first".
# It stays off until `pnp-expo` or the next boot.
pnp-stop() {
    systemctl is-active -q pnp-expo && {
        sudo systemctl stop pnp-expo; echo "expo mode stopped, back on with pnp-expo"; }
    pkill -f "[g]ame/main.py" && sleep 0.5
    pnp-leds-off
    echo stopped
}

pnp-running() { ps -eo pid,etime,pcpu,args | grep "[g]ame/main.py"; }
alias pnp-log='tail -n 50 -f $PNP_LOG'
alias pnp-fps='PNP_FPSLOG=1 pnp-start'     # frame rate once a second in pnp-log
alias pnp-fake='PNP_CAMERA=0 pnp-start'    # without camera, fake markers
alias pnp-update='git -C $PNP pull --ff-only'

# Health in one screen: game process, temperature, throttling, voltage, errors
pnp-status() {
    pnp-running || echo "game: not running"
    for u in pnp-expo teleop pnp-update.timer; do
        printf '%-18s %-9s %-9s restarts %s\n' $u $(systemctl is-enabled $u) $(systemctl is-active $u) \
            "$(systemctl show -p NRestarts --value $u)"
    done
    vcgencmd measure_temp; vcgencmd get_throttled
    vcgencmd pmic_read_adc EXT5V_V
    echo "undervoltage since boot: $(sudo dmesg | grep -ci undervolt)"
    ls /dev/spidev5.0 > /dev/null && echo "LED device: ok"
    grep -iE "error|traceback|LEDs off" $PNP_LOG 2>/dev/null | tail -5
}

# LED strip: the four game states plus MLG, 4 s each. pnp-leds 0.1 for dim
pnp-leds() {
    pnp-running && { echo "game is running, pnp-stop first"; return 1; }
    PNP_LED_BRIGHT=${1:-1.0} timeout -s KILL 30 $PNP_PY -c "
import sys, time; sys.path.insert(0, '$PNP/game')
from hw import Leds
l = Leds()
for s in ('idle', 'game', 'hurry', 'score', 'mlg'):
    print(s, flush=True); l.show(s, 0.5); time.sleep(4)
l.close()" 2>&1 | grep -v pygame
}

# LED zones, interactive: arrow keys walk a cursor over the strip, spans get
# marked and saved to led_zones.json right away (tools/led_zones.py).
# pnp-led 0.1 for dimmer. No timeout: it waits for keys, it doesn't load the Pi.
pnp-led() {
    pnp-running && { echo "game is running, pnp-stop first"; return 1; }
    PYGAME_HIDE_SUPPORT_PROMPT=1 PNP_LED_BRIGHT=${1:-0.3} $PNP_PY $PNP/tools/led_zones.py
}

pnp-leds-off() {
    timeout -s KILL 10 $PNP_PY -c "
import sys; sys.path.insert(0, '$PNP/game')
from hw import Leds
Leds().close()" 2>&1 | grep -v pygame || true
}

# Buttons: live state for 15 s, True while pressed
pnp-buttons() {
    pnp-running && { echo "game is running, pnp-stop first"; return 1; }
    timeout -s KILL 15 $PNP_PY -c "
from gpiozero import Button
import time
b = {'up': Button(25), 'right': Button(8), 'left': Button(7), 'down': Button(1)}
while True:
    print('  '.join(f'{k}={int(v.is_pressed)}' for k, v in b.items()), end='\r', flush=True)
    time.sleep(0.05)"
    echo
}

# Expo mode (pi/setup.sh): the game as a systemd service that never gives up
alias pnp-expo='sudo systemctl start pnp-expo'
alias pnp-expo-stop='sudo systemctl stop pnp-expo'
alias pnp-expo-log='journalctl -u pnp-expo -u teleop -u pnp-update -f'
alias pnp-expo-on='sudo systemctl enable --now pnp-expo pnp-update.timer'     # autostart
alias pnp-expo-off='sudo systemctl disable --now pnp-expo pnp-update.timer'   # back to pnp-start
alias pnp-update-now='sudo systemctl start pnp-update'

# Teleop by hand instead of the service, e.g. with the geofence on. Stops the
# service meanwhile, both want the same two serial ports.
pnp-arm() {
    sudo systemctl stop teleop
    (cd $PNP && ~/miniforge3/envs/lerobot/bin/python teleop/run.py "$@")
    sudo systemctl start teleop
}
alias pnp-arm-test='pnp-arm --fence'            # play with the geofence on
alias pnp-arm-limits='pnp-arm --fence --show'   # plus live min/max, table points

# LeRobot calibration: pnp-arm-calibrate [follower|leader], default both.
# Teleop has to be off meanwhile -- a tty opens twice without complaint, and
# two processes on one bus garble each other's packets (28.9.). Asks on
# stdin: type c + ENTER to recalibrate over the existing file.
pnp-arm-calibrate() {
    local py=~/miniforge3/envs/lerobot/bin s=/dev/serial/by-id/usb-1a86_USB_Single_Serial_
    sudo systemctl stop teleop
    cp -a ~/.cache/huggingface/lerobot/calibration ~/calibration.bak-$(date +%Y%m%d-%H%M)
    [ "${1:-follower}" = leader ] || $py/lerobot-calibrate --robot.type=so101_follower \
        --robot.port=${s}5970073917-if00 --robot.id=my_follower_arm
    [ "${1:-leader}" = follower ] || $py/lerobot-calibrate --teleop.type=so101_leader \
        --teleop.port=${s}5970072402-if00 --teleop.id=my_leader_arm
    sudo systemctl start teleop
}

pnp-arm-help() {
    cat <<'EOF'
Geofencing: teleop/run.py --fence clamps every joint of the leader into its
band in LIMITS, and keeps the gripper above the table plane FLOOR by raising
shoulder_lift. At a band edge only that joint stops, the others keep
following, so the arm stays playable instead of looking broken. After a
start the follower glides to the leader for 1 s instead of jumping.
teleop.service runs WITHOUT --fence until it's tested -- only the servo
overload guard (0.5 s) is always on.

Dialing it in:
  1. pnp-arm-limits          the arm keeps following, with a live min/max table
  2. move every joint as far as the follower may go -- not into the cabinet
     wall, not past the tray. The follower moves along, so you see where it
     gets close instead of guessing from numbers.
  3. the table: hold the gripper just above it and press Enter, at 3-4 poses
     spread over the table (near, far, left, right, wrist bent differently).
     That's the table plane: shoulder_lift and elbow_flex can each be inside
     their band and still put the gripper on the table, the plane catches it.
  4. Ctrl-C prints LIMITS and FLOOR. Paste both into teleop/run.py.
  5. pnp-arm-test            play with the fence on, try to hit the table

Careful: the printed numbers are the leader's, before the fence. Where a
band is already narrow, the number keeps rising while the arm has stopped.
Re-measuring from scratch: set that joint back to (-100, 100) first, and
FLOOR back to None.
EOF
}

# MLG mode's clip (game/mlg.py). 360p on purpose: the screen crunches it to
# 320x180 anyway, and a small file costs the Pi nothing to decode. The sound
# goes to video.wav because cv2 plays no audio. Not in git.
pnp-mlg-video() {
    [ $# = 1 ] || { echo "usage: pnp-mlg-video YOUTUBE-URL"; return 1; }
    local d=$PNP/game/assets/mlg
    mkdir -p $d && rm -f $d/video.*
    yt-dlp -f "b[height<=360]" --remux-video mp4 -o "$d/video.%(ext)s" "$1" &&
    ffmpeg -y -loglevel error -i $d/video.mp4 -vn -ac 1 -ar 44100 $d/video.wav &&
    echo "ok, next MLG mode plays it: $d"
}

# Fair wifi: pnp-wifi-add SSID PASS. Replaces the previous fair network,
# the studio wifi stays. DHCP on, because a fair hands out its own addresses.
# netplan apply drops wifi for a moment -- do it at the keyboard, not over it.
pnp-wifi-add() {
    [ $# = 2 ] || { echo "usage: pnp-wifi-add SSID PASS"; return 1; }
    sudo tee /etc/netplan/60-pnp-wifi.yaml > /dev/null <<EOF
network:
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "$1":
          password: "$2"
EOF
    sudo chmod 600 /etc/netplan/60-pnp-wifi.yaml && sudo netplan apply
}

pnp-help() {
    # Which half of this list applies depends on expo mode, so it says so
    # first -- with the service running, pnp-start refuses and pnp-stop
    # stops the service.
    echo "expo mode: $(systemctl is-active pnp-expo) ($(systemctl is-enabled pnp-expo) at boot)," \
         "teleop: $(systemctl is-active teleop), auto-update: $(systemctl is-active pnp-update.timer)"
    cat <<'EOF'

game
  pnp-start [s]    start game (default 900 s), detached -- not in expo mode
  pnp-stop         stop game, LEDs off. Stops expo mode too, until pnp-expo
  pnp-log          follow game output
  pnp-fps [s]      start with frame rate log
  pnp-fake [s]     start without camera

expo mode (systemd: game, teleop, auto-update from branch expo)
  pnp-expo         start the game service    pnp-expo-stop   stop it
  pnp-expo-on      autostart + auto-update   pnp-expo-off    both off again
  pnp-expo-log     follow game, teleop and updater
  pnp-update-now   run the updater now (waits for the round to end)
  pnp-update       plain git pull, for a Pi without expo mode

hardware
  pnp-status       process, temp, throttling, voltage, errors
  pnp-leds [0..1]  LED test, all four states plus MLG
  pnp-leds-off     strip dark
  pnp-led [0..1]   LED zones, interactive: mark side / top center, saves itself
  pnp-buttons      button test, 15 s
  pnp-arm-limits   dial in the geofence (stops teleop meanwhile)
  pnp-arm-test     play with the geofence on (stops teleop meanwhile)
  pnp-arm-calibrate [follower|leader]  LeRobot calibration (stops teleop meanwhile)
  pnp-arm-help     how to dial in the geofence
  pnp-wifi-add SSID PASS      fair wifi, with DHCP

All four buttons held for 5 s restart the game. In expo mode that's the way
back from a stuck screen, without a keyboard.

MLG mode: blue + yellow held for 2 s, from any scene (a running round is
dropped). Red ends it. Green = air horn, blue/yellow = more text.
  pnp-mlg-video URL   clip for it (yt-dlp + ffmpeg), otherwise synth only
EOF
}
