import importlib
import os
import sys
import pygame

# ── Display ───────────────────────────────────────────────────────────────
# Design resolution = panel resolution of the Asus MB169CK, native and
# without pygame.SCALED. Scaling 1200 -> 1080 measured at around 20 ms per
# frame, and it put the 8x8 pixel font on a grid with factor 0.9 -- i.e.
# unevenly sized glyph pixels. Every coordinate in scenes.py is an absolute
# number for this grid; a different panel means touching the layout.
WIDTH, HEIGHT = 1920, 1080

# 30, not 60. Two reasons, both independent of compute power:
#
# 1. 60/30 = 2, so every frame stands for exactly two refreshes and the
#    cadence is even. At 40 fps, 60/40 = 1.5: alternating one and two
#    refreshes, visible stutter at a *higher* frame rate. Below 60, 30 is
#    the only even number on a 60 Hz panel.
# 2. The cameras deliver 30 frames/s. Anything above that shows the same
#    camera frame twice during the round.
#
# There is no 60 Hz motion in this game: second counter, total, blinking
# text, camera image. The arcade look comes from scanlines, barrel
# distortion, and hard pixel edges, not from the frame rate. Half the render
# load is also half the heat, and the Pi throttles together with teleop.
FPS = 30
IDLE_FPS = int(os.environ.get("PNP_IDLE_FPS", "15"))
                     # half of FPS, so the cadence stays even.
                     # The idle screen changes twice a second -- anything
                     # more is six hours of heat for nothing.
                     # PNP_IDLE_FPS=30 lets the render path be measured under
                     # game-scene load, without anyone having to press a button.
# Default is the cabinet. For development and remote maintenance over SSH,
# the three can be switched via environment variable without editing the
# file (otherwise the next git pull would overwrite the local change):
#   PNP_FULLSCREEN=0  window instead of fullscreen
#   PNP_CAMERA=0      FakeDetector, no camera access
#   PNP_FPSLOG=1      frame rate once a second on stdout
#   PNP_VSYNC=0       without vsync, costs tearing
#
# On the Mac the defaults are those of the dev machine: window, no GPIO
# buttons (arrow keys), the built-in webcam in both panes. No separate
# branch -- that would drift away from the cabinet. The cabinet is Linux, so
# none of this changes anything there.
MAC        = sys.platform == "darwin"
FULLSCREEN = os.environ.get("PNP_FULLSCREEN", "0" if MAC else "1") != "0"
FPSLOG     = os.environ.get("PNP_FPSLOG") == "1"
# Measured to cost 12 to 19% at 60 Hz. At 30 fps the budget is there, and
# tearing running through a pixel font is visible instantly from 8 m. Stays on.
VSYNC      = os.environ.get("PNP_VSYNC", "1") != "0"

# OpenCV threads for remap and multiply in the render path. Three, not four:
# the fourth core belongs to the teleop process (CPUAffinity=3 in its unit).
# Without this line OpenCV grabs all cores and crowds out exactly the loop
# that's the only one on a deadline.
CV_THREADS = int(os.environ.get("PNP_CV_THREADS", "3"))

# The one line that says what the four buttons do -- in the same place in
# every scene. Scene content ends above SAFE_BOTTOM, so a growing list
# (leaderboard from the DB) never runs into the footer.
# Distance from the bottom edge, not a fraction of the height: the band is a
# fixed row at the screen edge, it doesn't scale along. 80 and 160 like
# before at 1200.
FOOTER_Y    = 1000
SAFE_BOTTOM = 920

# ── Timing (seconds) ──────────────────────────────────────────────────────
WARN_SECONDS  = 5     # from here on the screen tints
IDLE_TIMEOUT  = 20    # non-idle scenes fall back on their own
CONFIRM_SECONDS = 3   # window for the double-confirm to abort
# ROUND_SECONDS and PERFECT_HOLD depend on difficulty and therefore live in
# the game mode section further below, not here.

