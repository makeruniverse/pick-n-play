import os
import pygame

# ── Display ────────────────────────────────────────────────────────────────
# Design resolution = native panel resolution of the Asus 15" display (16:10).
# Every coordinate in scenes.py is defined against this raster.
# pygame.SCALED handles different panel sizes without changing constants here.
WIDTH, HEIGHT = 1920, 1200
FPS = 60
IDLE_FPS = int(os.environ.get("PNP_IDLE_FPS", "20"))
                     # the Idle screen changes twice per second. 60 Hz
                     # six hours at 60 Hz would only create heat for no gain.
                     # PNP_IDLE_FPS=60 measures render cost at game-scene load
                     # without anyone having to touch a button.
# Default behavior is kiosk mode. For development and remote SSH support,
# switch these with environment variables instead of editing this file
# (otherwise the next git pull may overwrite local tweaks):
#   PNP_FULLSCREEN=0  windowed mode instead of fullscreen
#   PNP_CAMERA=0      FakeDetector, no camera access
#   PNP_FPSLOG=1      frame rate once per second on stdout
FULLSCREEN = os.environ.get("PNP_FULLSCREEN", "1") != "0"
FPSLOG     = os.environ.get("PNP_FPSLOG") == "1"

# The one line that says what the four buttons do -- in every scene
# the same place. Scene content ends above SAFE BOTTOM so that a
# growing list (best list from the DB) never goes into the footer.
FOOTER_Y    = 1120
SAFE_BOTTOM = 1040

# ── Timing (seconds) ──────────────────────────────────────────────────────
ROUND_SECONDS = 60
WARN_SECONDS  = 5     # from here the screen fades
IDLE_TIMEOUT  = 20    # Non-Idle scenes fall by themselves
CONFIRM_SECONDS = 3   # Window for the demolition double confirmation
PERFECT_HOLD  = 5.0   # as long as OFF BY 0 has to stand, then the round is over

# ponytail: >-Taps in the round that they end immediately. 0 = from (Automat)
CHEAT_TAPS = 5

# ── Colors ────────────────────────────────────────────────────────────────
# Black background, high contrast, HPI red and orange directly from the logo.
# Six colors as ladder from quiet to loud, each with exactly one job:
BLACK  = (0, 0, 0)          # reason, always
GREY   = (120, 120, 120)    # Beschriftungen
WHITE  = (240, 240, 240)    # neutrale Werte
YELLOW = (255, 200, 0)      # what the visitor has just influenced
ORANGE = (222, 98, 7)       # Warnung          (HPI #DE6207)
RED    = (177, 7, 58)       # the last seconds (HPI #B1073A)
# YELLOW is brighter than the HPI yellow #F7A900 — on black wins from 8 m
# the brighter, and compared to the logo you do not see the difference.

# ── Schrift ───────────────────────────────────────────────────────────────
# Press Start 2P (SIL OFL, is in assets/). 8x8-Raster: Groesse / 8 is the
# Edges of a glyph pixel, therefore all seams can be divided by 8
# — otherwise the pixels within a glyph become unevenly large.
# Path from   file  , not relative to cwd: the systemd start has another.
FONT_PATH  = os.path.join(os.path.dirname(__file__), "assets",
                          "PressStart2P-Regular.ttf")
FONT_SIZES = {"big": 168, "mid": 88, "small": 48, "tiny": 32}

# ── CRT-Overlay ───────────────────────────────────────────────────────────
# PNP CRT=0 and PNP BARREL=0 turn off the two to measure without the file
# to touch. Designed for A/B load on the Pi, the machine takes the defaults.
CRT            = os.environ.get("PNP_CRT", "1") != "0"
SCANLINE_STEP  = 3     # each third row darken
SCANLINE_ALPHA = 60    # in the hall, in doubt down
VIGNETTE_ALPHA = 90    # Abdunklung in den Ecken
BARREL_K       = float(os.environ.get("PNP_BARREL", "0.05"))
                       # Wooling. 0 only switches it off, scanlines remain —
                       # this is the expensive post if the Pi does not come

