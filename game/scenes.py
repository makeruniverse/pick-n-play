import math
import random
import textwrap
import pygame
from functools import lru_cache
from typing import NamedTuple
from balance import gap, points
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
        self.i, self.n, self.t = 0, 0.0, 0.0

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

    def handle(self, action):
        if action == "right":
            self.switch_to(EntryScene(self.ctx))
        elif action == "down":
            self.switch_to(EntryScene(self.ctx, digits=True))
        elif action == "up":
            if self.ask > 0:
                self.ctx.lang = "de" if self.ctx.lang == "en" else "en"
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
        footer(screen, f, self.t("lang"), self.t("again"),
               note=self.t("lang_ok") if self.ask > 0 else None)


class EntryScene(SceneBase):
    """Three letters (new player) or three digits (player number).

    The arrows sit where the button acts: a blue ▲ above the active letter,
    a yellow ▼ below it. The old screen had big ◀ ▶ arrows at the sides that
    promised a control the buttons didn't have.
    """

    MUSIC_IN = (0.0, 800)   # fades in, instead of hitting hard out of silence
    COLS = (750, 960, 1170)
    LETTERS, DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789"

    def __init__(self, ctx, digits=False):
        super().__init__(ctx)
        self.digits = digits
        self.chars = self.DIGITS if digits else self.LETTERS
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
        if not self.digits:
            no = self.ctx.db.new_player(text)
            self.switch_to(StoryScene(self.ctx, no, text, new=True))
            return "ok"
        name = self.ctx.db.player(int(text))
        if not name:
            self.error = CONFIRM_SECONDS
            return None     # "nope", and the footer says why
        self.switch_to(StoryScene(self.ctx, int(text), name, new=False))
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
        draw(screen, f["mid"], self.t("ask_no" if self.digits else "ask_name"),
             960, 150, ACCENT)
        for i, x in enumerate(self.COLS):
            on = i == self.cursor
            draw(screen, f["big"], self.chars[self.slots[i]], x, 470,
                 ACCENT if on else WHITE)
            if on:
                draw_hint(screen, f["mid"], "▲", x, 320 + hop(self.now, 0, 6))
                draw_hint(screen, f["mid"], "▼", x, 620 - hop(self.now, 0, 6))
        draw_hint(screen, f["small"], self.t("pick_123" if self.digits else "pick_abc"),
                  960, 760, GREY)
        last = self.cursor == len(self.slots) - 1
        footer(screen, f, self.t("back"), self.t("done" if last else "next"),
               note=self.t("unknown") if self.error > 0 else None)


class StoryScene(SceneBase):
    """Bella says hello, and gives out the player number.

    The number is the link to the sign-up form, so it gets its own page and
    stays on screen from then on -- the booth team reads it off here. A
    returning player gets one line and skips the practice.
    """

    MUSIC_IN = (0.0, 800)

    def __init__(self, ctx, player, name, new):
        super().__init__(ctx)
        self.player, self.name, self.new = player, name, new
        text = ("|".join((self.t("hello", name=name), self.t("number", no=player),
                          self.t("help")))
                if new else self.t("welcome", name=name))
        self.dialog = Dialog(ctx.music, "baker", self.t("baker"), text)
        self.idle = self.now = 0.0
        ctx.leds.show("idle")

    def handle(self, action):
        self.idle = 0.0
        if action != "right":
            return None
        if self.dialog.next():
            self.switch_to(GameScene(self.ctx, self.player, self.name, tutorial=self.new))
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
        self.dialog.update(dt)
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        parade(screen, self.now, 96, 60)
        stamp(screen, self.dialog.face(), 12, 560, 450 + hop(self.now, 0, 6))
        if self.dialog.i >= 1 or not self.new:
            draw(screen, f["mid"], self.t("player", no=self.player), 1360, 450, ACCENT)
        self.dialog.draw(screen, f)
        done = self.dialog.last and not self.dialog.typing
        footer(screen, f, right=self.t("go" if done else "next"))


