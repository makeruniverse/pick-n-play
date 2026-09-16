import pygame
from functools import lru_cache
from balance import gap
from config import *
from app import SceneBase


@lru_cache(maxsize=256)
def render(font, text, color):
    """Reduced text patches, noted instead of any image newly built.

Press Start 2P in 168 px was the most expensive item in the render path:
Screen shows a few dozen different strings, and
the most are standing there for seconds unaltered.
Pi 5 at 9.9.2026, Idle screen driven to 60 Hz.

256 Intercepts range with distance: numbers, residual time and initials are
the only ones who often change, and LRU throws the rest out of itself.
"""
    return font.render(text, False, color)


def draw(screen, font, text, x, y, color):
    surf = render(font, str(text), color)
    screen.blit(surf, surf.get_rect(center=(x,y)))


def footer(screen, f, left=None, right=None, note=None):
    """The lower line: what the four buttons are doing right now.

Four unlabeled arcade bones are only operable when the screen
says what does -- always at the same place, otherwise seek
the eye every time new.

'note' (double confirmation) *replaces the notes instead of
stand. That's the reason why there's nothing left here: there are
no second element that could collide with the line. And it is
the better check-out -- the answer to a push of a button appears
where it says what the button does.

Position instead of word position dares the direction: arrow always first, the
left indicator box left, right.
"""
    if note:
        draw(screen, f["tiny"], note, 960, FOOTER_Y, YELLOW)
        return
    if left:
        draw(screen, f["tiny"], left, 600, FOOTER_Y, GREY)
    if right:
        draw(screen, f["tiny"], right, 1320, FOOTER_Y, GREY)


class IdleScene(SceneBase):

    TICK  = IDLE_FPS   # no one looks, and the Pi is in the cabinet
    MUSIC = None       # remains mute, see   init    

    def __init__(self, ctx):
        super().__init__(ctx)
        # Six hours of chip tune at the neck are exhausting -- and they
        # do not mark anything. Only with a silent iddle will the musical effort in
        # next scene to the signal "going". stop() also the
        # postponed idle music that DisplayScoreScene has planned.
        ctx.music.stop()
        self.t = 0.0
        self.top = ctx.db.top(5)

    def handle(self, action):
        if action == "right":
            self.switch_to(HowToScene(self.ctx))
            return "ok"     # the fanfare honed at the round start, not here

    def update(self, dt):
        self.t += dt

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BLACK)
        draw(screen, f["big"], "PICK'N'PLAY", 960, 260, YELLOW)
        if int(self.t * 2) % 2:
            draw(screen, f["mid"], "PRESS ▶", 960, 560, WHITE)
        # "LOWEST WINS" is mandatory, not decoration: any best list that a child
        # the largest number is sorted upwards. Here wins
        # smallest, and without this line you read the list wrongly.
        draw(screen, f["tiny"], "THE LOWER THE BETTER", 960, 690, GREY)
        for i, (name, score) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {score}", 960, 750 + i * 66, WHITE)


class HowToScene(SceneBase):
    """Enlightenment and demo clip. This is where the music starts.

The clip laughs here and not in the iddle: in the Attract Mode the six
hours of decoding in a closed aluminium cabinett for an image that
No one looks. Here are a few seconds per visitor, right before
a round in which the Pi anyway manages two cameras and the CRT overlay.

Without a clip (DEMO VIDEO = None), the scene as a pure text page -- the
There is film only when there is a structure for filming, and until then may
the feature is not blocked.
"""

    MUSIC_IN = (0.0, 800)   # dazzles, instead of banging out of silence

    def __init__(self, ctx):
        super().__init__(ctx)
        self.idle = 0.0
        self.dt = 0.0

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
        self.dt = dt        # the clip only takes time when drawing
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BLACK)
        draw(screen, f["mid"], "HOW TO PLAY", 960, 110, YELLOW)
        clip = self.ctx.demo.surface(self.dt) if self.ctx.demo else None
        if clip:
            r = clip.get_rect(center=(960, 500))
            screen.fill(GREY, r.inflate(8, 8))
            screen.blit(clip, r)
        # Without clip, the text stretches into the middle instead of under a black
        # Hole. DEMO VIDEO = None is the extradition state, not the
        # Exception -- the page must also look so finished.
        for i, line in enumerate(HOWTO):
            draw(screen, f["tiny"], line, 960, (900 if clip else 500) + i * 60, WHITE)
        footer(screen, f, "◀ BACK", "▶ START")


