import math
import random
import pygame
from functools import lru_cache
from typing import NamedTuple
from balance import gap, points
from config import *
from app import SceneBase
from sprites import sprite

# Die Sprites der Objekte, billig -> teuer. Szenen nennen nie einen Sprite-Namen
# selbst, sonst haengt ein Themawechsel an Stellen ausserhalb der Themadatei.
LADDER = [SPRITE[k] for k in sorted(VALUES, key=VALUES.get)]


@lru_cache(maxsize=512)
def render(font, text, color):
    """Gerenderte Textflaeche, gemerkt statt jedes Bild neu gebaut.

    Press Start 2P in 168 px war der teuerste Posten im Renderpfad: der
    Schirm zeigt hoechstens ein paar Dutzend verschiedene Zeichenketten, und
    die allermeisten stehen sekundenlang unveraendert da. Gemessen auf dem
    Pi 5 am 9.9.2026, Idle-Screen auf 60 Hz getrieben.

    512 statt frueher 256, seit draw_hint() die Hinweiszeile zeichenweise
    faerbt: jeder Buchstabe darin ist ein eigener Eintrag. Es bleibt trotzdem
    weit im Bereich der paar Dutzend Zeichenketten, die der Schirm zeigt.
    """
    return font.render(text, False, color)


def draw(screen, font, text, x, y, color):
    surf = render(font, str(text), color)
    screen.blit(surf, surf.get_rect(center=(x,y)))


def euro(units, sign=True):
    """Preis in 10-Cent-Einheiten -> Anzeigetext. Die EINZIGE Stelle, an der
    aus der Rechengroesse ein Preis wird.

    Gerechnet wird ueberall in Einheiten, weil die Preise teilerfremd sein
    muessen (siehe VALUES in config.py). Geteilt wird hier und sonst nirgends
    -- eine andere Einheit ist damit diese Funktion und keine Suche durch
    sechs Szenen.

    `sign=False` fuer die Preiszeile im Reveal: dort stehen zehn Zellen im
    168er-Raster, und fuenf Glyphen passen nicht nebeneinander. Das € steht
    dann in der Ueberschrift.
    """
    return f"{'€' if sign else ''}{units * CENTS / 100:.2f}"


def tray_sum(marks):
    """Was auf dem Tablett liegt, in Einheiten.

    Eine Funktion und keine dreimal hingeschriebene Summe: jede eigene
    Schreibweise ist eine Gelegenheit, VALUES zu vergessen, und ein
    Wertungsfehler sieht am Messetag wie ein Erkennungsproblem aus.
    """
    return sum(VALUES[i] for i in marks)


class Result(NamedTuple):
    """Was eine Runde hinterlaesst.

    Ein Objekt statt wachsender Parameterlisten: Score-Screen und Namens-
    eingabe brauchen beide alles davon, und die Datenbank noch einmal
    dasselbe. Ein Modus, der spaeter etwas dazulegt (Zuege, Schwierigkeit),
    haengt es hier an und nicht an drei Signaturen.

    Gespeichert wird die physische Wahrheit, gerechnet wird daraus -- dieselbe
    Trennung wie in db.py.
    """

    target: int          # Zielsumme in Einheiten
    total: int           # was am Rundenende lag
    dist:  int           # Abstand bei Rundenbeginn, der Nenner der Wertung
    left:  float         # Restzeit. > 0 heisst perfekt, sonst endete die Uhr
    marks: dict          # id -> Viereck, fuer den Preisreveal

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
    """Sprite zentriert auf (x, y). Eine eigene Funktion wie draw(), damit der
    Layout-Selbsttest sie genauso abfangen und auf Ueberdeckung pruefen kann."""
    s = sprite(name, scale)
    screen.blit(s, s.get_rect(center=(round(x), round(y))))


def hop(t, i=0, px=8):
    """Arcade-Huepfer: zwei Stellungen im 4-Hz-Takt, kein Sinus. 8-Bit-Figuren
    hatten keine Zwischenbilder, und genau das liest man als 8 Bit."""
    return -px if int(t * 4 + i) % 2 else 0


