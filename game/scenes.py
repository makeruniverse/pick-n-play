import pygame
from functools import lru_cache
from balance import gap
from config import *
from app import SceneBase


@lru_cache(maxsize=256)
def render(font, text, color):
    """Gerenderte Textflaeche, gemerkt statt jedes Bild neu gebaut.

    Press Start 2P in 168 px war der teuerste Posten im Renderpfad: der
    Schirm zeigt hoechstens ein paar Dutzend verschiedene Zeichenketten, und
    die allermeisten stehen sekundenlang unveraendert da. Gemessen auf dem
    Pi 5 am 9.9.2026, Idle-Screen auf 60 Hz getrieben.

    256 Eintraege reichen mit Abstand: Ziffern, Restzeit und Initialen sind
    die einzigen, die sich oft aendern, und LRU wirft den Rest von allein raus.
    """
    return font.render(text, False, color)


def draw(screen, font, text, x, y, color):
    surf = render(font, str(text), color)
    screen.blit(surf, surf.get_rect(center=(x,y)))


def footer(screen, f, left=None, right=None, note=None):
    """Die untere Zeile: was die vier Knoepfe gerade tun.

    Vier unbeschriftete Arcade-Knoepfe sind nur bedienbar, wenn der Schirm
    sagt, welcher was tut -- und zwar immer an derselben Stelle, sonst sucht
    das Auge jedes Mal neu.

    `note` (die Doppelbestaetigung) *ersetzt* die Hinweise, statt daneben zu
    stehen. Das ist der Grund, warum hier nichts mehr klippen kann: es gibt
    kein zweites Element, das mit der Zeile kollidieren koennte. Und es ist
    die bessere Rueckmeldung -- die Antwort auf einen Knopfdruck erscheint
    dort, wo schon steht, was der Knopf tut.

    Position statt Wortstellung traegt die Richtung: Pfeil immer zuerst, das
    linke Hinweisfeld links, das rechte rechts.
    """
    if note:
        draw(screen, f["tiny"], note, 960, FOOTER_Y, YELLOW)
        return
    if left:
        draw(screen, f["tiny"], left, 600, FOOTER_Y, GREY)
    if right:
        draw(screen, f["tiny"], right, 1320, FOOTER_Y, GREY)


class IdleScene(SceneBase):

    TICK  = IDLE_FPS   # niemand schaut hin, und der Pi steht im Kabinett
    MUSIC = None       # bleibt stumm, siehe __init__

    def __init__(self, ctx):
        super().__init__(ctx)
        # Sechs Stunden Chiptune am Stueck sind anstrengend -- und sie
        # markieren nichts. Erst mit stillem Idle wird der Musikeinsatz in der
        # naechsten Szene zum Signal "es geht los". stop() raeumt auch die
        # aufgeschobene Idle-Musik weg, die DisplayScoreScene eingeplant hat.
        ctx.music.stop()
        self.t = 0.0
        self.top = ctx.db.top(5)

    def handle(self, action):
        if action == "right":
            self.switch_to(HowToScene(self.ctx))
            return "ok"     # die Fanfare gehoert an den Rundenstart, nicht hier

    def update(self, dt):
        self.t += dt

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BLACK)
        draw(screen, f["big"], "PICK'N'PLAY", 960, 260, YELLOW)
        if int(self.t * 2) % 2:
            draw(screen, f["mid"], "PRESS ▶", 960, 560, WHITE)
        # "LOWEST WINS" ist Pflicht, nicht Deko: jede Bestenliste, die ein Kind
        # kennt, sortiert die groesste Zahl nach oben. Hier gewinnt die
        # kleinste, und ohne diese Zeile liest man die Liste falsch herum.
        draw(screen, f["tiny"], "THE LOWER THE BETTER", 960, 690, GREY)
        for i, (name, score) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {score}", 960, 750 + i * 66, WHITE)


