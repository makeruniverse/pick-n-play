import fcntl
import os
import random
import struct
import threading
import time

import cv2
import numpy as np
import pygame

from config import (VALUES, CAM_SIZE, CAM_VIEW, MARKER_HOLD, DETECT_HZ,
                    TRAY_ROI, DEMO_SIZE, BUTTON_PINS, KEY_REPEAT,
                    LED_DEV, LED_COUNT, LED_ORDER, LED_BRIGHT, LED_FPS,
                    LED_STRIPES, LED_A, LED_B, LED_RED)


def _quad(cx, cy, r=0.06):
    """Viereck um einen Mittelpunkt, in Bildanteilen. Nur fuer FakeDetector."""
    return ((cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r))


class FakeDetector:
    """Attrappe: ein leeres Tablett, das sich nach und nach fuellt.

    ponytail: legt alle `period` Sekunden ein Stueck dazu und raeumt ab, wenn
    eine Weile niemand gefragt hat. Ersetzt durch ArucoDetector(Camera()),
    eine Zeile in main.py.

    Warum nicht mehr fuenf gewuerfelte Marker auf einmal: das war das Spiel
    von vor der Wertungssitzung, in dem das Tablett vorbeladen war und
    umgeraeumt wurde. Heute wird es nach jeder Runde geleert und aufgebaut --
    eine Attrappe, die damit nicht anfaengt, laesst jede lokale Runde bei einer
    anderen Aufgabe beginnen als am Automaten, und genau das soll sie nicht.

    Abgeraeumt wird ueber die Luecke zwischen zwei Abfragen: nur die Runde
    fragt den Detector, der Idle-Screen nicht. Eine lange Pause heisst also
    "es lief keine Runde", und in der Zeit leert am Automaten jemand das
    Tablett. Die Attrappe braucht dafuer kein Wissen ueber Szenen.
    """

    def __init__(self, period=3.0):
        self.period = period
        self.t = self.seen = 0.0
        self.marks = {}
        self.rest = []

    def fresh(self):
        now = time.monotonic()
        if now - self.seen > self.period * 3:      # Pause = jemand hat geraeumt
            self.marks, self.rest = {}, random.sample(sorted(VALUES), len(VALUES))
            self.t = now
        self.seen = now
        if self.rest and now - self.t > self.period:
            self.t = now
            n = len(self.marks)
            self.marks[self.rest.pop()] = _quad(0.25 + n % 4 * 0.17,
                                                0.35 + n // 4 * 0.25)
        return self.marks


class Camera:
    """Grabber-Thread. read() liefert immer das NEUESTE Bild, nie ein altes.

    cap.read() ist C++-Code und gibt das GIL frei, also ist ein Thread hier
    echte Parallelitaet. BUFFERSIZE=1, sonst reicht V4L2 alte Frames nach und
    die Erkennung hinkt sichtbar hinterher.
    """

    def __init__(self, index, size=CAM_SIZE, warmup=3.0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            # Laut scheitern, nicht leise auf Attrappe zurueckfallen: erfundene
            # Zahlen auf dem Automaten waeren am Messetag nicht zu erkennen.
            raise RuntimeError(f"Kamera {index} laesst sich nicht oeffnen")
        # MJPG vor der Groesse setzen: als YUYV kostet 720p ein Vielfaches an
        # USB-Bandbreite, und daran haengt, ob zwei Kameras an einem Bus gehen.
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.lock = threading.Lock()
        self.frame = None
        self.seq = 0          # zaehlt neue Bilder, damit CameraView cachen kann
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        # isOpened() sagt nur, dass sich das Geraet oeffnen liess -- ob Bilder
        # kommen, sagt erst ein Bild. Ist die Kamera belegt (zweiter Spielstart,
        # anderes Programm), liefert macOS ein offenes Handle und read() danach
        # fuer immer False. Ohne diese Schleife bleiben beide Panes einfach
        # schwarz und das Spiel laeuft weiter: genau der stille Fehler, den der
        # raise darueber verhindern sollte. Kostet Startzeit, keine Laufzeit.
        t0 = time.monotonic()
        while self.frame is None and time.monotonic() - t0 < warmup:
            time.sleep(0.05)
        if self.frame is None:
            self.close()
            raise RuntimeError(f"Kamera {index} liefert kein Bild "
                               f"(belegt? Kamerarechte?)")

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                # Kamera weg oder haengt: nicht busy-loopen. Das letzte Bild
                # bleibt stehen, die Hysterese laeuft ab, tray_sum() geht auf 0.
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame
                self.seq += 1

    def read(self):
        with self.lock:
            return self.seq, self.frame

    def close(self):
        self.running = False
        self.cap.release()


class ArucoDetector:
    """Marker -> {id: Viereck}. Gleiche Signatur wie FakeDetector.

    Eigener Thread mit DETECT_HZ statt 60 Hz: detectMarkers ist teuer, und
    niemand schiebt Pucks 60-mal pro Sekunde.

    Die Vierecke kommen als Anteile am ganzen Bild (0..1) heraus, nicht als
    Pixel. Sonst muesste die Szene die Kameraaufloesung kennen — und die
    stimmt in dem Moment nicht mehr, in dem ein UVC-Geraet die angeforderte
    Groesse nicht liefert. Das tun sie regelmaessig, und der Fehler waere ein
    Overlay, das systematisch danebenliegt.
    """

    def __init__(self, cam, hold=MARKER_HOLD, roi=TRAY_ROI):
        self.cam = cam
        self.hold = hold
        self.roi = roi
        self.lock = threading.Lock()
        self.marks = {}         # marker_id -> (Zeitpunkt, Viereck in 0..1)
        # Auch helle Zellen auf dunklem Grund: Schokokuchen tragen den Marker
        # invertiert. Normale Marker findet er weiterhin, er probiert beides.
        params = cv2.aruco.DetectorParameters()
        params.detectInvertedMarker = True
        self.det = cv2.aruco.ArucoDetector(
            cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), params)
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        rx, ry, rw, rh = self.roi
        while True:
            _, frame = self.cam.read()
            if frame is not None:
                h, w = frame.shape[:2]
                x0, y0 = int(rx * w), int(ry * h)
                x1, y1 = x0 + int(rw * w), y0 + int(rh * h)
                # Zuschneiden statt hinterher zu filtern: erledigt beides in
                # einem Schritt, und die Erkennung kostet nur noch, was das
                # Fenster gross ist. Gemessen 1,21 statt 2,00 ms bei 60 % x 70 %.
                # Der Ausschnitt ist eine numpy-Sicht, keine Kopie.
                gray = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
                corners, ids, _ = self.det.detectMarkers(gray)
                now = time.monotonic()
                found = {}
                for c, i in zip(corners, ids.flatten() if ids is not None else ()):
                    if int(i) not in VALUES:
                        continue    # fremder Marker, gehoert nicht zum Spiel
                    # Fenster- zurueck in Bildanteile, damit die Szene nur noch
                    # mit dem Pane-Rechteck multiplizieren muss.
                    q = c.reshape(4, 2) / (x1 - x0, y1 - y0) * (rw, rh) + (rx, ry)
                    found[int(i)] = (now, tuple(map(tuple, q)))
                with self.lock:
                    self.marks.update(found)
            time.sleep(1 / DETECT_HZ)

    def fresh(self):
        # Hysterese: ein Marker zaehlt weiter, solange er kuerzer als hold
        # verdeckt ist. Das ist die Loesung fuer die Hand ueber dem Tablett,
        # nicht fuer Pucks, die wirklich weggenommen werden.
        # Der Lock ist Pflicht, nicht Vorsicht: ohne ihn wirft die Iteration
        # RuntimeError, sobald der Thread waehrenddessen eine neue ID einfuegt.
        now = time.monotonic()
        with self.lock:
            return {i: q for i, (t, q) in self.marks.items() if now - t < self.hold}


class Buttons:
    """Vier Arcade-Taster an GPIO. Einmal pro Bild abgefragt, nicht per Callback.

    Der Overview sah hier gpiozero-Callbacks in eine `queue.SimpleQueue` vor,
    die der Loop leert. Das ist eine Zeile mehr Code an drei Stellen: ein
    fremder Thread, eine Queue und -- weil `pygame.key.set_repeat()` nur fuer
    die Tastatur gilt -- eine zweite Uhr fuer die Wiederholung beim Halten.

    Stattdessen abgefragt: ein Tastendruck dauert 80 bis 200 ms, ein Bild 33.
    Es gibt nichts zu verpassen. Damit gilt hier dasselbe wie ueberall sonst im
    Spiel -- der Loop besitzt die Zeit, `pump(dt)` bekommt sie durchgereicht,
    und die Wiederholung rechnet mit demselben `dt` wie der Rundenzaehler.
    Kein Lock, kein Thread, keine zweite Zeitquelle.

    `KEY_REPEAT` gilt fuer beide Wege: was am Automaten passiert, wenn man den
    Knopf haelt, ist dasselbe wie beim Entwickeln auf der Tastatur. Genau davor
    warnt der Overview, und das ist die Stelle, an der es sonst auseinanderginge.
    """

    def __init__(self, pins=BUTTON_PINS, repeat=KEY_REPEAT):
        # Import erst hier: gpiozero und lgpio gibt es nur auf dem Pi
        # (pyproject-Extra `pi`). Am Entwicklungsrechner laeuft das Spiel mit
        # PNP_BUTTONS=0 und die Zeile wird nie ausgefuehrt.
        from gpiozero import Button
        self.delay, self.rate = (ms / 1000 for ms in repeat)
        # bounce_time entprellt in gpiozero, damit sitzt kein Kondensator im
        # Kabelbaum, den am Messetag niemand nachloetet.
        self.btns = {a: Button(p, pull_up=True, bounce_time=0.02)
                     for p, a in pins.items()}
        self.wait = {}     # action -> Sekunden bis zur naechsten Wiederholung

    def pump(self, dt):
        """Aktionen, die seit dem letzten Bild ausgeloest haben."""
        out = []
        for a, b in self.btns.items():
            if not b.is_pressed:
                self.wait.pop(a, None)     # losgelassen: naechstes Mal frisch
                continue
            w = self.wait.get(a)
            if w is None:
                out.append(a)              # Flanke: sofort, nicht erst nach delay
                self.wait[a] = self.delay
                continue
            w -= dt
            # while, nicht if: bei einem langen Bild sind mehrere Wiederholungen
            # faellig, und += rate haelt die Kadenz, waehrend = rate driften wuerde.
            while w <= 0:
                out.append(a)
                w += self.rate
            self.wait[a] = w
        return out

    def close(self):
        for b in self.btns.values():
            b.close()


class VideoView:
    """Clip aus einer Datei, in Schleife. Gleiche Konvertierung wie CameraView.

    pygame kann kein Video, aber cv2.VideoCapture nimmt eine Datei genauso wie
    ein Geraet -- der Player ist damit dieselbe Klasse wie der Passthrough, nur
    mit einer Uhr statt einem Grabber. Eine Kamera *drueckt* Bilder (deshalb
    dort ein Thread und ein Sequenzzaehler), eine Datei wird *gezogen* (deshalb
    hier dt).

    ponytail: dekodiert im Renderthread. Bei 1120x630 sind das wenige
    Millisekunden, 25-mal pro Sekunde, und nur solange die Szene steht. Wird es
    auf dem Pi eng: derselbe Grabber-Thread wie in Camera, die Form passt schon.
    """

    def __init__(self, path, size=DEMO_SIZE):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Demo-Clip {path} laesst sich nicht oeffnen")
        self.size = size
        self.step = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 25)
        self.t = self.step      # erstes Bild sofort, nicht erst nach step
        self.surf = None

    def surface(self, dt):
        self.t += dt
        if self.t < self.step:
            return self.surf    # Clip laeuft mit 25 Hz, gerendert wird mit 60
        self.t = 0.0
        ok, frame = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # am Ende von vorn
            ok, frame = self.cap.read()
        if ok:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
        return self.surf

    def close(self):
        self.cap.release()


