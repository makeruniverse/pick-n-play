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
# black (label text 5.0 : 1). The jobs apply to every theme -- a new one swaps
# the colors, not the roles:
BG     = (52, 22, 42)       # background, always. Was (40, 16, 32) until
                            # 2026-09-16, too dark on the cabinet panel
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

# ── Text ──────────────────────────────────────────────────────────────────
# Every word on the screen, in both languages. Scenes only name keys, so a
# third language or a reworded line never touches scenes.py. {name}, {no},
# {goal} ... are filled in by the scene. "|" splits a speech line into pages
# of the text box -- three lines of 30 glyphs each, the self-test in
# scenes.py checks every page.
#
# Uppercase only, like the rest of the screen. Press Start 2P has no capital
# ẞ (it draws the missing-glyph box), but its lowercase ß reads fine among
# capitals, so German keeps its ß: HEIßT, SÜßIGKEIT, GRÖßER.
#
# Written for the fair, not translated: each language says it the way a
# machine in that language would. No "--" in anything a visitor reads.
#
# The story: BELLA runs the bakery, OSKAR is the customer with a birthday
# and exactly that much money. Fictional on purpose -- a real person as the
# baker needs their okay first.
TEXT = {
    "en": dict(
        press="PRESS ▶", best="TODAY'S BEST", play="▶ PLAY",
        lang="▲ DEUTSCH", lang_ok="▲ NOCHMAL FÜR DEUTSCH",
        again="▼ PLAYED BEFORE?",
        ask_name="WHAT'S YOUR NAME?", which="WHICH {name} ARE YOU?",
        pick_abc="▲▼ PICK A LETTER", pick_no="▲▼ FIND YOURS",
        days=("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"),
        back="◀ BACK", next="▶ NEXT", done="▶ OK", unknown="NAME NOT FOUND",
        baker="BELLA", guest="OSKAR",
        hello="HI {name}! I'M BELLA. WELCOME TO MY LITTLE BAKERY!",
        help="SEE THE ARM IN FRONT OF YOU? MOVE IT, AND THE ROBOT COPIES "
             "EVERY MOVE.|"
             "EVERY TREAT HAS ITS PRICE. THE BIGGER IT IS, THE MORE IT COSTS.",
        welcome="{name}, YOU'RE BACK! READY TO BEAT YOUR SCORE?",
        practice="PRACTICE", tut_head="1 TREAT ON THE TRAY",
        tut="WARM-UP: PUT ANY TREAT ON THE TRAY, CODE FACING UP SO THE TOP CAMERA SEES IT.",
        tut_done="NICE! THAT ONE IS {price}. OH, HERE COMES A CUSTOMER!",
        skip="▶ SKIP", skip_ok="▶ AGAIN TO SKIP", quit="◀ QUIT", quit_ok="◀ AGAIN TO QUIT",
        order_head="BUDGET",
        order="HI! IT'S MY BIRTHDAY, AND I'VE GOT EXACTLY {goal}.|"
              "CAN YOU PICK ME TREATS THAT ADD UP TO EXACTLY {goal}?|"
              "THE CLOCK ISN'T RUNNING YET. DO THE MATH NOW: WHICH TREATS UP TOP MAKE {goal}?",
        go="▶ START", add="ADD", over="OVER BUDGET", hold="HANDS OFF! {n}",
        perfect="PERFECT", player="PLAYER #{no}",
        score="SCORE", rank="#{place} OF {count} TODAY",
        remember="WANT ANOTHER GO? JUST REMEMBER YOUR NUMBER: #{no}",
        react=("OH, THE TRAY IS STILL EMPTY. MAYBE NEXT TIME!",
               "THANKS! THAT'S A GOOD START.",
               "WOW, SO CLOSE! THANK YOU SO MUCH!",
               "SPOT ON! BEST BIRTHDAY EVER!"),
    ),
    "de": dict(
        press="DRÜCK ▶", best="DIE BESTEN VON HEUTE", play="▶ SPIELEN",
        lang="▲ ENGLISH", lang_ok="▲ AGAIN FOR ENGLISH",
        again="▼ SCHON GESPIELT?",
        ask_name="WIE HEIßT DU?", which="WANN WARST DU DA?",
        pick_abc="▲▼ BUCHSTABEN WÄHLEN", pick_no="▲▼ AUSWÄHLEN",
        days=("SO", "MO", "DI", "MI", "DO", "FR", "SA"),
        back="◀ ZURÜCK", next="▶ WEITER", done="▶ OK",
        unknown="NAME UNBEKANNT",
        baker="BELLA", guest="OSKAR",
        hello="HALLO {name}! ICH BIN BELLA. WILLKOMMEN IN MEINER BÄCKEREI!",
        help="SIEHST DU DEN ARM VOR DIR? WENN DU IHN BEWEGST, MACHT DER "
             "ROBOTER ALLES NACH.|"
             "JEDE SÜßIGKEIT HAT IHREN PREIS. JE GRÖßER, DESTO TEURER.",
        welcome="SCHÖN, DASS DU WIEDER DA BIST, {name}! KNACKST DU DEINEN "
                "REKORD?",
        practice="PROBERUNDE", tut_head="1 SÜßIGKEIT AUFLEGEN",
        tut="ZUM ÜBEN: LEG EINE SÜßIGKEIT AUFS TABLETT. CODE NACH OBEN "
            "ZUR KAMERA!",
        tut_done="SUPER! DIE KOSTET {price}. OH, DA KOMMT SCHON KUNDSCHAFT!",
        skip="▶ ÜBERSPRINGEN", skip_ok="▶ NOCHMAL ZUM ÜBERSPRINGEN",
        quit="◀ ABBRECHEN",
        quit_ok="◀ NOCHMAL ZUM ABBRECHEN",
        order_head="BUDGET",
        order="HALLO! ICH HAB HEUTE GEBURTSTAG UND GENAU {goal} DABEI.|"
              "SUCHST DU MIR SÜßIGKEITEN FÜR GENAU {goal} AUS?|"
              "NOCH LÄUFT KEINE ZEIT. RECHNE JETZT: WELCHE SÜßIGKEITEN OBEN ERGEBEN {goal}?",
        go="▶ LOS GEHT'S", add="ES FEHLEN NOCH", over="ÜBER BUDGET",
        hold="NICHT MEHR ANFASSEN! {n}",
        perfect="PERFEKT", player="SPIELER #{no}",
        score="PUNKTE", rank="PLATZ {place} VON {count} HEUTE",
        remember="LUST AUF NOCH EINE RUNDE? MERK DIR DEINE NUMMER: #{no}",
        react=("OH, DAS TABLETT IST JA NOCH LEER. VIELLEICHT NÄCHSTES MAL!",
               "DANKE! DAS IST SCHON MAL EIN ANFANG.",
               "WOW, FAST GENAU! VIELEN DANK!",
               "AUF DEN CENT GENAU! BESTER GEBURTSTAG ÜBERHAUPT!"),
    ),
}

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