class HowToScene(SceneBase):
    """Erklaerung und Demo-Clip. Hier faengt die Musik an.

    Der Clip laeuft hier und nicht im Idle: im Attract Mode waeren das sechs
    Stunden Dekodierung im geschlossenen Alu-Kabinett fuer ein Bild, das
    niemand ansieht. Hier sind es ein paar Sekunden pro Besucher, direkt vor
    einer Runde, in der der Pi ohnehin zwei Kameras und das CRT-Overlay stemmt.

    Ohne Clip (DEMO_VIDEO = None) laeuft die Szene als reine Textseite -- den
    Film gibt es erst, wenn es einen Aufbau zum Filmen gibt, und bis dahin darf
    das Feature nicht blockiert sein.
    """

    MUSIC_IN = (0.0, 800)   # blendet ein, statt aus der Stille zu knallen

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
        self.dt = dt        # der Clip braucht die Zeit erst beim Zeichnen
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
        # Ohne Clip rueckt der Text in die Mitte statt unter ein schwarzes
        # Loch. DEMO_VIDEO = None ist der Auslieferungszustand, nicht der
        # Ausnahmefall -- die Seite muss auch so fertig aussehen.
        for i, line in enumerate(HOWTO):
            draw(screen, f["tiny"], line, 960, (900 if clip else 500) + i * 60, WHITE)
        footer(screen, f, "◀ BACK", "▶ START")


