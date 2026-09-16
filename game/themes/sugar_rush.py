"""Theme "Sugar Rush" -- sweets, value = price. Decided on 2026-09-11.

A theme is exactly this file. Everything that makes the machine look like
something lives here; scenes, LEDs, and tools read it via config.py and don't
know the theme's name. New theme (say, PCB components):

    1. Copy the file: themes/pcb.py
    2. Swap colors, texts, sprites, SPRITE mapping
    3. PNP_THEME=pcb uv run game/main.py        (default is in config.py)
    4. uv run game/sprites.py                   checks every theme in themes/

Not here, because they don't belong to the theme: RED/ORANGE (HPI logo), the
button colors (physical buttons), VALUES (scoring), the title PICK'N'PLAY.
"""

# ── Screen ────────────────────────────────────────────────────────────────
# Chocolate background instead of black, pink instead of yellow, cream instead
# of white. The background is dark enough that contrast stays the same as on
# black (label text 5.4 : 1). The jobs apply to every theme -- a new one swaps
# the colors, not the roles:
BG     = (40, 16, 32)       # background, always
GREY   = (176, 128, 158)    # labels
WHITE  = (255, 236, 246)    # neutral values
ACCENT = (255, 101, 189)    # what the visitor is currently affecting
# Check for every new theme: ACCENT on RED (final seconds). Here it's only
# 2.7 : 1, so GameScene.acc() switches to WHITE there.

# Decoration for title and sprinkles, never for game values. Bambu PLA Matte,
# so the screen shows the same colors as the printed objects.
CANDY = ((255, 101, 189),   # ACCENT
         (163, 216, 225),   # Ice Blue     #A3D8E1
         (247, 217, 89),    # Lemon Yellow #F7D959
         (194, 225, 137),   # Apple Green  #C2E189
         (232, 175, 207))   # Sakura Pink  #E8AFCF

# {secs} is filled in by the scene from the game mode -- the round length gets
# tried out and must not be frozen into a theme.
# The tray starts empty: it's built up, not rearranged.
HOWTO = ("EVERY TREAT HAS A HIDDEN PRICE",
         "FILL THE TRAY TO MATCH THE GOAL",
         "{secs} SECONDS. CLOSEST WINS.")

# ── LED strip ─────────────────────────────────────────────────────────────
# The candy cane's two stripe colors (idle/score) and the round's bar color
# (A). LEDs, not screen: red dominates there, otherwise pink turns purple.
LED_A = (255, 40, 120)
LED_B = (255, 255, 255)

# ── Sprites ───────────────────────────────────────────────────────────────
# 16 x 16, notated as text. One shape, several palettes. Letters:
#   k outline   a main color   b highlight   c batter/cup   d second layer
#   r cherry/jam   w white   y m sprinkles   e plate
SHAPES = {
    "cupcake": (
        "......kkkk......",
        ".....krrrrk.....",
        ".....krwrrk.....",
        "......kkkk......",
        "....kkaaaakk....",
        "...kabbaaaaak...",
        "..kabaaayaaaak..",
        "..kaaamaaaawak..",
        ".kaawaaaaaaaaak.",
        ".kaaaaayaaamaak.",
        "kkkkkkkkkkkkkkkk",
        ".kcdcdcdcdcdcdk.",
        ".kcdcdcdcdcdcdk.",
        "..kcdcdcdcdcdk..",
        "..kcdcdcdcdcdk..",
        "...kkkkkkkkkk...",
    ),
    "slice": (
        "................",
        "...........kk...",
        "..........krrk..",
        "..........krwk..",
        "......kkkkkkkkk.",
        "....kkaaaaaaaak.",
        "..kkabaaaaaaaak.",
        "kkaaaaaaaaaaaak.",
        "kaaaaaaaaaaaaak.",
        "kacaacaaacaacak.",
        "kccccccccccccck.",
        "kccccccccccccck.",
        "kdddddddddddddk.",
        "kccccccccccccck.",
        "kccccccccccccck.",
        "kkkkkkkkkkkkkkk.",
    ),
    "donut": (
        "................",
        ".....kkkkkk.....",
        "...kkaaaaaakk...",
        "..kabaaamaaaak..",
        ".kabaayaaaawaak.",
        ".kaaaakkkkaaaak.",
        "kawaak....kayaak",
        "kaaaak....kaaaak",
        "kamaak....kaawak",
        "kaaaak....kaaaak",
        ".kaaaakkkkaaaak.",
        ".kaamaaaaayaaak.",
        "..kaaaaaaaaddk..",
        "...kkddaaddkk...",
        ".....kkkkkk.....",
        "................",
    ),
    "macaron": (
        "................",
        "................",
        "................",
        "...kkkkkkkkkk...",
        "..kaaaaaaaaaak..",
        ".kabaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        ".kkkkkkkkkkkkkk.",
        "..kcccccccccck..",
        ".kkkkkkkkkkkkkk.",
        ".kaaaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        "..kaaaaaaaaaak..",
        "...kkkkkkkkkk...",
        "................",
        "................",
    ),
    "bonbon": (
        "................",
        "................",
        "................",
        "................",
        "kk....kkkk....kk",
        "kdk..kaaaak..kdk",
        "kddkkabaaaakkddk",
        "kdddkaawaaakdddk",
        "kdddkawaaaakdddk",
        "kddkkaaaaaakkddk",
        "kdk..kaaaak..kdk",
        "kk....kkkk....kk",
        "................",
        "................",
        "................",
        "................",
    ),
    "cake": (
        ".......yy.......",
        ".......yy.......",
        ".......ww.......",
        ".......ww.......",
        "..kkkkkkkkkkkk..",
        ".kaaaaaaaaaaaak.",
        "kabaamaaaayaaaak",
        "kacaacaaacaacaak",
        "kcccccccccccccck",
        "kddddddddddddddk",
        "kcccccccccccccck",
        "kcccccccccccccck",
        "kddddddddddddddk",
        "kcccccccccccccck",
        "kkkkkkkkkkkkkkkk",
        ".eeeeeeeeeeeeee.",
    ),
    "petitfour": (
        "................",
        "................",
        "......kkkk......",
        ".....kwyywk.....",
        "..kkkkkwwkkkkk..",
        ".kbbaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        ".kkkkkkkkkkkkkk.",
        ".kaaaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        ".kddddddddddddk.",
        ".kaaaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        ".kaaaaaaaaaaaak.",
        ".kkkkkkkkkkkkkk.",
        "................",
    ),
    "bar": (
        "................",
        "................",
        "................",
        "kkkkkkkkkkkkkkkk",
        "kbckbckaaaaaaaak",
        "kcckcckaawwwwaak",
        "kkkkkkkaawyywaak",
        "kbckbckaawyywaak",
        "kcckcckaawwwwaak",
        "kkkkkkkaaaaaaaak",
        "kbckbckaaaaaaaak",
        "kcckcckaaaaaaaak",
        "kkkkkkkkkkkkkkkk",
        "................",
        "................",
        "................",
    ),
    "berliner": (
        "................",
        "................",
        "................",
        "................",
        "......kkkk......",
        "....kkwwwwkk....",
        "...kwwwbwwwwk...",
        "..kawwwwwwwwak..",
        ".kaaawwawwwaaak.",
        ".kaaaaaaaaaaaak.",
        "kaaaaaaaaaarraak",
        "kaaaaaaaaaarraak",
        ".kdaaaaaaaaaadk.",
        "..kddddddddddk..",
        "...kkkkkkkkkk...",
        "................",
    ),
}