def _sym(*halves):
    """32-wide rows from their left half, mirrored: faces stay symmetric and
    every row has to be counted to 16, not 32."""
    return tuple(h + h[::-1] for h in halves)


def _swap(rows, **by_row):
    """Copy of a shape with some rows replaced (r18=...). The three faces of
    a character share everything below the hat and above the collar."""
    rows = list(rows)
    for key, half in by_row.items():
        rows[int(key[1:])] = half + half[::-1]
    return tuple(rows)


def _poke(rows, *pixels):
    """Asymmetric pixels on top of a mirrored shape, e.g. one sweat drop."""
    rows = [list(r) for r in rows]
    for y, x, ch in pixels:
        rows[y][x] = ch
    return tuple("".join(r) for r in rows)


# 32 x 32, twice the treats' grid: a face needs eyes, cheeks and a mouth
# that can change, and at 16 that's three pixels. Letters on top of BASE:
#   s skin   h hair   c cheek   a hat / apron   d stripe   g shirt
#
# Both faces were reworked on 2026-09-24 ("they look like standard
# sprites"). Three changes, in order of effect:
#
#   1. Eyes 3 x 3 instead of 2 x 2, with a white pixel in the top outer
#      corner. Big eyes with a catchlight are the whole baby schema -- at
#      2 x 2 there's no room for one, and an eye without a highlight reads
#      as a printed dot rather than something looking back at you.
#   2. The skull loses its corners. Both heads were rectangles; the
#      outline now steps in twice at the top and twice at the chin, so
#      the silhouette reads round at 3 m.
#   3. The mouth shrinks from 10 px wide to 6 and moves a row down. The
#      old one was as wide as both eyes together, which is a grin, not a
#      face -- small mouth under big eyes is what makes it cute.
#
# The cheeks move below the eyes at the same time, because the eye's third
# row now sits where they used to be.
SHAPES["baker"] = _sym(
    "............kkkk",
    "......kkkk.kwwww",
    ".....kwwwwkwwwww",
    "....kwwwwwwwwwww",
    "....kwwwwwwwwwww",
    "....kwwwwwewwwww",
    "....kewwwwewwwww",
    ".....kwwwwewwwww",
    "......kwwwwwwwww",
    ".......kwwwwwwww",
    ".......keeeeeeee",
    ".......kkkkkkkkk",
    "......khhhhhhhhh",
    ".....khhssssssss",
    "....khhsssssssss",
    "....khhsswkkssss",
    "....khhsskkkssss",
    "....khhsskkkssss",
    "....khhccsssskss",
    "....khhssssssskk",
    ".....khhssssssss",
    "......khhkkkkkkk",
    "......kkk..kssss",
    ".....kkwwwwwwwww",
    "....kwwwwwwwwwww",
    "...kwwwwwwkaaaaa",
    "...kwwwwwwkaaaaa",
    "..kwwwwwwwkaaaya",
    "..kwwkwwwwkaaaaa",
    "..kwwkwwwwkaaaaa",
    "..ksskkwwwkaaaaa",
    "...kk..kkkkkkkkk",
)
# Mouth open, for every other beat while the text box types.
SHAPES["baker_talk"] = _swap(SHAPES["baker"],
                             r18="....khhccsssskkk",
                             r19="....khhsssssskrr",
                             r20=".....khhsssssskk")