# ponytail: >-taps during the round that end it immediately. 0 = off (cabinet)
CHEAT_TAPS = 5

# ── Theme ─────────────────────────────────────────────────────────────────
# Colors, texts, sprites, LED colors, and which sprite belongs to which
# marker live in ONE file: themes/<name>.py. Switch without a code change:
#   PNP_THEME=pcb uv run game/main.py
# The names below are the contract -- every theme supplies exactly these,
# and `uv run game/sprites.py` checks that for every file in themes/.
# New theme: copy sugar_rush.py, the file's header says what to do.
THEME = os.environ.get("PNP_THEME", "sugar_rush")
THEME_KEYS = ("BG", "GREY", "WHITE", "ACCENT", "CANDY", "HOWTO",
              "LED_A", "LED_B", "BASE", "SHAPES", "SPRITES", "SPRITE")
_theme = importlib.import_module(f"themes.{THEME}")
(BG, GREY, WHITE, ACCENT, CANDY, HOWTO,
 LED_A, LED_B, BASE, SHAPES, SPRITES, SPRITE) = (getattr(_theme, k) for k in THEME_KEYS)

# ── Colors ────────────────────────────────────────────────────────────────
# Six colors as a ladder from quiet to loud, each with exactly one job:
#   BG base · GREY labels · WHITE neutral values · ACCENT what the visitor
#   influences (all four from the theme) · ORANGE warning · RED the final
#   seconds. These two stay HPI regardless of theme:
ORANGE = (222, 98, 7)       # HPI #DE6207
RED    = (177, 7, 58)       # HPI #B1073A

# The colors of the four arcade buttons. Their own ladder, deliberately kept
# apart from the one above: they say nothing about game state, only which
# *physical* button is meant. That's why they appear in exactly one place --
# the footer band, the one row that never carries a game value. That keeps
# the rule "one color, one job" intact. Since ACCENT is pink, yellow now
# appears only on the button at all.
BTN_GREEN  = (0, 208, 96)     # right -- forward, confirm
BTN_RED    = (255, 72, 72)    # left  -- back, cancel
BTN_BLUE   = (64, 156, 255)   # up
BTN_YELLOW = (255, 200, 0)    # down
# BTN_RED is noticeably lighter than RED, and that's not taste: in the last
# five seconds the background tints toward RED, and a glyph in the same tone
# would then disappear exactly where "CANCEL" is most needed.

# ── Font ──────────────────────────────────────────────────────────────────
# Press Start 2P (SIL OFL, lives in assets/). 8x8 grid: size / 8 is the edge
# length of one glyph pixel, so all sizes are divisible by 8 -- otherwise the
# pixels within a glyph would come out unevenly sized.
# Path from __file__, not relative to cwd: the systemd start has a different one.
FONT_PATH  = os.path.join(os.path.dirname(__file__), "assets",
                          "PressStart2P-Regular.ttf")
# "title" only for PICK'N'PLAY: 11 glyphs at 168 are 1848 of 1920 px, no margin left.
FONT_SIZES = {"big": 168, "title": 144, "mid": 88, "small": 48, "tiny": 32}

# ── CRT overlay ───────────────────────────────────────────────────────────
# PNP_CRT=0 and PNP_BARREL=0 turn the two off for measuring, without touching
# the file. Meant for A/B runs on the Pi, the cabinet uses the defaults.
CRT            = os.environ.get("PNP_CRT", "1") != "0"
SCANLINE_STEP  = 3     # darken every third row
SCANLINE_ALPHA = 60    # tune at the venue, lower it if in doubt
VIGNETTE_ALPHA = 90    # darkening in the corners
BARREL_K       = float(os.environ.get("PNP_BARREL", "0.05"))
                       # distortion of the scanlines and nothing more: they
                       # curve as if on a tube and draw together toward the
                       # edge. Costs nothing at runtime, the map is built at
                       # startup. 0 = horizontal lines.
                       # The image itself is no longer warped, see
                       # crt_gain() in app.py