class CameraView:
    """Passthrough: neuestes Kamerabild als pygame-Surface in Insetgroesse.

    Erst verkleinern, dann kopieren — die Konvertierung kostet proportional
    zur Pixelzahl, und 400x300 sind ein Zwanzigstel von 1280x720.
    frombuffer mit "BGR" spart das cvtColor: pygame-ce nimmt OpenCVs
    Kanalreihenfolge direkt an.

    INTER_LINEAR, nicht INTER_AREA: gemessen 0,17 ms statt 3,5 ms pro Frame.
    AREA mittelt beim Verkleinern ueber alle Quellpixel und ist bei Faktor 3
    zwanzigmal teurer — fuer ein Inset hinter Scanlines sieht das niemand,
    aber 3,5 ms waeren auf dem Pi ein Fuenftel des Frame-Budgets.
    """

    def __init__(self, cam, det=None, size=CAM_VIEW):
        self.cam = cam
        self.det = det      # nur das Top-Down-Pane hat einen: das Arm-Bild ist
        self.size = size    # reiner Passthrough, dort gaebe es nichts zu zeigen
        self.seq = -1
        self.surf = None

    def surface(self):
        seq, frame = self.cam.read()
        # Die Kamera liefert 30 Bilder/s, gerendert wird mit 60: ohne diesen
        # Vergleich wird jedes Bild zweimal konvertiert, fuer nichts.
        if seq != self.seq and frame is not None:
            small = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            self.surf = pygame.image.frombuffer(small.tobytes(), self.size, "BGR")
            self.seq = seq
        return self.surf


