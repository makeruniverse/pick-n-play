"""Zielwert-Findung: wie weit ist das Ziel von dem entfernt, was schon liegt.

Der Zielwert wird nicht frei gewuerfelt, sondern als Distanz zur tatsaechlichen
Tablettsumme gewaehlt. Das ist der ganze Fairness-Mechanismus: gewuerfelt man
frei, entscheidet der Zufall, ob jemand 3 oder 200 Punkte zu ueberbruecken hat
-- und die Bestenliste vergleicht dann Runden, die nichts miteinander zu tun
haben.

Zwei Bedingungen an die Distanz, beide gegen das *echte* Tablett geprueft:

  1. In GAP_MOVES Zuegen exakt schliessbar. Es gibt also immer eine perfekte
     Loesung, keine Runde ist unmoeglich.
  2. Der beste einzelne Zug landet zwischen GAP_ONE_MISS und GAP_ONE_MAX
     daneben. Die Untergrenze verhindert, dass ein Gluecks-Puck auf null
     fuehrt -- OFF BY 0 kostet mehr als einen Zug. Die Obergrenze verhindert
     das Gegenteil: eine Runde, die nach dem besten Einzelzug noch 67 offen
     laesst, ist in 60 Sekunden praktisch nicht mehr zu holen.

Damit hat jede Runde dieselbe Form, egal in welchem Zustand der Vorgaenger das
Tablett hinterlassen hat.
"""

import random

from config import (VALUES, GAP_MIN, GAP_MAX, GAP_MOVES,
                    GAP_ONE_MISS, GAP_ONE_MAX)


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
    print(f"ok  (ein Zug daneben: median {statistics.median(misses)}, "
          f"max {max(misses)} | in zwei Zuegen loesbar: {sum(perfect)}/200)")