# Bambu PLA Matte, hex from the official table. MILK is the exception:
# Dark Chocolate #4D3324 disappears on the screen's chocolate background,
# so a lighter milk chocolate stands in for the same part there.
SAKURA, LEMON, ICE = (232, 175, 207), (247, 217, 89), (163, 216, 225)
APPLE, LILAC, SCARLET = (194, 225, 137), (174, 150, 212), (222, 67, 67)
IVORY, TAN, LATTE = (255, 255, 255), (232, 219, 183), (211, 183, 167)
CARAMEL, BONE, MILK = (174, 131, 91), (203, 198, 184), (128, 84, 60)

# Applies to every sprite, individual palettes override it.
BASE = dict(k=(18, 6, 14), w=IVORY, y=LEMON, m=ICE, r=SCARLET, e=BONE, b=IVORY)

SPRITES = {
    "cupcake_pink":   ("cupcake",   dict(a=SAKURA, c=ICE, d=(118, 176, 190))),
    "cupcake_lemon":  ("cupcake",   dict(a=LEMON, c=SAKURA, d=(196, 130, 168))),
    "cupcake_mint":   ("cupcake",   dict(a=APPLE, c=LILAC, d=(132, 108, 176))),
    "cupcake_choc":   ("cupcake",   dict(a=MILK, b=LATTE, c=TAN, d=CARAMEL)),
    "slice_straw":    ("slice",     dict(a=SAKURA, c=TAN, d=SCARLET)),
    "slice_choc":     ("slice",     dict(a=MILK, b=LATTE, c=CARAMEL, d=LATTE)),
    "slice_lemon":    ("slice",     dict(a=LEMON, c=TAN, d=IVORY)),
    "donut_pink":     ("donut",     dict(a=SAKURA, d=CARAMEL)),
    "donut_choc":     ("donut",     dict(a=MILK, b=LATTE, d=CARAMEL)),
    "macaron_pink":   ("macaron",   dict(a=SAKURA, c=IVORY)),
    "macaron_mint":   ("macaron",   dict(a=ICE, c=IVORY)),
    "macaron_lemon":  ("macaron",   dict(a=LEMON, c=IVORY)),
    "bonbon_red":     ("bonbon",    dict(a=SCARLET, d=ICE)),
    "bonbon_mint":    ("bonbon",    dict(a=APPLE, d=SAKURA)),
    "cake_straw":     ("cake",      dict(a=SAKURA, c=TAN, d=SCARLET)),
    "cake_choc":      ("cake",      dict(a=MILK, b=LATTE, c=CARAMEL, d=LATTE)),
    "petitfour_pink": ("petitfour", dict(a=SAKURA, d=ICE)),
    "petitfour_mint": ("petitfour", dict(a=ICE, d=SAKURA)),
    "bar_milk":       ("bar",       dict(a=SCARLET, c=MILK, b=LATTE)),
    "berliner":       ("berliner",  dict(a=CARAMEL, d=(140, 100, 66))),
}

# marker_id -> sprite. The screen must show the same thing that's on the
# tray -- otherwise the price reveal teaches the wrong association.
# ponytail: placeholder, cheap/light -> expensive/wobbly. Reassign once
# the printed objects are settled; one line per object. Donuts are missing
# on purpose: the hole cuts through the marker.
SPRITE = {0: "macaron_pink",   1: "bar_milk",      2: "petitfour_pink",
          3: "berliner",       4: "cupcake_pink",  5: "cupcake_lemon",
          6: "slice_straw",    7: "cake_choc",     8: "slice_choc",
          9: "cake_straw"}