class GameScene(SceneBase):
    """Practice, order, round -- one scene, because it's one screen.

    tutorial  Bella: put any treat on the tray. Waits for the camera.
    tut_done  Bella: that one costs X. The first success, before any clock.
    order     Oskar names his budget. The target is rolled here, from what's
              on the tray now -- the practice treat stays and counts.
    play      the round: fuse burning, bar, price strip.

    The camera panes stay the same through all four, so the player never
    has to find their way around a new screen.
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
    GUEST = (960, 440)          # the guest stands between the panes
    POP = (960, 610)            # ... and "+2,40" pops up under him

    def __init__(self, ctx, player, name, tutorial=True):
        super().__init__(ctx)
        self.player, self.name = player, name
        # A copy: FakeDetector hands out the same dict every time, and a
        # snapshot that changes under us can't be compared with the next.
        self.marks = dict(ctx.detector.fresh())
        self.total = tray_sum(self.marks)
        self.left = float(ROUND_SECONDS)
        self.confirm = self.hit = self.clock = self.still = 0.0
        self.taps = 0
        self.fx = self.pop = self.first = None
        self.target = self.dist = None
        ctx.leds.show("idle")
        # A treat left over from the last round: no practice needed, the
        # tray already shows what the camera sees.
        if tutorial and not self.marks:
            self.phase = "tutorial"
            self.dialog = Dialog(ctx.music, "baker", self.t("baker"), self.t("tut"))
        else:
            self.order()

    def order(self):
        self.phase = "order"
        # The target follows what's actually there. Rolled freely, chance
        # would decide whether someone has to bridge EUR 0.30 or EUR 20.
        self.dist = gap(self.marks, up=True)
        self.target = self.total + self.dist
        self.dialog = Dialog(self.ctx.music, "guest", self.t("guest"),
                             self.t("order", goal=euro(self.target)))

    def handle(self, action):
        if action == "left":
            self.taps = 0
            if self.confirm > 0:
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        if action != "right":
            return None
        if self.phase == "tutorial":
            self.order()
        elif self.phase == "tut_done" and self.dialog.next():
            self.order()
        elif self.phase == "order" and self.dialog.next():
            self.phase, self.dialog = "play", None
            self.ctx.music.stage(self.left)
            return "start"
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
        # One look at the detector per frame: total, overlay, pop-up and
        # sound come from the same snapshot and can't contradict each other.
        marks = dict(self.ctx.detector.fresh())
        new, gone = marks.keys() - self.marks.keys(), self.marks.keys() - marks.keys()
        if new or gone:
            # One pop-up per change, with the net price: two treats at once
            # show "+5,10", not two boxes on top of each other.
            v = sum(VALUES[i] for i in new) - sum(VALUES[i] for i in gone)
            self.pop = [SPRITE[min(new or gone)],
                        ("+" if v >= 0 else "-") + euro(abs(v), sign=False), 0.0]
            self.still = 0.0
        if new:
            # Only on NEWLY detected, otherwise it fires DETECT_HZ times a second.
            self.ctx.music.sfx("blip")
            if self.first is None:
                self.first = self.clock
            if self.phase == "tutorial":
                self.phase = "tut_done"
                self.fx = Sprinkles(*self.POP)
                self.ctx.music.sfx("ok")
                self.dialog = Dialog(self.ctx.music, "baker", self.t("baker"),
                                     self.t("tut_done", price=euro(VALUES[min(new)])))
        self.marks = marks
        self.total = tray_sum(marks)
        if self.pop:
            self.pop[2] += dt
            if self.pop[2] > POP_SECONDS:
                self.pop = None
        if self.dialog:
            self.dialog.update(dt)
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
            # Everything the round physically was -- the database computes
            # the score itself, so a later formula also applies to old rounds.
            self.ctx.db.add(self.name, res.off, goal=res.target, total=res.total,
                            dist=res.dist, secs=res.left, player=self.player,
                            first=self.first)
            self.switch_to(DisplayScoreScene(self.ctx, res, self.player))

    def hint(self):
        """The treat that gets closest in one move -- once the tray has sat
        still for HINT_SECONDS. A hop instead of a sentence: it points at the
        answer without reading it out."""
        diff = (self.target or 0) - self.total
        if self.phase != "play" or self.still < HINT_SECONDS or not diff:
            return None
        pool = [i for i in VALUES if (i in self.marks) == (diff < 0)]
        return min(pool, key=lambda i: abs(abs(diff) - VALUES[i]), default=None)

    def mood(self):
        """Oskar's face: sweating when over budget, beaming when it's exact."""
        if self.hit > 0:
            return "guest_joy"
        return "guest_sweat" if self.target and self.total > self.target else "guest"

    def overlay(self, screen, r):
        """Detection window and a frame around every marker the camera sees.

        The frame answers "did it count?" right on the image, where the
        player is looking anyway -- without covering the treat the way a
        price label did.
        """
        rx, ry, rw, rh = TRAY_ROI
        pygame.draw.rect(screen, GREY, (r.x + rx * r.w, r.y + ry * r.h,
                                        rw * r.w, rh * r.h), MARK_WIDTH)
        for quad in self.marks.values():
            pygame.draw.polygon(screen, ACCENT, [(r.x + x * r.w, r.y + y * r.h)
                                                 for x, y in quad], MARK_WIDTH)

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
            stamp(screen, SPRITE[k], 4, x,
                  self.STRIP_Y + (hop(self.clock, 0, 8) if k == hint else 0))
            # The hinted price blinks along with the hop: 8 px alone was too
            # subtle to catch from the leader arm.
            color = ACCENT if k in self.marks else WHITE
            if k == hint and blink:
                color = BG
            draw(screen, f["tiny"], euro(VALUES[k], sign=False), x, self.STRIP_Y + 54, color)

    def _x(self, value):
        """Price -> x in the bar. Clamped so nothing runs out."""
        r = self.BAR
        return r.x + round(r.w * min(max(value, 0), self.SCALE) / self.SCALE)

    def render(self, screen):
        # Priority is the camera images: the player steers the arm by them.
        f = self.ctx.fonts
        screen.fill(BG)
        for view, pos in zip(self.ctx.views, CAM_POS):
            cam = view.surface()
            if cam:
                r = cam.get_rect(center=pos)
                screen.fill(GREY, r.inflate(8, 8))
                screen.blit(cam, r)
                if view.det:
                    self.overlay(screen, r)
        if self.fx:
            self.fx.draw(screen)    # over the panes, under the numbers
        # The top says what to do, with a verb: "ADD 3,20 €", not "OFF BY".
        # Every phase uses the same two lines, so there's one place to look.
        big = f["big"]
        if self.phase in ("tutorial", "tut_done"):
            label, value, big = self.t("practice"), self.t("tut_head"), f["mid"]
        elif self.phase == "order":
            label, value = self.t("order_head"), euro(self.target)
        elif self.hit > 0:
            label = self.t("hold", n=int(PERFECT_HOLD - self.hit) + 1)
            value = self.t("perfect")
        else:
            diff = self.target - self.total
            label, value = self.t("add" if diff > 0 else "over"), euro(abs(diff))
        draw(screen, f["small"], label, 960, 64, GREY)
        draw(screen, big, value, 960, 196, ACCENT)
        tag = self.t("player", no=self.player)
        draw_left(screen, f["tiny"], tag, WIDTH - 30 - f["tiny"].size(tag)[0], 40, GREY)
        if self.phase in ("order", "play"):
            stamp(screen, self.mood(), 6, *self.GUEST)
        if self.pop:
            name, text, age = self.pop
            rise = round(age * 20)
            stamp(screen, name, 4, self.POP[0], self.POP[1] - rise)
            draw(screen, f["tiny"], text, self.POP[0], self.POP[1] + 58 - rise, ACCENT)
        if self.dialog:
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
            done = self.phase == "order" and self.dialog.last and not self.dialog.typing
            right = self.t("go" if done else "next")
        footer(screen, f, self.t("quit"), right,
               note=self.t("quit_ok") if self.confirm > 0 else None)


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
        self.place, self.count = ctx.db.rank(player)
        self.shown = 0
        self.done = False
        self.idle = self.now = 0.0
        self.fx = Sprinkles(960, 300)
        who = ("guest_sweat", "guest", "guest_joy", "guest_joy")[res.stars]
        self.dialog = Dialog(ctx.music, who, self.t("guest"), self.t("react")[res.stars])
        ctx.leds.show("score")

    def handle(self, action):
        self.idle = 0.0
        if action != "right":
            return None
        if not self.done or self.dialog.typing:
            self.now = max(self.now, self.COUNT)     # skip the count-up
            self.dialog.next()
        else:
            self.switch_to(IdleScene(self.ctx))
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.now += dt
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
            draw(screen, f["small"], self.t("rank", place=self.place, count=self.count),
                 960, 600, WHITE)
            self.dialog.draw(screen, f)
        footer(screen, f, right=self.t("next"))


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

    class _Stub:
        """Covers Music, DB, and Detector -- they all do nothing in the test."""
        tray = {}
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [(f"WW{i}", 999) for i in range(n)]
        def fresh(self):     return self.tray
        def rank(self, p):   return 999, 999
        def player(self, n): return "WWW" if n else None
        def new_player(self, name): return 999
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             leds=_s, views=(), lang="en"))()

    # Panes aren't a draw(), but they still count toward overlap.
    panes = [("pane", x - CAM_VIEW[0]//2 - 4, y - CAM_VIEW[1]//2 - 4,
                      x + CAM_VIEW[0]//2 + 4, y + CAM_VIEW[1]//2 + 4)
             for x, y in CAM_POS]
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

    widest = dict(name="WWW", no=999, goal=euro(88), price=euro(52))
    for lang in TEXT:
        ctx.lang = lang
        T = TEXT[lang]
        # Every speech line fits the box: at most three lines per page.
        for key in ("hello", "number", "help", "welcome", "tut", "tut_done", "order"):
            for page in T[key].format(**widest).split("|"):
                n = len(textwrap.wrap(page, Dialog.COLS))
                assert n <= 3, f"{lang}.{key}: {n} lines: {page!r}"
        for line in T["react"]:
            assert len(textwrap.wrap(line, Dialog.COLS)) <= 3, (lang, line)

        check(f"{lang} idle", IdleScene(ctx))
        check(f"{lang} idle ask", IdleScene(ctx), ask=2.0)
        for digits in (False, True):
            for cur in range(3):
                check(f"{lang} entry {digits} {cur}", EntryScene(ctx, digits), cursor=cur)
            check(f"{lang} entry error", EntryScene(ctx, digits), cursor=2, error=2.0)

        for new in (True, False):
            st = StoryScene(ctx, 999, "WWW", new)
            for i, _ in enumerate(read(st.dialog)):
                st.dialog.i, st.dialog.n = i, 1e9
                check(f"{lang} story new={new} page {i}", st)

        # The phases of a round: empty tray -> practice, a treat lands ->
        # tut_done, ▶ -> order, ▶▶ -> play.
        _s.tray = {}
        g = GameScene(ctx, 999, "WWW")
        assert g.phase == "tutorial"
        check(f"{lang} tutorial", g, panes)
        _s.tray = {9: [(.3, .3)] * 4}
        g.update(0.05)
        assert g.phase == "tut_done" and g.pop and g.first is not None
        check(f"{lang} tut_done", g, panes)
        read(g.dialog)
        g.handle("right")
        assert g.phase == "order" and g.target > g.total
        check(f"{lang} order", g, panes)
        read(g.dialog)
        assert g.handle("right") == "start" and g.phase == "play"
        _s.tray = {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}
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
            check(f"{lang} score done {stars}", DisplayScoreScene(ctx, res, 999),
                  shown=res.score, done=True, now=2.5)

    # The fuse: full at the start, gone at the end, never outside the screen.
    surf = pygame.Surface((WIDTH, HEIGHT))
    for frac in (1.0, 0.5, 0.01, 0.0):
        fuse(surf, frac, ACCENT, 0.0)
    print("ok")