# ── Sound ─────────────────────────────────────────────────────────────────
# The music goes short under any effect. On real arcade hardware
# this happened by itself: NES and C64 had four to five voices, and one
# Effect has taken one of them. Here it is a channel volume, softer.
DUCK         = 0.55   # Music level during an effect (~-5 dB)
DUCK_RELEASE = 0.35   # seconds back to full

# ── Spielwerte ────────────────────────────────────────────────────────────
# marker id -> point value. Changeable without code change, this is the whole
# Reason for ArUco instead of a trained model.
#
# Just one marker per physical puck. ArucoDetector.marks is a dict with
# the ID as a key -- two pucks with the same marker will steal once, and
# that would be a silent evaluation error that looks like a detection problem.
#
# Values without common dividers (ggT 1). Were they like fruits all by 5
# the game binaer: distance divided by 5 -> a puck genuegt,
# otherwise not accessible. Measured above the distances 30..120 were from
# 76 distances, which does not create a single train, can only be praised 4 in two trains.
# With this sentence there are 71 out of 74 -- only with that there is "nappily next".
VALUES = {0: 4, 1: 7, 2: 12, 3: 18, 4: 23,
          5: 29, 6: 36, 7: 44, 8: 53, 9: 67}

# The target value is not picked freely; it is chosen as a distance from the
# current tray sum (see balance.py). Otherwise luck decides whether someone
# must bridge 3 or 200 points, and the leaderboard compares unfair rounds.
GAP_MIN, GAP_MAX = 25, 130
GAP_MOVES    = 3   # perfect solutions may take up to this many moves
GAP_ONE_MISS = 2   # best single move must be at least this far away
GAP_ONE_MAX  = 15  # ... and at most this far away; otherwise one round can
                   # be almost solved after one move while the next remains far off

# ── Intermission scene ────────────────────────────────────────────────────
# The Idle screen is mute, the music fades here. Six hours Chiptune
# as permanent carpets are exhausting -- and they do not mark anything. With silent
# Idle will use the music to the signal "it's going on".
DEMO_VIDEO = None            # Path to demo clip. None = text-only scene
DEMO_SIZE  = (1120, 630)     # 16:9 -- other ratio distorted as with CAM VIEW
HOWTO = ("EVERY PUCK HAS A HIDDEN PRICE",
         "MOVE THEM UNTIL TOTAL MEETS GOAL",
         "60 SECONDS. CLOSEST WINS.")

# ── Persistenz ────────────────────────────────────────────────────────────
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
    pygame.K_q:    "quit",   # ponytail: only development, there is not this at the machine
}

# Keep scrolling through the letters: (zogulation, repetition rate) in ms
KEY_REPEAT = (400, 60)

# ── Hardware ──────────────────────────────────────────────────────────────
CAMERA        = os.environ.get("PNP_CAMERA", "1") != "0"   # 0 = FakeDetector
# (Arm camera, top down). twice the same index = a webcam in both
# Panes, this is the layout dock.
# The detector always hits the second, the top down camera.
#
# At the machine (9.9.2026 in the picture, not guessed): video0 stands sideways
# and turned by 90 degrees on arm, video2 looks perpendicular to the tray.
# NOT (0, 1): video1 and video3 are metadata nodes and do not provide a picture.
CAM_INDEXES   = (0, 2)
CAM_SIZE      = (1280, 720)
CAM_VIEW      = (880, 495)     # 16:9 wie CAM_SIZE — andere Ratio verzerrt
CAM_POS       = ((490, 740), (1430, 740))   # Centers, left arm
MARKER_HOLD   = 0.5    # Hysteresis: marker is kept while occluded briefly
DETECT_HZ     = 15     # Erkennungsrate, entkoppelt von den 60 FPS
# Detection window of the top down camera, as components (x, y, broad, hoehe).
# The wide-angle lens otherwise sees half the booth; is recognized only,
# what's in here. The rectangle is drawn into the picture, so you put it
# it in the hall when aligning the camera and immediately sees the result.
TRAY_ROI      = (0.20, 0.15, 0.60, 0.70)
MARK_FONT     = "small"   # font size of the hidden values
MARK_WIDTH    = 5         # Strichstaerke des Detektionsfensters
BUTTON_PINS   = {17: "up", 27: "down", 22: "left", 23: "right"}