# WS2812 ueber SPI: jedes Datenbit wird ein SPI-Byte. Bei 6,5 MHz dauert ein
# Byte 1,23 us, das ist das 800-kHz-Raster des Streifens. 0b11000000 haelt die
# Leitung 0,3 us hoch (eine 0), 0b11111100 0,9 us (eine 1). Muster und Takt wie
# rpi5-ws2812, das damit auf dem Pi 5 laeuft -- hier ohne die Abhaengigkeit,
# weil es ein ioctl und ein write sind.
SPI_HZ     = 6_500_000
BIT0, BIT1 = 0b11000000, 0b11111100
SPI_IOC_WR_MAX_SPEED_HZ = 0x40046B04   # _IOW('k', 4, u32) aus linux/spi/spidev.h
# 300 Nullbytes = 370 us Low vor jedem Bild: Latch fuer das vorige, auch fuer
# den neueren WS2812B, der erst nach 280 us uebernimmt.
RESET = bytes(300)


def led_encode(rgb, order=LED_ORDER):
    """(n, 3) uint8 in RGB -> SPI-Bytes, eines pro Datenbit, Reset davor."""
    idx = ["RGB".index(c) for c in order]
    bits = np.unpackbits(np.ascontiguousarray(rgb[:, idx], np.uint8).ravel())
    return RESET + np.where(bits, BIT1, BIT0).astype(np.uint8).tobytes()