class GameScene(SceneBase):

    MUSIC = None   # die Intensitaetsstufe haengt an der Restzeit, siehe update()

    def __init__(self, ctx):
        super().__init__(ctx)
        self.marks = ctx.detector.fresh()   # id -> Viereck, eine Momentaufnahme
        self.total = sum(VALUES[i] for i in self.marks)
        # Das Ziel folgt dem, was tatsaechlich liegt. Frei gewuerfelt entschied
        # der Zufall, ob jemand 3 oder 200 Punkte zu ueberbruecken hat.
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
        # ponytail: Entwickler-Abkuerzung. Nicht in die Runde springen, sondern
        # in ihr Ende -- update() macht Sound, Musik und Szenenwechsel wie immer.
        if action == "right" and CHEAT_TAPS:
            self.taps += 1
            if self.taps >= CHEAT_TAPS:
                self.left = 0.0
            return "ok"
        self.taps = 0

    def update(self, dt):
        self.left -= dt
        self.confirm = max(0.0, self.confirm - dt)
        # Ein Blick auf den Detector pro Frame: Summe, Overlay und Ton kommen
        # aus derselben Momentaufnahme und koennen sich nicht widersprechen.
        marks = self.ctx.detector.fresh()
        self.total = sum(VALUES[i] for i in marks)
        if marks.keys() - self.marks.keys():
            # Nur bei NEU erkannt, sonst feuert es DETECT_HZ-mal pro Sekunde.
            # Fuenf Pucks gleichzeitig geben einen Ton, nicht fuenf: der
            # Mengenvergleich fasst sie von selbst zusammen.
            self.ctx.music.sfx("blip")
        self.marks = marks
        # Treffer muss stehen, nicht aufblitzen: die Hysterese in fresh() faengt
        # das Flackern ab, PERFECT_HOLD faengt die Absicht. Bleiben weniger als
        # PERFECT_HOLD Sekunden, laeuft der Zaehler nicht voll und die Runde
        # endet ueber left -- kein Sonderfall fuer "kurz vor Schluss" noetig.
        self.hit = self.hit + dt if self.total == self.target else 0.0
        self.ctx.music.stage(self.left)
        if self.left <= 0 or self.hit >= PERFECT_HOLD:
            self.ctx.music.sfx("finish")
            # marks statt total: die Summe steckt drin, und der Score-Screen
            # braucht ausserdem, *welche* Werte lagen (Preiszeile).
            self.switch_to(DisplayScoreScene(self.ctx, self.target, self.marks))

    def overlay(self, screen, r):
        """Detektionsfenster und erkannte Werte, gezeichnet ins Pane-Rechteck.

        Der Detector liefert Anteile von 0..1, hier wird einmal mit r
        multipliziert — deshalb stimmt das Overlay auch dann, wenn die Kamera
        eine andere Aufloesung liefert als angefordert.
        """
        f = self.ctx.fonts[MARK_FONT]
        rx, ry, rw, rh = TRAY_ROI
        # GREY, nicht YELLOW: das Fenster ist Chrome, kein Spielwert. Es steht
        # im Bild, damit man beim Ausrichten der Kamera sieht, wo Erkennung
        # aufhoert — sonst stellt man es blind ein.
        pygame.draw.rect(screen, GREY, (r.x + rx * r.w, r.y + ry * r.h,
                                        rw * r.w, rh * r.h), MARK_WIDTH)
        # Nur die Zahl, kein Viereck und keine Unterlage. Der Marker markiert
        # sich selbst -- ein gelber Rahmen drumherum sagt nichts, was das Bild
        # nicht schon zeigt, und verdeckt den Puck.
        for i, quad in self.marks.items():
            v = render(f, str(VALUES[i]), YELLOW)
            screen.blit(v, v.get_rect(center=(
                r.x + sum(x for x, _ in quad) / 4 * r.w,
                r.y + sum(y for _, y in quad) / 4 * r.h)))

    def bg(self):
        k = min(1.0, max(0.0, (WARN_SECONDS - self.left) / WARN_SECONDS))
        return tuple(round(b + (r - b) * k) for b, r in zip(BLACK, RED))

    def render(self, screen):
        # Kopfzeile in drei Spalten, darunter die beiden Kamerabilder. Die
        # Spaltenmitten 490 / 960 / 1430 gelten fuer beides, damit Zahl und
        # zugehoeriges Bild uebereinander stehen.
        f = self.ctx.fonts
        screen.fill(self.bg())
        draw(screen, f["small"], "GOAL",  490, 70, GREY)
        draw(screen, f["mid"], self.target, 490, 145, WHITE)
        draw(screen, f["small"], "TIME",  960, 70, GREY)
        draw(screen, f["mid"], int(self.left) + 1, 960, 145, WHITE)
        draw(screen, f["small"], "TOTAL", 1430, 70, GREY)
        draw(screen, f["mid"], self.total, 1430, 145, YELLOW)
        # Die Differenz ist die eigentliche Spielzahl. Vorher standen GOAL und
        # TOTAL 940 px auseinander und der Besucher musste sie im Kopf
        # subtrahieren -- unter Zeitdruck, aus 8 m, in einer lauten Halle. Die
        # Denkaufgabe ist Pucks schieben, nicht Kopfrechnen.
        #
        # Dasselbe Wort wie auf dem Score-Screen: einmal gelernt, zweimal
        # benutzt. Und PERFECT erbt genau diesen Platz -- deshalb gibt es
        # keine zweite Stelle mehr, an der Countdown und Abbruchwarnung sich
        # um dieselbe Zeile streiten (vorher per elif zugedeckt).
        perfect = self.hit > 0
        draw(screen, f["small"], "PERFECT" if perfect else "OFF BY", 960, 265, GREY)
        draw(screen, f["big"],
             int(PERFECT_HOLD - self.hit) + 1 if perfect
             else abs(self.target - self.total),
             960, 380, YELLOW)
        # Passthrough nur hier: im Idle bleibt die Bandbreite frei und der
        # Pi kalt. Rahmen statt Beschriftung — aus 8 m liest niemand ein Label,
        # und welches Bild der Arm ist, sieht man ohne Wort.
        for view, pos in zip(self.ctx.views, CAM_POS):
            cam = view.surface()
            if cam:
                r = cam.get_rect(center=pos)
                screen.fill(GREY, r.inflate(8, 8))
                screen.blit(cam, r)
                if view.det:
                    self.overlay(screen, r)
        # ◀ steht permanent da, nicht erst nach dem ersten Druck: ein
        # verstecktes Bedienelement ist keins. Das Versehen faengt die
        # Doppelbestaetigung ab, nicht die Unsichtbarkeit.
        footer(screen, f, "◀ QUIT",
               note="◀ AGAIN TO QUIT" if self.confirm > 0 else None)