SHAPES["guest"] = _sym(
    "..............ky",
    ".............kyy",
    ".............kaa",
    "............kaad",
    "............kdda",
    "...........kaadd",
    "...........kddaa",
    "..........kaaddd",
    "..........kdddaa",
    ".........kaaaddd",
    "........kkkkkkkk",
    ".......khhhhhhhh",
    "......khhhhhhhhh",
    ".....khhssssssss",
    ".....khsssssssss",
    "....kkhsswkkssss",
    "....kshsskkkssss",
    "....kkhsskkkssss",
    ".....khccsssskss",
    ".....khssssssskk",
    "......khssssssss",
    ".......kkkkkkkkk",
    "...........kssss",
    ".....kkggggkssss",
    "....kgggggggkkss",
    "...kgggggggggggg",
    "...kgggggggggggg",
    "..kggggkgggggggg",
    "..kggggkggggyggg",
    "..kggggkgggggggg",
    "..kssskkgggggggg",
    "...kkk.kkkkkkkkk",
)
# Over the target: worried brows, mouth turned down, one sweat drop.
SHAPES["guest_sweat"] = _poke(_swap(SHAPES["guest"],
                                    r14=".....khsssskksss",
                                    r18=".....khccssssskk",
                                    r19=".....khsssssskss"),
                              (10, 28, "k"), (11, 27, "k"), (11, 28, "m"),
                              (11, 29, "k"), (12, 26, "k"), (12, 27, "m"),
                              (12, 28, "w"), (12, 29, "m"), (12, 30, "k"),
                              (13, 27, "m"), (13, 28, "m"), (13, 29, "m"),
                              (13, 30, "k"), (14, 27, "k"), (14, 28, "k"),
                              (14, 29, "k"))