class GameScene(SceneBase):

    MUSIC = None   # the level of intensities depends on the residual time, see update()

    def __init__(self, ctx):
        super().__init__(ctx)
        self.marks = ctx.detector.fresh()   # id -> Square, a snapshot
        self.total = sum(VALUES[i] for i in self.marks)
        # The target follows the real tray state. A fully random target would
        # let luck decide whether a player must bridge 3 or 200 points.
        self.target = self.total + gap(self.marks)
        self.left = float(ROUND_SECONDS)
        self.confirm = 0.0
        self.hit = 0.0
        self.taps = 0
        ctx.music.stage(self.left)

    def handle(self, action):
        if action == "left":
            self.taps = 0
            if self.confirm > 0:
                self.switch_to(IdleScene(self.ctx))
            else:
                self.confirm = CONFIRM_SECONDS
            return "ok"
        # ponytail: Developer-Abkuerzung. Don't jump into the round, but
        # in her end -- update() makes sound, music and scene change as always.
        if action == "right" and CHEAT_TAPS:
            self.taps += 1
            if self.taps >= CHEAT_TAPS:
                self.left = 0.0
            return "ok"
        self.taps = 0

    def update(self, dt):
        self.left -= dt
        self.confirm = max(0.0, self.confirm - dt)
        # A look at the Detector per Frame: Sum, Overlay and Tone Coming
        # from the same snapshot and cannot contradict each other.
        marks = self.ctx.detector.fresh()
        self.total = sum(VALUES[i] for i in marks)
        if marks.keys() - self.marks.keys():
            # Only recognized at NEW, otherwise it fires DETECT HZ times per second.
            # Five pucks at once should trigger one tone, not five: the
            # It summarizes it by itself.
            self.ctx.music.sfx("blip")
        self.marks = marks
        # Hit must stand, not flash: the hysteresis in fresh() fades
        # the flickering off, PERFECT HOLD makes the intention. Stay less than
        # PERFECT HOLD seconds, the Zaehler does not release the round
        # ends above `left` -- no special case for "short before end" needed.
        self.hit = self.hit + dt if self.total == self.target else 0.0
        self.ctx.music.stage(self.left)
        if self.left <= 0 or self.hit >= PERFECT_HOLD:
            self.ctx.music.sfx("finish")
            # marks instead of total: the sum is in, and the score screen
            # braucht ausserdem, *welche* Werte lagen (Preiszeile).
            self.switch_to(DisplayScoreScene(self.ctx, self.target, self.marks))

    def overlay(self, screen, r):
        """Detection window and detected values, drawn into the Pane rectangular.

The detector delivers shares of 0..1, here once with r
multiplies — so the overlay is also true when the camera
provides a different solution than requested.
"""
        f = self.ctx.fonts[MARK_FONT]
        rx, ry, rw, rh = TRAY_ROI
        # GREY, not YELLOW: the window is Chrome, no play value. It stands
        # in the picture to see when aligning the camera, where detection
        # aufhoert — sonst stellt man es blind ein.
        pygame.draw.rect(screen, GREY, (r.x + rx * r.w, r.y + ry * r.h,
                                        rw * r.w, rh * r.h), MARK_WIDTH)
        # Only the number, no square and no base. The marker marked
        # itself -- a yellow frame around it says nothing what the picture
        # not already showing, and hiding the puck.
        for i, quad in self.marks.items():
            v = render(f, str(VALUES[i]), YELLOW)
            screen.blit(v, v.get_rect(center=(
                r.x + sum(x for x, _ in quad) / 4 * r.w,
                r.y + sum(y for _, y in quad) / 4 * r.h)))

    def bg(self):
        k = min(1.0, max(0.0, (WARN_SECONDS - self.left) / WARN_SECONDS))
        return tuple(round(b + (r - b) * k) for b, r in zip(BLACK, RED))

    def render(self, screen):
        # Header in three columns, including the two camera images. The
        # Column Issues 490 / 960 / 1430 apply both, so that number and
        # tormented image above each other.
        f = self.ctx.fonts
        screen.fill(self.bg())
        draw(screen, f["small"], "GOAL",  490, 70, GREY)
        draw(screen, f["mid"], self.target, 490, 145, WHITE)
        draw(screen, f["small"], "TIME",  960, 70, GREY)
        draw(screen, f["mid"], int(self.left) + 1, 960, 145, WHITE)
        draw(screen, f["small"], "TOTAL", 1430, 70, GREY)
        draw(screen, f["mid"], self.total, 1430, 145, YELLOW)
        # The difference is the actual number of games. Previously GOAL and
        # TOTAL 940 px apart and the visitor had to head it
        # subtract -- under time pressure, from 8 m, in a loud hall. The
        # Purchasing is pucks, not head Calculation.
        #
        # The same word as on the score screen: once learned, twice
        # used. And PERFECT inherits exactly this place -- so there is
        # no longer a second position, at the countdown and demolition warning
        # to deny the same line (previously covered by elif).
        perfect = self.hit > 0
        draw(screen, f["small"], "PERFECT" if perfect else "OFF BY", 960, 265, GREY)
        draw(screen, f["big"],
             int(PERFECT_HOLD - self.hit) + 1 if perfect
             else abs(self.target - self.total),
             960, 380, YELLOW)
        # Passthrough only here: the bandwidth remains free and the
        # Pi cold. frame instead of marking — from 8 m no one reads a label,
        # and which image is the arm, you can see without word.
        for view, pos in zip(self.ctx.views, CAM_POS):
            cam = view.surface()
            if cam:
                r = cam.get_rect(center=pos)
                screen.fill(GREY, r.inflate(8, 8))
                screen.blit(cam, r)
                if view.det:
                    self.overlay(screen, r)
        # ̧ is permanently there, not only after the first pressure:
        # hidden operating element is not one. The mistake fades the
        # Double determination, not invisibility.
        footer(screen, f, "◀ QUIT",
               note="◀ AGAIN TO QUIT" if self.confirm > 0 else None)


