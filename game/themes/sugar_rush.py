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
# Uppercase only, like the rest of the screen: Press Start 2P has the
# umlauts, but ß has no capital here, so it's written SS.
#
# The story: BELLA runs the bakery, OSKAR is the customer with a birthday
# and exactly that much money. Fictional on purpose -- a real person as the
# baker needs their okay first.
TEXT = {
    "en": dict(
        press="PRESS ▶", best="TODAY'S BEST",
        lang="▲ DEUTSCH", lang_ok="▲ NOCHMAL: DEUTSCH",
        again="▼ PLAYED BEFORE?",
        ask_name="WHAT'S YOUR NAME?", which="WHICH {name} ARE YOU?",
        pick_abc="▲▼ CHANGE LETTER", pick_no="▲▼ PICK YOURS",
        days=("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"),
        back="◀ BACK", next="▶ NEXT", done="▶ DONE", unknown="NAME NOT FOUND",
        baker="BELLA", guest="OSKAR",
        hello="HI {name}! I'M BELLA, AND THIS IS MY LITTLE BAKERY.",
        help="MOVE THE BIG ARM -- THE ROBOT COPIES YOU.|"
             "EVERY TREAT HAS A PRICE. BIGGER TREATS COST MORE!",
        welcome="WELCOME BACK, {name}! LET'S BEAT YOUR SCORE.",
        practice="PRACTICE", tut_head="1 TREAT ON THE TRAY",
        tut="PUT ANY TREAT ON THE TRAY IN THE MIDDLE.",
        tut_done="YUMMY! THAT ONE COSTS {price}. HERE COMES OUR FIRST GUEST!",
        skip="▶ SKIP", quit="◀ QUIT", quit_ok="◀ AGAIN TO QUIT",
        order_head="ORDER",
        order="HI! IT'S MY BIRTHDAY, AND I HAVE EXACTLY {goal}.|"
              "PICK ME TREATS THAT COST EXACTLY {goal} TOGETHER!",
        go="▶ GO!", add="ADD", over="TOO MUCH", hold="HOLD {n}",
        perfect="PERFECT", player="PLAYER #{no}",
        score="SCORE", rank="#{place} OF {count} TODAY",
        remember="WANT TO PLAY AGAIN? REMEMBER YOUR NUMBER: #{no}.",
        react=("HM, THE TRAY STAYED EMPTY. NEXT TIME!",
               "THANK YOU! THAT'S A GREAT START.",
               "WOW, ALMOST EXACTLY! THANK YOU SO MUCH!",
               "PERFECT! BEST BIRTHDAY EVER!"),
    ),
    "de": dict(
        press="DRÜCK ▶", best="BESTE HEUTE",
        lang="▲ ENGLISH", lang_ok="▲ AGAIN: ENGLISH",
        again="▼ SCHON GESPIELT?",
        ask_name="WIE HEISST DU?", which="WELCHER {name} BIST DU?",
        pick_abc="▲▼ BUCHSTABE ÄNDERN", pick_no="▲▼ AUSWÄHLEN",
        days=("SO", "MO", "DI", "MI", "DO", "FR", "SA"),
        back="◀ ZURÜCK", next="▶ WEITER", done="▶ FERTIG",
        unknown="NAME NICHT GEFUNDEN",
        baker="BELLA", guest="OSKAR",
        hello="HALLO {name}! ICH BIN BELLA, UND DAS IST MEINE KLEINE BÄCKEREI.",
        help="BEWEG DEN GROSSEN ARM -- DER ROBOTER MACHT DICH NACH.|"
             "JEDER TREAT HAT EINEN PREIS. GRÖSSERE TREATS KOSTEN MEHR!",
        welcome="SCHÖN, DASS DU WIEDER DA BIST, {name}! SCHLAG DEINEN REKORD.",
        practice="ÜBUNG", tut_head="1 TREAT AUFS TABLETT",
        tut="LEG IRGENDEINEN TREAT AUFS TABLETT IN DER MITTE.",
        tut_done="LECKER! DER KOSTET {price}. DA KOMMT SCHON UNSER ERSTER GAST!",
        skip="▶ ÜBERSPRINGEN", quit="◀ AUFHÖREN", quit_ok="◀ NOCHMAL = AUFHÖREN",
        order_head="BESTELLUNG",
        order="HALLO! ICH HABE GEBURTSTAG UND GENAU {goal} DABEI.|"
              "STELL MIR TREATS ZUSAMMEN, DIE ZUSAMMEN GENAU {goal} KOSTEN!",
        go="▶ LOS!", add="NOCH DAZU", over="ZU VIEL", hold="HALTEN {n}",
        perfect="PERFEKT", player="SPIELER #{no}",
        score="PUNKTE", rank="PLATZ {place} VON {count} HEUTE",
        remember="WILLST DU NOCHMAL SPIELEN? MERK DIR DEINE NUMMER: #{no}.",
        react=("HM, DAS TABLETT BLIEB LEER. NÄCHSTES MAL!",
               "DANKE! DAS IST EIN SUPER ANFANG.",
               "WOW, FAST GENAU! VIELEN DANK!",
               "PERFEKT! BESTER GEBURTSTAG ALLER ZEITEN!"),
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
# The demo on the story screen: the gripper and the tray it drops into.
# Not treats, so they live outside SPRITES and never ride the idle belt.
#
# Both grids are aligned to their box edges, because scenes place them by
# box and the layout self-test rejects any overlap: the gripper's fingers
# end on the last row, the tray's rim starts on the first. A treat box set
# directly underneath the gripper is then held by it, and one set directly
# above the tray is lying in it -- no pixel nudging in the scene.
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
# ponytail: placeholder, cheap/light -> expensive/wobbly. Reassign once
# the printed objects are settled; one line per object. Donuts are missing
# on purpose: the hole cuts through the marker.
SPRITE = {0: "macaron_pink",   1: "bar_milk",      2: "petitfour_pink",
          3: "berliner",       4: "cupcake_pink",  5: "cupcake_lemon",
          6: "slice_straw",    7: "cake_choc",     8: "slice_choc",
          9: "cake_straw"}
