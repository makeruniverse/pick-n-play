import math
import random
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

    `sign=False` for the price row in the reveal: there are ten cells there
    in the 168-grid, and six glyphs don't fit side by side. The € then
    sits in the heading.

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
    marks: dict          # id -> quad, for the price reveal

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


@lru_cache(maxsize=256)
def pie(steps, text, font, color, cells=21, px=8):
    """Countdown pie in coarse pixels, with the seconds inside as a negative.

    Drawn at cells x cells and scaled up by px: one pie pixel is one glyph
    pixel of the 168 font, so it reads as the same 8-bit screen. The pie
    shrinks clockwise from 12 o'clock; `steps` is the remaining share in
    1/STEPS, quantized so the cache stays small.

    The number is punched out of the pie (the background shows through) and
    white where the pie is already gone -- so it is there, but never the
    loudest thing, and an empty pie leaves a plain white number.
    """
    c = cells / 2
    low = pygame.Surface((cells, cells), pygame.SRCALPHA)
    if steps >= PIE_STEPS:
        pygame.draw.circle(low, color, (c, c), c)
    elif steps > 0:
        arc = [(c + c * 1.5 * math.sin(a), c - c * 1.5 * math.cos(a))
               for a in (2 * math.pi * steps / PIE_STEPS * k / 32 for k in range(33))]
        pygame.draw.polygon(low, color, [(c, c)] + arc)
        mask = pygame.Surface((cells, cells), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (c, c), c)
        low.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    ring = pygame.Surface((cells, cells), pygame.SRCALPHA)
    pygame.draw.circle(ring, GREY, (c, c), c, 1)
    size = (cells * px, cells * px)
    cake = pygame.transform.scale(low, size)
    num = pygame.Surface(size, pygame.SRCALPHA)
    t = font.render(text, False, WHITE)
    num.blit(t, t.get_rect(center=(size[0] // 2, size[1] // 2)))
    cake_m, num_m = pygame.mask.from_surface(cake), pygame.mask.from_surface(num)
    out = pygame.transform.scale(ring, size)
    hole = cake_m.copy()
    hole.erase(num_m, (0, 0))
    out.blit(hole.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)), (0, 0))
    num_m.erase(cake_m, (0, 0))
    out.blit(num_m.to_surface(setcolor=WHITE, unsetcolor=(0, 0, 0, 0)), (0, 0))
    return out


PIE_STEPS = 120


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
    if note:
        # Brighter than the normal hints: the follow-up question isn't a
        # label, it's a question that needs an answer. The urgency is still
        # carried by the red arrow, not the word.
        draw_hint(screen, f["tiny"], note, 960, FOOTER_Y, WHITE)
        return
    if left:
        draw_hint(screen, f["tiny"], left, 600, FOOTER_Y)
    if right:
        draw_hint(screen, f["tiny"], right, 1320, FOOTER_Y)


class IdleScene(SceneBase):

    TICK  = IDLE_FPS   # nobody's watching, and the Pi sits in the cabinet
    MUSIC = None       # stays silent, see __init__

    def __init__(self, ctx):
        super().__init__(ctx)
        # Six hours of chiptune in a row is exhausting -- and it marks
        # nothing. Only with a silent idle does the music kicking in during
        # the next scene become the signal "it's starting". stop() also
        # clears the deferred idle music that DisplayScoreScene scheduled.
        ctx.music.stop()
        ctx.leds.show("idle")
        self.t = 0.0
        self.top = ctx.db.top(5)

    def handle(self, action):
        if action == "right":
            self.switch_to(HowToScene(self.ctx))
            return "ok"     # the fanfare belongs at the round start, not here

    def update(self, dt):
        self.t += dt

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        # The display scrolls by at top and bottom, in opposite directions
        # -- that's the attract mode. From 8 m you see motion before you read text.
        parade(screen, self.t, 96, 60)
        parade(screen, self.t, 984, -60)
        # Title character by character: every letter in a candy color, as a
        # wave. Monospace, one character width is the step like in draw_hint().
        title = "PICK'N'PLAY"
        w = f["title"].size("A")[0]
        for i, c in enumerate(title):
            draw(screen, f["title"], c, 960 + w * (i + 0.5 - len(title) / 2),
                 250 + round(14 * math.sin(self.t * 3 - i * 0.6)),
                 CANDY[i % len(CANDY)])
        # The cheapest and the most expensive piece -- from the theme, not named here.
        stamp(screen, LADDER[0], 8, 330, 430 + hop(self.t, 0, 8))
        stamp(screen, LADDER[-1], 8, 1590, 430 + hop(self.t, 1, 8))
        # Mostly on, briefly off: it has to be read, the blink only draws the eye.
        if self.t % 2 < 1.6:
            draw_hint(screen, f["mid"], "PRESS ▶", 960, 430, WHITE)
        # This used to say "THE LOWER THE BETTER" -- mandatory as long as the
        # list sorted ascending. Since the score is high when it's good, the
        # list explains itself, and the line now says what it is instead of
        # how to read it.
        draw(screen, f["tiny"], "TODAY'S BEST", 960, 556, GREY)
        for i, (name, pts) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {pts}", 960, 640 + i * 64, WHITE)


class HowToScene(SceneBase):
    """Explanation and demo clip. This is where the music starts.

    The clip runs here and not in idle: in attract mode that would be six
    hours of decoding in the closed aluminum cabinet for an image nobody
    watches. Here it's a few seconds per visitor, right before a round,
    where the Pi is already carrying two cameras and the CRT overlay anyway.

    Without a clip (DEMO_VIDEO = None) the scene runs as a plain text page
    -- there's no footage yet until there's a setup to film it, and until
    then the feature must not be blocked.
    """

    MUSIC_IN = (0.0, 800)   # fades in, instead of hitting hard out of silence

    def __init__(self, ctx):
        super().__init__(ctx)
        self.idle = 0.0
        self.dt = 0.0
        self.t = 0.0      # keeps running, idle is zeroed on every button press

    def handle(self, action):
        self.idle = 0.0
        if action == "right":
            self.switch_to(GameScene(self.ctx))
            return "start"
        if action == "left":
            self.switch_to(IdleScene(self.ctx))
            return "ok"

    def update(self, dt):
        self.idle += dt
        self.t += dt
        self.dt = dt        # the clip only needs the time when drawing
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        draw(screen, f["mid"], "HOW TO PLAY", 960, 150, ACCENT)
        clip = self.ctx.demo.surface(self.dt) if self.ctx.demo else None
        if clip:
            r = clip.get_rect(center=(960, 460))
            screen.fill(GREY, r.inflate(8, 8))
            screen.blit(clip, r)
        else:
            # The display shows *what* is on the tray before the text says
            # what to do with it. Without a clip, there'd otherwise be a
            # hole here. All ten, in the same 168-grid as the price row in
            # the reveal.
            for i, name in enumerate(LADDER):
                stamp(screen, name, 6, 204 + i * 168, 330 + hop(self.t, i, 6))
        # Without a clip the text moves to the center instead of sitting
        # under a black hole. DEMO_VIDEO = None is the shipped state, not
        # the exception -- the page has to look finished that way too.
        # {secs} instead of a number in the theme: round length lives in
        # the mode and gets tried out a lot -- it must not live in two places.
        for i, line in enumerate(HOWTO):
            draw(screen, f["tiny"], line.format(secs=ROUND_SECONDS),
                 960, (800 if clip else 476) + i * 50, WHITE)
        footer(screen, f, "◀ BACK", "▶ START")


class GameScene(SceneBase):

    MUSIC = None   # the intensity level depends on time left, see update()

    # The bar, absolute coordinates like everything else in this file.
    # Below the cameras and exactly as wide as both panes together.
    BAR   = pygame.Rect(108, 770, 1704, 70)
    # Countdown pie in the gap between the panes, see pie().
    PIE   = pygame.Rect(0, 0, 168, 168)
    PIE.center = (960, 510)
    # Scale of the bar: the largest possible target, not the sum of all ten
    # cupcakes. As long as the tray was pre-loaded and rearranged, "everything
    # there is at all" was the right length -- the total could wander there.
    # Since the tray starts empty and the perfect solution is two pieces,
    # everything plays out under GAP_MAX: the goal line would then sit in
    # the left quarter and the bar would have no resolution left in the
    # range that actually matters.
    #
    # GAP_MAX stays the same across all rounds, so the line keeps meaning
    # the same thing everywhere. Whoever loads on more than the largest
    # target runs into the stop on the right -- _x() clamps, and "way over"
    # is exactly the right statement. The exact number stands below it anyway.
    SCALE = GAP_MAX
    GOAL_W, GOAL_OVER = 9, 18   # width and overhang of the goal line
    LEGEND_Y = 892

    def __init__(self, ctx):
        super().__init__(ctx)
        self.marks = ctx.detector.fresh()   # id -> quad, a snapshot
        self.total = tray_sum(self.marks)
        # The target follows what's actually there -- at the cabinet that's
        # an empty tray, but a leftover cupcake then adjusts the task
        # instead of breaking it. Rolled freely, chance would decide
        # whether someone has to bridge EUR 0.30 or EUR 20.
        self.dist = gap(self.marks)
        self.target = self.total + self.dist
        self.left = float(ROUND_SECONDS)
        self.confirm = 0.0
        self.hit = 0.0
        self.taps = 0
        self.fx = None      # sprinkles, only while PERFECT is shown
        ctx.music.stage(self.left)

    def handle(self, action):
        if action == "left":
            self.taps = 0
            if self.confirm > 0:
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        # ponytail: developer shortcut. Doesn't jump into the round, but
        # into its end -- update() handles sound, music, and scene switch as usual.
        if action == "right" and CHEAT_TAPS:
            self.taps += 1
            if self.taps >= CHEAT_TAPS:
                self.left = 0.0
            return "ok"
        self.taps = 0

    def update(self, dt):
        self.left -= dt
        self.confirm = max(0.0, self.confirm - dt)
        # One look at the detector per frame: total, overlay, and sound
        # come from the same snapshot and can't contradict each other.
        marks = self.ctx.detector.fresh()
        self.total = tray_sum(marks)
        if marks.keys() - self.marks.keys():
            # Only on NEWLY detected, otherwise it fires DETECT_HZ times per
            # second. Five pucks at once give one sound, not five: the set
            # comparison merges them by itself.
            self.ctx.music.sfx("blip")
        self.marks = marks
        # A hit must hold, not flash: the hysteresis in fresh() catches the
        # flicker, PERFECT_HOLD catches the intent. If fewer than
        # PERFECT_HOLD seconds remain, the counter doesn't fill up and the
        # round ends via left -- no special case for "right before the end"
        # is needed.
        self.hit = self.hit + dt if self.total == self.target else 0.0
        if self.hit > 0:
            self.fx = self.fx or Sprinkles(960, 196)    # pops from PERFECT
            self.fx.update(dt)
        else:
            self.fx = None
        self.ctx.music.stage(self.left)
        # Every frame, not just on change: the bar lives off left, and
        # show() is an assignment. Red from the same threshold as the background.
        self.ctx.leds.show("hurry" if self.left <= WARN_SECONDS else "game",
                           max(0.0, self.left) / ROUND_SECONDS)
        if self.left <= 0 or self.hit >= PERFECT_HOLD:
            self.ctx.music.sfx("finish")
            # One result instead of four arguments. left gets clamped here:
            # the loop counts past zero, and a negative time left would be
            # a lie in the database instead of a zero.
            self.switch_to(DisplayScoreScene(self.ctx, Result(
                self.target, self.total, self.dist,
                max(0.0, self.left), self.marks)))

    def overlay(self, screen, r):
        """Detection window, drawn into the pane rectangle.

        The detector delivers fractions from 0..1, here they get multiplied
        by r once — so the overlay stays correct even when the camera
        delivers a different resolution than requested.
        """
        rx, ry, rw, rh = TRAY_ROI
        # GREY, not ACCENT: the window is chrome, not a game value. It's in
        # the image so that when aligning the camera you can see where
        # detection stops — otherwise you'd be setting it blind.
        pygame.draw.rect(screen, GREY, (r.x + rx * r.w, r.y + ry * r.h,
                                        rw * r.w, rh * r.h), MARK_WIDTH)
        # The price used to be shown next to every detected cupcake. Removed
        # on 2026-09-11: it went against the game's basic rule. "EVERY TREAT
        # HAS A HIDDEN PRICE" — anyone who can read the prices during the
        # round calculates instead of estimating, and the reveal at the end
        # loses its learning moment. From 8 m nobody read it anyway; at the
        # cabinet, where the hands are on the leader arm, they would.
        #
        # Stays as a comment because it's useful when setting up the camera:
        # it's the only display that shows WHICH marker detection currently
        # sees, not just that it sees one.
        # MARK_FONT in config.py exists only for these lines now.
        #
        # f = self.ctx.fonts[MARK_FONT]
        # for i, quad in self.marks.items():
        #     v = render(f, euro(VALUES[i], sign=False), ACCENT)
        #     screen.blit(v, v.get_rect(center=(
        #         r.x + sum(x for x, _ in quad) / 4 * r.w,
        #         r.y + sum(y for _, y in quad) / 4 * r.h)))

    def bg(self):
        k = min(1.0, max(0.0, (WARN_SECONDS - self.left) / WARN_SECONDS))
        return tuple(round(b + (r - b) * k) for b, r in zip(BG, RED))

    def acc(self):
        """ACCENT, except on a red background: pink on RED is 2.7:1, cream is 6:1."""
        return WHITE if self.left <= WARN_SECONDS else ACCENT

    def bar(self, screen):
        """Where the total stands and where it needs to go, as one image.

        The bar does what four numbers couldn't: direction and distance
        without reading. Fill left of the line means load more, right of it
        means take away, and how far is visible without subtracting.

        Order: fill first, then frame. The other way around, the fill would
        cover the left frame edge.

        The fill is a candy cane that slowly travels: the bar says the same
        thing as before, but it's alive. Motion here is decoration, length
        remains the only statement.
        """
        r = self.BAR
        fill = stripes(r.w, r.h, self.acc())
        off = round((ROUND_SECONDS - self.left) * 40) % 48
        screen.blit(fill, r.topleft, (48 - off, 0, self._x(self.total) - r.x, r.h))
        pygame.draw.rect(screen, GREY, r, 3)
        # The goal line sticks out at top and bottom. Without the overhang
        # it disappears exactly when it matters -- namely when the fill has
        # almost reached it and stands light on light.
        screen.fill(WHITE, (self._x(self.target) - self.GOAL_W // 2,
                            r.y - self.GOAL_OVER,
                            self.GOAL_W, r.h + 2 * self.GOAL_OVER))

    def legend(self, screen, f):
        """ON TRAY under the left end of the bar, GOAL under the right end,
        flush with the bar edges. draw() centers, so the centers are computed
        from the monospace glyph widths."""
        y, r = self.LEGEND_Y, self.BAR
        tw, sw = f["tiny"].size("A")[0], f["small"].size("A")[0]
        v = euro(self.total)
        draw(screen, f["tiny"], "ON TRAY", r.x + 7 * tw / 2, y, GREY)
        draw(screen, f["small"], v, r.x + 8 * tw + len(v) * sw / 2, y, self.acc())
        v = euro(self.target)
        draw(screen, f["small"], v, r.right - len(v) * sw / 2, y, WHITE)
        draw(screen, f["tiny"], "GOAL", r.right - len(v) * sw - 5 * tw / 2 - tw, y, GREY)

    def _x(self, value):
        """Point value -> x in the bar. Clamped so nothing runs out."""
        r = self.BAR
        return r.x + round(r.w * min(max(value, 0), self.SCALE) / self.SCALE)

    def render(self, screen):
        # Priority is the camera images: the player steers the arm by them.
        # Above them the instruction, alone on the full width; below them the
        # bar, and under its two ends what's on the tray and the goal -- a
        # legend for the bar, not a headline of their own.
        f = self.ctx.fonts
        screen.fill(self.bg())
        # Passthrough only here: in idle, bandwidth stays free and the Pi
        # stays cool. Frame instead of label — from 8 m nobody reads a
        # label, and which image is the arm is visible without a word.
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
        # The screen says what to do instead of reporting how things stand.
        # "OFF BY 60" was a report: correct number, no direction -- and the
        # visitor first had to realize it even had one. Now there's a verb
        # there, and the number is its argument.
        #
        # PERFECT inherits exactly this spot, so there's no second place
        # where two messages could compete for the same line.
        diff = self.target - self.total
        if self.hit > 0:
            label, big = f"HOLD {int(PERFECT_HOLD - self.hit) + 1}", "PERFECT"
        else:
            # "ADD POINTS 60" used to be a score -- and that doesn't exist
            # during the round anymore. What's shown here is a price,
            # because that's the only quantity the visitor is looking at
            # during the round.
            label, big = ("ADD" if diff > 0 else "REMOVE"), euro(abs(diff))
        draw(screen, f["small"], label, 960, 64, GREY)
        draw(screen, f["big"], big, 960, 196, self.acc())
        frac = min(1.0, max(0.0, self.left / ROUND_SECONDS))
        screen.blit(pie(math.ceil(frac * PIE_STEPS), str(max(0, int(self.left) + 1)),
                        f["small"], self.acc()), self.PIE)
        self.bar(screen)
        self.legend(screen, f)
        # ◀ is permanently there, not only after the first press: a hidden
        # control isn't one. The double-confirm catches an accidental
        # press, not invisibility.
        footer(screen, f, "◀ QUIT",
               note="◀ AGAIN TO QUIT" if self.confirm > 0 else None)


class DisplayScoreScene(SceneBase):
    """The spinner: a number counts up toward the score, nothing else.

    During the round, deliberately no score shows on the screen -- there
    it's purely about hitting the price. The scoring happens here, and it
    happens as an event, not a display: first the number counts up, then
    what it's made of appears, and below that sits the price reveal.

    The order is the whole trick. If the breakdown were there right away,
    you could calculate the end of the count-up before it starts -- and
    that would kill the effect it exists for.
    """

    # The finish sound needs room to breathe. Let it ring out first, then
    # the idle music fades in -- the silence in between is the effect.
    MUSIC_IN = (2.2, 1500)
    # Seconds until the number settles. Shorter reads like a jump, longer
    # like a loading bar. Stays under MUSIC_IN, otherwise the idle music
    # kicking in would fall inside the count-up.
    COUNT = 1.8

    def __init__(self, ctx, res):
        super().__init__(ctx)
        self.res = res
        # One marker per cupcake and all-distinct prices, so the set is
        # lossless -- it says "was on the tray", the price row doesn't
        # need more than that.
        self.mine = {VALUES[i] for i in res.marks}
        self.shown = 0
        self.done = False
        self.idle = 0.0
        self.t = 0.0
        self.fx = Sprinkles(960, 300)   # everyone gets the pop -- no failure, just a number
        ctx.leds.show("score")

    def handle(self, action):
        self.idle = 0.0
        if action == "right":
            self.switch_to(LeaderboardScene(self.ctx, self.res))
        elif action == "left":
            self.switch_to(IdleScene(self.ctx))
        else:
            return None
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.t += dt
        self.fx.update(dt)
        # Fast in, slow out: (1-k)**3 is the curve a boxing machine winds
        # down with. Counting up linearly looks like a progress bar, not a
        # result.
        k = min(1.0, self.t / self.COUNT)
        shown = round(self.res.score * (1 - (1 - k) ** 3))
        if shown // 100 > self.shown // 100:
            # One tick per hundred. "blip" is thin and quiet and built
            # exactly for this -- a dedicated sound would be work for the
            # same effect.
            self.ctx.music.sfx("blip")
        self.shown = shown
        if not self.done and k >= 1.0:
            self.done = True                    # fires once, even at 0 points
            self.ctx.music.sfx("ok")
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        res = self.res
        screen.fill(BG)
        self.fx.draw(screen)
        draw(screen, f["small"], "SCORE", 960, 130, GREY)
        draw(screen, f["big"], self.shown, 960, 300, ACCENT)
        # The breakdown -- only once the number settles. One headline and one
        # line of context: three equal columns read as three equal numbers,
        # and at mid size they didn't even fit side by side.
        #
        # The headline switches, because otherwise one of the two cases
        # would show a number twice. Whoever missed wants to know by how
        # much; whoever hit it already sees that from GOAL and YOURS being
        # equal -- there the time bonus is the only thing that still says
        # something. And it says exactly what sets it apart from the other
        # perfects.
        if self.done:
            label, value = (("TIME BONUS", f"+{res.bonus}") if res.bonus
                            else ("OFF BY", euro(res.off)))
            draw(screen, f["small"], label, 960, 450, GREY)
            draw(screen, f["mid"], value, 960, 530, ACCENT)
            draw(screen, f["small"], f"GOAL {euro(res.target)}", 620, 620, GREY)
            draw(screen, f["small"], f"YOURS {euro(res.total)}", 1300, 620, GREY)
        # The reveal. This used to say "0 = 4, 1 = 7, ..." -- the left
        # column was the ArUco ID, and that appears as a digit on no
        # cupcake. Half the table's content demanded a mapping whose key
        # nobody has.
        #
        # Now: every piece as a sprite with its price below, ascending, and
        # pink and hopping the ones that were actually on the tray at the
        # end of the round. That makes it no longer a lookup table but a
        # picture of the round -- the display and what you had of it. And
        # it's the learning moment: "the chocolate cake was the expensive one".
        #
        # The € sits in the heading and not in every cell: ten cells in the
        # 168-grid, four glyphs fit side by side there, not five.
        draw(screen, f["tiny"], "PRICES IN €", 960, 690, GREY)
        for i, k in enumerate(sorted(VALUES, key=VALUES.get)):
            mine = VALUES[k] in self.mine
            x = 204 + i * 168
            stamp(screen, SPRITE[k], 5, x, 768 + (hop(self.t, i, 10) if mine else 0))
            draw(screen, f["tiny"], euro(VALUES[k], sign=False), x, 850,
                 ACCENT if mine else WHITE)
        footer(screen, f, "◀ BACK", "▶ NEXT")


class LeaderboardScene(SceneBase):

    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, ctx, res):
        super().__init__(ctx)
        self.res = res
        self.idle = 0.0
        self.cursor = 0
        self.slots = [0, 0, 0]
        self.confirm = 0.0
        self.top = ctx.db.top(5)
        self.t = 0.0

    # ◀, three letters, ▶. Saving is its own stop: from the last letter ▶
    # first moves onto the arrow, and only pressing it again saves -- one
    # press too many used to store a half-finished name.
    COLS = (420, 750, 960, 1170, 1500)
    SAVE = len(COLS) - 1
    # The cursor bar is a fill(), not a draw() -- without the constant it
    # wouldn't show up in the layout self-test, and that's exactly the
    # class of bug it catches.
    CURSOR_Y, CURSOR_H = 490, 9

    def name(self):
        return "".join(self.LETTERS[i] for i in self.slots)

    def handle(self, action):
        self.idle = 0.0
        if action == "left":
            if self.cursor == 0:
                if self.confirm > 0:
                    self.switch_to(IdleScene(self.ctx))
                else:
                    self.confirm = CONFIRM_SECONDS
            else:
                self.cursor -= 1
        elif action == "right":
            if self.cursor == self.SAVE:
                # Everything the round physically was -- the database
                # computes the score itself, so a later formula also
                # applies to old rounds.
                self.ctx.db.add(self.name(), self.res.off, goal=self.res.target,
                                total=self.res.total, dist=self.res.dist,
                                secs=self.res.left)
                self.switch_to(IdleScene(self.ctx))
                return "finish"
            else:
                self.cursor += 1
        elif action in ("up", "down") and 0 < self.cursor < self.SAVE:
            i = self.cursor - 1
            step = 1 if action == "down" else - 1
            self.slots[i] = (self.slots[i] + step) % len(self.LETTERS)
        else:
            return None
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.t += dt
        self.confirm = max(0.0, self.confirm - dt)
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        stamp(screen, LADDER[1], 6, 180, 110 + hop(self.t, 0, 6))
        stamp(screen, LADDER[-2], 6, 1740, 110 + hop(self.t, 1, 6))
        # Not "TOP 10!": db.qualifies() isn't a gate, everyone lands here --
        # even with OFF BY 200. The heading promised something the code
        # doesn't check, and showed five rows instead of ten. The screen is
        # an input, so it's named like one.
        draw(screen, f["mid"], "ENTER YOUR NAME", 960, 110, ACCENT)
        # The arrows take the colour of their physical button when selected:
        # there they *are* the button, the one exception to the footer rule.
        cols = [BTN_RED] + [ACCENT] * len(self.slots) + [BTN_GREEN]
        glyphs = ["◀"] + [self.LETTERS[i] for i in self.slots] + ["▶"]
        for i, (g, c) in enumerate(zip(glyphs, cols)):
            draw(screen, f["big"], g, self.COLS[i], 380,
                 c if self.cursor == i else WHITE)
        screen.fill(cols[self.cursor], (self.COLS[self.cursor] - 68, self.CURSOR_Y,
                                        135, self.CURSOR_H))
        draw(screen, f["tiny"], "TODAY'S BEST", 960, 556, GREY)
        # The fifth row was the clipping bug from August 28: it sat below
        # SAFE_BOTTOM and covered the cancel confirmation, only visible once
        # there were five entries in the DB. At 1080 the list ends at 912.
        for i, (name, pts) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {pts}", 960, 632 + i * 64, WHITE)
        # The hint says what ▶ does *right now*. That the last field saves
        # used to be stated nowhere -- you had to discover it.
        footer(screen, f,
               left  = ("◀ DISCARD" if self.cursor == 0 else
                        "◀ BACK" if self.cursor == self.SAVE else "▲▼ LETTER"),
               right = "▶ SAVE" if self.cursor == self.SAVE else "▶ NEXT",
               note  = "◀ AGAIN TO DISCARD" if self.confirm > 0 else None)