# Perfect: happy ^ ^ eyes and a big open smile.
SHAPES["guest_joy"] = _swap(SHAPES["guest"],
                            r15="....kkhsssksssss",
                            r16="....kshsskskssss",
                            r17="....kkhsssssskkk",
                            r18=".....khccsssskrr",
                            r19=".....khsssssskkk")

# Reworked on 2026-09-24 along with the faces. The old one had a 2 px
# needle for a top point and legs that ended in a stump -- pointy where
# everything else on this screen is round. Now: a blunt 4 px tip, a wider
# neck, legs that taper over three rows, and the highlight as a 2 x 2 blob
# instead of a one-pixel diagonal, so it reads as a glint at 6 x scale.
# The tray the arm drops a treat into, on the story screen. Not a treat,
# so it lives outside SPRITES and never rides the idle belt. Aligned to the
# top of its box: the rim starts on the first row, so a treat box set
# directly above it is lying in it and not floating.
#
# The arm that reaches into it is no longer a grid at all -- it is drawn
# from the real SO-101 CAD, see arm.py.
SHAPES["tray"] = (
    "kkkkkkkkkkkkkkkk",
    "keeeeeeeeeeeeeek",
    "keeeeeeeeeeeeeek",
    "kkeeeeeeeeeeeekk",
    ".kkeeeeeeeeeekk.",
    "..kkeeeeeeeekk..",
    "...kkkkkkkkkk...",
) + ("................",) * 9

SHAPES["star"] = (
    "......kaak......",
    ".....kaaaak.....",
    ".....kaaaak.....",
    "....kaaaaaak....",
    "kkkkkaaaaaakkkkk",
    "kaaaabbaaaaaaaak",
    ".kaaabbaaaaaaak.",
    "..kaaaaaaaaaak..",
    "...kaaaaaaaak...",
    "...kaaaaaaaak...",
    "..kaaaaaaaaaak..",
    "..kaaaakkaaaak..",
    ".kaaaak..kaaaak.",
    ".kaaak....kaaak.",
    ".kkk........kkk.",
    "................",
)

# Bambu PLA Matte, hex from the official table. MILK is the exception:
# Dark Chocolate #4D3324 disappears on the screen's chocolate background,
# so a lighter milk chocolate stands in for the same part there.
SAKURA, LEMON, ICE = (232, 175, 207), (247, 217, 89), (163, 216, 225)
APPLE, LILAC, SCARLET = (194, 225, 137), (174, 150, 212), (222, 67, 67)
IVORY, TAN, LATTE = (255, 255, 255), (232, 219, 183), (211, 183, 167)
CARAMEL, BONE, MILK = (174, 131, 91), (203, 198, 184), (128, 84, 60)
STEEL = (86, 74, 92)        # the arm's servos, the only non-sweet colour

# The six spools the expo set is printed from (2026-09-25). SCARLET above is
# already Matte Scarlet Red, so it serves twice. These four are PLA Basic and
# therefore glossy -- the only reason that matters is the top-down camera, see
# the marker note in tools/voxel.py.
HOT_PINK, PURPLE = (236, 0, 140), (94, 67, 183)
BLUE, GRASS, YELLOW = (0, 134, 214), (97, 198, 128), (244, 238, 42)

# The robot, printed plate and servo. Its own key because arm.py draws from
# CAD instead of a grid, so it has no SPRITES entry to carry a palette. No
# pink in it: ACCENT means "what the visitor is affecting right now"
# everywhere else, and the arm only copies, it never signals.
# The plate is the real arm's translucent blue PLA, sampled from a photo
# (2026-09-28), so the screen shows the machine next to the visitor.
ARM = ((84, 124, 234), STEEL)