class DisplayScoreScene(SceneBase):

    # Der Fertigsound braucht Luft. Erst ausklingen lassen, dann blendet die
    # Idle-Musik ein -- die Stille dazwischen ist der Effekt.
    MUSIC_IN = (2.2, 1500)

    def __init__(self, ctx, target, marks):
        super().__init__(ctx)
        self.target = target
        # Ein Marker pro Puck und lauter verschiedene Werte, also ist die
        # Menge verlustfrei -- sie sagt "lag auf dem Tablett", mehr braucht
        # die Preiszeile nicht.
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
        # Zwei Spalten mit Label darueber -- dieselbe Anordnung wie in der
        # Kopfzeile der Runde, die der Besucher gerade 60 s lang gelesen hat.
        draw(screen, f["small"], "GOAL",   660, 600, GREY)
        draw(screen, f["mid"], self.target, 660, 690, WHITE)
        draw(screen, f["small"], "TOTAL", 1260, 600, GREY)
        draw(screen, f["mid"], self.total, 1260, 690, WHITE)
        # Der Reveal. Vorher stand hier "0 = 4, 1 = 7, ..." -- die linke Spalte
        # war die ArUco-ID, und die steht auf keinem Puck als Ziffer. Der halbe
        # Tabelleninhalt verlangte eine Zuordnung, deren Schluessel niemand hat.
        #
        # Jetzt: nur die Werte, aufsteigend, und gelb die, die am Rundenende
        # tatsaechlich lagen. Damit ist es keine Nachschlagetabelle mehr,
        # sondern ein Bild der Runde -- der Preiskatalog und was man davon
        # hatte. Der Font ist monospace, also sitzen zehn Zellen im festen
        # 192er-Raster ohne eine einzige Breitenrechnung.
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
        # Nicht "TOP 10!": db.qualifies() ist kein Gate, hier landet jeder --
        # auch mit OFF BY 200. Die Ueberschrift versprach etwas, das der Code
        # nicht prueft, und zeigte fuenf Zeilen statt zehn. Der Screen ist
        # eine Eingabe, also heisst er wie eine.
        draw(screen, f["mid"], "ENTER YOUR NAME", 960, 130, YELLOW)
        draw(screen, f["big"], "◀", self.COLS[0], 470,
            YELLOW if self.cursor == 0 else WHITE)
        for i, slot in enumerate(self.slots):
            draw(screen, f["big"], self.LETTERS[slot], self.COLS[i + 1], 470,
                YELLOW if self.cursor == i + 1 else WHITE)
        screen.fill(YELLOW, (self.COLS[self.cursor] - 68, 580, 135, 9))
        draw(screen, f["tiny"], "LOWER MEANS BETTER", 960, 660, GREY)
        # 750/66 statt 860/65: die fuenfte Zeile lag vorher auf y 1096..1144
        # und die Rueckfrage auf 1114..1146 -- 528 x 30 px Ueberdeckung,
        # sichtbar sobald die DB fuenf Eintraege hatte. Jetzt endet die Liste
        # bei 1004, unter SAFE_BOTTOM.
        for i, (name, score) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {score}", 960, 720 + i * 64, WHITE)
        # Der Hinweis sagt, was ▶ *jetzt* tut. Dass im letzten Feld gespeichert
        # wird, stand vorher nirgends -- man musste es finden.
        footer(screen, f,
               left  = "▲▼ LETTER" if self.cursor else "◀ DISCARD",
               right = "▶ SAVE" if self.cursor == 3 else "▶ NEXT",
               note  = "◀ AGAIN TO DISCARD" if self.confirm > 0 else None)


if __name__ == "__main__":
    # Layout-Selbsttest. Genau der Fehler, der hier zweimal drin war: ein
    # Element wandert unter SAFE_BOTTOM oder ueberdeckt ein anderes, und
    # sichtbar wird es erst, wenn die DB genug Zeilen hat. Der Test faengt
    # jeden draw()-Aufruf ab und prueft die Rechtecke -- kein Screenshot,
    # kein Framework, kein Vergleichsbild das gepflegt werden muesste.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    _fonts = {k: pygame.font.Font(FONT_PATH, s) for k, s in FONT_SIZES.items()}

    boxes, _draw = [], draw
    def draw(screen, font, text, x, y, color):          # noqa: F811
        w, h = font.size(str(text))
        boxes.append((str(text), x - w//2, y - h//2, x + w//2, y + h//2))

    class _Stub:
        """Deckt Music, DB und Detector ab -- sie tun im Test alle nichts."""
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [(f"WW{i}", 999) for i in range(n)]
        def fresh(self):     return {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             views=(), demo=None))()

    # Panes sind kein draw(), zaehlen aber beim Ueberdecken mit.
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
                f"{label}: {t!r} ragt unter SAFE_BOTTOM (y {tp}..{b})"
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, c = bs[i], bs[j]
                assert not (a[1] < c[3] and c[1] < a[3]
                            and a[2] < c[4] and c[2] < a[4]), \
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