if __name__ == "__main__":
    # Layout self-test. Exactly the bug that was in here twice: an element
    # drifts below SAFE_BOTTOM or covers another one, and it only becomes
    # visible once the DB has enough rows. The test intercepts every
    # draw() call and checks the rectangles -- no screenshot, no
    # framework, no reference image that would need maintaining.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    _fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}

    boxes, _draw = [], draw
    def draw(screen, font, text, x, y, color):          # noqa: F811
        w, h = font.size(str(text))
        boxes.append((str(text), x - w//2, y - h//2, x + w//2, y + h//2))

    # Sprites count too, with their full edge: 16 sprite pixels.
    def stamp(screen, name, scale, x, y):               # noqa: F811
        boxes.append((name, x - 8 * scale, y - 8 * scale, x + 8 * scale, y + 8 * scale))

    class _Stub:
        """Covers Music, DB, and Detector -- they all do nothing in the test."""
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [(f"WW{i}", 999) for i in range(n)]
        def fresh(self):     return {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             leds=_s, views=(), demo=None))()

    # Panes aren't a draw(), but they still count toward overlap.
    panes = [("pane", x - CAM_VIEW[0]//2 - 4, y - CAM_VIEW[1]//2 - 4,
                      x + CAM_VIEW[0]//2 + 4, y + CAM_VIEW[1]//2 + 4)
             for x, y in CAM_POS]

    def check(label, scene, extra=(), **state):
        scene.__dict__.update(state)
        boxes.clear()
        scene.render(pygame.Surface((WIDTH, HEIGHT)))
        bs = boxes + list(extra)
        for t, l, tp, r, b in bs:
            assert 0 <= l and r <= WIDTH,  f"{label}: {t!r} x {l}..{r}"
            assert 0 <= tp and b <= HEIGHT, f"{label}: {t!r} y {tp}..{b}"
            assert b <= SAFE_BOTTOM or tp >= FOOTER_Y - 40, \
                f"{label}: {t!r} sticks out below SAFE_BOTTOM (y {tp}..{b})"
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, c = bs[i], bs[j]
                assert not (a[1] < c[3] and c[1] < a[3]
                            and a[2] < c[4] and c[2] < a[4]), \
                    f"{label}: {a[0]!r} overlaps {c[0]!r}"

    # The bar is a fill(), not a draw() -- without this line it wouldn't
    # show up in the test, and that's exactly the class of bug it catches.
    # The goal line sits inside it by construction and is covered by the
    # rectangle too.
    bar = [("bar", GameScene.BAR.x, GameScene.BAR.y - GameScene.GOAL_OVER,
                   GameScene.BAR.right, GameScene.BAR.bottom + GameScene.GOAL_OVER),
           ("pie", *GameScene.PIE.topleft, *GameScene.PIE.bottomright)]

    check("idle",  IdleScene(ctx))
    check("howto", HowToScene(ctx))
    g = GameScene(ctx)
    check("game",         g, panes + bar)
    check("game confirm", g, panes + bar, confirm=2.0)
    check("game perfect", g, panes + bar, confirm=0.0, hit=1.0)
    # Both directions of the instruction. The number below is now a price
    # and therefore wider than before -- it sits in the middle, where it's
    # most likely to collide.
    check("game remove",  g, panes + bar, hit=0.0, total=g.target + 40)
    # Edge cases of the bar: empty tray (the normal case at the cabinet) and
    # target at the upper stop. The widest number that can ever appear in
    # the header is the sum of ALL prices -- the bar clamps there, but the
    # number next to it doesn't, and that's the one that could collide.
    check("game empty",   g, panes + bar, total=0, target=GameScene.SCALE)
    check("game full",    g, panes + bar, total=sum(VALUES.values()), target=0)

    # The score screen in both states: while the number counts up the
    # breakdown isn't there yet, afterward it is. The second one needs
    # checking -- there are three columns there where there used to be two.
    res = Result(target=67, total=64, dist=50, left=0.0,
                 marks={0: 1, 3: 1, 7: 1, 9: 1})
    check("score counting", DisplayScoreScene(ctx, res))
    check("score done",     DisplayScoreScene(ctx, res),
          shown=res.score, done=True, t=2.5)
    # And a perfect round: four-digit score, "+100" instead of "+0".
    best = Result(target=67, total=67, dist=50,
                  left=ROUND_SECONDS - PERFECT_HOLD, marks=dict.fromkeys(VALUES, 1))
    check("score perfect", DisplayScoreScene(ctx, best),
          shown=best.score, done=True, t=2.5)
    for cur in range(len(LeaderboardScene.COLS)):
        for conf in (0.0, 2.0):
            L = LeaderboardScene
            bar = [("cursor", L.COLS[cur] - 68, L.CURSOR_Y,
                              L.COLS[cur] + 67, L.CURSOR_Y + L.CURSOR_H)]
            check(f"board cursor={cur} confirm={conf}",
                  L(ctx, res), bar, cursor=cur, confirm=conf)
    print("ok")
