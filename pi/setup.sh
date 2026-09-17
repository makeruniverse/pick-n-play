#!/bin/bash
# Expo mode, layers 1, 2 and 4 of docs/expo-plan.md. Idempotent, on the Pi:
#     sudo bash ~/picknplay/pi/setup.sh
# Installs and enables, restarts nothing. pnp-update.sh runs it again
# whenever this file changes. Watchdog and logind take effect after a reboot.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
R=/home/ubuntu/picknplay
U=/etc/systemd/system

# ── Layer 1: game and teleop start on boot and never give up ──────────────
# Backoff 3 s -> 2 min instead of StartLimitBurst: a broken arm heats the Pi
# less at one try per 2 min, and it comes back by itself once fixed.
cat > $U/pnp-expo.service <<EOF
[Unit]
Description=PICK'N'PLAY game (expo mode)
StartLimitIntervalSec=0

[Service]
Type=notify
User=ubuntu
WorkingDirectory=$R
Environment=PYTHONUNBUFFERED=1
ExecStart=$R/.venv/bin/python game/main.py
ExecStopPost=$R/.venv/bin/python pi/leds.py
Restart=always
RestartSec=3
RestartSteps=10
RestartMaxDelaySec=120
# main.py pings only while every camera delivers: hung loop or dead camera -> restart
WatchdogSec=15
TimeoutStartSec=120
# sshd and teleop always win against the game
Nice=5
CPUWeight=50
RuntimeDirectory=pnp

[Install]
WantedBy=multi-user.target
EOF

# No network dependency anymore: the arm doesn't need one, and the old
# After=network-online.target held teleop back for 2 min without a cable.
cat > $U/teleop.service <<EOF
[Unit]
Description=PICK'N'PLAY teleop with geofencing
StartLimitIntervalSec=0

[Service]
Type=notify
User=ubuntu
WorkingDirectory=$R
ExecStart=/home/ubuntu/miniforge3/envs/lerobot/bin/python teleop/run.py
Restart=always
RestartSec=2
RestartSteps=10
RestartMaxDelaySec=120
WatchdogSec=10
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
EOF
rm -rf $U/teleop.service.d   # old StartLimitBurst / StandardOutput=null override

# ── Layer 2: the Pi itself ────────────────────────────────────────────────
mkdir -p /etc/systemd/system.conf.d /etc/systemd/logind.conf.d \
         $U/systemd-networkd-wait-online.service.d
printf '[Manager]\nRuntimeWatchdogSec=30\n' > /etc/systemd/system.conf.d/pnp.conf
printf '[Login]\nHandlePowerKey=reboot\n'   > /etc/systemd/logind.conf.d/pnp.conf
echo "kernel.panic = 10" > /etc/sysctl.d/90-pnp.conf
sysctl -q -p /etc/sysctl.d/90-pnp.conf
# sshd came up 2 min after boot: netplan makes wait-online wait for eth0,
# which has no cable, and cloud-init (and with it ssh) waits for that.
printf '[Service]\nExecStart=\nExecStart=/lib/systemd/systemd-networkd-wait-online --any --timeout=15\n' \
    > $U/systemd-networkd-wait-online.service.d/20-pnp.conf
# Nobody installs updates at the fair: no apt run eating CPU at boot,
# no snap refresh restarting things mid-day.
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service 2>/dev/null || true
snap refresh --hold >/dev/null 2>&1 || true
# git: fsync on write, so a pulled plug doesn't leave half-written objects
sudo -u ubuntu git -C $R config core.fsync committed

# ── Layer 4: auto-update from branch expo ─────────────────────────────────
cat > $U/pnp-update.service <<EOF
[Unit]
Description=PICK'N'PLAY auto-update from branch expo

[Service]
Type=oneshot
ExecStart=/bin/bash $R/pi/update.sh
StateDirectory=pnp
# waits for the round to end, 30 min is the ceiling
TimeoutStartSec=30min
EOF
cat > $U/pnp-update.timer <<EOF
[Unit]
Description=PICK'N'PLAY auto-update every 5 min

[Timer]
OnBootSec=2min
OnUnitInactiveSec=5min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable -q pnp-expo.service teleop.service pnp-update.timer
echo "expo setup done"
