"""Thema "Sugar Rush" -- Suessigkeiten, Wert = Preis. Entschieden am 11.9.2026.

Ein Thema ist genau diese Datei. Alles, was den Automaten nach etwas aussehen
laesst, steht hier; Szenen, LEDs und Werkzeuge lesen es ueber config.py und
kennen den Namen des Themas nicht. Neues Thema (etwa PCB-Bauteile):

    1. Datei kopieren: themes/pcb.py
    2. Farben, Texte, Sprites, SPRITE-Zuordnung tauschen
    3. PNP_THEME=pcb uv run game/main.py        (Default steht in config.py)
    4. uv run game/sprites.py                   prueft jedes Thema in themes/

Nicht hier, weil sie nicht zum Thema gehoeren: RED/ORANGE (HPI-Logo), die
Knopffarben (physische Knoepfe), VALUES (Wertung), der Titel PICK'N'PLAY.
"""

# ── Bildschirm ────────────────────────────────────────────────────────────
# Schokoladengrund statt Schwarz, Pink statt Gelb, Sahne statt Weiss. Der Grund
# ist so dunkel, dass der Kontrast wie auf Schwarz bleibt (Beschriftung 5,4 : 1).
# Die Jobs gelten fuer jedes Thema -- ein neues tauscht die Farben, nicht die Rollen:
BG     = (40, 16, 32)       # Grund, immer
GREY   = (176, 128, 158)    # Beschriftungen
WHITE  = (255, 236, 246)    # neutrale Werte
ACCENT = (255, 101, 189)    # was der Besucher gerade beeinflusst
# Pruefen bei jedem neuen Thema: ACCENT auf RED (letzte Sekunden). Hier nur
# 2,7 : 1, deshalb schaltet GameScene.acc() dort auf WHITE.

# Deko fuer Titel und Streusel, nie fuer Spielwerte. Bambu PLA Matte, damit der
# Schirm dieselben Farben zeigt wie die gedruckten Objekte.
CANDY = ((255, 101, 189),   # ACCENT
         (163, 216, 225),   # Ice Blue     #A3D8E1
         (247, 217, 89),    # Lemon Yellow #F7D959
         (194, 225, 137),   # Apple Green  #C2E189
         (232, 175, 207))   # Sakura Pink  #E8AFCF

# {secs} fuellt die Szene aus dem Spielmodus -- die Rundenlaenge wird
# durchprobiert und darf nicht in einem Thema eingefroren sein.
# Das Tablett startet leer: es wird aufgebaut, nicht umgeraeumt.
HOWTO = ("EVERY TREAT HAS A HIDDEN PRICE",
         "FILL THE TRAY TO MATCH THE GOAL",
         "{secs} SECONDS. CLOSEST WINS.")

# ── LED-Streifen ──────────────────────────────────────────────────────────
# Die beiden Streifenfarben der Zuckerstange (idle/score) und die Balkenfarbe
# der Runde (A). LEDs, nicht Bildschirm: Rot dominiert, sonst wird Pink lila.
LED_A = (255, 40, 120)
LED_B = (255, 255, 255)

# ── Sprites ───────────────────────────────────────────────────────────────
# 16 x 16, als Text notiert. Eine Form, mehrere Paletten. Buchstaben:
#   k Umriss   a Hauptfarbe   b Glanzlicht   c Teig/Becher   d zweite Schicht
#   r Kirsche/Marmelade   w weiss   y m Streusel   e Teller
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

# Bambu PLA Matte, Hex aus der offiziellen Tabelle. MILK ist die Ausnahme:
# Dark Chocolate #4D3324 verschwindet auf dem Schokoladengrund des Schirms,
# also steht dort eine hellere Milchschokolade fuer dasselbe Teil.
SAKURA, LEMON, ICE = (232, 175, 207), (247, 217, 89), (163, 216, 225)
APPLE, LILAC, SCARLET = (194, 225, 137), (174, 150, 212), (222, 67, 67)
IVORY, TAN, LATTE = (255, 255, 255), (232, 219, 183), (211, 183, 167)
CARAMEL, BONE, MILK = (174, 131, 91), (203, 198, 184), (128, 84, 60)

# Gilt fuer jedes Sprite, einzelne Paletten ueberschreiben.
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

# marker_id -> Sprite. Der Schirm muss dasselbe Ding zeigen, das auf dem
# Tablett liegt -- sonst lehrt der Preisreveal die falsche Zuordnung.
# ponytail: Platzhalter, billig/leicht -> teuer/kippelig. Neu belegen, sobald
# die gedruckten Objekte feststehen; eine Zeile pro Objekt. Donuts fehlen mit
# Absicht: das Loch schneidet den Marker.
SPRITE = {0: "macaron_pink",   1: "bar_milk",      2: "petitfour_pink",
          3: "berliner",       4: "cupcake_pink",  5: "cupcake_lemon",
          6: "slice_straw",    7: "cake_choc",     8: "slice_choc",
          9: "cake_straw"}
