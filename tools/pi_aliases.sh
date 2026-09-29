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
# A pnp-start game still holds the buttons' GPIO: the service dies on 'GPIO busy'
unalias pnp-expo 2>/dev/null   # was an alias: re-sourcing a shell would choke
pnp-expo() { pnp-running > /dev/null && pnp-stop; sudo systemctl start pnp-expo; }
alias pnp-expo-stop='sudo systemctl stop pnp-expo'
alias pnp-expo-log='journalctl -u pnp-expo -u teleop -u pnp-update -f'
alias pnp-expo-on='sudo systemctl enable --now pnp-expo pnp-update.timer'     # autostart
alias pnp-expo-off='sudo systemctl disable --now pnp-expo pnp-update.timer'   # back to pnp-start
# --no-block: a plain start waits for idle + the 2 min health check (Ctrl-C
# every time, 28.9.). Shows up to 15 s of the updater, the rest is in pnp-expo-log.
unalias pnp-update-now 2>/dev/null
pnp-update-now() {
    local t=$(date '+%F %T')
    sudo systemctl start --no-block pnp-update
    for _ in $(seq 15); do sleep 1; [ "$(systemctl is-active pnp-update)" = activating ] || break; done
    journalctl -u pnp-update --since "$t" -o cat
    echo "HEAD $(git -C $PNP log --oneline -1) -- updater: $(systemctl is-active pnp-update)"
}

# Round length for the expo service: pnp-time 150 sets it and restarts the
# game (a running round is lost), pnp-time alone shows it. systemd drop-in,
# so it survives reboots and auto-updates; config.py reads PNP_ROUND_SECONDS.
pnp-time() {
    local d=/etc/systemd/system/pnp-expo.service.d
    if [ -z "$1" ]; then
        grep -ho 'PNP_ROUND_SECONDS=[0-9]*' $d/time.conf 2>/dev/null || echo "default (config.py MODES)"
        return
    fi
    case $1 in *[!0-9]*) echo "seconds, e.g. pnp-time 150"; return 1;; esac
    sudo mkdir -p $d
    printf '[Service]\nEnvironment=PNP_ROUND_SECONDS=%s\n' "$1" | sudo tee $d/time.conf >/dev/null
    sudo systemctl daemon-reload && sudo systemctl restart pnp-expo && echo "round $1 s, game restarted"
}

# Best rounds for the prize: player no., name, score, EUR off, seconds left
# (only a perfect ends early, so > 0 means perfect and faster = more), time
# to first treat. pnp-winners 20 for more rows.
pnp-winners() { (cd $PNP && PYGAME_HIDE_SUPPORT_PROMPT=1 $PNP_PY game/db.py winners "$@"); }

# Game log: every scene switch, phase, tray change, hint, quit and round end
# (events table in scores.db). pnp-events 200 for more; SQL for the rest.
pnp-events() { (cd $PNP && PYGAME_HIDE_SUPPORT_PROMPT=1 $PNP_PY game/db.py events "$@"); }

# Think time during Oskar's order (panes off, then the round starts itself):
# pnp-think 30 sets it and restarts the game, pnp-think alone shows it.
pnp-think() {
    local d=/etc/systemd/system/pnp-expo.service.d
    if [ -z "$1" ]; then
        grep -ho 'PNP_THINK_SECONDS=[0-9]*' $d/think.conf 2>/dev/null || echo "default (config.py MODES)"
        return
    fi
    case $1 in *[!0-9]*) echo "seconds, e.g. pnp-think 30"; return 1;; esac
    sudo mkdir -p $d
    printf '[Service]\nEnvironment=PNP_THINK_SECONDS=%s\n' "$1" | sudo tee $d/think.conf >/dev/null
    sudo systemctl daemon-reload && sudo systemctl restart pnp-expo && echo "think $1 s, game restarted"
}

# Camera layout: pnp-layout top (default: top-down big in the center, arm cam
# small), split (the two equal panes) or solo (top-down only, no arm cam).
# Restarts the game.
pnp-layout() {
    local d=/etc/systemd/system/pnp-expo.service.d
    if [ -z "$1" ]; then
        grep -ho 'PNP_LAYOUT=[a-z]*' $d/layout.conf 2>/dev/null || echo "default (top)"
        return
    fi
    case $1 in top|split|solo) ;; *) echo "pnp-layout top|split|solo"; return 1;; esac
    sudo mkdir -p $d
    printf '[Service]\nEnvironment=PNP_LAYOUT=%s\n' "$1" | sudo tee $d/layout.conf >/dev/null
    sudo systemctl daemon-reload && sudo systemctl restart pnp-expo && echo "layout $1, game restarted"
}

