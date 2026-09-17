#!/bin/bash
# Auto-update from origin/expo. pnp-update.timer, every 5 min, as root.
#
# New commit -> wait until the game shows IdleScene -> switch -> restart.
# Unhealthy within 2 min -> back to the old commit, and the bad one is never
# tried again. Offline -> nothing happens, next try in 5 min.
#
# Everything sits in main(): git rewrites this very file mid-run, and bash
# reads scripts lazily. The function makes it parse the whole file first.
set -u
R=/home/ubuntu/picknplay
URL=https://github.com/makeruniverse/pick-n-play.git
BAD=/var/lib/pnp/bad

# as ubuntu, via setpriv: sudo would log two PAM lines per call, every 5 min
as_ubuntu() { HOME=/home/ubuntu setpriv --reuid=ubuntu --regid=ubuntu --init-groups "$@"; }
g()       { as_ubuntu timeout 120 git -C $R "$@"; }
changed() { ! g diff --quiet "$old" "$new" -- "$@"; }
uv_sync() { as_ubuntu timeout 600 /home/ubuntu/.local/bin/uv --directory $R sync --extra pi; }
healthy() {
    for u in $units; do
        systemctl is-active -q $u || return 1
        [ "$(systemctl show -p NRestarts --value $u)" = "${n0[$u]}" ] || return 1
    done
}

main() {
    # Corrupt repo (plug pulled mid-write): fresh clone, keep venv and scores
    if ! g fsck --connectivity-only --no-progress >/dev/null 2>&1; then
        echo "repo broken, re-cloning"
        rm -rf $R.new
        as_ubuntu timeout 300 git clone -q -b expo $URL $R.new || return 0
        mv $R/.venv $R/scores.db* $R.new/ 2>/dev/null
        mv $R $R.broken.$(date +%s) && mv $R.new $R
        systemctl restart pnp-expo teleop
        return 0
    fi

    g fetch -q origin expo || return 0
    new=$(g rev-parse origin/expo)
    old=$(g rev-parse HEAD)
    [ "$new" = "$old" ] && return 0
    [ "$new" = "$(cat $BAD 2>/dev/null)" ] && return 0

    # No state file = game isn't running, fine to switch.
    # ponytail: idle can become a round between this check and the restart;
    # that visitor loses one round. Rare enough.
    until [ "$(cat /run/pnp/state 2>/dev/null || echo IdleScene)" = IdleScene ]; do
        sleep 5
    done

    echo "update ${old:0:7} -> ${new:0:7}"
    g checkout -q -f -B expo "$new" || return 0
    changed uv.lock pyproject.toml && uv_sync
    changed pi/setup.sh && bash $R/pi/setup.sh
    units=pnp-expo
    changed teleop && units="$units teleop"   # restarting teleop drops the arm, only if needed

    systemctl restart $units
    declare -gA n0
    for u in $units; do n0[$u]=$(systemctl show -p NRestarts --value $u); done
    sleep 120
    healthy && { echo "update ${new:0:7} ok"; return 0; }

    echo "update ${new:0:7} unhealthy, rolling back to ${old:0:7}"
    echo "$new" > $BAD
    g checkout -q -f -B expo "$old"
    changed uv.lock pyproject.toml && uv_sync
    changed pi/setup.sh && bash $R/pi/setup.sh
    systemctl restart $units
}

main
exit
