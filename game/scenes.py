import math
import os
import random
import textwrap
import pygame
from functools import lru_cache
from typing import NamedTuple
import arm
from balance import gap, next_move, points
from config import *
from app import SceneBase
from sprites import sprite

# The sprites of the objects, cheap -> expensive. Scenes never name a
# sprite themselves, otherwise a theme switch would depend on places outside
# the theme file.
LADDER = [SPRITE[k] for k in sorted(VALUES, key=VALUES.get)]


@lru_cache(maxsize=512)
def render(font, text, color):
    """Rendered text surface, memoized instead of rebuilding every frame.

    Press Start 2P at 168 px was the most expensive item in the render path:
    the screen shows at most a few dozen different strings, and most of them
    sit unchanged for seconds at a time. Measured on the Pi 5 on 2026-09-09,
    idle screen driven at 60 Hz.

    512 instead of the earlier 256, since draw_hint() colors the hint line
    character by character: every letter in it is its own entry. It still
    stays well within the range of the few dozen strings the screen shows.
    """
    return font.render(text, False, color)


def draw(screen, font, text, x, y, color):
    surf = render(font, str(text), color)
    screen.blit(surf, surf.get_rect(center=(x,y)))


def euro(units, sign=True):
    """Price in 10-cent units -> display text. The ONE place where the
    computed quantity turns into a price.

    Everything is computed in units throughout, because the prices need to
    be coprime (see VALUES in config.py). Division happens here and nowhere
    else -- a different unit is thus just this function, not a search
    through six scenes.

    `sign=False` for the price strip: ten cells of 170 px, and six glyphs
    don't fit side by side.

    German format, decimal comma and the sign after the number: the machine
    stands at a German fair, and "€3.40" reads as a typo there.
    """
    return f"{units * CENTS / 100:.2f}".replace(".", ",") + (" €" if sign else "")


def tray_sum(marks):
    """What's on the tray, in units.

    One function instead of the sum written out three times: every separate
    spelling is a chance to forget VALUES, and a scoring bug looks like a
    detection problem on show day.
    """
    return sum(VALUES[i] for i in marks)


class Result(NamedTuple):
    """What a round leaves behind.

    An object instead of growing parameter lists: the score screen and the
    name entry both need all of it, and the database needs the same again.
    A mode that adds something later (moves, difficulty) attaches it here
    instead of to three signatures.

    The physical truth is what's stored, everything else is computed from
    it -- the same separation as in db.py.
    """

    target: int          # target total, in units
    total: int           # what was there at the end of the round
    dist:  int           # distance at round start, the denominator of the score
    left:  float         # time left. > 0 means perfect, otherwise the clock ran out
    marks: dict          # id -> quad, what was on the tray

    @property
    def off(self):
        return abs(self.target - self.total)

    @property
    def accuracy(self):
        return points(self.off, self.dist)          # ohne Zeitbonus

    @property
    def score(self):
        return points(self.off, self.dist, self.left)

    @property
    def bonus(self):
        return self.score - self.accuracy

    @property
    def stars(self):
        """0..3. One for anything on the tray, two from STAR_TWO, three for
        exact. Nearly everyone walks away with a star -- that was the brief."""
        if self.off == 0:
            return 3
        return 2 if self.accuracy >= STAR_TWO else int(self.total > 0)


def stamp(screen, name, scale, x, y):
    """Sprite centered on (x, y). Its own function like draw(), so the
    layout self-test can intercept it the same way and check for overlap."""
    s = sprite(name, scale)
    screen.blit(s, s.get_rect(center=(round(x), round(y))))


TREAT_DIR = os.path.join(os.path.dirname(__file__), "assets", "treats")


@lru_cache(maxsize=None)
def _prints():
    """The printed treats as voxel pictures (tools/treat_pics.py), by marker id."""
    out = {}
    for k in SPRITE:
        try:
            out[k] = pygame.image.load(os.path.join(TREAT_DIR, f"{k}.png"))
        except (pygame.error, FileNotFoundError):
            pass     # pic() falls back to the sprite
    return out


@lru_cache(maxsize=64)
def _print(k, w, h):
    """Picture #k, scaled by the ONE factor that fits the largest print of
    the set into w x h. A shared factor keeps the torte bigger than the
    macaron -- heavier is dearer, readable without the price."""
    imgs = _prints()
    f = min(w / max(i.get_width() for i in imgs.values()),
            h / max(i.get_height() for i in imgs.values()))
    i = imgs[k]
    return pygame.transform.smoothscale(i, (round(i.get_width() * f), round(i.get_height() * f)))


def pic(screen, k, w, h, x, bottom, scale):
    """Treat #k standing on the line `bottom`, centered on x: the printed
    object, where the visitor has to find it on the table (price ladder,
    strip, pop-up). The sprite at `scale` if its picture is missing."""
    if k not in _prints():
        n = len(SHAPES[SPRITES[SPRITE[k]][0]]) * scale
        return stamp(screen, SPRITE[k], scale, x, bottom - n / 2)
    s = _print(k, w, h)
    r = s.get_rect(midbottom=(round(x), round(bottom)))
    screen.blit(s, r)
    area(SPRITE[k], r)


def area(name, rect):
    """A drawn region that isn't one sprite. Draws nothing -- it exists so
    the layout self-test can intercept it the way it intercepts stamp().

    The demo on the story screen needs this: it is a little scene of its
    own, and inside it things are supposed to overlap -- the arm holds the
    treat, the treat lies in the tray. What must not overlap is the demo
    and Bella, so the demo reports one box and draws inside it directly."""


def hop(t, i=0, px=8):
    """Arcade hop: two positions at a 4 Hz beat, no sine. 8-bit sprites had
    no in-between frames, and that's exactly what reads as 8-bit."""
    return -px if int(t * 4 + i) % 2 else 0