# ── Sound ─────────────────────────────────────────────────────────────────
# The music briefly ducks under every effect. On real arcade hardware that
# happened by itself: NES and C64 had four to five voices, and an effect
# took one of them. Here it's a channel volume, softer.
DUCK         = 0.55   # music level during an effect (~-5 dB)
DUCK_RELEASE = 0.35   # seconds back to full

# ── Game values ───────────────────────────────────────────────────────────
# marker_id -> price in 10-CENT UNITS. Changeable without a code change,
# that's the whole reason for ArUco instead of a trained model.
#
# Why not in cents: the prices need to be coprime (gcd 1). Round prices
# computed in cents would have gcd 10, which would make the game binary --
# a distance would either be divisible by the divisor and then reachable in
# a single move, or not reachable at all. There would be no "just off", and
# without that no leaderboard with resolution, just a list of zeros and
# impossibilities.
#
# In 10-cent units, 1.40 / 1.70 / 2.10 ... are coprime and still look like
# prices. Everything is computed in units throughout, division happens only
# at display time -- exactly once, in euro() in scenes.py.
#
# Exactly one marker per physical cupcake. ArucoDetector.marks is a dict
# keyed by ID -- two cupcakes with the same marker count once, and that
# would be a silent scoring bug that looks like a detection problem on show day.
VALUES = {0: 14, 1: 17, 2: 21, 3: 24, 4: 28,
          5: 32, 6: 36, 7: 41, 8: 46, 9: 52}
CENTS  = 10        # one VALUES step in cents. Only read by euro().

# ── Game mode ─────────────────────────────────────────────────────────────
# Everything that makes a round easier or harder lives here as a number --
# and only here. A hard mode is thus just another entry in MODES, no code
# change, and round length can be tried out without touching the file:
#
#   PNP_MODE=hard uv run game/main.py          whole set
#   PNP_ROUND_SECONDS=20 uv run game/main.py   single value, beats the set
#
# Adding a mode here changes numbers, not behavior. A mode that needs more
# (FPV, an opponent) gets its seam where it needs it -- a speculative
# interface would guess the wrong place.
#
# ROUND_SECONDS  round length. 30 instead of 60 since the scoring meeting:
#                double throughput at the booth, and perfect becomes rare
#                enough that the 1000 means something.
# PERFECT_HOLD   how long the total has to be right before the round ends
#                early. The old 5 s would be a sixth of the round at 30 s.
#                MARKER_HOLD is enough against flicker anyway.
# GAP_MOVES      how many moves the perfect solution may cost. A
#                teleoperated pick takes 10-20 s -- at 30 s round time, three
#                moves would be a promise the arm can't keep.
# GAP_MIN/MAX    band the distance to the target may fall in. Not the
#                binding dial, see GAP_ONE_MAX.
# GAP_ONE_MISS   how far off the best SINGLE move must be at minimum.
#                Without this lower bound a lucky grab wins, and that's a
#                raffle, not a task.
# GAP_ONE_MAX    ... and at most this far off. The binding dial for variety:
#                on an empty tray, 15 (EUR 1.50) leaves exactly 14 possible
#                targets for the whole show day, 25 leaves 21. Measured with
#                this price set, the self-test in balance.py prints the
#                number on every run.
MODES = {
    "normal": dict(ROUND_SECONDS=30, PERFECT_HOLD=3.0, GAP_MOVES=2,
                   GAP_MIN=25, GAP_MAX=98, GAP_ONE_MISS=2, GAP_ONE_MAX=25),
}
MODE = os.environ.get("PNP_MODE", "normal")


