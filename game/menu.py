"""The secret staff menu: hold ◀ + ▶ for MENU_HOLD seconds, from any scene.

Everything the pnp-* commands do over SSH, for whoever stands at the booth.
▲▼ picks a line, ◀▶ changes a value or runs an action. Settings go to
settings.json (settings.py puts them on trial, so a bad one rolls itself
back) and take effect with SAVE + RESTART. Dangerous actions ask twice.
Nothing touched for MENU_IDLE seconds: back to idle, nothing saved.
"""
import json
import os
import subprocess

import settings
from app import SceneBase
from config import *
from scenes import IdleScene, draw, draw_left, footer

MENU_IDLE = 60
ARM_FILE = os.path.join(settings.ROOT, "arm.json")


def steps(lo, hi, step):
    n = round((hi - lo) / step)
    return [f"{lo + i * step:g}" for i in range(n + 1)]


# key -> choices. The current value is the first shown; unknown values are kept.
CHOICES = {
    "ROUND_SECONDS": steps(60, 240, 10),
    "THINK_SECONDS": steps(0, 60, 5),
    "TUT_SECONDS":   steps(15, 60, 5),
    "LAYOUT":        ["split", "top", "solo", "fpv"],
    "LANG":          ["de", "en"],
    "ASK_NAME":      ["0", "1"],
    "VOLUME":        steps(0, 3, 0.25),
    "LED_BRIGHT":    steps(0.1, 1.0, 0.1),
    "VIEW_GAMMA":    steps(0.3, 1.0, 0.05),
}
# what the game runs with now, as a string like settings.json holds it
NOW = {"ROUND_SECONDS": ROUND_SECONDS, "THINK_SECONDS": THINK_SECONDS,
       "TUT_SECONDS": TUT_SECONDS, "LAYOUT": LAYOUT, "LANG": LANG,
       "ASK_NAME": int(ASK_NAME), "VOLUME": VOLUME, "LED_BRIGHT": LED_BRIGHT,
       "VIEW_GAMMA": env("VIEW_GAMMA", "0.55")}

ACTIONS = ["SAVE + RESTART GAME", "RESTART ARM", "GRIPPER INVERT", "WINNERS",
           "SETTINGS TO DEFAULT", "REBOOT PI", "SHUT DOWN PI", "CLOSE"]
DANGER = {"SETTINGS TO DEFAULT", "REBOOT PI", "SHUT DOWN PI"}


def sh(*cmd):
    """Run a root command without waiting on it; its failure is shown, not raised."""
    try:
        return subprocess.run(["sudo", "-n", *cmd], capture_output=True, text=True,
                              timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def grip_inverted():
    try:
        with open(ARM_FILE) as f:
            return bool(json.load(f).get("grip_invert"))
    except (OSError, ValueError, AttributeError):
        return False


def status():
    """One line: version, temperature, what's broken."""
    def run(*c):
        try:
            return subprocess.run(c, capture_output=True, text=True, timeout=3).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return "?"
    ver = run("git", "-C", settings.ROOT, "log", "-1", "--format=%h")
    temp = run("vcgencmd", "measure_temp").replace("temp=", "")
    arm = run("systemctl", "is-active", "teleop")
    return f"{ver}  {temp or '-'}  ARM {arm or '-'}"


class MenuScene(SceneBase):
    MUSIC = None

    def __init__(self, ctx):
        super().__init__(ctx)
        ctx.leds.show("idle")
        saved = settings.load()
        self.values = {k: str(saved.get(k, NOW[k])) for k in CHOICES}
        self.start = dict(self.values)
        self.lines = list(CHOICES) + ACTIONS
        self.cur = self.idle = self.ask = 0.0
        self.cur = 0
        self.msg = status()
        self.winners = None
        ctx.db.log("menu")

    def handle(self, action):
        self.idle = 0.0
        if self.winners is not None:        # any button closes the list
            self.winners = None
            return "ok"
        line = self.lines[self.cur]
        if action in ("up", "down"):
            self.cur = (self.cur + (1 if action == "down" else -1)) % len(self.lines)
            self.ask = 0.0
            return "ok"
        if line in CHOICES:
            ch = CHOICES[line]
            v = self.values[line]
            i = ch.index(v) if v in ch else 0
            self.values[line] = ch[(i + (1 if action == "right" else -1)) % len(ch)]
            return "ok"
        if action != "right":
            return None
        if line in DANGER and self.ask <= 0:
            self.ask = CONFIRM_SECONDS
            self.msg = f"▶ AGAIN: {line}"
            return "ok"
        self.run(line)
        return "ok"

    def run(self, line):
        self.ctx.db.log("menu_action", action=line)
        if line == "SAVE + RESTART GAME":
            settings.save({k: v for k, v in self.values.items() if v != self.start[k]})
            self.next = None                 # exits; systemd starts the game again
        elif line == "RESTART ARM":
            self.msg = "ARM RESTARTING" if sh("systemctl", "restart", "teleop") else "FAILED"
        elif line == "GRIPPER INVERT":
            inv = not grip_inverted()
            tmp = ARM_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump({"grip_invert": inv}, f)
            os.replace(tmp, ARM_FILE)
            ok = sh("systemctl", "restart", "teleop")
            self.msg = f"GRIPPER {'INVERTED' if inv else 'NORMAL'}" + ("" if ok else " (ARM RESTART FAILED)")
        elif line == "WINNERS":
            self.winners = self.ctx.db.winners(8) if hasattr(self.ctx.db, "winners") else []
        elif line == "SETTINGS TO DEFAULT":
            settings.save({k: None for k in settings.load()})
            self.next = None
        elif line == "REBOOT PI":
            self.msg = "REBOOTING" if sh("systemctl", "reboot") else "FAILED"
        elif line == "SHUT DOWN PI":
            self.msg = "SHUTTING DOWN, UNPLUG IN 30 S" if sh("systemctl", "poweroff") else "FAILED"
        elif line == "CLOSE":
            self.switch_to(IdleScene(self.ctx))

    def update(self, dt):
        self.idle += dt
        self.ask = max(0.0, self.ask - dt)
        if self.idle > MENU_IDLE:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        draw(screen, f["small"], "STAFF MENU", 960, 60, ACCENT)
        draw(screen, f["tiny"], self.msg[:56], 960, 120, GREY)
        if self.winners is not None:
            for i, (pl, name, score, off, secs, ts) in enumerate(self.winners):
                draw_left(screen, f["tiny"], f"{i + 1}. #{pl or '-'}  {score}  "
                          f"OFF {off / 10:.2f}  {str(ts)[5:16]}", 200, 200 + i * 60, WHITE)
            footer(screen, f, None, "▶ BACK")
            return
        # a window of 12 lines around the cursor
        top = max(0, min(self.cur - 6, len(self.lines) - 12))
        for row, line in enumerate(self.lines[top:top + 12]):
            i = top + row
            color = ACCENT if i == self.cur else WHITE
            text = f"{line}: ◀ {self.values[line]} ▶" if line in CHOICES else line
            if line in CHOICES and self.values[line] != self.start[line]:
                text += " *"
            draw_left(screen, f["tiny"], ("> " if i == self.cur else "  ") + text, 200, 190 + row * 58, color)
        footer(screen, f, None, None, note="▲▼ PICK  ◀▶ CHANGE / RUN")
