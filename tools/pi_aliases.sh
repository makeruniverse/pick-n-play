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

# LED strip: the four game states, 4 s each. pnp-leds 0.1 for dim
pnp-leds() {
    pnp-running && { echo "game is running, pnp-stop first"; return 1; }
    PNP_LED_BRIGHT=${1:-1.0} timeout -s KILL 30 $PNP_PY -c "
import sys, time; sys.path.insert(0, '$PNP/game')
from hw import Leds
l = Leds()
for s in ('idle', 'game', 'hurry', 'score'):
    print(s, flush=True); l.show(s, 0.5); time.sleep(4)
l.close()" 2>&1 | grep -v pygame
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

# Geofencing: teleop with a live min/max table, Ctrl-C prints LIMITS.
# Stops the service meanwhile, both want the same two serial ports.
pnp-arm-limits() {
    sudo systemctl stop teleop
    (cd $PNP && ~/miniforge3/envs/lerobot/bin/python teleop/run.py --show)
    sudo systemctl start teleop
}

pnp-arm-help() {
    cat <<'EOF'
Geofencing: teleop/run.py clamps every joint of the leader into its band in
LIMITS before the follower sees it. At the edge only that joint stops, the
others keep following, so the arm stays playable instead of looking broken.

Dialing the bands in:
  1. pnp-arm-limits          the arm keeps following, with a live min/max table
  2. move every joint as far as the follower may go -- not onto the table,
     not into the cabinet wall, not past the tray. The follower moves along,
     so you see where it gets close instead of guessing from numbers.
  3. also try the bad combinations: shoulder_lift and elbow_flex can each be
     inside their band and still put the gripper on the table. Each band is
     its own joint, the pair is not a region in space -- when in doubt, tighter.
  4. Ctrl-C prints a LIMITS block. Paste it into teleop/run.py, commit,
     push to expo -- the updater restarts teleop by itself.

Careful: the printed numbers are the leader's, before the clamp. Where a
band is already narrow, the number keeps rising while the arm has stopped.
Re-measuring from scratch: set that joint back to (-100, 100) first.
EOF
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
  pnp-leds [0..1]  LED test, all four states
  pnp-leds-off     strip dark
  pnp-buttons      button test, 15 s
  pnp-arm-limits   dial in the geofence (stops teleop meanwhile)
  pnp-arm-help     how to dial in the geofence
  pnp-wifi-add SSID PASS      fair wifi, with DHCP

All four buttons held for 5 s restart the game. In expo mode that's the way
back from a stuck screen, without a keyboard.
EOF
}