# Arm cam orientation: pnp-mirror on (left/right) | ud (upside down) |
# 180 (both) | off. Test: turn the leader arm left -> the arm cam image
# should slide RIGHT, like turning your head. Restarts the game.
pnp-mirror() {
    local d=/etc/systemd/system/pnp-expo.service.d m u
    if [ -z "$1" ]; then
        cat $d/mirror.conf 2>/dev/null | grep -o 'PNP_ARM_[A-Z]*=[01]' || echo "default (off)"
        return
    fi
    case $1 in on) m=1 u=0;; ud) m=0 u=1;; 180) m=1 u=1;; off) m=0 u=0;;
        *) echo "pnp-mirror on|ud|180|off"; return 1;; esac
    sudo mkdir -p $d
    printf '[Service]\nEnvironment=PNP_ARM_MIRROR=%s\nEnvironment=PNP_ARM_UD=%s\n' "$m" "$u" | sudo tee $d/mirror.conf >/dev/null
    sudo systemctl daemon-reload && sudo systemctl restart pnp-expo && echo "arm cam $1, game restarted"
}

# Empty the leaderboard: backup next to it, then runs + players deleted.
# The game keeps its connection, the next round reads the empty tables.
pnp-db-reset() {
    local b=$PNP/scores.backup-$(date +%Y%m%d-%H%M%S).db
    $PNP_PY -c "import sqlite3,sys; c=sqlite3.connect('$PNP/scores.db'); c.backup(sqlite3.connect('$b'))
c.execute('DELETE FROM runs'); c.execute('DELETE FROM players'); c.commit(); print('empty, backup', sys.argv[1])" "$b"
}

# Camera exposure/zoom live while the game runs, saved to cam.json (tools/cam.py)
pnp-cam() { PYGAME_HIDE_SUPPORT_PROMPT=1 $PNP_PY $PNP/tools/cam.py "$@"; }

# Teleop by hand instead of the service, e.g. with the geofence on. Stops the
# service meanwhile, both want the same two serial ports.
# The pnp-arm* bodies are ( subshells ) with an EXIT trap: a second Ctrl-C
# kills python by SIGINT, bash then drops the rest of the function, and a
# trailing `systemctl start teleop` never ran -- the arm stayed dead (28.9.).
pnp-arm() (
    trap 'sudo systemctl start teleop' EXIT
    sudo systemctl stop teleop
    cd $PNP && ~/miniforge3/envs/lerobot/bin/python teleop/run.py "$@"
)
alias pnp-arm-test='pnp-arm --fence'            # play with the geofence on
alias pnp-arm-limits='pnp-arm --fence --show'   # plus live min/max, table points

# Live bus check: voltage per motor on both buses, DROP when one goes missing.
# Move the leader and wiggle cables meanwhile. pnp-arm-bus [s], default 60.
pnp-arm-bus() (
    trap 'sudo systemctl start teleop' EXIT
    sudo systemctl stop teleop
    ~/miniforge3/envs/lerobot/bin/python $PNP/tools/scan_motors.py --watch ${1:-60}
)

# LeRobot calibration: pnp-arm-calibrate [follower|leader], default both.
# Teleop has to be off meanwhile -- a tty opens twice without complaint, and
# two processes on one bus garble each other's packets (28.9.). Asks on
# stdin: type c + ENTER to recalibrate over the existing file. The leader's
# gripper direction is set in teleop/run.py, don't edit drive_mode in the json.
pnp-arm-calibrate() (
    local py=~/miniforge3/envs/lerobot/bin s=/dev/serial/by-id/usb-1a86_USB_Single_Serial_
    trap 'sudo systemctl start teleop' EXIT
    sudo systemctl stop teleop
    cp -a ~/.cache/huggingface/lerobot/calibration ~/calibration.bak-$(date +%Y%m%d-%H%M)
    [ "${1:-follower}" = leader ] || $py/lerobot-calibrate --robot.type=so101_follower \
        --robot.port=${s}5970073917-if00 --robot.id=my_follower_arm
    [ "${1:-leader}" = follower ] || $py/lerobot-calibrate --teleop.type=so101_leader \
        --teleop.port=${s}5970072402-if00 --teleop.id=my_leader_arm
)

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
  pnp-update-now   run the updater in the background, 15 s of its log
  pnp-update       plain git pull, for a Pi without expo mode

hardware
  pnp-status       process, temp, throttling, voltage, errors
  pnp-leds [0..1]  LED test, all four states plus MLG
  pnp-leds-off     strip dark
  pnp-led [0..1]   LED zones, interactive: mark side / top center, saves itself
  pnp-buttons      button test, 15 s
  pnp-cam          camera values; pnp-cam top exposure 60 (lower = darker,
                   auto = camera decides), zoom 46, gain, brightness -- live,
                   kept for the next start. pnp-cam snap: frames + detection box
  pnp-arm-limits   dial in the geofence (stops teleop meanwhile)
  pnp-arm-test     play with the geofence on (stops teleop meanwhile)
  pnp-arm-bus [s]  live servo voltages, DROP when a motor goes missing
  pnp-arm-calibrate [follower|leader]  LeRobot calibration (stops teleop meanwhile)
  pnp-arm-help     how to dial in the geofence
  pnp-wifi-add SSID PASS      fair wifi, with DHCP

All four buttons held for 5 s restart the game. In expo mode that's the way
back from a stuck screen, without a keyboard.

MLG mode: blue + yellow held for 4 s, from any scene (a running round is
dropped). Red ends it. Green = air horn, blue/yellow = more text.
  pnp-mlg-video URL   clip for it (yt-dlp + ffmpeg), otherwise synth only
EOF
}