class DisplayScoreScene(SceneBase):

    # The finished sound needs air. First let the sound out, then the
    # Idle music -- the silence in between is the effect.
    MUSIC_IN = (2.2, 1500)

    def __init__(self, ctx, target, marks):
        super().__init__(ctx)
        self.target = target
        # A marker per puck and louder different values, so the
        # Quantity loss-free -- she says "lag on the tray", more needs
        # the price line not.
        self.mine = {VALUES[i] for i in marks}
        self.total = sum(VALUES[i] for i in marks)
        self.score = abs(target - self.total)
        self.idle = 0.0

    def handle(self, action):
        self.idle = 0.0
        if action == "right":
            self.switch_to(LeaderboardScene(self.ctx, self.score))
        elif action == "left":
            self.switch_to(IdleScene(self.ctx))
        else:
            return None
        return "ok"

    def update(self, dt):
        self.idle += dt
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BLACK)
        draw(screen, f["small"], "OFF BY", 960, 150, GREY)
        draw(screen, f["big"], self.score, 960, 380, YELLOW)
        # Two columns with labels above -- the same arrangement as in the
        # Headline of the round that the visitor just read 60 s long.
        draw(screen, f["small"], "GOAL",   660, 600, GREY)
        draw(screen, f["mid"], self.target, 660, 690, WHITE)
        draw(screen, f["small"], "TOTAL", 1260, 600, GREY)
        draw(screen, f["mid"], self.total, 1260, 690, WHITE)
        # The Reveal. Previously there was "0 = 4, 1 = 7, ..." -- the left column
        # was the ArUco ID, and it is not a puck as a number. Half
        # Table content required an assignment whose key no one has.
        #
        # Now: only the values, ascendant, and yellow the ones at the round end
        # in fact. It is no longer a reference table,
        # but a picture of the round -- the price catalogue and what to do
        # had. The font is monospace, so ten cells are fixed
        # 192 wheel without a single width calculation.
        draw(screen, f["tiny"], "PRICES", 960, 860, GREY)
        for i, value in enumerate(sorted(VALUES.values())):
            draw(screen, f["small"], value, 204 + i * 168, 940,
                 YELLOW if value in self.mine else WHITE)
        footer(screen, f, "◀ BACK", "▶ NEXT")


