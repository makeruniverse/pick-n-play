"""Target-value finding and scoring.

The target value isn't rolled freely, but chosen as a distance from what's
actually on the tray at round start. That's the whole fairness mechanism: if
it were rolled freely, chance would decide whether someone has to bridge
0.30 EUR or 20 EUR -- and the leaderboard would then be comparing rounds that
have nothing to do with each other.

At the machine the tray is cleared after every round, so the start is empty
and only placing is possible. The function knows nothing about that: it reads
the tray, and the empty case falls out on its own as a special case (from an
empty set, _reach can only add). If a cupcake is left over because someone
was sloppy clearing up, the round is still correct -- that's why the real
tray is read here instead of a constant.

Price of emptiness: the start state is the same every round, so the set of
permissible targets is also the same every round. How large it is depends
almost entirely on GAP_ONE_MAX -- the self-test below prints the number.

Two conditions on the distance, both checked against the *real* tray:

  1. Exactly closeable in GAP_MOVES moves. So there's always a perfect
     solution, no round is impossible.
  2. The best single move lands between GAP_ONE_MISS and GAP_ONE_MAX off.
     The lower bound prevents a lucky grab from landing on zero -- perfect
     costs more than one move. The upper bound prevents the opposite: a
     round that still leaves 6.70 EUR open after the best single move can no
     longer be closed within the round time.

That gives every round the same shape, regardless of what state the tray is
in at the start.
"""

import random

from config import (VALUES, GAP_MIN, GAP_MAX, GAP_MOVES,
                    GAP_ONE_MISS, GAP_ONE_MAX, ROUND_SECONDS, PERFECT_HOLD,
                    SCORE_MAX, SCORE_TIME, SCORE_CURVE)