def parade(screen, t, y, speed, scale=5, gap=160):
    """Conveyor belt of all sprites across the screen, attract-mode decoration.

    Blits directly instead of via stamp(): the belt deliberately runs off
    the left and right edge of the image, and that's exactly what the
    self-test would flag as a bug.
    """
    names = list(SPRITES)
    # The belt length must be a whole number of slots: with span = WIDTH + gap
    # and one slot too many, the last sprite sat exactly on the first.
    n = -(-(WIDTH + gap) // gap)
    span = n * gap
    for i in range(n):
        x = (i * gap + t * speed) % span - gap / 2
        s = sprite(names[i % len(names)], scale)
        screen.blit(s, s.get_rect(center=(round(x), y + hop(t, i, scale))))


# The demo loop on the story screen: the robot picks a treat off the table
# and puts it on the tray, over and over.
#
# This is what the todo meant by "less text, more pictures": the sentence
# it replaces did the work for everyone who can already read and none at
# all for the five-year-olds the practice round exists for.
#
# A gripper was tried here on 2026-09-24 and thrown out the same day -- at
# the treats' 16 x 16 a two-jaw claw reads as a crucifix. It came back on a
# 32 x 32 grid, and it still only read as a crane hook, because the whole
# picture slid from frame to frame: a claw that moves its own shoulder is
# not an arm. Since 2026-09-25 it is the SO-101 itself, drawn from the
# published CAD and moved by its own kinematics -- arm.py has the details.
# The scene only says where the machine stands and how big it is.
ARM_SCALE = 6               # arm.MM is 4, so this is 1.5 px per millimetre
ARM_BASE = (1130, 690)      # the base pivot: the arm stands on this point
# Not a taste: arm.TREAT is the widest thing these jaws can close around
# without cutting into it, and this is that width in sprite pixels.
DEMO_SCALE = round(arm.TREAT * ARM_SCALE / arm.MM / 16)
# The dearest cupcake, not the middle of the ladder. arm.TREAT is only a
# width; what the drawn jaws actually need is a silhouette with a waist, and
# only the cupcake has one -- a wide disc or box is already in the jaw at the
# height where a cup still tapers. The self-test at the bottom of this file
# names the frame if a theme picks a shape that clips, so this stays a
# one-line choice instead of a rule nobody can check.
DEMO_TREAT = [s for s in LADDER if SPRITES[s][0] == "cupcake"][-1]
# The tray stands where the arm lets go, taken from the arm's own key so the
# two can never drift apart. The tray fills the top 7 of its 16 rows, so a
# box centred one row below the counter puts the bowl on it.
TRAY_ROWS = 7
DEMO_TRAY = (arm.to_screen(ARM_BASE, ARM_SCALE, arm.KEYS[5])[0],
             ARM_BASE[1] + (8 - TRAY_ROWS) * DEMO_SCALE)
# The counter all three stand on. Without it the base, the treat and the
# tray each float at their own height and the picture has no ground.
COUNTER = tuple(c + (255 - c) // 4 for c in BG)


def treat_at(treat):
    """Screen centre of the treat, for a spot the arm reported."""
    return arm.to_screen(ARM_BASE, ARM_SCALE, treat)


def _box():
    """One box for the whole demo, because inside it the overlap is the
    point -- the arm holds the treat, the treat lies in the tray.

    Taken from what actually gets drawn: the arm's surface, the treat at
    every step of the loop, the tray. Written out by hand it would be four
    numbers that quietly stop being true the first time the machine moves
    or the loop is retimed."""
    box = pygame.Rect(ARM_BASE[0] - arm.ORIGIN[0] * ARM_SCALE,
                      ARM_BASE[1] - arm.ORIGIN[1] * ARM_SCALE,
                      arm.W * ARM_SCALE, arm.H * ARM_SCALE)
    n = 16 * DEMO_SCALE
    for x, y in (treat_at(t) for _, t in arm.loop()):
        box.union_ip(pygame.Rect(x - n // 2, y - n // 2, n, n))
    # The tray only counts its filled rows: the rest of its grid is blank,
    # and counting it would push the box down into the text box.
    box.union_ip(pygame.Rect(DEMO_TRAY[0] - n // 2, DEMO_TRAY[1] - n // 2,
                             n, TRAY_ROWS * DEMO_SCALE))
    return box


DEMO_BOX = _box()


def demo(screen, t):
    """One frame of the arm putting the treat on the tray.

    Counter, tray, treat, arm -- in that order, because the order is a
    depth statement: seen from the side the near jaw is in front of what it
    is holding. It is no longer what makes the grip read, though. The jaws
    close on the treat's own width now and never share a pixel with it, so
    nothing here is covering up an overlap the way it used to.
    """
    area("demo", DEMO_BOX)
    pose, treat = arm.cycle(t)
    pygame.draw.rect(screen, COUNTER,
                     (DEMO_BOX.left, ARM_BASE[1], DEMO_BOX.width, 6))
    for name, at in (("tray", DEMO_TRAY), (DEMO_TREAT, treat_at(treat))):
        s = sprite(name, DEMO_SCALE)
        screen.blit(s, s.get_rect(center=at))
    arm.draw(screen, ARM_BASE, ARM_SCALE, pose)


def park_demo(screen, t):
    """The arm leaving the treat on the tray and going back to rest: the
    practice end (29.9., fair). Drawn where the camera panes were, because
    that's where people were looking, not at the text."""
    area("demo", DEMO_BOX)
    pygame.draw.rect(screen, COUNTER,
                     (DEMO_BOX.left, ARM_BASE[1], DEMO_BOX.width, 6))
    for name, at in (("tray", DEMO_TRAY), (DEMO_TREAT, treat_at(arm.KEYS[5][:2]))):
        s = sprite(name, DEMO_SCALE)
        screen.blit(s, s.get_rect(center=at))
    arm.draw(screen, ARM_BASE, ARM_SCALE, arm.park(t))


@lru_cache(maxsize=4)
def stripes(w, h, color, period=48):
    """Diagonal stripes for the bar (a candy cane in Sugar Rush), built once. One
    period wider than the bar, so a shifted crop continues seamlessly."""
    s = pygame.Surface((w + period, h))
    s.fill(color)
    light = tuple(c + (255 - c) // 2 for c in color)
    for x in range(-h, w + period, period):
        pygame.draw.polygon(s, light, [(x, 0), (x + period // 2, 0),
                                       (x + period // 2 + h, h), (x + h, h)])
    return s


class Sprinkles:
    """Sprinkle burst: on PERFECT and on the score screen.

    One pop from a point, then gravity, then gone after about 1.3 s. The
    earlier rain covered the numbers for ten seconds -- exactly the moment
    people are trying to read them.

    Rectangles instead of sprites, upright or sideways -- that's what
    sprinkles look like on a cupcake, and fill() is the cheapest thing
    pygame can do. They sit behind the text.

    Fixed seed: otherwise every build-log screenshot looks different, and
    `git diff --stat docs/shots` reports scenes that haven't actually changed.
    """

    N = 90
    GRAVITY = 2200      # px/s²

    def __init__(self, x=WIDTH / 2, y=HEIGHT / 2):
        rng = random.Random(7)
        self.p = []
        for _ in range(self.N):
            a = rng.uniform(0, 2 * math.pi)
            v = rng.uniform(500, 1500)
            w, h = rng.choice(((14, 40), (40, 14)))
            # x, y, vx, vy (a bit upward, it's a pop), life, w, h, colour
            self.p.append([x, y, v * math.cos(a), v * math.sin(a) - 400,
                           rng.uniform(0.8, 1.3), w, h, rng.choice(CANDY)])

    def update(self, dt):
        for q in self.p:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += self.GRAVITY * dt
            q[4] -= dt
        self.p = [q for q in self.p if q[4] > 0 and q[1] < HEIGHT]

    def draw(self, screen):
        for x, y, _, _, _, w, h, c in self.p:
            screen.fill(c, (x - w / 2, y - h / 2, w, h))


def draw_left(screen, font, text, x, y, color):
    """draw(), but x is the left edge. Goes through draw(), so the layout
    self-test sees it."""
    text = str(text)
    draw(screen, font, text, x + font.size(text)[0] / 2, y, color)


# The timer: a fuse around the screen edge, burning clockwise from 12
# o'clock. It used to be a pie between the camera panes -- that spot now
# belongs to the guest, and an edge takes no room from the images the
# player steers by. Read from the corner of the eye, which is all a timer
# needs.
FUSE = [(960, 0), (WIDTH, 0), (WIDTH, HEIGHT), (0, HEIGHT), (0, 0), (960, 0)]


def fuse(screen, frac, color, t):
    """What's left of the fuse, plus a flickering spark where it burns."""
    burnt = (1 - frac) * 2 * (WIDTH + HEIGHT)
    edge = screen.get_rect()
    spark, s = None, 0
    for (x0, y0), (x1, y1) in zip(FUSE, FUSE[1:]):
        n = abs(x1 - x0) + abs(y1 - y0)
        a = min(max(burnt - s, 0), n)
        if a < n:
            px, py = x0 + (x1 - x0) * a / n, y0 + (y1 - y0) * a / n
            spark = spark or (px, py)
            r = pygame.Rect(min(px, x1), min(py, y1), abs(x1 - px), abs(y1 - py))
            r.w, r.h = max(r.w, FUSE_W), max(r.h, FUSE_W)
            screen.fill(color, r.clamp(edge))     # clamp pulls the band inward
        s += n
    if spark:
        r = pygame.Rect(0, 0, 2 * FUSE_W, 2 * FUSE_W)
        r.center = spark
        screen.fill(CANDY[int(t * 12) % len(CANDY)], r.clamp(edge))


class Dialog:
    """Pokémon-style text box: a portrait, a name, and text that types itself
    out with a blip per letter.

    ▶ first completes the page, then turns it -- the same button for
    "faster" and "next", like every handheld RPG. A blinking green ▶ says
    when the page is done: the arrow in the color of its button, like the
    footer.

    The pages are wrapped once, up front, so a word never jumps to the next
    line halfway through typing.
    """

    BOX = pygame.Rect(108, 726, 1704, 194)
    TEXT_X, COLS, LINE = 306, 30, 58

    def __init__(self, music, who, name, text):
        self.music, self.who, self.name = music, who, name
        self.pages = [textwrap.wrap(p, self.COLS) for p in text.split("|")]
        self.i, self.n, self.t, self.wait = 0, 0.0, 0.0, 0.0

    @property
    def due(self):
        """The page has been sitting there typed out for PAGE_SECONDS: the
        scene presses ▶ itself."""
        return self.wait > PAGE_SECONDS

    @property
    def typing(self):
        return self.n < sum(map(len, self.pages[self.i]))

    @property
    def last(self):
        return self.i == len(self.pages) - 1

    def face(self, who=None):
        """Sprite name, mouth open on every other beat while typing."""
        who = who or self.who
        talk = who + "_talk"
        return talk if self.typing and talk in EXTRAS and int(self.t * 8) % 2 else who

    def update(self, dt):
        self.t += dt
        self.wait = 0.0 if self.typing else self.wait + dt
        if self.typing:
            before = int(self.n)
            self.n += TALK_CPS * dt
            if int(self.n) > before:
                self.music.sfx(f"talk{random.randrange(4)}")

    def next(self):
        """▶. True once the last page has been read."""
        if self.typing:
            self.n = float(sum(map(len, self.pages[self.i])))
            return False
        if self.last:
            return True
        self.i, self.n = self.i + 1, 0.0
        return False

    def draw(self, screen, f):
        r = self.BOX
        screen.fill(BOX_BG, r)
        pygame.draw.rect(screen, ACCENT, r, 4)
        stamp(screen, self.face(), 4, r.x + 90, r.y + 76)
        draw(screen, f["tiny"], self.name, r.x + 90, r.bottom - 26, ACCENT)
        left = self.n
        for k, line in enumerate(self.pages[self.i]):
            shown = line[:max(0, int(left))]
            left -= len(line)
            if shown:
                draw_left(screen, f["small"], shown, self.TEXT_X,
                          r.y + 40 + k * self.LINE, WHITE)
        if not self.typing and int(self.t * 3) % 2:
            draw_hint(screen, f["small"], "▶", r.right - 34, r.bottom - 36)


BOX_BG = tuple(c // 2 for c in BG)


def draw_hint(screen, font, text, x, y, base=GREY):
    """Hint line, drawn character by character: every arrow in the color of
    its physical button.

    The four buttons on the panel are green, red, blue, and yellow.
    Unlabeled, they're only operable if the screen establishes the mapping
    itself -- and color establishes it faster than position: the visitor
    looks for "the green one," not "the right one." That's why the arrow
    gets colored and not the word next to it; the word says what happens,
    the arrow says with what.

    Press Start 2P is monospace, so one character width is enough as the
    step. Without that, every color in the text would need its own width
    calculation.
    """
    w = font.size("A")[0]
    x0 = x - w * len(text) / 2
    for i, c in enumerate(text):
        draw(screen, font, c, x0 + w * (i + 0.5), y,
             BUTTON_COLORS.get(ARROWS.get(c), base))


def tag(screen, f, no):
    """The player number, bare and small, in the bottom right corner.

    Shown from the entry screen onwards (2026-09-24). It used to appear
    only during the practice round, which was enough for the booth team but
    made it a surprise for the player -- a number you're handed once at the
    end is a number nobody writes down. On screen the whole time, it turns
    into something you've already read three times by then.

    Bare "#42", no label: the word PLAYER next to it would compete with the
    footer hints, and every other screen that shows a number (the pick
    list) writes it the same way.
    """
    text = f"#{no}"
    draw_left(screen, f["tiny"], text, WIDTH - 30 - f["tiny"].size(text)[0],
              FOOTER_Y, GREY)


def footer(screen, f, left=None, right=None, note=None):
    """The bottom row: what the four buttons currently do.

    Always in the same place, otherwise the eye has to search anew every time.

    `note` (the double-confirm) *replaces* the hints instead of sitting next
    to them. That's why nothing here can clip anymore: there's no second
    element that could collide with the row. And it's the better feedback
    -- the response to a button press appears right where it already said
    what the button does.

    Position instead of word order carries the direction: arrow always
    first, the left hint field on the left, the right one on the right.
    """
    # WHITE and "small" since 2026-09-16: GREY "tiny" was too dark and hard
    # to read at the cabinet's poor viewing angles. The urgency of the
    # follow-up question is carried by the red arrow, not the word.
    if note:
        draw_hint(screen, f["small"], note, 960, FOOTER_Y, WHITE)
        return
    if left:
        draw_hint(screen, f["small"], left, 600, FOOTER_Y, WHITE)
    if right:
        draw_hint(screen, f["small"], right, 1320, FOOTER_Y, WHITE)


class IdleScene(SceneBase):
    """Attract screen. ▶ new player, ▼ played before, ▲▲ switches language.

    The language asks twice on purpose: a kid mashing buttons shouldn't flip
    the screen into a language the next kid can't read. The question is in
    the *other* language, because that's the one the person pressing reads.
    """

    TICK  = IDLE_FPS   # nobody's watching, and the Pi sits in the cabinet
    MUSIC = None       # stays silent, see __init__

    # The leaderboard as a podium: first place big and pink, 2-3 white,
    # the rest small. Names only -- a 948 next to a 1000 said "you won't get
    # here" to everyone who hasn't played yet.
    PODIUM = (("mid", ACCENT, 612), ("small", WHITE, 700), ("small", WHITE, 760),
              ("tiny", GREY, 816), ("tiny", GREY, 860))

    def __init__(self, ctx):
        super().__init__(ctx)
        # Six hours of chiptune in a row is exhausting -- and it marks
        # nothing. Only with a silent idle does the music kicking in during
        # the next scene become the signal "it's starting". stop() also
        # clears the deferred idle music that DisplayScoreScene scheduled.
        ctx.music.stop()
        ctx.leds.show("idle")
        self.now = 0.0
        self.ask = 0.0
        self.top = ctx.db.top(len(self.PODIUM))
        # The number a new player gets, before any name (29.9., booth ask)
        self.no = ctx.db.next_player()

    def handle(self, action):
        if action == "right":
            if ASK_NAME:
                self.switch_to(EntryScene(self.ctx))
            else:
                name = f"#{self.ctx.db.next_player()}"
                no = self.ctx.db.new_player(name)
                self.switch_to(StoryScene(self.ctx, no, name, new=True))
        elif action == "down":
            if ASK_NAME:
                self.switch_to(EntryScene(self.ctx, again=True))
            elif rows := self.ctx.db.players_named(None):
                self.switch_to(PickScene(self.ctx, None, rows))
            else:
                return None     # nobody has played yet
        elif action == "up":
            if self.ask > 0:
                self.ctx.lang = "de" if self.ctx.lang == "en" else "en"
                self.ctx.db.log("lang", lang=self.ctx.lang)
                self.ask = 0.0
            else:
                self.ask = CONFIRM_SECONDS
        else:
            return None
        return "ok"

    def update(self, dt):
        self.now += dt
        self.ask = max(0.0, self.ask - dt)

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        # The display scrolls by at the top -- that's the attract mode. From
        # 8 m you see motion before you read text.
        parade(screen, self.now, 96, 60)
        # Title character by character: every letter in a candy color, as a
        # wave. Monospace, one character width is the step like in draw_hint().
        title = "PICK'N'PLAY"
        w = f["title"].size("A")[0]
        for i, c in enumerate(title):
            draw(screen, f["title"], c, 960 + w * (i + 0.5 - len(title) / 2),
                 250 + round(14 * math.sin(self.now * 3 - i * 0.6)),
                 CANDY[i % len(CANDY)])
        # The cheapest and the most expensive piece -- from the theme, not named here.
        stamp(screen, LADDER[0], 8, 330, 430 + hop(self.now, 0, 8))
        stamp(screen, LADDER[-1], 8, 1590, 430 + hop(self.now, 1, 8))
        # Mostly on, briefly off: it has to be read, the blink only draws the eye.
        if self.now % 2 < 1.6:
            draw_hint(screen, f["mid"], self.t("press"), 960, 430, WHITE)
        if self.top:
            draw(screen, f["tiny"], self.t("best"), 960, 540, GREY)
        # Left-aligned on one column, so the rows line up instead of
        # shrinking toward the middle.
        x = 960 - f["mid"].size("1. WWW")[0] / 2
        for i, (name, _) in enumerate(self.top):
            size, color, y = self.PODIUM[i]
            draw_left(screen, f[size], f"{i + 1}. {name}", x, y, color)
        # Three hints, ▶ in the middle (29.9., fair): visitors read the
        # bottom row and missed the ▶ in the middle of the screen. Left and
        # right hug the edges so the German "▼ SCHON GESPIELT?" leaves room.
        if self.ask > 0:
            footer(screen, f, note=self.t("lang_ok"))
        else:
            w = f["small"].size("A")[0]
            left, mid, right = self.t("lang"), self.t("play"), self.t("again")
            x0, x1 = 40 + w * len(left), WIDTH - 40 - w * len(right)
            draw_hint(screen, f["small"], left, x0 - w * len(left) / 2, FOOTER_Y, WHITE)
            draw_hint(screen, f["small"], mid, (x0 + x1) / 2, FOOTER_Y, ACCENT)
            draw_hint(screen, f["small"], right, x1 + w * len(right) / 2, FOOTER_Y, WHITE)
        # Right under PRESS: that is the number pressing gets you. tiny fits
        # the gap to BEST, small does not (layout test).
        draw(screen, f["tiny"], self.t("player", no=self.no), 960, 499, ACCENT)


class EntryScene(SceneBase):
    """Three letters -- the name, for a new player and a returning one alike.

    Until 2026-09-24 coming back meant typing the player number. Nobody
    remembers a number they were shown once, so it's the name again, and
    PickScene sorts out which MAX this is.

    The arrows sit where the button acts: a blue ▲ above the active letter,
    a yellow ▼ below it. The old screen had big ◀ ▶ arrows at the sides that
    promised a control the buttons didn't have.
    """

    MUSIC_IN = (0.0, 800)   # fades in, instead of hitting hard out of silence
    COLS = (750, 960, 1170)
    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, ctx, again=False):
        super().__init__(ctx)
        self.again = again
        # A new player sees their number here already -- db.next_player()
        # is what the INSERT on submit will hand out. Coming back, the
        # number isn't picked yet: PickScene lists them, and from the story
        # screen on it's in the corner like everywhere else.
        self.no = None if again else ctx.db.next_player()
        self.chars = self.LETTERS
        self.slots = [0, 0, 0]
        self.cursor = 0
        self.idle = self.error = self.now = 0.0

    def handle(self, action):
        self.idle = 0.0
        if action in ("up", "down"):
            step = 1 if action == "down" else -1
            self.slots[self.cursor] = (self.slots[self.cursor] + step) % len(self.chars)
        elif action == "left":
            if self.cursor:
                self.cursor -= 1
            else:
                self.switch_to(IdleScene(self.ctx))
        elif action == "right":
            if self.cursor < len(self.slots) - 1:
                self.cursor += 1
            else:
                return self.submit()
        else:
            return None
        return "ok"

    def submit(self):
        text = "".join(self.chars[i] for i in self.slots)
        if not self.again:
            no = self.ctx.db.new_player(text)
            self.switch_to(StoryScene(self.ctx, no, text, new=True))
            return "ok"
        rows = self.ctx.db.players_named(text)
        if not rows:
            self.error = CONFIRM_SECONDS
            return None     # "nope", and the footer says why
        self.switch_to(PickScene(self.ctx, text, rows))
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
        self.error = max(0.0, self.error - dt)
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        draw(screen, f["mid"], self.t("ask_name"), 960, 150, ACCENT)
        for i, x in enumerate(self.COLS):
            on = i == self.cursor
            draw(screen, f["big"], self.chars[self.slots[i]], x, 470,
                 ACCENT if on else WHITE)
            if on:
                draw_hint(screen, f["mid"], "▲", x, 320 + hop(self.now, 0, 6))
                draw_hint(screen, f["mid"], "▼", x, 620 - hop(self.now, 0, 6))
        draw_hint(screen, f["small"], self.t("pick_abc"), 960, 760, GREY)
        if self.no:
            tag(screen, f, self.no)
        last = self.cursor == len(self.slots) - 1
        footer(screen, f, self.t("back"), self.t("done" if last else "next"),
               note=self.t("unknown") if self.error > 0 else None)


class PickScene(SceneBase):
    """Which of the MAXes are you? The numbers behind one name, no scores.

    Weekday and time are the only thing separating two rows, and they're
    enough: "I played yesterday evening". A score in the row would make
    this screen a leaderboard you can read without playing -- and it would
    tell the person which number is the good one, which is not the
    question being asked.

    Newest first: whoever comes back is most often the one from ten
    minutes ago, so the cursor already sits on the right row.
    """

    MUSIC_IN = (0.0, 800)
    ROWS = 5            # more would run into the hint line at 760
    TOP, STEP = 330, 78

    def __init__(self, ctx, name, rows):
        super().__init__(ctx)
        self.name, self.rows = name, rows
        self.cursor = 0
        self.idle = self.now = 0.0

    @property
    def start(self):
        """First visible row: the cursor stays in the middle while it can."""
        return max(0, min(self.cursor - self.ROWS // 2, len(self.rows) - self.ROWS))

    def handle(self, action):
        self.idle = 0.0
        if action in ("up", "down"):
            step = 1 if action == "down" else -1
            self.cursor = (self.cursor + step) % len(self.rows)
        elif action == "left":
            self.switch_to(EntryScene(self.ctx, again=True) if ASK_NAME
                           else IdleScene(self.ctx))
        elif action == "right":
            no = self.rows[self.cursor][0]
            self.switch_to(StoryScene(self.ctx, no, self.name or f"#{no}", new=False))
        else:
            return None
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        draw(screen, f["mid"], self.t("which", name=self.name) if self.name
             else self.t("when"), 960, 150, ACCENT)
        days = self.t("days")
        for i in range(self.start, min(self.start + self.ROWS, len(self.rows))):
            no, wd, hhmm = self.rows[i]
            on = i == self.cursor
            # The ▶ marker is drawn through draw_hint, so it carries the
            # color of the button that confirms it, like everywhere else.
            draw_hint(screen, f["small"], f"{'▶' if on else ' '} #{no}  "
                      f"{days[wd]} {hhmm}", 960,
                      self.TOP + (i - self.start) * self.STEP,
                      ACCENT if on else GREY)
        draw_hint(screen, f["small"], self.t("pick_no"), 960, 760, GREY)
        footer(screen, f, self.t("back"), self.t("done"))


class StoryScene(SceneBase):
    """Bella says hello. A returning player gets one line and skips practice.

    The player number stands big at the top (29.9., fair). On 24.9. it had
    been moved to a small corner tag as "homework before the game"; at the
    fair the team needs it for the sign-up form and nobody saw it.
    """

    MUSIC_IN = (0.0, 800)

    def __init__(self, ctx, player, name, new):
        super().__init__(ctx)
        self.player, self.name, self.new = player, name, new
        text = ("|".join((self.t("hello", name=name), self.t("help")))
                if new else self.t("welcome", name=name))
        self.dialog = Dialog(ctx.music, "baker", self.t("baker"), text)
        self.idle = self.now = self.confirm = 0.0
        ctx.leds.show("idle")

    def handle(self, action):
        self.idle = 0.0
        # ◀◀ back to idle from the very first screen (29.9., fair): ◀ did
        # nothing here, so whoever pressed ▶ by mistake was stuck in it.
        if action == "left":
            if self.confirm > 0:
                self.ctx.db.log("quit", self.player, phase="story")
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        if action != "right":
            return None
        if self.dialog.next():
            self.switch_to(GameScene(self.ctx, self.player, self.name, tutorial=self.new))
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
        self.confirm = max(0.0, self.confirm - dt)
        self.dialog.update(dt)
        if self.dialog.due:
            self.handle("right")
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        # The number up top, big, in the game's header style (29.9., fair):
        # small in the corner, nobody noticed it before the end.
        draw(screen, f["small"], self.t("your_no"), 960, 64, GREY)
        draw(screen, f["mid"], f"#{self.player}", 960, 196, ACCENT)
        stamp(screen, self.dialog.face(), 12, 560, 450 + hop(self.now, 0, 6))
        demo(screen, self.now)
        self.dialog.draw(screen, f)
        done = self.dialog.last and not self.dialog.typing
        tag(screen, f, self.player)
        footer(screen, f, self.t("quit"), self.t("go" if done else "next"),
               note=self.t("quit_ok") if self.confirm > 0 else None)


class GameScene(SceneBase):
    """Practice, order, round -- one scene, because it's one screen.

    tut_intro "Up next: practice, doesn't count" + the camera rule. No clock.
    tutorial  Bella: put any treat on the tray. TUT_SECONDS on the fuse,
              which only burns once her line is typed out.
    tut_done  Bella: that one costs X -- or, on timeout, "no problem, it
              was only practice". Either way a soft landing, never a cut.
    read      Oskar names his budget, no clock. The target is rolled here,
              from what's on the tray now -- the practice treat stays.
    order     think time: ladder, countdown, one line of Oskar.
    go        GET READY 3-2-1, the same for ▶ and for the timer.
    play      the round: fuse burning, bar, price strip.

    The camera panes stay the same through practice and round, so the
    player never has to find their way around a new screen. The reading
    screens have none (29.9., fair): with the timer already running under
    the text, nobody read it and nobody pressed ▶ -- the order came as a
    cold shower. Every screen is one or two pages, the queue is waiting.
    """

    MUSIC = None   # idle music carries on; the round stages start at "play"

    # Below the cameras and exactly as wide as both panes together.
    BAR   = pygame.Rect(108, 738, 1704, 56)
    # Scale of the bar: the largest possible target. The tray starts empty
    # and the perfect solution is two or three pieces, so everything plays
    # out under GAP_MAX -- the goal line would otherwise sit in the left
    # quarter. Whoever loads on more runs into the stop on the right; _x()
    # clamps, and "way over" is exactly the right statement.
    SCALE = GAP_MAX + max(VALUES.values())
    GOAL_W, GOAL_OVER = 9, 12   # width and overhang of the goal line
    STRIP_Y = 848               # price strip: sprites here, prices below
    LADDER_Y, LADDER_ROW = 355, 215   # order phase: ladder in two rows, pane area
    GUEST = (GUEST_X, 440)      # the guest stands beside the top-down pane
    POP = (GUEST_X, 610)        # ... and "+2,40" pops up under him

    def __init__(self, ctx, player, name, tutorial=True):
        super().__init__(ctx)
        self.player, self.name = player, name
        # A copy: FakeDetector hands out the same dict every time, and a
        # snapshot that changes under us can't be compared with the next.
        self.marks = dict(ctx.detector.fresh())
        self.total = tray_sum(self.marks)
        self.left = float(ROUND_SECONDS)
        self.confirm = self.skip = self.hit = self.clock = self.still = 0.0
        self.tut = float(TUT_SECONDS)
        self.go, self.how = 0.0, None
        # Every marker seen since the scene started. Practice ends on one
        # that was never seen (29.9.): a leftover blinking back in after the
        # arm passed over it was "new" and ended practice at second 0.
        self.seen = set(self.marks)
        self.taps = 0
        self.fx = self.pop = self.first = None
        self.target = self.dist = None
        ctx.leds.show("idle")
        # Practice even with treats already on the tray (29.9.): a leftover
        # or one stray detection skipped it for new players at the fair.
        # It ends on a NEWLY seen marker, so leftovers can't finish it.
        self.phase, self.hinted = "start", None
        self.log("round", tray=sorted(self.marks), total=self.total, lang=ctx.lang,
                 secs=ROUND_SECONDS, tutorial=tutorial)
        if tutorial:
            self.phase = "tut_intro"
            self.dialog = Dialog(ctx.music, "baker", self.t("baker"), self.t("tut_intro"))
        else:
            self.read()

    def log(self, event, **data):
        """Every round event with phase and scene clock, for the analysis."""
        self.ctx.db.log(event, self.player, phase=self.phase,
                        clock=round(self.clock, 2), **data)

    def read(self):
        """Oskar's order as a reading screen: no clock until ▶ READY."""
        self.phase = "read"
        # The target follows what's actually there. Rolled freely, chance
        # would decide whether someone has to bridge EUR 0.30 or EUR 20.
        self.dist = gap(self.marks, up=True)
        self.target = self.total + self.dist
        self.log("order", tray=sorted(self.marks), total=self.total,
                 dist=self.dist, target=self.target)
        self.dialog = Dialog(self.ctx.music, "guest", self.t("guest"),
                             self.t("order", goal=euro(self.target), think=THINK_SECONDS))

    def plan(self):
        """Read -> think time. Not `think`: that's the countdown."""
        self.phase, self.think = "order", float(THINK_SECONDS)
        self.log("think", read=round(self.clock, 1))
        self.dialog = Dialog(self.ctx.music, "guest", self.t("guest"),
                             self.t("think_q", goal=euro(self.target)))

    def start(self, how):
        """Order -> go: by ▶ on Oskar's last page, or when THINK_SECONDS
        run out. `how` goes to the log, it says who reads the text at all.
        Both land on the same 3-2-1 (29.9.): the timer path used to drop
        people into the round without a word."""
        self.phase, self.dialog, self.how, self.go = "go", None, how, float(GO_SECONDS)
        self.ctx.music.sfx("blip")

    def play(self):
        """Go -> play: the fuse starts burning."""
        self.phase = "play"
        self.log("play", how=self.how, think=round(THINK_SECONDS - self.think, 1),
                 tray=sorted(self.marks), total=self.total, target=self.target)
        self.ctx.music.sfx("start")
        self.ctx.music.stage(self.left)

    def handle(self, action):
        if action == "left":
            self.taps = 0
            if self.confirm > 0:
                self.log("quit", tray=sorted(self.marks), total=self.total,
                         target=self.target, left=round(self.left, 1))
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        if action != "right":
            return None
        if self.phase == "tut_intro" and self.dialog.next():
            self.phase = "tutorial"
            self.dialog = Dialog(self.ctx.music, "baker", self.t("baker"), self.t("tut"))
        elif self.phase == "tutorial":
            # Double-confirm like ◀: the practice is the only place the
            # player learns what the arm does, one bumped ▶ shouldn't cost it.
            if self.skip > 0:
                self.log("tut_skip")
                self.read()
            else:
                self.skip = CONFIRM_SECONDS
        elif self.phase == "tut_done" and self.dialog.next():
            self.read()
        elif self.phase == "read" and self.dialog.next():
            self.plan()
        elif self.phase == "order" and self.dialog.next():
            self.start("button")
        elif self.phase == "play" and CHEAT_TAPS:
            # ponytail: developer shortcut. Doesn't jump into the round, but
            # into its end -- update() handles sound, music, and switch as usual.
            self.taps += 1
            if self.taps >= CHEAT_TAPS:
                self.left = 0.0
        return "ok"

    def update(self, dt):
        self.clock += dt
        self.confirm = max(0.0, self.confirm - dt)
        self.skip = max(0.0, self.skip - dt)
        # One look at the detector per frame: total, overlay, pop-up and
        # sound come from the same snapshot and can't contradict each other.
        marks = dict(self.ctx.detector.fresh())
        new, gone = marks.keys() - self.marks.keys(), self.marks.keys() - marks.keys()
        if new or gone:
            # One pop-up per change, with the net price: two treats at once
            # show "+5,10", not two boxes on top of each other.
            v = sum(VALUES[i] for i in new) - sum(VALUES[i] for i in gone)
            self.pop = [min(new or gone),
                        ("+" if v >= 0 else "-") + euro(abs(v), sign=False), 0.0]
            self.still = 0.0
            self.log("tray", add=sorted(new), off=sorted(gone), total=tray_sum(marks),
                     target=self.target, left=round(self.left, 1))
        if new:
            # Only on NEWLY detected, otherwise it fires DETECT_HZ times a second.
            self.ctx.music.sfx("blip")
            if self.first is None:
                self.first = self.clock
            if self.phase == "tutorial" and (placed := new - self.seen):
                self.log("tut_done", treat=min(placed))
                self.phase = "tut_done"
                self.fx = Sprinkles(*self.POP)
                self.ctx.music.sfx("ok")
                self.dialog = Dialog(self.ctx.music, "baker", self.t("baker"),
                                     self.t("tut_done", price=euro(VALUES[min(placed)])))
        self.seen |= marks.keys()
        self.marks = marks
        self.total = tray_sum(marks)
        if self.pop:
            self.pop[2] += dt
            if self.pop[2] > POP_SECONDS:
                self.pop = None
        if self.dialog:
            self.dialog.update(dt)
            # Pages turn themselves -- except in practice, where ▶ means
            # skip, and in the think time, where it starts the round.
            if self.dialog.due and self.phase in ("tut_intro", "tut_done", "read"):
                self.log("auto", page=self.dialog.i)
                self.handle("right")
        if self.phase == "order":
            self.think -= dt
            if self.think <= 0:
                self.start("timer")
        elif self.phase == "go":
            n = math.ceil(self.go)
            self.go -= dt
            if self.go <= 0:
                self.play()
            elif math.ceil(self.go) < n:
                self.ctx.music.sfx("blip")      # one tick per number
        if self.phase == "tutorial":
            # The fuse waits until Bella's line stands (29.9., floor: it
            # burned while she was still typing).
            if self.dialog.wait > TUT_GRACE:
                self.tut -= dt
            if self.tut <= 0:
                # A soft landing instead of a cut straight to Oskar: failing
                # the practice has to feel fine (29.9., floor).
                self.log("tut_timeout")
                self.phase = "tut_done"
                self.dialog = Dialog(self.ctx.music, "baker", self.t("baker"),
                                     self.t("tut_fail"))
        if self.phase != "play":
            if self.fx:
                self.fx.update(dt)
            return

        self.left -= dt
        self.still += dt
        # A hit must hold, not flash: the hysteresis in fresh() catches the
        # flicker, PERFECT_HOLD catches the intent. If fewer than
        # PERFECT_HOLD seconds remain, the counter doesn't fill up and the
        # round ends via left -- no special case for "right before the end".
        self.hit = self.hit + dt if self.total == self.target else 0.0
        if self.hit > 0:
            self.fx = self.fx or Sprinkles(960, 196)    # pops from PERFECT
            self.fx.update(dt)
        else:
            self.fx = None
        h = self.hint()
        if h != self.hinted:
            self.hinted = h
            if h is not None:
                self.log("hint", treat=h, take=h in self.marks, total=self.total,
                         target=self.target, left=round(self.left, 1))
        self.ctx.music.stage(self.left)
        # The LEDs still go red for the last seconds: that's for the booth
        # team, not the player, so the screen stays calm.
        self.ctx.leds.show("hurry" if self.left <= WARN_SECONDS else "game",
                           max(0.0, self.left) / ROUND_SECONDS)
        if self.left <= 0 or self.hit >= PERFECT_HOLD:
            self.ctx.music.sfx("finish")
            # left gets clamped: the loop counts past zero, and a negative
            # time left would be a lie in the database instead of a zero.
            res = Result(self.target, self.total, self.dist,
                         max(0.0, self.left), self.marks)
            self.log("end", why="perfect" if self.hit >= PERFECT_HOLD else "time",
                     tray=sorted(self.marks), total=self.total, target=self.target,
                     off=abs(self.target - self.total), left=round(res.left, 1),
                     first=self.first)
            # Everything the round physically was -- the database computes
            # the score itself, so a later formula also applies to old rounds.
            self.ctx.db.add(self.name, res.off, goal=res.target, total=res.total,
                            dist=res.dist, secs=res.left, player=self.player,
                            first=self.first)
            self.switch_to(DisplayScoreScene(self.ctx, res, self.player))

    def hint(self):
        """The next treat to move on a shortest way to the target -- once the
        tray has sat still for HINT_SECONDS. A hop instead of a sentence: it points at the
        answer without reading it out."""
        if self.phase != "play" or self.still < HINT_SECONDS or self.total == self.target:
            return None
        # First step of a shortest way, not the greedy closest treat (29.9.)
        return next_move(frozenset(self.marks), self.target)

    def mood(self):
        """Oskar's face: sweating when over budget, beaming when it's exact."""
        if self.hit > 0:
            return "guest_joy"
        return "guest_sweat" if self.target and self.total > self.target else "guest"

    def overlay(self, screen, r, mirror=False, ud=False):
        """Detection window and a frame around every marker the camera sees.

        The frame answers "did it count?" right on the image, where the
        player is looking anyway -- without covering the treat the way a
        price label did. Flipped like the pane (pnp-cam top flip).
        """
        fx = (lambda x: 1 - x) if mirror else (lambda x: x)
        fy = (lambda y: 1 - y) if ud else (lambda y: y)
        px = lambda x, y: (r.x + fx(x) * r.w, r.y + fy(y) * r.h)
        rx, ry, rw, rh = TRAY_ROI
        (x0, y0), (x1, y1) = px(rx, ry), px(rx + rw, ry + rh)
        pygame.draw.rect(screen, GREY, (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)),
                         MARK_WIDTH)
        for quad in self.marks.values():
            pygame.draw.polygon(screen, ACCENT, [px(x, y) for x, y in quad], MARK_WIDTH)

    def bar(self, screen):
        """Where the total stands and where it needs to go, as one image.

        Fill left of the line means load more, right of it means take away,
        and how far is visible without subtracting. The candy cane travels:
        motion is decoration, length remains the only statement.
        """
        r = self.BAR
        fill = stripes(r.w, r.h, ACCENT)
        off = round(self.clock * 40) % 48
        screen.blit(fill, r.topleft, (48 - off, 0, self._x(self.total) - r.x, r.h))
        pygame.draw.rect(screen, GREY, r, 3)
        # The goal line sticks out at top and bottom. Without the overhang
        # it disappears exactly when the fill has almost reached it.
        screen.fill(WHITE, (self._x(self.target) - self.GOAL_W // 2,
                            r.y - self.GOAL_OVER,
                            self.GOAL_W, r.h + 2 * self.GOAL_OVER))

    def strip(self, screen, f):
        """Every treat with its price, cheap to expensive -- which is also
        small to big. What's on the tray is pink; the hint hops."""
        hint = self.hint()
        blink = int(self.clock * 4) % 2
        for i, k in enumerate(sorted(VALUES, key=VALUES.get)):
            x = self.BAR.x + self.BAR.w * (i + 0.5) / len(VALUES)
            pic(screen, k, 190, 68, x, self.STRIP_Y + 32
                + (hop(self.clock, 0, 8) if k == hint else 0), 4)
            # The hinted price blinks along with the hop: 8 px alone was too
            # subtle to catch from the leader arm.
            color = ACCENT if k in self.marks else WHITE
            if k == hint and blink:
                color = BG
            draw(screen, f["tiny"], euro(VALUES[k], sign=False), x, self.STRIP_Y + 54, color)

    def ladder(self, screen, f):
        """Oskar's order: every treat with its price, cheap to dear, in two
        rows where the panes usually are -- one row left the prices too
        small to read from the leader arm."""
        order = sorted(VALUES, key=VALUES.get)
        per = (len(order) + 1) // 2
        for i, k in enumerate(order):
            row, col = divmod(i, per)
            n = per if row == 0 else len(order) - per
            x = WIDTH * (col + 0.5) / n
            y = self.LADDER_Y + row * self.LADDER_ROW
            # Standing on one line, so bigger print = bigger picture reads
            pic(screen, k, 300, 110, x, y + 40, 5)
            draw(screen, f["small"], euro(VALUES[k], sign=False), x, y + 90, WHITE)

    def _x(self, value):
        """Price -> x in the bar. Clamped so nothing runs out."""
        r = self.BAR
        return r.x + round(r.w * min(max(value, 0), self.SCALE) / self.SCALE)

    def render(self, screen):
        # Priority is the camera images: the player steers the arm by them.
        f = self.ctx.fonts
        screen.fill(BG)
        # No panes while Oskar orders (29.9., fair): with the image on,
        # people started placing treats before the round. The ladder takes
        # their place instead, big enough to do the sums from.
        reading = self.phase in ("tut_intro", "tut_done", "read", "order", "go")
        views = () if reading else zip(self.ctx.views, CAM_POS)
        # The prices only come with the think time (29.9.): shown while
        # Oskar still talks, people stared at them and missed the order.
        if self.phase == "order":
            self.ladder(screen, f)
        if self.phase == "read":
            stamp(screen, self.dialog.face(), 10, 960, 520 + hop(self.clock, 0, 6))
        if self.phase == "tut_intro":     # Bella and the arm, as in the story
            stamp(screen, self.dialog.face(), 12, 560, 450 + hop(self.clock, 0, 6))
            demo(screen, self.clock)
        if self.phase == "tut_done":      # ... and the arm going back to rest
            stamp(screen, self.dialog.face(), 12, 560, 450 + hop(self.clock, 0, 6))
            park_demo(screen, self.clock)
        for view, pos in views:
            cam = view.surface()
            if cam:
                r = cam.get_rect(center=pos)
                screen.fill(GREY, r.inflate(8, 8))
                screen.blit(cam, r)
                if view.det:
                    self.overlay(screen, r, getattr(view, "mirror", False),
                                 getattr(view, "ud", False))
        if self.fx:
            self.fx.draw(screen)    # over the panes, under the numbers
        # The top says what to do, with a verb: "ADD 3,20 €", not "OFF BY".
        # Every phase uses the same two lines, so there's one place to look.
        big = f["big"]
        if self.phase == "tut_intro":
            label, value, big = self.t("up_next"), self.t("just_practice"), f["mid"]
        elif self.phase == "tutorial":
            label = self.t("practice_n", n=max(0, math.ceil(self.tut)))
            value, big = self.t("tut_head"), f["mid"]
        elif self.phase == "tut_done":
            # The practice is over and the hand has to leave the arm: said
            # big, not only in the box (29.9., floor).
            label, value, big = self.t("tut_over"), self.t("let_go"), f["mid"]
        elif self.phase in ("read", "order", "go"):
            label, value = self.t("order_head"), euro(self.target)
        elif self.hit > 0:
            label = self.t("hold", n=int(PERFECT_HOLD - self.hit) + 1)
            value = self.t("perfect")
        else:
            diff = self.target - self.total
            label, value = self.t("add" if diff > 0 else "over"), euro(abs(diff))
        if self.phase == "order":
            label = self.t("think", n=max(0, math.ceil(self.think)))
        draw(screen, f["small"], label, 960, 64, GREY)
        draw(screen, big, value, 960, 196, ACCENT)
        tag(screen, f, self.player)
        if self.phase == "play":    # in "order" his face is in the dialog
            stamp(screen, self.mood(), 6, *self.GUEST)
        if self.pop and not reading:    # would sit on the ladder / Bella
            k, text, age = self.pop
            rise = round(age * 20)
            pic(screen, k, 120, 80, self.POP[0], self.POP[1] + 32 - rise, 4)
            draw(screen, f["tiny"], text, self.POP[0], self.POP[1] + 58 - rise, ACCENT)
        if self.phase == "order":
            fuse(screen, max(0.0, self.think / THINK_SECONDS) if THINK_SECONDS else 0.0,
                 WHITE, self.clock)
        if self.phase == "tutorial":
            fuse(screen, max(0.0, self.tut / TUT_SECONDS) if TUT_SECONDS else 0.0,
                 ACCENT, self.clock)
        if self.phase == "tut_done":
            # Burns down until Oskar comes: the next screen is announced,
            # not a surprise (29.9., floor). One page, so the page clock is it.
            fuse(screen, 1 - min(1.0, self.dialog.wait / PAGE_SECONDS), WHITE, self.clock)
        if self.phase == "go":
            # The budget stays on top, the countdown takes the pane area:
            # the one thing to see before the arm starts to count.
            draw(screen, f["mid"], self.t("get_ready"), 960, 470, WHITE)
            draw(screen, f["big"], max(1, math.ceil(self.go)), 960, 680,
                 CANDY[math.ceil(self.go) % len(CANDY)])
        elif self.dialog:
            self.dialog.draw(screen, f)
        else:
            self.bar(screen)
            self.strip(screen, f)
            frac = min(1.0, max(0.0, self.left / ROUND_SECONDS))
            blink = self.left <= FUSE_PULSE and int(self.clock * 4) % 2
            fuse(screen, frac, WHITE if blink else ACCENT, self.clock)
        # ◀ is permanently there, not only after the first press: a hidden
        # control isn't one. The double-confirm catches an accidental press.
        right = None
        if self.phase == "tutorial":
            right = self.t("skip")
        elif self.dialog:
            done = self.dialog.last and not self.dialog.typing
            right = self.t(dict(tut_intro="go", read="ready", order="go")
                           .get(self.phase, "next") if done else "next")
        footer(screen, f, self.t("quit"), right,
               note=self.t("quit_ok") if self.confirm > 0
               else self.t("skip_ok") if self.skip > 0 and self.phase == "tutorial"
               else None)


class DisplayScoreScene(SceneBase):
    """The score counts up, then the stars, the place, and Oskar says thanks.

    The order is the trick: while the number counts, nothing else is there
    to read, so the count-up is an event and not a table. Everyone gets the
    sprinkles and at least a friendly line -- no failure, just a number.
    """

    # The finish sound needs room to breathe. Let it ring out first, then
    # the idle music fades in -- the silence in between is the effect.
    MUSIC_IN = (2.2, 1500)
    # Seconds until the number settles. Shorter reads like a jump, longer
    # like a loading bar. Stays under MUSIC_IN.
    COUNT = 1.8
    STARS = (800, 960, 1120)

    def __init__(self, ctx, res, player):
        super().__init__(ctx)
        self.res = res
        self.player = player
        self.place, self.count = ctx.db.rank(player)
        self.shown = 0
        self.done = self.bye = False
        self.idle = self.now = self.confirm = 0.0
        self.fx = Sprinkles(960, 300)
        who = ("guest_sweat", "guest", "guest_joy", "guest_joy")[res.stars]
        self.dialog = Dialog(ctx.music, who, self.t("guest"), self.t("react")[res.stars])
        ctx.leds.show("score")

    def handle(self, action):
        self.idle = 0.0
        if action == "left":                # ◀◀ straight to idle, like everywhere
            if self.confirm > 0:
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        if action != "right":
            return None
        if not self.done or self.dialog.typing:
            self.now = max(self.now, self.COUNT)     # skip the count-up
            self.dialog.next()
        elif not self.bye:
            # Oskar has said his thanks; now Bella hands over the number.
            # Last page of the evening, and the only place it's spoken --
            # here it answers a question the player actually has.
            self.bye = True
            self.dialog = Dialog(self.ctx.music, "baker", self.t("baker"),
                                 self.t("remember", no=self.player))
        else:
            self.switch_to(IdleScene(self.ctx))
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
        self.confirm = max(0.0, self.confirm - dt)
        self.fx.update(dt)
        # Fast in, slow out: (1-k)**3 is the curve a boxing machine winds
        # down with. Counting up linearly looks like a progress bar.
        k = min(1.0, self.now / self.COUNT)
        shown = round(self.res.score * (1 - (1 - k) ** 3))
        if shown // 100 > self.shown // 100:
            self.ctx.music.sfx("blip")     # one tick per hundred
        self.shown = shown
        if not self.done and k >= 1.0:
            self.done = True                    # fires once, even at 0 points
            self.ctx.music.sfx("ok")
        if self.done:
            self.dialog.update(dt)
            # Pages turn themselves like everywhere else (29.9.): a player
            # who walked off held the machine for the full IDLE_TIMEOUT.
            if self.dialog.due:
                self.handle("right")
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        self.fx.draw(screen)
        draw(screen, f["small"], self.t("score"), 960, 110, GREY)
        draw(screen, f["big"], self.shown, 960, 270, ACCENT)
        if self.done:
            for i, x in enumerate(self.STARS):
                on = i < self.res.stars
                stamp(screen, "star_on" if on else "star_off", 6, x,
                      460 + (hop(self.now, i, 8) if on else 0))
            # The place has been read by the time Bella speaks; the number
            # takes its line, bigger and pink -- it's the one thing worth
            # taking home from this screen.
            if self.bye:
                draw(screen, f["mid"], self.t("player", no=self.player), 960, 600, ACCENT)
            else:
                draw(screen, f["small"],
                     self.t("rank", place=self.place, count=self.count), 960, 600, WHITE)
            self.dialog.draw(screen, f)
        # Also in the corner, even on the page where Bella says it out loud:
        # the corner is where it has stood since the entry screen, and
        # "remember your number" lands better pointing at a spot the player
        # has already seen it in.
        tag(screen, f, self.player)
        footer(screen, f, self.t("quit"), self.t("next"),
               note=self.t("quit_ok") if self.confirm > 0 else None)


if __name__ == "__main__":
    # Layout self-test. Exactly the bug that was in here twice: an element
    # drifts below SAFE_BOTTOM or covers another one, and it only becomes
    # visible once the DB has enough rows. The test intercepts every
    # draw() call and checks the rectangles -- no screenshot, no
    # framework, no reference image that would need maintaining.
    # Runs every scene in both languages: German words are longer.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    _fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}
    _all = {**SPRITES, **EXTRAS}

    boxes, _draw = [], draw
    def draw(screen, font, text, x, y, color):          # noqa: F811
        w, h = font.size(str(text))
        boxes.append((str(text), x - w/2, y - h/2, x + w/2, y + h/2))

    # Sprites count too, with their full edge.
    def stamp(screen, name, scale, x, y):               # noqa: F811
        n = len(SHAPES[_all[name][0]]) * scale / 2
        boxes.append((name, x - n, y - n, x + n, y + n))

    def area(name, rect):                               # noqa: F811
        boxes.append((name, rect.left, rect.top, rect.right, rect.bottom))

    class _Stub:
        """Covers Music, DB, and Detector -- they all do nothing in the test."""
        tray = {}
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [("#999", 999) for i in range(n)]
        def fresh(self):     return self.tray
        def rank(self, p):   return 999, 999
        def new_player(self, name): return 999
        def next_player(self): return 999
        def players_named(self, name): return [(999, 3, "14:20")]
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             leds=_s, views=(), lang="en"))()

    # Panes aren't a draw(), but they still count toward overlap.
    panes = [("pane", x - w//2 - 4, y - h//2 - 4, x + w//2 + 4, y + h//2 + 4)
             for (x, y), (w, h) in zip(CAM_POS, CAM_VIEWS)]
    G = GameScene
    bar = [("bar", G.BAR.x, G.BAR.y - G.GOAL_OVER, G.BAR.right, G.BAR.bottom + G.GOAL_OVER)]
    fuse_ = [("fuse", 0, 0, WIDTH, FUSE_W), ("fuse", 0, HEIGHT - FUSE_W, WIDTH, HEIGHT),
             ("fuse", 0, 0, FUSE_W, HEIGHT), ("fuse", WIDTH - FUSE_W, 0, WIDTH, HEIGHT)]

    def check(label, scene, extra=(), **state):
        scene.__dict__.update(state)
        boxes.clear()
        scene.render(pygame.Surface((WIDTH, HEIGHT)))
        bs = boxes + list(extra)
        for t, l, tp, r, b in bs:
            assert 0 <= l and r <= WIDTH,  f"{label}: {t!r} x {l}..{r}"
            assert 0 <= tp and b <= HEIGHT, f"{label}: {t!r} y {tp}..{b}"
            assert b <= SAFE_BOTTOM or tp >= FOOTER_Y - 40 or t == "fuse", \
                f"{label}: {t!r} sticks out below SAFE_BOTTOM (y {tp}..{b})"
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, c = bs[i], bs[j]
                assert a[0] == c[0] == "fuse" or not (a[1] < c[3] and c[1] < a[3]
                            and a[2] < c[4] and c[2] < a[4]), \
                    f"{label}: {a[0]!r} overlaps {c[0]!r}"

    def read(d):
        """Every page of a dialog, fully typed."""
        pages = []
        while True:
            d.n = 1e9
            pages.append(d.pages[d.i])
            if d.last:
                return pages
            d.next()

    # The grip, checked on the pixels that actually get drawn rather than on
    # the numbers behind them. Two things have to hold in every frame of the
    # demo loop: the arm never shares a pixel with the treat, and while it is
    # being carried a jaw is right there on each side -- push the treat one
    # arm pixel either way and it runs into one. That pair is what pins down
    # arm.TREAT, arm.SHUT and arm.TCP; a new treat sprite that does not fit
    # these jaws fails here instead of quietly going back to clipping.
    #
    # One arm pixel is also the tightest a grip can be: the arm is drawn at
    # four millimetres a pixel, so a jaw's edge can only land on that grid,
    # while the treat lands where the kinematics put it. Asking for less air
    # than that asks for overlap in whichever frame rounds the other way.
    _slack = ARM_SCALE + 1
    _t = sprite(DEMO_TREAT, DEMO_SCALE)
    _tm, (_w, _h) = pygame.mask.from_surface(_t), _t.get_size()
    for _k, (_pose, _spot) in enumerate(arm.loop()):
        _s2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        arm.draw(_s2, ARM_BASE, ARM_SCALE, _pose)
        _am = pygame.mask.from_surface(_s2)
        _x, _y = treat_at(_spot)
        _off = (_x - _w // 2, _y - _h // 2)
        assert not _am.overlap_area(_tm, _off), f"demo {_k}: the arm cuts into the treat"
        if _k // arm.STEPS in arm.CARRY:
            for _d in (-_slack, _slack):
                assert _am.overlap_area(_tm, (_off[0] + _d, _off[1])), \
                    f"demo {_k}: no jaw on the {'left' if _d < 0 else 'right'}"

    widest = dict(name="#999", no=999, goal=euro(88), price=euro(52), think=99)
    for lang in TEXT:
        ctx.lang = lang
        T = TEXT[lang]
        # Every speech line fits the box: at most three lines per page.
        for key in ("hello", "help", "welcome", "tut_intro", "tut", "tut_done",
                    "tut_fail", "order", "think_q", "remember"):
            for page in T[key].format(**widest).split("|"):
                n = len(textwrap.wrap(page, Dialog.COLS))
                assert n <= 3, f"{lang}.{key}: {n} lines: {page!r}"
        for line in T["react"]:
            assert len(textwrap.wrap(line, Dialog.COLS)) <= 3, (lang, line)

        check(f"{lang} idle", IdleScene(ctx))
        check(f"{lang} idle ask", IdleScene(ctx), ask=2.0)
        if not ASK_NAME:        # ▶ skips the name, ▼ lists every number
            idle = IdleScene(ctx)
            idle.handle("right")
            assert isinstance(idle.next, StoryScene) and idle.next.name == "#999"
            idle.handle("down")
            assert isinstance(idle.next, PickScene) and idle.next.name is None
            idle.next.handle("right")
            assert idle.next.next.name == "#999", "returning player keeps the #"
        for again in (False, True):
            for cur in range(3):
                check(f"{lang} entry {again} {cur}", EntryScene(ctx, again), cursor=cur)
            check(f"{lang} entry error", EntryScene(ctx, again), cursor=2, error=2.0)

        # The pick list: one row, and more rows than fit -- the window has
        # to scroll with the cursor instead of drawing past the hint line.
        rows = [(n, n % 7, "14:20") for n in range(999, 989, -1)]
        check(f"{lang} pick one", PickScene(ctx, "WWW", rows[:1]))
        check(f"{lang} pick all", PickScene(ctx, None, rows))
        for cur in (0, 4, 9):
            check(f"{lang} pick {cur}", PickScene(ctx, "WWW", rows), cursor=cur)

        for new in (True, False):
            st = StoryScene(ctx, 999, "WWW", new)
            for i, _ in enumerate(read(st.dialog)):
                st.dialog.i, st.dialog.n = i, 1e9
                # The demo is one box, so one frame would do -- but the
                # treat is drawn by the arm's own kinematics, and a pose
                # that pushes it out of that box is exactly the kind of
                # thing nobody looks at. So walk the whole loop.
                for k in range(len(arm.loop())):
                    check(f"{lang} story new={new} page {i} demo {k}", st,
                          now=k / arm.HZ)

        # The phases of a round: announcement -> ▶ -> practice, a treat
        # lands -> tut_done, ▶ -> read, ▶ -> order (think), ▶ -> play.
        # tutorial has exactly one page: ▶ there means skip, not next page.
        assert "|" not in T["tut"]
        # ... and so has the practice end: its fuse is the page clock
        assert "|" not in T["tut_done"] + T["tut_fail"]
        _s.tray = {}
        g = GameScene(ctx, 999, "WWW")
        assert g.phase == "tut_intro"
        for k in range(len(arm.loop())):
            check(f"{lang} tut_intro demo {k}", g, clock=k / arm.HZ)
        read(g.dialog)
        g.handle("right")
        assert g.phase == "tutorial"
        check(f"{lang} tutorial", g, panes + fuse_)
        g.handle("right")
        assert g.phase == "tutorial" and g.skip > 0, "one ▶ only asks"
        check(f"{lang} tutorial skip?", g, panes + fuse_)
        g.update(CONFIRM_SECONDS + 0.1)
        g.handle("right")
        assert g.phase == "tutorial", "the question times out"
        g.handle("right")
        assert g.phase == "read", "▶▶ skips"
        # Nobody manages the practice: its clock ends it -- but only once
        # Bella's line stands, and it lands on "no problem", not on Oskar.
        g = GameScene(ctx, 999, "WWW")
        read(g.dialog)
        g.handle("right")
        for _ in range(8):
            g.update(0.25)
        assert g.tut == TUT_SECONDS, "the fuse burns while Bella still types"
        for _ in range(4 * (TUT_SECONDS + TUT_GRACE + 2)):    # + typing
            g.update(0.25)
        assert g.phase == "tut_done" and g.dialog.pages[0] == \
            textwrap.wrap(T["tut_fail"], Dialog.COLS), "the practice times out softly"
        check(f"{lang} tut_fail", g, fuse_)
        assert g.next is g, "no button in practice is no walk-away"
        # Nobody presses anything: every reading page turns itself, then
        # the think time runs out -- the round starts without a button.
        for _ in range(400):
            g.update(0.25)
        assert g.phase == "play" and g.next is g
        # A leftover that blinks out under the arm and back is no placement
        _s.tray = {9: [(.3, .3)] * 4}
        g = GameScene(ctx, 999, "WWW")
        read(g.dialog)
        g.handle("right")
        _s.tray = {}
        g.update(0.05)
        _s.tray = {9: [(.3, .3)] * 4}
        g.update(0.05)
        assert g.phase == "tutorial", "a leftover ended the practice"
        _s.tray = {}
        # ... but the practice never skips itself
        g = GameScene(ctx, 999, "WWW")
        read(g.dialog)
        g.handle("right")
        g.update(PAGE_SECONDS + 1)
        g.update(PAGE_SECONDS + 1)
        assert g.phase == "tutorial" and g.skip == 0
        st = StoryScene(ctx, 999, "WWW", True)
        for _ in range(400):
            st.update(0.25)
        assert isinstance(st.next, GameScene), "Bella's pages turn themselves"
        # ◀◀ leaves from the very first screen, one ◀ only asks
        st = StoryScene(ctx, 999, "WWW", True)
        st.handle("left")
        assert st.next is st and st.confirm > 0
        check(f"{lang} story quit?", st)
        st.handle("left")
        assert isinstance(st.next, IdleScene), "◀◀ on Bella goes back"
        g = GameScene(ctx, 999, "WWW")
        read(g.dialog)
        g.handle("right")
        _s.tray = {9: [(.3, .3)] * 4}
        g.update(0.05)
        assert g.phase == "tut_done" and g.pop and g.first is not None
        for k in range(len(arm.park_loop())):     # every frame of the way to rest
            check(f"{lang} tut_done park {k}", g, fuse_, clock=k / arm.HZ)
        read(g.dialog)
        g.handle("right")
        assert g.phase == "read" and g.target > g.total
        g.update(THINK_SECONDS + 0.1)
        assert g.phase == "read", "no clock while reading"
        for i, _ in enumerate(read(g.dialog)):
            g.dialog.i, g.dialog.n = i, 1e9
            check(f"{lang} read page {i}", g, [])    # own screen, no panes
        g.handle("right")
        assert g.phase == "order"
        check(f"{lang} order", g, fuse_)
        read(g.dialog)
        g.handle("right")
        assert g.phase == "go" and g.dialog is None, "▶ goes to the 3-2-1"
        for go in (2.5, 1.5, 0.5):
            check(f"{lang} go {go}", g, [], go=go)
        g.update(GO_SECONDS + 0.1)
        assert g.phase == "play"
        # Nobody presses ▶: the think time runs out, the same 3-2-1, the round
        g2 = GameScene(ctx, 999, "WWW", tutorial=False)
        assert g2.phase == "read"
        read(g2.dialog)
        g2.handle("right")
        g2.update(THINK_SECONDS + 0.1)
        assert g2.phase == "go" and g2.dialog is None
        g2.update(GO_SECONDS + 0.1)
        assert g2.phase == "play"
        # Four treats off the actual price list, not four literal IDs: which
        # markers exist is print-day data since 2026-09-25.
        _s.tray = {i: [(.3, .3)] * 4 for i in sorted(VALUES)[:4]}
        g.update(0.05)
        check(f"{lang} play", g, panes + bar + fuse_)
        check(f"{lang} play confirm", g, panes + bar + fuse_, confirm=2.0)
        check(f"{lang} play perfect", g, panes + bar + fuse_, confirm=0.0,
              hit=1.0, total=g.target)
        check(f"{lang} play over", g, panes + bar + fuse_, hit=0.0, total=g.target + 40)
        check(f"{lang} play hint", g, panes + bar + fuse_, total=0, still=99.0, clock=0.3)
        # Edge cases of the bar: nothing on it, and the widest number that
        # can ever appear in the header (the sum of all prices).
        check(f"{lang} play full", g, panes + bar + fuse_, total=sum(VALUES.values()))
        assert g.hint() is not None

        for stars, res in enumerate((
                Result(target=67, total=0, dist=67, left=0.0, marks={}),
                Result(target=67, total=40, dist=67, left=0.0, marks={0: 1}),
                Result(target=67, total=64, dist=67, left=0.0, marks={0: 1, 9: 1}),
                Result(target=67, total=67, dist=50, left=80.0, marks={0: 1}))):
            assert res.stars == stars, (res, res.stars)
            check(f"{lang} score counting {stars}", DisplayScoreScene(ctx, res, 999))
            sc = DisplayScoreScene(ctx, res, 999)
            check(f"{lang} score done {stars}", sc, shown=res.score, done=True, now=2.5)
            read(sc.dialog)
            sc.handle("right")                  # Oskar done -> Bella, the number
            assert sc.bye, "the last ▶ hands over to Bella, not to idle"
            check(f"{lang} score bye {stars}", sc, shown=res.score, done=True, now=2.5)
            sc = DisplayScoreScene(ctx, res, 999)
            for _ in range(4 * 25):
                sc.update(0.25)
            assert isinstance(sc.next, IdleScene), "the score pages turn themselves"
            sc = DisplayScoreScene(ctx, res, 999)
            sc.handle("left")
            check(f"{lang} score quit? {stars}", sc)
            sc.handle("left")
            assert isinstance(sc.next, IdleScene), "◀◀ on the score goes back"

    # The fuse: full at the start, gone at the end, never outside the screen.
    surf = pygame.Surface((WIDTH, HEIGHT))
    for frac in (1.0, 0.5, 0.01, 0.0):
        fuse(surf, frac, ACCENT, 0.0)
    print("ok")
