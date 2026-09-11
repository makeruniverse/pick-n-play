"""Zielwert-Findung und Wertung.

Der Zielwert wird nicht frei gewuerfelt, sondern als Distanz zu dem gewaehlt,
was bei Rundenstart tatsaechlich auf dem Tablett liegt. Das ist der ganze
Fairness-Mechanismus: wuerfelt man frei, entscheidet der Zufall, ob jemand
0,30 EUR oder 20 EUR zu ueberbruecken hat -- und die Bestenliste vergleicht
dann Runden, die nichts miteinander zu tun haben.

Am Automaten wird das Tablett nach jeder Runde geleert, der Start ist also
leer und nur Auflegen moeglich. Die Funktion weiss davon nichts: sie liest das
Tablett, und der leere Fall faellt als Sonderfall von selbst heraus (aus einer
leeren Menge kann _reach nur hinzufuegen). Bleibt ein Cupcake liegen, weil
jemand beim Raeumen geschlampt hat, stimmt die Runde trotzdem -- das ist der
Grund, warum hier das echte Tablett gelesen wird und keine Konstante steht.

Preis der Leere: der Startzustand ist jede Runde derselbe, also ist auch die
Menge zulaessiger Ziele jede Runde dieselbe. Wie gross sie ist, haengt fast
allein an GAP_ONE_MAX -- der Selbsttest unten gibt die Zahl aus.

Zwei Bedingungen an die Distanz, beide gegen das *echte* Tablett geprueft:

  1. In GAP_MOVES Zuegen exakt schliessbar. Es gibt also immer eine perfekte
     Loesung, keine Runde ist unmoeglich.
  2. Der beste einzelne Zug landet zwischen GAP_ONE_MISS und GAP_ONE_MAX
     daneben. Die Untergrenze verhindert, dass ein Gluecksgriff auf null
     fuehrt -- perfekt kostet mehr als einen Zug. Die Obergrenze verhindert
     das Gegenteil: eine Runde, die nach dem besten Einzelzug noch 6,70 EUR
     offen laesst, ist in der Rundenzeit nicht mehr zu holen.

Damit hat jede Runde dieselbe Form, egal in welchem Zustand das Tablett beim
Start ist.
"""

import random

from config import (VALUES, GAP_MIN, GAP_MAX, GAP_MOVES,
                    GAP_ONE_MISS, GAP_ONE_MAX, ROUND_SECONDS, PERFECT_HOLD,
                    SCORE_MAX, SCORE_TIME, SCORE_CURVE)


def _reach(on, moves):
    """Alle Summenaenderungen, die in <= moves Zuegen erreichbar sind.

    Der Zustandsraum sieht gross aus, aber fuer die Wertung zaehlt nur die
    Summe -- gespeichert werden deshalb Differenzen, nicht Belegungen. Ein Zug
    ist auflegen oder wegnehmen; ein Tausch ist zwei Zuege und faellt von
    selbst mit heraus.
    """
    on = frozenset(on)
    states, seen = {(on, frozenset(VALUES) - on): 0}, {0}
    for _ in range(moves):
        nxt = {}
        for (o, f), d in states.items():
            for i in f:
                nxt[(o | {i}, f - {i})] = d + VALUES[i]
            for i in o:
                nxt[(o - {i}, f | {i})] = d - VALUES[i]
        states = nxt
        seen |= set(states.values())
    return seen


def gap(on):
    """Distanz zum Ziel fuer ein Tablett mit den Marker-IDs `on`.

    Vorzeichen inklusive: liegt schon alles auf dem Tablett, kommen nur noch
    negative Distanzen heraus, weil _reach dann nur Wegnehmen kennt. Der Fall
    regelt sich also von selbst und braucht keinen Sonderzweig.
    """
    one = _reach(on, 1)
    band = [g for g in _reach(on, GAP_MOVES) if GAP_MIN <= abs(g) <= GAP_MAX]
    ok = [g for g in band
          if GAP_ONE_MISS <= min(abs(g - d) for d in one) <= GAP_ONE_MAX]
    # ponytail: Rueckfall auf die schwaechere Bedingung. Am Automaten laeuft das
    # ohne Aufsicht -- eine leere Auswahl waere ein IndexError mitten in der
    # Runde, und das ist teurer als eine Runde, die einen Zug zu leicht ist.
    return random.choice(ok or band or [GAP_MIN])