def parade(screen, t, y, speed, scale=5, gap=160):
    """Laufband aus allen Sprites quer ueber den Schirm, Attract-Mode-Deko.

    Blittet direkt statt ueber stamp(): das Band laeuft absichtlich links und
    rechts aus dem Bild, und genau das wuerde der Selbsttest als Fehler melden.
    """
    names = list(SPRITES)
    span = WIDTH + gap
    for i in range(span // gap + 1):
        x = (i * gap + t * speed) % span - gap / 2
        s = sprite(names[i % len(names)], scale)
        screen.blit(s, s.get_rect(center=(round(x), y + hop(t, i, scale))))


@lru_cache(maxsize=4)
def stripes(w, h, color, period=48):
    """Diagonale Streifen fuer den Balken (bei Sugar Rush eine Zuckerstange), einmal gebaut. Um eine Periode
    breiter als der Balken, damit ein verschobener Ausschnitt nahtlos weiterlaeuft."""
    s = pygame.Surface((w + period, h))
    s.fill(color)
    light = tuple(c + (255 - c) // 2 for c in color)
    for x in range(-h, w + period, period):
        pygame.draw.polygon(s, light, [(x, 0), (x + period // 2, 0),
                                       (x + period // 2 + h, h), (x + h, h)])
    return s


class Sprinkles:
    """Streusel, die von oben fallen: bei PERFECT und im Preisreveal.

    Rechtecke statt Sprites, hochkant oder quer -- so sehen Streusel auf einem
    Cupcake aus, und fill() ist das Billigste, was pygame kann. Sie liegen
    hinter der Schrift, die Zahl bleibt lesbar.

    Fester Seed: sonst sieht jeder Build-Log-Screenshot anders aus, und
    `git diff --stat docs/shots` meldet Szenen, an denen sich nichts geaendert hat.
    """

    N = 90

    def __init__(self):
        self.rng = random.Random(7)
        # Schon ueber den Schirm verteilt: das erste Bild ist voll, nicht leer.
        self.p = [self._new(self.rng.uniform(-HEIGHT, HEIGHT)) for _ in range(self.N)]

    def _new(self, y):
        w, h = self.rng.choice(((14, 40), (40, 14)))
        return [self.rng.uniform(0, WIDTH), y, self.rng.uniform(160, 320),
                w, h, self.rng.choice(CANDY)]

    def update(self, dt, more=True):
        for q in self.p:
            q[1] += q[2] * dt
        self.p = [q for q in self.p if q[1] < HEIGHT]
        if more:    # ohne Nachschub regnet es aus, statt abzureissen
            self.p += [self._new(-30) for _ in range(self.N - len(self.p))]

    def draw(self, screen):
        for x, y, _, w, h, c in self.p:
            screen.fill(c, (x, y, w, h))


def draw_hint(screen, font, text, x, y, base=GREY):
    """Hinweiszeile, zeichenweise gezeichnet: jeder Pfeil in der Farbe seines
    physischen Knopfes.

    Die vier Knoepfe am Panel sind gruen, rot, blau und gelb. Unbeschriftet
    sind sie nur bedienbar, wenn der Schirm die Zuordnung selbst herstellt --
    und Farbe stellt sie schneller her als Position: der Besucher sucht "den
    gruenen", nicht "den rechten". Deshalb faerbt sich der Pfeil und nicht das
    Wort daneben; das Wort sagt, was passiert, der Pfeil sagt, womit.

    Press Start 2P ist monospace, eine Zeichenbreite reicht also als
    Schrittweite. Ohne das waere jede Farbe im Text eine eigene
    Breitenrechnung.
    """
    w = font.size("A")[0]
    x0 = x - w * len(text) / 2
    for i, c in enumerate(text):
        draw(screen, font, c, x0 + w * (i + 0.5), y,
             BUTTON_COLORS.get(ARROWS.get(c), base))


def footer(screen, f, left=None, right=None, note=None):
    """Die untere Zeile: was die vier Knoepfe gerade tun.

    Immer an derselben Stelle, sonst sucht das Auge jedes Mal neu.

    `note` (die Doppelbestaetigung) *ersetzt* die Hinweise, statt daneben zu
    stehen. Das ist der Grund, warum hier nichts mehr klippen kann: es gibt
    kein zweites Element, das mit der Zeile kollidieren koennte. Und es ist
    die bessere Rueckmeldung -- die Antwort auf einen Knopfdruck erscheint
    dort, wo schon steht, was der Knopf tut.

    Position statt Wortstellung traegt die Richtung: Pfeil immer zuerst, das
    linke Hinweisfeld links, das rechte rechts.
    """
    if note:
        # Heller als die normalen Hinweise: die Rueckfrage ist keine
        # Beschriftung, sondern eine Frage, die eine Antwort braucht. Die
        # Dringlichkeit traegt trotzdem der rote Pfeil, nicht das Wort.
        draw_hint(screen, f["tiny"], note, 960, FOOTER_Y, WHITE)
        return
    if left:
        draw_hint(screen, f["tiny"], left, 600, FOOTER_Y)
    if right:
        draw_hint(screen, f["tiny"], right, 1320, FOOTER_Y)


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
        ctx.leds.show("idle")
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
        screen.fill(BG)
        # Oben und unten laeuft die Auslage vorbei, gegenlaeufig -- das ist
        # der Attract Mode. Aus 8 m sieht man Bewegung, bevor man Text liest.
        parade(screen, self.t, 56, 60)
        parade(screen, self.t, 1016, -60)
        # Titel zeichenweise: jede Letter in einer Bonbonfarbe, als Welle.
        # Monospace, eine Zeichenbreite ist die Schrittweite wie in draw_hint().
        title = "PICK'N'PLAY"
        w = f["big"].size("A")[0]
        for i, c in enumerate(title):
            draw(screen, f["big"], c, 960 + w * (i + 0.5 - len(title) / 2),
                 210 + round(14 * math.sin(self.t * 3 - i * 0.6)),
                 CANDY[i % len(CANDY)])
        # Das billigste und das teuerste Stueck -- aus dem Thema, nicht hier benannt.
        stamp(screen, LADDER[0], 8, 330, 430 + hop(self.t, 0, 8))
        stamp(screen, LADDER[-1], 8, 1590, 430 + hop(self.t, 1, 8))
        if int(self.t * 2) % 2:
            draw_hint(screen, f["mid"], "PRESS ▶", 960, 430, WHITE)
        # Frueher stand hier "THE LOWER THE BETTER" -- Pflicht, solange die
        # Liste aufsteigend sortierte. Seit die Punktzahl hoch ist wenn sie gut
        # ist, erklaert die Liste sich selbst, und die Zeile sagt jetzt was sie
        # ist statt wie man sie liest.
        draw(screen, f["tiny"], "TODAY'S BEST", 960, 556, GREY)
        for i, (name, pts) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {pts}", 960, 640 + i * 64, WHITE)


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
        self.t = 0.0      # laeuft weiter, idle wird bei jedem Knopf genullt

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
        self.dt = dt        # der Clip braucht die Zeit erst beim Zeichnen
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        draw(screen, f["mid"], "HOW TO PLAY", 960, 96, ACCENT)
        clip = self.ctx.demo.surface(self.dt) if self.ctx.demo else None
        if clip:
            r = clip.get_rect(center=(960, 460))
            screen.fill(GREY, r.inflate(8, 8))
            screen.blit(clip, r)
        else:
            # Die Auslage zeigt, *was* auf dem Tablett liegt, bevor der Text
            # sagt, was man damit tut. Ohne Clip ist hier sonst ein Loch.
            # Alle zehn, im selben 168er-Raster wie die Preiszeile im Reveal.
            for i, name in enumerate(LADDER):
                stamp(screen, name, 6, 204 + i * 168, 300 + hop(self.t, i, 6))
        # Ohne Clip rueckt der Text in die Mitte statt unter ein schwarzes
        # Loch. DEMO_VIDEO = None ist der Auslieferungszustand, nicht der
        # Ausnahmefall -- die Seite muss auch so fertig aussehen.
        # {secs} statt einer Zahl im Thema: die Rundenlaenge steht im Modus und
        # wird viel durchprobiert -- sie darf nicht an zwei Stellen leben.
        for i, line in enumerate(HOWTO):
            draw(screen, f["tiny"], line.format(secs=ROUND_SECONDS),
                 960, (800 if clip else 476) + i * 50, WHITE)
        footer(screen, f, "◀ BACK", "▶ START")


class GameScene(SceneBase):

    MUSIC = None   # die Intensitaetsstufe haengt an der Restzeit, siehe update()

    # Der Balken, absolute Koordinaten wie alles andere in dieser Datei.
    BAR   = pygame.Rect(240, 250, 1440, 70)
    # Skala des Balkens: das groesstmoegliche Ziel, nicht die Summe aller zehn
    # Cupcakes. Solange das Tablett vorbeladen war und umgeraeumt wurde, war
    # "alles was es ueberhaupt gibt" die richtige Laenge -- die Summe konnte
    # dorthin wandern. Seit das Tablett leer startet und die perfekte Loesung
    # zwei Stueck sind, spielt sich alles unter GAP_MAX ab: die Ziellinie stand
    # damit im linken Viertel und der Balken hatte in dem Bereich, auf den es
    # ankommt, keine Aufloesung mehr.
    #
    # GAP_MAX bleibt ueber alle Runden gleich, die Linie bedeutet also weiter
    # ueberall dasselbe. Wer mehr auflegt als das groesste Ziel, laeuft rechts
    # gegen den Anschlag -- _x() klemmt, und "weit drueber" ist als Aussage
    # genau richtig. Die genaue Zahl steht ohnehin darunter.
    SCALE = GAP_MAX
    GOAL_W, GOAL_OVER = 9, 18   # Breite und Ueberstand der Ziellinie

    def __init__(self, ctx):
        super().__init__(ctx)
        self.marks = ctx.detector.fresh()   # id -> Viereck, eine Momentaufnahme
        self.total = tray_sum(self.marks)
        # Das Ziel folgt dem, was tatsaechlich liegt -- am Automaten ist das
        # ein leeres Tablett, aber ein liegengebliebener Cupcake aendert die
        # Aufgabe dann mit, statt sie kaputtzumachen. Frei gewuerfelt entschied
        # der Zufall, ob jemand 0,30 EUR oder 20 EUR zu ueberbruecken hat.
        self.dist = gap(self.marks)
        self.target = self.total + self.dist
        self.left = float(ROUND_SECONDS)
        self.confirm = 0.0
        self.hit = 0.0
        self.taps = 0
        self.fx = None      # Streusel, nur solange PERFECT steht
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
        self.total = tray_sum(marks)
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
        if self.hit > 0:
            self.fx = self.fx or Sprinkles()
            self.fx.update(dt)
        else:
            self.fx = None
        self.ctx.music.stage(self.left)
        # Jedes Bild, nicht nur beim Wechsel: der Balken lebt von left, und
        # show() ist eine Zuweisung. Rot ab derselben Grenze wie der Grund.
        self.ctx.leds.show("hurry" if self.left <= WARN_SECONDS else "game",
                           max(0.0, self.left) / ROUND_SECONDS)
        if self.left <= 0 or self.hit >= PERFECT_HOLD:
            self.ctx.music.sfx("finish")
            # Ein Ergebnis statt vier Argumenten. left wird hier geklemmt:
            # die Schleife zaehlt ueber null hinaus, und eine negative Restzeit
            # waere in der Datenbank eine Luege statt einer Null.
            self.switch_to(DisplayScoreScene(self.ctx, Result(
                self.target, self.total, self.dist,
                max(0.0, self.left), self.marks)))

    def overlay(self, screen, r):
        """Detektionsfenster, gezeichnet ins Pane-Rechteck.

        Der Detector liefert Anteile von 0..1, hier wird einmal mit r
        multipliziert — deshalb stimmt das Overlay auch dann, wenn die Kamera
        eine andere Aufloesung liefert als angefordert.
        """
        rx, ry, rw, rh = TRAY_ROI
        # GREY, nicht ACCENT: das Fenster ist Chrome, kein Spielwert. Es steht
        # im Bild, damit man beim Ausrichten der Kamera sieht, wo Erkennung
        # aufhoert — sonst stellt man es blind ein.
        pygame.draw.rect(screen, GREY, (r.x + rx * r.w, r.y + ry * r.h,
                                        rw * r.w, rh * r.h), MARK_WIDTH)
        # Hier stand der Preis an jedem erkannten Cupcake. Entfernt am
        # 11.9.2026: er stand gegen die Grundregel des Spiels. "EVERY TREAT HAS
        # A HIDDEN PRICE" — wer die Preise waehrend der Runde ablesen kann,
        # rechnet, statt zu schaetzen, und der Reveal am Ende verliert seinen
        # Lernmoment. Aus 8 m las das ohnehin niemand; am Automaten, wo die
        # Haende am Leader-Arm liegen, schon.
        #
        # Bleibt als Kommentar stehen, weil es beim Einrichten der Kamera
        # nuetzlich ist: es ist die einzige Anzeige, die zeigt, WELCHEN Marker
        # die Erkennung gerade sieht, nicht nur dass sie einen sieht.
        # MARK_FONT in config.py existiert nur noch fuer diese Zeilen.
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
        """ACCENT, ausser auf rotem Grund: Pink auf RED hat 2,7 : 1, Sahne 6 : 1."""
        return WHITE if self.left <= WARN_SECONDS else ACCENT

    def bar(self, screen):
        """Wo die Summe steht und wo sie hin muss, als ein Bild.

        Der Balken macht das, was vier Zahlen nicht geschafft haben: Richtung
        und Abstand ohne Lesen. Fuellung links von der Linie heisst auflegen,
        rechts davon heisst wegnehmen, und wie weit sieht man, ohne zu
        subtrahieren.

        Reihenfolge: erst fuellen, dann rahmen. Andersherum deckt die Fuellung
        die linke Rahmenkante zu.

        Die Fuellung ist eine Zuckerstange, die langsam wandert: der Balken
        sagt dasselbe wie vorher, aber er lebt. Bewegung ist hier Deko, die
        Laenge bleibt die einzige Aussage.
        """
        r = self.BAR
        fill = stripes(r.w, r.h, self.acc())
        off = round((ROUND_SECONDS - self.left) * 40) % 48
        screen.blit(fill, r.topleft, (48 - off, 0, self._x(self.total) - r.x, r.h))
        pygame.draw.rect(screen, GREY, r, 3)
        # Die Ziellinie ragt oben und unten heraus. Ohne den Ueberstand
        # verschwindet sie genau dann, wenn es darauf ankommt -- naemlich wenn
        # die Fuellung sie fast erreicht hat und hell auf hell steht.
        screen.fill(WHITE, (self._x(self.target) - self.GOAL_W // 2,
                            r.y - self.GOAL_OVER,
                            self.GOAL_W, r.h + 2 * self.GOAL_OVER))

    def _x(self, value):
        """Punktwert -> x im Balken. Geklemmt, damit nichts herauslaeuft."""
        r = self.BAR
        return r.x + round(r.w * min(max(value, 0), self.SCALE) / self.SCALE)

    def render(self, screen):
        # Drei Spalten, links wo man steht, rechts wo man hin muss -- dieselbe
        # Leserichtung wie der Balken darunter. Die Spaltenmitten 490 / 960 /
        # 1430 gelten auch fuer die Kamerabilder.
        f = self.ctx.fonts
        screen.fill(self.bg())
        if self.fx:
            self.fx.draw(screen)    # hinter allem, die Zahlen bleiben oben
        draw(screen, f["small"], "ON TRAY", 490, 60, GREY)
        draw(screen, f["mid"], euro(self.total), 490, 132, self.acc())
        draw(screen, f["small"], "TIME", 960, 60, GREY)
        draw(screen, f["mid"], int(self.left) + 1, 960, 132, WHITE)
        draw(screen, f["small"], "GOAL", 1430, 60, GREY)
        draw(screen, f["mid"], euro(self.target), 1430, 132, WHITE)
        self.bar(screen)
        # Der Schirm sagt, was zu tun ist, statt zu melden, wie es steht.
        # "OFF BY 60" war eine Meldung: richtige Zahl, keine Richtung -- und
        # der Besucher musste erst darauf kommen, dass sie ueberhaupt eine hat.
        # Jetzt steht dort ein Verb, und die Zahl ist sein Argument.
        #
        # PERFECT erbt genau diesen Platz, deshalb gibt es keine zweite Stelle,
        # an der sich zwei Meldungen um dieselbe Zeile streiten koennten.
        diff = self.target - self.total
        if self.hit > 0:
            label, big = f"HOLD {int(PERFECT_HOLD - self.hit) + 1}", "PERFECT"
        else:
            # "ADD POINTS 60" war eine Punktzahl -- und die gibt es in der
            # Runde nicht mehr. Hier steht ein Preis, weil das die einzige
            # Groesse ist, auf die der Besucher waehrend der Runde schaut.
            label, big = ("ADD" if diff > 0 else "REMOVE"), euro(abs(diff))
        draw(screen, f["small"], label, 960, 400, GREY)
        draw(screen, f["big"], big, 960, 510, self.acc())
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
    """Der Hochdreher: eine Zahl laeuft auf die Punktzahl zu, sonst nichts.

    Waehrend der Runde steht bewusst keine Punktzahl auf dem Schirm -- dort
    geht es allein darum, den Preis zu treffen. Die Wertung passiert hier, und
    sie passiert als Ereignis, nicht als Anzeige: erst laeuft die Zahl hoch,
    dann erscheint, woraus sie besteht, und darunter liegt der Preisreveal.

    Die Reihenfolge ist der ganze Trick. Steht die Aufschluesselung sofort da,
    kann man das Ende des Hochlaufs ausrechnen, bevor er anfaengt -- und damit
    ist der Effekt weg, fuer den es ihn gibt.
    """

    # Der Fertigsound braucht Luft. Erst ausklingen lassen, dann blendet die
    # Idle-Musik ein -- die Stille dazwischen ist der Effekt.
    MUSIC_IN = (2.2, 1500)
    # Sekunden bis die Zahl steht. Kuerzer liest sich wie ein Sprung, laenger
    # wie ein Ladebalken. Bleibt unter MUSIC_IN, sonst faellt der Einsatz der
    # Idle-Musik in den Hochlauf.
    COUNT = 1.8

    def __init__(self, ctx, res):
        super().__init__(ctx)
        self.res = res
        # Ein Marker pro Cupcake und lauter verschiedene Preise, also ist die
        # Menge verlustfrei -- sie sagt "lag auf dem Tablett", mehr braucht
        # die Preiszeile nicht.
        self.mine = {VALUES[i] for i in res.marks}
        self.shown = 0
        self.done = False
        self.idle = 0.0
        self.t = 0.0
        self.fx = Sprinkles()   # jeder bekommt den Regen -- kein Scheitern, nur eine Zahl
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
        self.fx.update(dt, more=self.t < 2.5)   # ein Schauer, dann regnet es aus
        # Schnell an, langsam aus: (1-k)**3 ist die Kurve, mit der eine
        # Boxmaschine austrudelt. Linear hochzaehlen sieht aus wie ein Fortschritt
        # und nicht wie ein Ergebnis.
        k = min(1.0, self.t / self.COUNT)
        shown = round(self.res.score * (1 - (1 - k) ** 3))
        if shown // 100 > self.shown // 100:
            # Ein Tick je Hundert. "blip" ist duenn und leise und genau dafuer
            # gebaut -- ein eigener Klang waere Arbeit fuer dieselbe Wirkung.
            self.ctx.music.sfx("blip")
        self.shown = shown
        if not self.done and k >= 1.0:
            self.done = True                    # feuert einmal, auch bei 0 Punkten
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
        # Die Runde in drei Spalten -- erst wenn die Zahl steht. Auf den Mitten
        # der Runde (490 / 960 / 1430): dort hat das Auge gerade eine halbe
        # Minute lang gelesen, es muss die Stellen nicht neu suchen.
        #
        # Die dritte Spalte wechselt, weil sonst eine der beiden Lagen eine
        # Zahl doppelt zeigt. Wer danebenlag, will wissen wie weit; wer
        # getroffen hat, sieht das schon daran, dass GOAL und YOURS gleich
        # sind -- dort ist der Zeitbonus das Einzige, was noch etwas sagt.
        # Und er sagt genau das, was ihn von den anderen Perfekten trennt.
        if self.done:
            draw(screen, f["small"], "GOAL", 490, 500, GREY)
            draw(screen, f["mid"], euro(res.target), 490, 590, WHITE)
            draw(screen, f["small"], "YOURS", 960, 500, GREY)
            draw(screen, f["mid"], euro(res.total), 960, 590, WHITE)
            label, value = (("TIME BONUS", f"+{res.bonus}") if res.bonus
                            else ("OFF BY", euro(res.off)))
            draw(screen, f["small"], label, 1430, 500, GREY)
            draw(screen, f["mid"], value, 1430, 590, WHITE)
        # Der Reveal. Vorher stand hier "0 = 4, 1 = 7, ..." -- die linke Spalte
        # war die ArUco-ID, und die steht auf keinem Cupcake als Ziffer. Der
        # halbe Tabelleninhalt verlangte eine Zuordnung, deren Schluessel
        # niemand hat.
        #
        # Jetzt: jedes Teil als Sprite mit seinem Preis darunter, aufsteigend,
        # und pink und huepfend die, die am Rundenende tatsaechlich lagen.
        # Damit ist es keine Nachschlagetabelle mehr, sondern ein Bild der
        # Runde -- die Auslage und was man davon hatte. Und es ist der
        # Lernmoment: "der Schokokuchen war der teure".
        #
        # Das € steht in der Ueberschrift und nicht in jeder Zelle: zehn Zellen
        # im 168er-Raster, da passen vier Glyphen nebeneinander und nicht fuenf.
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

    COLS = (510, 840, 1050, 1260)
    # Der Cursorbalken ist ein fill(), kein draw() -- ohne Konstante kaeme er
    # im Layout-Selbsttest nicht vor, und genau die Klasse Fehler faengt der ab.
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
            if self.cursor == 3:
                # Alles, was die Runde physisch war -- die Punktzahl rechnet
                # die Datenbank selbst aus, damit eine spaetere Formel auch
                # fuer alte Runden gilt.
                self.ctx.db.add(self.name(), self.res.off, goal=self.res.target,
                                total=self.res.total, dist=self.res.dist,
                                secs=self.res.left)
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
        self.t += dt
        self.confirm = max(0.0, self.confirm - dt)
        if self.idle > IDLE_TIMEOUT:
            self.switch_to(IdleScene(self.ctx))

    def render(self, screen):
        f = self.ctx.fonts
        screen.fill(BG)
        stamp(screen, LADDER[1], 6, 180, 110 + hop(self.t, 0, 6))
        stamp(screen, LADDER[-2], 6, 1740, 110 + hop(self.t, 1, 6))
        # Nicht "TOP 10!": db.qualifies() ist kein Gate, hier landet jeder --
        # auch mit OFF BY 200. Die Ueberschrift versprach etwas, das der Code
        # nicht prueft, und zeigte fuenf Zeilen statt zehn. Der Screen ist
        # eine Eingabe, also heisst er wie eine.
        draw(screen, f["mid"], "ENTER YOUR NAME", 960, 110, ACCENT)
        draw(screen, f["big"], "◀", self.COLS[0], 380,
            ACCENT if self.cursor == 0 else WHITE)
        for i, slot in enumerate(self.slots):
            draw(screen, f["big"], self.LETTERS[slot], self.COLS[i + 1], 380,
                ACCENT if self.cursor == i + 1 else WHITE)
        screen.fill(ACCENT, (self.COLS[self.cursor] - 68, self.CURSOR_Y,
                             135, self.CURSOR_H))
        draw(screen, f["tiny"], "TODAY'S BEST", 960, 556, GREY)
        # Die fuenfte Zeile war der Klippfehler vom 28. August: sie lag unter
        # SAFE_BOTTOM und ueberdeckte die Abbruch-Rueckfrage, sichtbar erst ab
        # fuenf Eintraegen in der DB. Auf 1080 endet die Liste bei 912.
        for i, (name, pts) in enumerate(self.top):
            draw(screen, f["small"], f"{i+1}. {name}  {pts}", 960, 632 + i * 64, WHITE)
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

    # Sprites zaehlen mit, mit ihrer vollen Kante: 16 Sprite-Pixel.
    def stamp(screen, name, scale, x, y):               # noqa: F811
        boxes.append((name, x - 8 * scale, y - 8 * scale, x + 8 * scale, y + 8 * scale))

    class _Stub:
        """Deckt Music, DB und Detector ab -- sie tun im Test alle nichts."""
        def __getattr__(self, _): return lambda *a, **k: None
        def top(self, n=5):  return [(f"WW{i}", 999) for i in range(n)]
        def fresh(self):     return {i: [(.3, .3)] * 4 for i in (0, 3, 7, 9)}
    _s = _Stub()
    ctx = type("C", (), dict(detector=_s, db=_s, fonts=_fonts, music=_s,
                             leds=_s, views=(), demo=None))()

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

    # Der Balken ist ein fill(), kein draw() -- ohne diese Zeile kaeme er im
    # Test nicht vor, und genau die Klasse Fehler faengt er ab. Die Ziellinie
    # liegt per Konstruktion darin und wird vom Rechteck mit abgedeckt.
    bar = [("bar", GameScene.BAR.x, GameScene.BAR.y - GameScene.GOAL_OVER,
                   GameScene.BAR.right, GameScene.BAR.bottom + GameScene.GOAL_OVER)]

    check("idle",  IdleScene(ctx))
    check("howto", HowToScene(ctx))
    g = GameScene(ctx)
    check("game",         g, panes + bar)
    check("game confirm", g, panes + bar, confirm=2.0)
    check("game perfect", g, panes + bar, confirm=0.0, hit=1.0)
    # Beide Richtungen der Handlungsanweisung. Die Zahl darunter ist jetzt ein
    # Preis und damit breiter als frueher -- sie steht in der Mitte, wo sie am
    # ehesten anstoesst.
    check("game remove",  g, panes + bar, hit=0.0, total=g.target + 40)
    # Randlagen des Balkens: leeres Tablett (der Normalfall am Automaten) und
    # Ziel am oberen Anschlag. Die breiteste Zahl, die je in der Kopfzeile
    # stehen kann, ist die Summe ALLER Preise -- der Balken klemmt dort zwar,
    # die Zahl daneben nicht, und sie ist es, die anstossen koennte.
    check("game empty",   g, panes + bar, total=0, target=GameScene.SCALE)
    check("game full",    g, panes + bar, total=sum(VALUES.values()), target=0)

    # Der Score-Screen in beiden Zustaenden: waehrend die Zahl hochlaeuft
    # steht die Aufschluesselung noch nicht da, danach schon. Geprueft werden
    # muss der zweite -- dort stehen drei Spalten, wo vorher zwei standen.
    res = Result(target=67, total=64, dist=50, left=0.0,
                 marks={0: 1, 3: 1, 7: 1, 9: 1})
    check("score counting", DisplayScoreScene(ctx, res))
    check("score done",     DisplayScoreScene(ctx, res),
          shown=res.score, done=True, t=2.5)
    # Und eine perfekte Runde: vierstellige Punktzahl, "+100" statt "+0".
    best = Result(target=67, total=67, dist=50,
                  left=ROUND_SECONDS - PERFECT_HOLD, marks=dict.fromkeys(VALUES, 1))
    check("score perfect", DisplayScoreScene(ctx, best),
          shown=best.score, done=True, t=2.5)
    for cur in range(4):
        for conf in (0.0, 2.0):
            L = LeaderboardScene
            bar = [("cursor", L.COLS[cur] - 68, L.CURSOR_Y,
                              L.COLS[cur] + 67, L.CURSOR_Y + L.CURSOR_H)]
            check(f"board cursor={cur} confirm={conf}",
                  L(ctx, res), bar, cursor=cur, confirm=conf)
    print("ok")
