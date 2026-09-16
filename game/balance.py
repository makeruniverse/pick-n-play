"""Target value finding: how far is the goal from what is already located.

The target value is not freely selected, but as a distance to the actual
A total of pills. This is the whole fairness-mechanism: it is true
free, the chance decides whether someone has 3 or 200 points to overbruecken
-- and the best list then compares rounds that do nothing with each other
have.

Two conditions to the distance, both denounced against the *real* tray:

1. In GAP MOVES enclosures exactly lockable. So there is always a perfect
Loesung, no round is uneasy.
2. The best single train lands between GAP ONE MISS and GAP ONE MAX
next. The lower limit prevents a gluecks puck to zero
fuehrt -- OFF BY 0 costs more than one train. The upper limit prevents
the opposite: a round that still 67 open after the best single move
read, it is practically impossible to get in 60 seconds.

This means that each round has the same shape, no matter what condition of the forerunners
Leave a tray.
"""

import random

from config import (VALUES, GAP_MIN, GAP_MAX, GAP_MOVES,
                    GAP_ONE_MISS, GAP_ONE_MAX)


def _reach(on, moves):
    """All summings available in <= moves Zuegen.

The state space looks great, but for the evaluation only the
Sum -- are therefore stored differences, not documents. A train
is placed or taken away; a pigeon is two goats and faelled by
even out.
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
    """Distance to the target for a tray with the marker IDs `on`.

Signs included: everything is on the tray, only come
negative distances out because  reach then only knows how to remove. The case
therefore regulates itself and does not need a special branch.
"""
    one = _reach(on, 1)
    band = [g for g in _reach(on, GAP_MOVES) if GAP_MIN <= abs(g) <= GAP_MAX]
    ok = [g for g in band
          if GAP_ONE_MISS <= min(abs(g - d) for d in one) <= GAP_ONE_MAX]
    # Fallback to the weaker condition. On the kiosk, an empty selection would
    # raise IndexError mid-round, which is worse than a round that is slightly
    # too easy.
    return random.choice(ok or band or [GAP_MIN])


if __name__ == "__main__":
    # uv run game/balance.py -> ok
    import math
    import statistics

    assert math.gcd(*VALUES.values()) == 1, "common divisor: distance values lock up"

    # 1 · _reach counts correctly: one move from an empty tray is exactly one value
    assert _reach((), 1) == {0} | set(VALUES.values())
    # ... and from a full tablet exactly a value less
    assert _reach(VALUES, 1) == {0} | {-v for v in VALUES.values()}

    # 2. The commitment of the function applies to each tray, not only on average
    rng = random.Random(0)
    misses, perfect = [], []
    for _ in range(200):
        on = frozenset(rng.sample(sorted(VALUES), rng.choice((3, 4, 5, 6, 7))))
        g = gap(on)
        assert GAP_MIN <= abs(g) <= GAP_MAX, g
        # exactly solvable in GAP_MOVES moves
        assert g in _reach(on, GAP_MOVES), (sorted(on), g)
        # but not in a train, and also not in close proximity
        near = min(abs(g - d) for d in _reach(on, 1))
        assert GAP_ONE_MISS <= near <= GAP_ONE_MAX, (sorted(on), g, near)
        misses.append(near)
        perfect.append(min(abs(g - d) for d in _reach(on, 2)) == 0)

    # 3 · Rounds stay close to each other -- that is the point of the exercise.
    #     Without the upper limit, the same test scattered from 2 to 67.
    assert max(misses) - min(misses) <= GAP_ONE_MAX - GAP_ONE_MISS
    print(f"ok  (one move off: median {statistics.median(misses)}, "
          f"max {max(misses)} | solvable in two moves: {sum(perfect)}/200)")