def points(off, distance, left=0.0):
    """Punktzahl 0..1000 aus Abstand, Startdistanz und Restzeit.

    Zwei Teile, wie bei einer Boxmaschine -- eine Zahl, die bis 1000 geht, und
    die 1000 sieht niemand:

        Genauigkeit  SCORE_MAX  * (1 - off/distance) ** SCORE_CURVE
        Zeit         SCORE_TIME * left / (ROUND_SECONDS - PERFECT_HOLD)

    Gewertet wird der *Anteil* der geschlossenen Distanz und nicht der absolute
    Fehler. Eine absolute Skala braeuchte eine Konstante ("so viele Punkte je
    10 Cent"), die bei jeder Preisaenderung neu geraten werden muss; der Anteil
    braucht keine und funktioniert in jeder Einheit. Nebenwirkung, die das
    Gleichstandsproblem der Bestenliste fast alleine loest: zwei Spieler, beide
    0,30 EUR daneben, bekommen bei verschiedener Startdistanz verschiedene
    Punkte -- exakte Gleichstaende werden selten, ohne dass dafuer etwas
    gebaut wird.

    Der Zeitbonus ist nur fuer Perfekte zu holen, und zwar ohne Sonderzweig:
    die Runde endet vorzeitig ausschliesslich ueber PERFECT_HOLD, also ist
    left > 0 gleichbedeutend mit off == 0. Wer 0,30 EUR daneben liegt und
    nachdenkt statt zu hetzen, verliert dadurch nichts -- und das ist wichtig,
    weil der Skill des Spiels das Schaetzen ist und nicht die Feinmotorik.

    SCORE_CURVE ist reine Optik und aendert die Reihenfolge nicht: linear
    draengt alle Spieler in das obere Drittel der Skala, quadriert spreizt
    genau den Bereich, in dem sie tatsaechlich landen.
    """
    # distance == 0 kann nicht vorkommen (GAP_MIN >= 25), aber ein ZeroDivision
    # mitten in der Runde waere am Messetag der teuerste denkbare Fehler.
    closed = max(0.0, 1 - off / distance) if distance else 0.0
    span = ROUND_SECONDS - PERFECT_HOLD
    bonus = SCORE_TIME * min(max(left, 0.0), span) / span if span > 0 else 0.0
    return round(SCORE_MAX * closed ** SCORE_CURVE + bonus)


if __name__ == "__main__":
    # uv run game/balance.py -> ok
    import math
    import statistics

    assert math.gcd(*VALUES.values()) == 1, "gemeinsamer Teiler: Distanzen rasten ein"

    # 1 · _reach zaehlt richtig: ein Zug von einem leeren Tablett ist genau ein Wert
    assert _reach((), 1) == {0} | set(VALUES.values())
    # ... und von einem vollen Tablett genau ein Wert weniger
    assert _reach(VALUES, 1) == {0} | {-v for v in VALUES.values()}

    # 2 · Die Zusage der Funktion gilt fuer jedes Tablett, nicht nur im Mittel
    rng = random.Random(0)
    misses, perfect = [], []
    for _ in range(200):
        on = frozenset(rng.sample(sorted(VALUES), rng.choice((3, 4, 5, 6, 7))))
        g = gap(on)
        assert GAP_MIN <= abs(g) <= GAP_MAX, g
        # in GAP_MOVES Zuegen exakt loesbar
        assert g in _reach(on, GAP_MOVES), (sorted(on), g)
        # aber in einem Zug nicht, und auch nicht knapp daneben
        near = min(abs(g - d) for d in _reach(on, 1))
        assert GAP_ONE_MISS <= near <= GAP_ONE_MAX, (sorted(on), g, near)
        misses.append(near)
        perfect.append(min(abs(g - d) for d in _reach(on, 2)) == 0)

    # 3 · Die Runden liegen eng beieinander -- das ist der Sinn der Uebung.
    #     Ohne die Obergrenze streute derselbe Test von 2 bis 67.
    assert max(misses) - min(misses) <= GAP_ONE_MAX - GAP_ONE_MISS

    # 4 · Der Normalfall am Automaten: leeres Tablett. Der Startzustand ist
    #     jede Runde derselbe, also ist die Zielmenge endlich und zaehlbar --
    #     und ihre Groesse ist die Vielfalt, die der Stand den ganzen Tag zeigt.
    one = _reach((), 1)
    goals = sorted(g for g in _reach((), GAP_MOVES)
                   if GAP_MIN <= abs(g) <= GAP_MAX
                   and GAP_ONE_MISS <= min(abs(g - d) for d in one) <= GAP_ONE_MAX)
    assert goals, "am leeren Tablett bleibt kein Ziel uebrig"
    assert all(gap(()) in goals for _ in range(50))
    # Unter zehn verschiedenen Zielen wiederholt sich der Stand zu sichtbar.
    # Der Regler dafuer ist GAP_ONE_MAX, siehe config.py.
    assert len(goals) >= 10, len(goals)

    # 5 · Die Wertung. Reihenfolge und Grenzen, nicht die Kurve selbst.
    span = ROUND_SECONDS - PERFECT_HOLD
    assert points(0, 50, span) == SCORE_MAX + SCORE_TIME == 1000
    assert points(0, 50) == SCORE_MAX          # perfekt in letzter Sekunde
    assert points(50, 50) == 0                 # nichts bewegt -> off == distance
    assert points(99, 50) == 0                 # schlimmer als nichts, nicht negativ
    # monoton: naeher dran ist nie weniger wert
    reihe = [points(o, 50) for o in range(0, 51)]
    assert reihe == sorted(reihe, reverse=True)
    # Zeit schlaegt Genauigkeit nicht -- kann gar nicht, weil left > 0 nur bei
    # off == 0 vorkommt, aber die Skala soll es auch rechnerisch nicht hergeben.
    assert points(1, 50, span) < points(0, 50, 0.0) + SCORE_TIME

    print(f"ok  (ein Zug daneben: median {statistics.median(misses)}, "
          f"max {max(misses)} | in zwei Zuegen loesbar: {sum(perfect)}/200 | "
          f"leeres Tablett: {len(goals)} moegliche Ziele)")