def _mode(key):
    """Value from the active mode, overridable via PNP_<KEY>.

    The type comes from the entry, not from the environment: PNP_PERFECT_HOLD=2.5
    thus stays a float and PNP_GAP_MOVES=3 becomes an int, without having to
    maintain a table of types here.
    """
    default = MODES[MODE][key]
    return type(default)(os.environ.get("PNP_" + key, default))


ROUND_SECONDS = _mode("ROUND_SECONDS")
PERFECT_HOLD  = _mode("PERFECT_HOLD")
GAP_MOVES     = _mode("GAP_MOVES")
GAP_MIN       = _mode("GAP_MIN")
GAP_MAX       = _mode("GAP_MAX")
GAP_ONE_MISS  = _mode("GAP_ONE_MISS")
GAP_ONE_MAX   = _mode("GAP_ONE_MAX")

# ── Scoring ───────────────────────────────────────────────────────────────
# The score goes up to 1000 like on a boxing machine: two parts, and the
# second is only there for those who were perfect. Formula and rationale
# live in balance.py at points().
SCORE_MAX  = 900   # for accuracy alone
SCORE_TIME = 100   # time bonus on top, together 1000
SCORE_CURVE = 2    # exponent. 1 = linear, 2 spreads out the range people
                   # actually land in. A knob to turn if it looks too harsh
                   # at the cabinet.

# ── Intermission scene ────────────────────────────────────────────────────
# The idle screen is silent, the music starts here. Six hours of chiptune as
# a constant backdrop is exhausting -- and it marks nothing. With a silent
# idle, the music kicking in becomes the signal "it's starting".
DEMO_VIDEO = None            # path to the clip. None = text only, scene still runs
DEMO_SIZE  = (1024, 576)     # 16:9 -- a different ratio distorts, like with CAM_VIEW
# HOWTO lives in the theme.

# ── Persistence ───────────────────────────────────────────────────────────
DB_PATH = "scores.db"
TOP_N   = 10

# ── Input ─────────────────────────────────────────────────────────────────
# Four arcade buttons, nothing else. Convention throughout the game:
#   right   = forward / confirm
#   left    = back / cancel
#   up/down = select
KEYMAP = {
    pygame.K_UP:   "up",   pygame.K_DOWN:  "down",
    pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    pygame.K_q:    "quit",   # ponytail: development only, doesn't exist on the cabinet
}

# The physical button behind each direction, as a color and as a glyph. The
# hint line tints each arrow with it, and that's the whole instruction
# manual: the visitor looks for the color, not the direction. Green = go,
# red = back are the only two color meanings everyone already knows; blue
# and yellow are free and so simply up and down.
BUTTON_COLORS = {"up": BTN_BLUE, "down": BTN_YELLOW,
                 "left": BTN_RED, "right": BTN_GREEN}
ARROWS = {"▲": "up", "▼": "down", "◀": "left", "▶": "right"}

# Holding scrolls through the letters: (delay, repeat rate) in ms
KEY_REPEAT = (400, 60)

# ── Hardware ──────────────────────────────────────────────────────────────
CAMERA        = os.environ.get("PNP_CAMERA", "1") != "0"   # 0 = FakeDetector
# (arm camera, top-down). Same index twice = one webcam in both panes,
# that's the layout mock.
# The detector always attaches to the second, the top-down, camera.
#
# On the cabinet (checked against the image on 2026-09-09, not guessed):
# video0 sits on the side and rotated 90 degrees on the arm, video2 looks
# straight down onto the tray.
# NOT (0, 1): video1 and video3 are metadata nodes and deliver no image.
CAM_INDEXES   = (0, 0) if MAC else (0, 2)
CAM_SIZE      = (1280, 720)
# 768 x 432 is exactly 16:9 (768 * 9/16 = 432) — a different ratio distorts.
# Twice the area of the earlier 544 x 306: the player steers the arm by these
# images, so they get priority. The instruction sits above, the bar below,
# the timer pie in the 192 px gap between the two.
CAM_VIEW      = (768, 432)
CAM_POS       = ((480, 486), (1440, 486))   # centers, left is the arm
MARKER_HOLD   = 0.5    # hysteresis: marker keeps counting while occluded for less than this
DETECT_HZ     = 15     # detection rate, decoupled from the 60 FPS
# Detection window of the top-down camera, as fractions (x, y, width, height).
# The wide-angle lens otherwise sees half the booth; only what's inside this
# window is detected. The rectangle is drawn into the image, so it's set in
# the hall while aligning the camera and the result is visible immediately.
TRAY_ROI      = (0.20, 0.15, 0.60, 0.70)
MARK_FONT     = "tiny"    # font size of the overlaid prices. Currently read
                          # by nothing: the overlay has been commented out
                          # since 2026-09-11, because the prices are meant to
                          # stay hidden during the round. Kept here so that
                          # uncommenting it in GameScene.overlay stays a
                          # one-line change -- when aligning the camera you
                          # want to see WHICH marker it detects.