def _reach(on, moves):
    """All sum changes reachable in <= moves moves.

    The state space looks big, but only the sum matters for scoring --
    so differences are stored, not placements. One move is placing or
    removing; a swap is two moves and falls out on its own.
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


def gap(on, up=False):
    """Distance to the target for a tray with the marker IDs `on`.

    Sign included: if everything is already on the tray, only negative
    distances come out, because _reach then only knows removal. So that case
    resolves on its own and needs no special branch.

    `up=True`: only targets above what's on the tray. The story has a guest
    with a budget, and after the practice treat a negative gap could make
    that budget EUR 0.00 -- a line nobody should have to read out.
    """
    one = _reach(on, 1)
    band = [g for g in _reach(on, GAP_MOVES)
            if GAP_MIN <= abs(g) <= GAP_MAX and (g > 0 or not up)]
    ok = [g for g in band
          if GAP_ONE_MISS <= min(abs(g - d) for d in one) <= GAP_ONE_MAX]
    # ponytail: fall back to the weaker condition. At the machine this runs
    # unsupervised -- an empty selection would be an IndexError mid-round,
    # and that's more expensive than a round that's one move too easy.
    return random.choice(ok or band or [GAP_MIN])


def points(off, distance, left=0.0):
    """Score 0..1000 from distance, starting distance, and time left.

    Two parts, like a boxing machine -- a number that goes up to 1000, and
    nobody sees the 1000:

        Accuracy  SCORE_MAX  * (1 - off/distance) ** SCORE_CURVE
        Time      SCORE_TIME * left / (ROUND_SECONDS - PERFECT_HOLD)

    Scored is the *fraction* of the closed distance, not the absolute error.
    An absolute scale would need a constant ("this many points per 10 cents")
    that has to be re-guessed on every price change; the fraction needs none
    and works in any unit. Side effect that solves the leaderboard's tie
    problem almost by itself: two players, both 0.30 EUR off, get different
    scores at different starting distances -- exact ties become rare without
    anything being built for that.

    The time bonus is only available for perfects, and without a special
    branch: the round only ends early via PERFECT_HOLD, so left > 0 is
    equivalent to off == 0. Someone who's 0.30 EUR off and thinks instead of
    rushing loses nothing for it -- and that matters, because the skill of
    this game is estimating, not fine motor control.

    SCORE_CURVE is purely cosmetic and doesn't change the ordering: linear
    crowds all players into the top third of the scale, squared spreads out
    exactly the range where they actually land.
    """
    # distance == 0 can't occur (GAP_MIN >= 25), but a ZeroDivision mid-round
    # would be the most expensive conceivable bug on show day.
    closed = max(0.0, 1 - off / distance) if distance else 0.0
    span = ROUND_SECONDS - PERFECT_HOLD
    bonus = SCORE_TIME * min(max(left, 0.0), span) / span if span > 0 else 0.0
    return round(SCORE_MAX * closed ** SCORE_CURVE + bonus)


if __name__ == "__main__":
    # uv run game/balance.py -> ok
    import math
    import statistics

    assert math.gcd(*VALUES.values()) == 1, "common divisor: distances would snap to a grid"

    # 1 · _reach counts correctly: one move from an empty tray is exactly one value
    assert _reach((), 1) == {0} | set(VALUES.values())
    # ... and from a full tray exactly one value less
    assert _reach(VALUES, 1) == {0} | {-v for v in VALUES.values()}

    # 2 · The function's guarantee holds for every tray, not just on average
    rng = random.Random(0)
    misses, perfect = [], []
    for _ in range(200):
        on = frozenset(rng.sample(sorted(VALUES), rng.choice((3, 4, 5, 6, 7))))
        g = gap(on)
        assert GAP_MIN <= abs(g) <= GAP_MAX, g
        # exactly solvable in GAP_MOVES moves
        assert g in _reach(on, GAP_MOVES), (sorted(on), g)
        # but not in one move, and not close either
        near = min(abs(g - d) for d in _reach(on, 1))
        assert GAP_ONE_MISS <= near <= GAP_ONE_MAX, (sorted(on), g, near)
        misses.append(near)
        perfect.append(min(abs(g - d) for d in _reach(on, 2)) == 0)

    # 3 · Rounds sit close together -- that's the whole point of this exercise.
    #     Without the upper bound, this same test spread from 2 to 67.
    assert max(misses) - min(misses) <= GAP_ONE_MAX - GAP_ONE_MISS

    # 4 · The normal case at the machine: empty tray. The start state is
    #     the same every round, so the target set is finite and countable --
    #     and its size is the variety the booth shows all day.
    one = _reach((), 1)
    goals = sorted(g for g in _reach((), GAP_MOVES)
                   if GAP_MIN <= abs(g) <= GAP_MAX
                   and GAP_ONE_MISS <= min(abs(g - d) for d in one) <= GAP_ONE_MAX)
    assert goals, "no target left over for the empty tray"
    assert all(gap(()) in goals for _ in range(50))
    # After the practice treat: any single piece on the tray still leaves
    # a target above it, so the guest's budget is never smaller than the tray.
    assert all(gap({i}, up=True) > 0 for i in VALUES for _ in range(20))
    # With fewer than ten different targets, the booth's state repeats too visibly.
    # The knob for that is GAP_ONE_MAX, see config.py.
    assert len(goals) >= 10, len(goals)

    # 5 · Scoring. Order and bounds, not the curve itself.
    span = ROUND_SECONDS - PERFECT_HOLD
    assert points(0, 50, span) == SCORE_MAX + SCORE_TIME == 1000
    assert points(0, 50) == SCORE_MAX          # perfect in the last second
    assert points(50, 50) == 0                 # nothing moved -> off == distance
    assert points(99, 50) == 0                 # worse than nothing, not negative
    # monotonic: closer is never worth less
    reihe = [points(o, 50) for o in range(0, 51)]
    assert reihe == sorted(reihe, reverse=True)
    # Time never beats accuracy -- can't, because left > 0 only occurs at
    # off == 0, but the scale shouldn't allow it even arithmetically.
    assert points(1, 50, span) < points(0, 50, 0.0) + SCORE_TIME

    print(f"ok  (one move off: median {statistics.median(misses)}, "
          f"max {max(misses)} | solvable in two moves: {sum(perfect)}/200 | "
          f"empty tray: {len(goals)} possible targets)")