class LeaderboardScene(SceneBase):

    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, ctx, score):
        super().__init__(ctx)
        self.score = score
        self.idle = 0.0
        self.cursor = 0
        self.slots = [0, 0, 0]
        self.confirm = 0.0
        self.top = ctx.db.top(5)

    COLS = (510, 840, 1050, 1260)

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
            if self.cursor == 3:
                self.ctx.db.add(self.name(), self.score)
                self.switch_to(IdleScene(self.ctx))
                return "finish"
            else:
                self.cursor += 1
        elif action in ("up", "down") and self.cursor > 0:
            i = self.cursor - 1
            step = 1 if action == "down" else - 1
            self.slots[i] = (self.slots[i] + step) % len(self.LETTERS)
        else:
            return None
        return "ok"

    def update(self, dt):
        self.idle += dt
        self.confirm = max(0.0, self.confirm - dt)
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BLACK)
        # Not "TOP 10!": db.qualifies() is not a gate, here everyone ends --
        # also with OFF BY 200. The title promised something that the code
        # and showed five lines instead of ten. The screen is
        # an input, so he's like one.
        draw(screen, f["mid"], "ENTER YOUR NAME", 960, 130, YELLOW)
        draw(screen, f["big"], "◀", self.COLS[0], 470,
            YELLOW if self.cursor == 0 else WHITE)
        for i, slot in enumerate(self.slots):
            draw(screen, f["big"], self.LETTERS[slot], self.COLS[i + 1], 470,
                YELLOW if self.cursor == i + 1 else WHITE)
        screen.fill(YELLOW, (self.COLS[self.cursor] - 68, 580, 135, 9))
        draw(screen, f["tiny"], "LOWER MEANS BETTER", 960, 660, GREY)
        # 750/66 instead of 860/65: the fifth line was previously y 1096..1144
        # and the back-confirmation prompt on 1114..1146 -- 528 x 30 px overlap,
        # visible as soon as the DB had five entries. Now the list ends
        # at 1004, under SAFE BOTTOM.
        for i, (name, score) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {score}", 960, 720 + i * 64, WHITE)
        # The note says what ▶*now* does. That stored in the last field
        # -- you had to find it.
        footer(screen, f,
               left  = "▲▼ LETTER" if self.cursor else "◀ DISCARD",
               right = "▶ SAVE" if self.cursor == 3 else "▶ NEXT",
               note  = "◀ AGAIN TO DISCARD" if self.confirm > 0 else None)


if __name__ == "__main__":
    # Layout self test. Just the mistake that was in here twice: one
    # element moves under SAFE BOTTOM or covers another, and
    # it becomes visible only when the DB has enough lines. The test fades
    # each draw() call off and breaks the rectangles -- no screenshot,
    # no framework, no comparison image that needs to be maintained.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    _fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}

    boxes, _draw = [], draw
    def draw(screen, font, text, x, y, color):          # noqa: F811
        w, h = font.size(str(text))
        boxes.append((str(text), x - w//2, y - h//2, x + w//2, y + h//2))

    class _Stub:
        """Covers Music, DB and Detector -- they do nothing in the test."""
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [(f"WW{i}", 999) for i in range(n)]
        def fresh(self):     return {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             views=(), demo=None))()

    # Panes are not a draw(), but are included in the cover.
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
            assert b <= SAFE_BOTTOM or tp >= FOOTER_Y - 40,\
                f"{label}: {t!r} ragt unter SAFE_BOTTOM (y {tp}..{b})"
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, c = bs[i], bs[j]
                assert not (a[1] < c[3] and c[1] < a[3]
                            and a[2] < c[4] and c[2] < a[4]),\
                    f"{label}: {a[0]!r} ueberdeckt {c[0]!r}"

    check("idle",  IdleScene(ctx))
    check("howto", HowToScene(ctx))
    g = GameScene(ctx)
    check("game",         g, panes)
    check("game confirm", g, panes, confirm=2.0)
    check("game perfect", g, panes, confirm=0.0, hit=1.0)
    check("score", DisplayScoreScene(ctx, 180, {0: 1, 3: 1, 7: 1, 9: 1}))
    for cur in range(4):
        for conf in (0.0, 2.0):
            check(f"board cursor={cur} confirm={conf}",
                  LeaderboardScene(ctx, 15), cursor=cur, confirm=conf)
    print("ok")