MARK_WIDTH    = 5         # line width of the detection window
# ── Buttons ───────────────────────────────────────────────────────────────
# BCM numbers, not header pins. Wired like this since 2026-09-11: header
# 22 · 24 · 26 · 28 are GPIO 25 · 8 · 7 · 1, common ground at header 30. One
# row, one connector.
#
# Two of these used to be listed as taken and no longer are:
#   1          ID_SC of the HAT EEPROM. Only read at boot, a normal pin
#              afterward. Don't hold the button down while powering on.
#   7, 8       CE1/CE0 of SPI0. That's why SPI0 must NOT be enabled
#              (dtparam=spi=on), otherwise the kernel claims the pins and
#              gpiozero reports "GPIO busy". The strip runs over SPI5, see below.
#
# Buttons against GND, internal pull-up, pressed = LOW. No resistor, no
# capacitor: debouncing is done by gpiozero.
#
# The emergency stop is NOT here. It sits in the servo power supply and cuts
# 12 V. An emergency stop that has to go through Python first isn't one.
BUTTON_PINS   = {25: "up", 1: "down", 7: "left", 8: "right"}   # blue, yellow, red, green
# Like CAMERA: default is the cabinet, PNP_BUTTONS=0 for developing without GPIO.
BUTTONS       = os.environ.get("PNP_BUTTONS", "0" if MAC else "1") != "0"

# ── LED strip ─────────────────────────────────────────────────────────────
# WS2812 protocol over SPI5, data on GPIO 14 (header 8). The RP1 on the Pi 5
# routes SPI5-MOSI out there (dtoverlay=spi5-1cs-pi5, also occupies 12, 13,
# 15), so the driver stays the same as on SPI0. GPIO 14 is otherwise UART0
# with the boot console: that has to be off, or kernel messages come out as
# colors. Setup in docs/operation.md. If the device is missing (Mac, SPI
# off), the LEDs stay silent -- like Music without an audio device.
LED_DEV     = "/dev/spidev5.0"
# Count and brightness via environment, so the first test on the strip needs
# no file change on the Pi: PNP_LED_COUNT=60 PNP_LED_BRIGHT=0.1
LED_COUNT   = int(os.environ.get("PNP_LED_COUNT", 480))   # ponytail: guessed, 3 m x 160/m
LED_ORDER   = "GRB"   # WS2812B. WS2811 strips (12/24 V) are often RGB -- check on the strip
LED_BRIGHT  = float(os.environ.get("PNP_LED_BRIGHT", 0.3))
                      # power budget: 3 m FCOB at full white ~8.5 A at 5 V.
                      # That's a PSU and heat question in one number, not taste.
LED_FPS     = 30
LED_STRIPES = 24      # candy-cane stripes across the full length, density-independent
# LED_A / LED_B (candy cane, bar) come from the theme; red stays HPI:
LED_RED     = (255, 0, 20)