# Applies to every sprite, individual palettes override it.
BASE = dict(k=(18, 6, 14), w=IVORY, y=LEMON, m=ICE, r=SCARLET, e=BONE, b=IVORY)


def _mix(c, f):
    """Same hue, f times as bright. f > 1 blends toward white instead of
    multiplying: a saturated blue has a zero channel, and scaling it up would
    leave a highlight that never lightens."""
    if f <= 1:
        return tuple(round(v * f) for v in c)
    return tuple(round(v + (255 - v) * (f - 1)) for v in c)


def _solid(c):
    """Palette for a treat printed in ONE filament.

    Every letter becomes a shade of the same colour, so the sprite gets its
    depth the way the real object does -- from light falling on geometry, not
    from a second material. Only k, the outline, stays dark. Without this a
    solid-printed treat would draw with BASE's white sprinkles and scarlet
    cherry, and the screen would promise a detail the tray can't show.
    """
    lo, hi = _mix(c, 0.72), _mix(c, 1.22)
    return dict(a=c, b=hi, c=lo, d=_mix(c, 0.58), r=c, w=hi, y=hi, m=hi, e=lo)


SPRITES = {
    # The six _solid ones are the expo set, one filament each; the colour is
    # the spool, straight from MARKERS in tools/voxel.py.
    "bar_red":          ("bar",       _solid(SCARLET)),
    "macaron_hot":      ("macaron",   _solid(HOT_PINK)),
    "slice_purple":     ("slice",     _solid(PURPLE)),
    "petitfour_yellow": ("petitfour", _solid(YELLOW)),
    "cupcake_green":    ("cupcake",   _solid(GRASS)),
    "cake_blue":        ("cake",      _solid(BLUE)),
    # The reprint of 2026-09-28 (tools/nachdruck.py), same rule.
    "bonbon_green":     ("bonbon",    _solid(GRASS)),
    "cupcake_yellow":   ("cupcake",   _solid(YELLOW)),
    "bar_blue":         ("bar",       _solid(BLUE)),
    "cupcake_red":      ("cupcake",   _solid(SCARLET)),
    "cake_hot":         ("cake",      _solid(HOT_PINK)),
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

# Characters and UI glyphs. Same format as SPRITES, but kept apart: the
# idle conveyor belt parades SPRITES, and a baker on the belt is a joke
# nobody asked for.
SKIN, HAIR = (240, 196, 160), (150, 92, 60)
_BELLA = dict(s=SKIN, h=HAIR, c=SAKURA, a=(255, 101, 189))
_OSKAR = dict(s=SKIN, h=CARAMEL, c=SAKURA, a=(255, 101, 189), d=ICE, g=APPLE)
EXTRAS = {
    "baker":       ("baker",       _BELLA),
    "baker_talk":  ("baker_talk",  _BELLA),
    "guest":       ("guest",       _OSKAR),
    "guest_sweat": ("guest_sweat", _OSKAR),
    "guest_joy":   ("guest_joy",   _OSKAR),
    "star_on":     ("star",        dict(a=LEMON, b=IVORY)),
    "star_off":    ("star",        dict(a=(96, 56, 82), b=(120, 76, 104))),
    "tray":        ("tray",        {}),
}

# marker_id -> sprite. The screen must show the same thing that's on the
# tray -- otherwise the price reveal teaches the wrong association.
# Everything printed solid (one filament plus marker cells), in the same
# order as VALUES, cheap and light first. Shape and colour together tell the
# treats apart: a solid object has no icing or filling left to do it. Where a
# colour repeats (yellow, green, red, blue, hot pink) the shape differs. Donuts stay missing on
# purpose: the hole cuts through the marker.
SPRITE = {4: "bonbon_green",     1: "bar_red",        0: "macaron_hot",
          10: "cupcake_yellow",  6: "slice_purple",   2: "petitfour_yellow",
          11: "cupcake_green",   7: "bar_blue",       5: "cupcake_red",
          9: "cake_blue",        8: "cake_hot"}