def led_frame(state, k, t, n):
    """Ein Bild des Streifens als (n, 3) RGB. Reine Funktion von Zustand und Zeit.

    idle   Zuckerstange, laeuft langsam -- Attract Mode, aus 8 m sichtbar
    game   Restzeit als Balken: k = Anteil der Runde, der noch uebrig ist
    hurry  letzte Sekunden, rot mit 2 Hz, gleichzeitig mit dem roten Bildschirm
    score  dieselbe Zuckerstange, viermal so schnell
    """
    i = np.arange(n)
    if state == "game":
        return np.where((i < k * n)[:, None], LED_A, np.multiply(LED_A, 0.08))
    if state == "hurry":
        return np.tile(LED_RED if int(t * 4) % 2 == 0 else (0, 0, 0), (n, 1))
    w = max(1, n // LED_STRIPES)
    shift = int(t * (4 if state == "score" else 1) * 2 * w)   # zwei Streifen pro Sekunde
    return np.where((((i + shift) // w) % 2 == 0)[:, None], LED_A, LED_B)


class Leds:
    """WS2812-Streifen an SPI0, ein Worker-Thread mit Zustandsslot.

    `show()` setzt nur den Slot und kehrt sofort zurueck -- LEDs blockieren
    den Renderloop nie. Ohne Geraet (Mac, SPI aus) ist alles still, wie Music
    ohne Audio: die Szenen merken davon nichts und brauchen keine None-Pruefung.
    """

    def __init__(self, dev=LED_DEV, n=LED_COUNT):
        self.slot = ("idle", 1.0)
        self.n = n
        self.run = False
        try:
            self.fd = os.open(dev, os.O_WRONLY)
        except OSError as e:
            print(f"LEDs aus: {e}")
            return
        fcntl.ioctl(self.fd, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("I", SPI_HZ))
        # spidev nimmt pro write() hoechstens bufsiz Bytes, Default 4096 -- ein
        # Bild mit 480 LEDs hat 11 820. Mehrere writes haben Luecken dazwischen,
        # und ein aelterer WS2812B latcht schon nach 50 us, also mitten im Bild.
        # Die Abhilfe gehoert in den Kernel (spidev.bufsiz, docs/betrieb.md).
        with open("/sys/module/spidev/parameters/bufsiz") as f:
            self.chunk = int(f.read())
        if len(RESET) + n * 24 > self.chunk:
            print(f"LEDs: Bild {len(RESET) + n * 24} B > spidev.bufsiz {self.chunk}, "
                  "wird gestueckelt -- kann flackern")
        self.run = True
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def show(self, state, k=1.0):
        self.slot = (state, k)    # ein Tupel zuzuweisen ist atomar, kein Lock

    def _loop(self):
        t0 = time.monotonic()
        while self.run:
            state, k = self.slot
            self._write(led_frame(state, k, time.monotonic() - t0, self.n))
            time.sleep(1 / LED_FPS)   # ponytail: plus Schreibzeit (~15 ms), also ~20 Bilder/s

    def _write(self, rgb):
        data = led_encode(np.clip(np.multiply(rgb, LED_BRIGHT), 0, 255).astype(np.uint8))
        for o in range(0, len(data), self.chunk):
            os.write(self.fd, data[o:o + self.chunk])

    def close(self):
        if not self.run:
            return
        self.run = False
        self.th.join()
        self._write(np.zeros((self.n, 3)))   # aus, nicht im letzten Bild stehen bleiben
        os.close(self.fd)


if __name__ == "__main__":
    # Selbsttest ohne Kamera: synthetisches Tablett. Prueft, dass Dictionary
    # und markers/ zusammenpassen, dass die Vierecke da liegen wo die Marker
    # gezeichnet wurden, dass das Fenster aussortiert und dass die Hysterese
    # erst haelt und dann abbaut. uv run game/hw.py -> ok
    import numpy as np

    W, H, MS = 640, 480, 90

    class _Still:
        def __init__(self, frame): self.frame = frame
        def read(self): return 1, self.frame

    def _tray(spots):
        """spots: {marker_id: (x, y) linke obere Ecke in Pixeln}"""
        frame = np.full((H, W, 3), 255, np.uint8)   # weiss = Ruhezone
        for i, (x, y) in spots.items():
            m = np.zeros((MS, MS), np.uint8)
            cv2.aruco.generateImageMarker(
                cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50),
                i, MS, m)
            frame[y:y + MS, x:x + MS] = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
        return frame

    def _settle(det):
        time.sleep(4 / DETECT_HZ)
        return det.fresh()

    # 1 · Erkennung, Werte und Lage der Vierecke bei offenem Fenster
    spots = {0: (60, 60), 4: (260, 60), 9: (460, 260)}
    still = _Still(_tray(spots))
    det_open = ArucoDetector(still, roi=(0, 0, 1, 1))
    marks = _settle(det_open)
    assert sorted(marks) == sorted(spots), marks
    assert sum(VALUES[i] for i in marks) == sum(VALUES[i] for i in spots)
    for i, (x, y) in spots.items():
        cx = sum(p[0] for p in marks[i]) / 4 * W
        cy = sum(p[1] for p in marks[i]) / 4 * H
        assert abs(cx - (x + MS / 2)) < 3 and abs(cy - (y + MS / 2)) < 3, (i, cx, cy)

    # 1b · Invertierter Marker (Schokokuchen) wird genauso erkannt
    det_inv = ArucoDetector(_Still(255 - _tray({5: (260, 160)})), roi=(0, 0, 1, 1))
    assert sorted(_settle(det_inv)) == [5], det_inv.fresh()

    # 2 · Fenster sortiert aus, was ausserhalb liegt
    det_roi = ArucoDetector(_Still(_tray(spots)), roi=(0.0, 0.0, 0.6, 0.5))
    assert sorted(_settle(det_roi)) == [0, 4], det_roi.fresh()   # 9 liegt draussen

    # 3 · Hysterese haelt kurz und baut dann ab
    still.frame = _tray({})                 # Tablett leer geraeumt
    time.sleep(MARKER_HOLD / 2)
    assert len(_ := det_open.fresh()) == 3, ("Hysterese haelt nicht", _)
    time.sleep(MARKER_HOLD * 2)
    assert det_open.fresh() == {}, "Hysterese baut nicht ab"

    # 4 · Wiederholung beim Halten, ohne GPIO. Zweierpotenzen als Zeiten: sie
    #     sind binaer exakt, sonst bleibt nach 4 x 0,1 von 0,4 ein Rest von
    #     5e-17 stehen und der Test wackelt an der Rundung statt an der Logik.
    class _Pin:
        is_pressed = False
    btn = Buttons.__new__(Buttons)
    btn.delay, btn.rate = 0.5, 0.25
    btn.btns, btn.wait = {"up": _Pin()}, {}
    assert btn.pump(0.125) == []                        # nicht gedrueckt
    btn.btns["up"].is_pressed = True
    assert btn.pump(0.125) == ["up"], "Flanke feuert nicht sofort"
    assert [btn.pump(0.125) for _ in range(3)] == [[], [], []], "feuert zu frueh"
    assert btn.pump(0.125) == ["up"], "Wiederholung setzt nicht ein"   # 0,5 s um
    assert [btn.pump(0.125) for _ in range(2)] == [[], ["up"]], "Rate stimmt nicht"
    # Ein langes Bild holt die faelligen Wiederholungen nach, statt sie zu schlucken
    assert btn.pump(0.75) == ["up"] * 3, "lange Bilder schlucken Wiederholungen"
    btn.btns["up"].is_pressed = False
    assert btn.pump(0.125) == [] and btn.wait == {}, "losgelassen nicht vergessen"

    # 5 · FakeDetector hat dieselbe Schnittstelle
    f = FakeDetector().fresh()
    assert len(f) == 5 and all(len(q) == 4 for q in f.values())

    # 6 · LED-Kodierung: Reihenfolge GRB, MSB zuerst, ein SPI-Byte pro Bit.
    #     Das ist die Stelle, die sich ohne Streifen nicht ansehen laesst.
    enc = led_encode(np.array([[0x80, 0x01, 0x00]]))          # R=0x80 G=0x01 B=0
    assert enc[:len(RESET)] == RESET and len(enc) == len(RESET) + 24
    g, r, b = (enc[len(RESET) + 8 * j:len(RESET) + 8 * j + 8] for j in range(3))
    assert g == bytes([BIT0] * 7 + [BIT1]), "G nicht zuerst oder LSB zuerst"
    assert r == bytes([BIT1] + [BIT0] * 7) and b == bytes([BIT0] * 8)
    # Restzeitbalken: halbe Runde = halber Streifen hell
    fr = led_frame("game", 0.5, 0.0, 100)
    assert (fr[:50] == LED_A).all() and not (fr[50:] == LED_A).all()
    # Ohne Geraet stumm statt Absturz -- so laeuft das Spiel am Mac
    q = Leds(dev="/nonexistent")
    q.show("game", 0.3)
    q.close()
    print("ok")
