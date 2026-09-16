import sqlite3
from config import DB_PATH, TOP_N

class DB:
    def __init__(self, path=DB_PATH):
        self.con = sqlite3.connect(path)
        self.con.execute("CREATE TABLE IF NOT EXISTS scores (name TEXT, score INT)")
        self.con.commit()

    def top(self, n=TOP_N):
        return self.con.execute(
            "SELECT name, score FROM scores ORDER BY score ASC, rowid ASC LIMIT ?", (n,)
        ).fetchall()

    def qualifies(self, score):
        t = self.top()
        return len(t) < TOP_N or score < t[-1][1]

    def add(self, initials, score):
        self.con.execute("INSERT INTO scores VALUES (?, ?)", (initials, score))
        self.con.commit()


if __name__ == "__main__":
    db = DB(":memory:")
    for n, s in [("AAA", 30), ("BBB", 5), ("CCC", 12)]:
        db.add(n, s)
    assert [r[0] for r in db.top(3)] == ["BBB", "CCC", "AAA"], db.top(3)
    assert db.qualifies(999)                      # List not full
    for i in range(TOP_N):
        db.add("XXX", i)
    assert not db.qualifies(999)                  # now full, 999 faells out
    assert db.qualifies(0)
    print("ok")