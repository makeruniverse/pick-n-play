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
    pnp-running && { echo "already running, pnp-stop first"; return 1; }
    (cd $PNP && PYTHONUNBUFFERED=1 setsid timeout -s KILL "${1:-900}" $PNP_PY game/main.py > $PNP_LOG 2>&1 < /dev/null &)
    sleep 1; echo "started for ${1:-900} s, log: pnp-log"
}

# Stop the game, then switch the strip off (KILL skips Leds.close())
pnp-stop() {
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

pnp-help() {
    cat <<'EOF'
pnp-start [s]    start game (default 900 s), detached
pnp-stop         stop game, LEDs off
pnp-log          follow game output
pnp-status       process, temp, throttling, voltage, errors
pnp-fps [s]      start with frame rate log
pnp-fake [s]     start without camera
pnp-leds [0..1]  LED test, all four states
pnp-leds-off     strip dark
pnp-buttons      button test, 15 s
pnp-update       git pull
EOF
}
