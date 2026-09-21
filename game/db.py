import csv
import sqlite3
import sys

from balance import points
from config import DB_PATH, TOP_N


class DB:
    """One row per round played. The leaderboard is a query on top of that.

    It used to be `scores(name, score)` with one row per entry. That raised
    the question of what happens when the same name comes back: overwrite
    (old run gone), a second row (name listed twice), or a special case for
    it. All three are work.

    With one row per *round*, the question goes away. `top()` groups by name
    and takes the best value -- "the same visitor comes back the next day and
    improves" is then not a special case but the normal case of the query.
    The old run stays, the attempts are all there in full, and press/PR gets
    a CSV on show night with every round in it.

    What's stored is the round's *physical truth*, not the score: `off`
    (distance to the target at the end), `dist` (distance at round start),
    and `secs` (time left). The score is a function of these three, it lives
    in balance.points(), and it's allowed to change without the database
    becoming wrong -- an old round then gets scored by the new formula, which
    is more correct than a frozen value.

    The price for that: the leaderboard can no longer be sorted in SQL,
    because the score is a ratio. `top()` therefore reads all rows and
    computes in Python.

    Since 2026-09-21 a round belongs to a *player number*, not to a name.
    The booth team writes that number into their sign-up form next to the
    email, so after the show `export` joins them. A number, not a hash of
    the name: two MAX are two people. Playing again means typing the number
    in again, and the best round per number counts -- improving is the
    point, a worse second try never costs anything.
    """

    def __init__(self, path=DB_PATH):
        self.con = sqlite3.connect(path)
        # WAL: a pulled plug loses at most the last round, never the file.
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("""CREATE TABLE IF NOT EXISTS runs (
                                ts    TEXT DEFAULT (datetime('now')),
                                name  TEXT NOT NULL,
                                off   INT  NOT NULL,
                                goal  INT,
                                total INT,
                                dist  INT,
                                secs  REAL)""")
        # INTEGER PRIMARY KEY is the rowid: 1, 2, 3 ... -- short enough to
        # read out at the booth and type into a form.
        self.con.execute("""CREATE TABLE IF NOT EXISTS players (
                                id   INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                ts   TEXT DEFAULT (datetime('now')))""")
        # Add columns retroactively if the table is older. ALTER TABLE ADD
        # COLUMN has no IF NOT EXISTS, so this checks the existing schema
        # instead of catching an error. `first`: seconds until the first
        # treat landed -- the number that says whether people fail at the
        # arm or at the puzzle.
        have = {r[1] for r in self.con.execute("PRAGMA table_info(runs)")}
        for col, typ in (("dist", "INT"), ("secs", "REAL"),
                         ("player", "INT"), ("first", "REAL")):
            if col not in have:
                self.con.execute(f"ALTER TABLE runs ADD COLUMN {col} {typ}")
        # Migrate the old table, once. Rename instead of DROP: it's only
        # 16 test rows, but a migration that throws away data isn't one
        # you want to have to rewrite the second time around.
        if self.con.execute("SELECT 1 FROM sqlite_master WHERE name='scores'"
                            ).fetchone():
            self.con.execute("INSERT INTO runs (name, off) "
                             "SELECT name, score FROM scores")
            self.con.execute("ALTER TABLE scores RENAME TO scores_v1")
        self.con.commit()

    def new_player(self, name):
        """Registers a player, returns their number."""
        cur = self.con.execute("INSERT INTO players (name) VALUES (?)", (name,))
        self.con.commit()
        return cur.lastrowid

    def player(self, no):
        """Name for a player number, or None if there is no such player."""
        row = self.con.execute("SELECT name FROM players WHERE id = ?",
                               (no,)).fetchone()
        return row and row[0]

    def add(self, name, off, goal=None, total=None, dist=None, secs=0.0,
            player=None, first=None):
        self.con.execute(
            "INSERT INTO runs (name, off, goal, total, dist, secs, player, first) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, off, goal, total, dist, secs, player, first))
        self.con.commit()

    def _best(self):
        """[(key, name, best score, rounds)], best first.

        The key is the player number; rounds from before player numbers
        group by name, like they always did. Rows without `dist` are from
        before scoring and have no comparable score -- they stay in the
        table, but in no list.

        ponytail: linear scan over all rounds. A show day is a few hundred
        rows; an index is worth it the day the table survives a show day.
        """
        best = {}
        for player, name, off, dist, secs in self.con.execute(
                "SELECT player, name, off, dist, secs FROM runs "
                "WHERE dist IS NOT NULL ORDER BY rowid"):
            key = player if player is not None else name
            pts = points(off, dist, secs or 0.0)
            _, _, top, n = best.get(key, (key, name, -1, 0))
            # Strictly greater, and rows arrive in rowid order: on a tie,
            # the earlier run stays. So whoever got there first stays in front.
            best[key] = (key, name, max(top, pts), n + 1)
        return sorted(best.values(), key=lambda r: -r[2])

    def top(self, n=TOP_N):
        """[(name, best score)] -- one row per player, high is good."""
        return [(name, pts) for _, name, pts, _ in self._best()[:n]]

    def rank(self, player):
        """(place, number of players) for the score screen."""
        rows = self._best()
        place = next((i + 1 for i, r in enumerate(rows) if r[0] == player), len(rows))
        return place, len(rows)

    def export(self, out):
        """One CSV row per player: number, name, best score, rounds played.
        The booth form has the number next to the email -- join on it."""
        w = csv.writer(out)
        w.writerow(("player", "name", "best", "rounds"))
        w.writerows(r for r in self._best() if isinstance(r[0], int))


if __name__ == "__main__" and sys.argv[1:] == ["export"]:
    # After the show, on the Pi:  uv run game/db.py export > players.csv
    DB().export(sys.stdout)
elif __name__ == "__main__":
    # uv run game/db.py -> ok
    import io
    from config import PERFECT_HOLD, ROUND_SECONDS
    span = ROUND_SECONDS - PERFECT_HOLD

    db = DB(":memory:")
    # Three rounds with the same starting distance: then `off` alone orders them.
    for n, off in [("AAA", 30), ("BBB", 5), ("CCC", 12)]:
        db.add(n, off, dist=50)
    assert [r[0] for r in db.top(3)] == ["BBB", "CCC", "AAA"], db.top(3)
    assert db.top(1)[0][1] == points(5, 50), db.top(1)

    # Same name the next day: the better run counts, a worse one doesn't hurt.
    db.add("AAA", 2, goal=180, total=178, dist=50)
    db.add("AAA", 49, dist=50)
    assert db.top(1) == [("AAA", points(2, 50))], db.top(1)
    assert len(db.top()) == 3, "exactly one row per name in the list"

    # Tie: whoever got there first stays in front.
    db.add("DDD", 5, dist=50)
    assert [r[0] for r in db.top()][:3] == ["AAA", "BBB", "DDD"], db.top()

    # Time left only decides among perfects -- and there it does decide.
    db.add("FAST", 0, dist=50, secs=span)
    db.add("SLOW", 0, dist=50, secs=0.0)
    assert db.top(1) == [("FAST", 1000)], db.top(1)

    # Player numbers: two MAX are two people, and the same number playing
    # again keeps its best round.
    p = DB(":memory:")
    a, b = p.new_player("MAX"), p.new_player("MAX")
    assert (a, b) == (1, 2) and p.player(2) == "MAX" and p.player(9) is None
    p.add("MAX", 30, dist=50, player=a, first=12.5)
    p.add("MAX", 10, dist=50, player=b)
    p.add("MAX", 0, dist=50, player=a)          # second try, perfect
    p.add("MAX", 40, dist=50, player=a)         # third try, worse -- doesn't count
    assert p.top() == [("MAX", 900), ("MAX", points(10, 50))], p.top()
    assert p.rank(a) == (1, 2) and p.rank(b) == (2, 2)
    buf = io.StringIO()
    p.export(buf)
    assert buf.getvalue().splitlines() == ["player,name,best,rounds",
                                           "1,MAX,900,3", f"2,MAX,{points(10, 50)},1"]

    # Migration: an old scores table migrates over completely. Its rows
    # have no `dist` and thus no comparable score -- they show up in the
    # CSV, but in no leaderboard.
    import os, tempfile
    path = os.path.join(tempfile.mkdtemp(), "old.db")
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE scores (name TEXT, score INT)")
    con.executemany("INSERT INTO scores VALUES (?, ?)", [("OLD", 7), ("OLD", 3)])
    con.commit()
    con.close()
    m = DB(path)
    assert m.top() == [], m.top()
    m.add("NEU", 4, dist=40)
    assert [r[0] for r in m.top()] == ["NEU"], m.top()
    m.con.close()
    DB(path).con.close()          # second startup doesn't migrate again
    count = lambda d: d.con.execute("SELECT COUNT(*) FROM runs WHERE name='OLD'").fetchone()[0]
    assert count(DB(path)) == 2, "migration ran twice"

    # And a table from before scoring gets all columns, without anyone
    # having to add them by hand.
    path2 = os.path.join(tempfile.mkdtemp(), "v2.db")
    con = sqlite3.connect(path2)
    con.execute("CREATE TABLE runs (ts TEXT, name TEXT NOT NULL, off INT NOT NULL,"
                " goal INT, total INT)")
    con.execute("INSERT INTO runs (name, off) VALUES ('ALT', 9)")
    con.commit()
    con.close()
    v = DB(path2)
    assert v.top() == []
    v.add("NEU", 1, dist=50, player=v.new_player("NEU"))
    assert v.top() == [("NEU", points(1, 50))], v.top()
    print("ok")
