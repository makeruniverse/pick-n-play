import sqlite3

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
        # Add columns retroactively if the table dates from before scoring.
        # ALTER TABLE ADD COLUMN has no IF NOT EXISTS, so this checks against
        # the existing schema instead of catching an error.
        have = {r[1] for r in self.con.execute("PRAGMA table_info(runs)")}
        for col, typ in (("dist", "INT"), ("secs", "REAL")):
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

    def add(self, name, off, goal=None, total=None, dist=None, secs=0.0):
        self.con.execute(
            "INSERT INTO runs (name, off, goal, total, dist, secs) "
            "VALUES (?, ?, ?, ?, ?, ?)", (name, off, goal, total, dist, secs))
        self.con.commit()

    def _scored(self):
        """(name, score) per round, in insertion order.

        Rows without `dist` are from before scoring and have no comparable
        score. They stay in the table -- the CSV for press/PR should be
        complete -- but they don't appear in any leaderboard.
        """
        return [(name, points(off, dist, secs or 0.0)) for name, off, dist, secs
                in self.con.execute("SELECT name, off, dist, secs FROM runs "
                                    "WHERE dist IS NOT NULL ORDER BY rowid")]

    def top(self, n=TOP_N):
        """Best run per name, descending. High is good.

        ponytail: linear scan over all rounds. A show day is a few hundred
        rows; an index is worth it the day the table survives a show day.
        """
        best = {}
        for name, pts in self._scored():
            # Strictly greater, and rows arrive in rowid order: on a tie,
            # the earlier run stays. So on equal scores, whoever got there
            # first stays in front.
            if pts > best.get(name, -1):
                best[name] = pts
        return sorted(best.items(), key=lambda kv: -kv[1])[:n]

    def best(self, name):
        """This name's best score so far, or None. For the callback."""
        pts = [p for n, p in self._scored() if n == name]
        return max(pts) if pts else None

    def attempts(self, name):
        return self.con.execute("SELECT COUNT(*) FROM runs WHERE name = ?",
                                (name,)).fetchone()[0]

    def qualifies(self, pts):
        t = self.top()
        return len(t) < TOP_N or pts > t[-1][1]


if __name__ == "__main__":
    # uv run game/db.py -> ok
    from config import PERFECT_HOLD, ROUND_SECONDS
    span = ROUND_SECONDS - PERFECT_HOLD

    db = DB(":memory:")
    # Three rounds with the same starting distance: then `off` alone orders them.
    for n, off in [("AAA", 30), ("BBB", 5), ("CCC", 12)]:
        db.add(n, off, dist=50)
    assert [r[0] for r in db.top(3)] == ["BBB", "CCC", "AAA"], db.top(3)
    assert db.top(1)[0][1] == points(5, 50), db.top(1)

    # Same name the next day: the better run counts, the old one stays.
    db.add("AAA", 2, goal=180, total=178, dist=50)
    assert db.top(1) == [("AAA", points(2, 50))], db.top(1)
    assert db.attempts("AAA") == 2
    assert db.best("AAA") == points(2, 50) and db.best("ZZZ") is None
    # ... and a worse run doesn't hurt the name.
    db.add("AAA", 49, dist=50)
    assert db.best("AAA") == points(2, 50) and db.attempts("AAA") == 3
    assert len(db.top()) == 3, "exactly one row per name in the list"

    # Tie: whoever got there first stays in front.
    db.add("DDD", 5, dist=50)
    assert [r[0] for r in db.top()][:3] == ["AAA", "BBB", "DDD"], db.top()

    # Time left only decides among perfects -- and there it does decide.
    db.add("FAST", 0, dist=50, secs=span)
    db.add("SLOW", 0, dist=50, secs=0.0)
    assert db.top(1) == [("FAST", 1000)], db.top(1)
    assert db.best("SLOW") < db.best("FAST")

    # Same distance off, larger starting distance -> more points. That's the
    # reason ties are rare: what's scored is the fraction.
    db.add("NAH", 3, dist=30)
    db.add("WEIT", 3, dist=90)
    assert db.best("WEIT") > db.best("NAH")

    assert db.qualifies(1000)                     # list not yet full
    for i in range(TOP_N):
        db.add(f"X{i:02d}", i, dist=50)
    assert not db.qualifies(1), "list full, a row with 1 point drops out"
    assert db.qualifies(1000)

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
    assert m.attempts("OLD") == 2, "rows are there, just not scoreable"
    assert m.best("OLD") is None
    m.add("NEU", 4, dist=40)
    assert [r[0] for r in m.top()] == ["NEU"], m.top()
    m.con.close()
    DB(path).con.close()          # second startup doesn't migrate again
    assert DB(path).attempts("OLD") == 2, "migration ran twice"

    # And a table from before this scoring session gets the columns,
    # without anyone having to add them by hand.
    path2 = os.path.join(tempfile.mkdtemp(), "v2.db")
    con = sqlite3.connect(path2)
    con.execute("CREATE TABLE runs (ts TEXT, name TEXT NOT NULL, off INT NOT NULL,"
                " goal INT, total INT)")
    con.execute("INSERT INTO runs (name, off) VALUES ('ALT', 9)")
    con.commit()
    con.close()
    v = DB(path2)
    assert v.attempts("ALT") == 1 and v.top() == []
    v.add("NEU", 1, dist=50)
    assert v.top() == [("NEU", points(1, 50))], v.top()
    print("ok")
