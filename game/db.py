import sqlite3
from config import DB_PATH, TOP_N


class DB:
    """Eine Zeile je gespielter Runde. Die Bestenliste ist eine Abfrage darauf.

    Vorher stand hier `scores(name, score)` und je Eintrag eine Zeile. Damit gab
    es die Frage, was passiert, wenn derselbe Name wiederkommt: ueberschreiben
    (alter Lauf weg), zweite Zeile (Name doppelt in der Liste) oder eine
    Sonderlogik dafuer. Alle drei sind Arbeit.

    Mit einer Zeile je *Runde* faellt die Frage weg. `top()` gruppiert nach
    Name und nimmt den besten Wert -- „derselbe Besucher kommt am naechsten Tag
    wieder und verbessert sich" ist dann kein Sonderfall, sondern der
    Normalfall der Abfrage. Der alte Lauf bleibt stehen, die Versuche sind
    vollstaendig da, und die ÖA bekommt am Messeabend eine CSV, in der jede
    Runde steht.

    Gespeichert wird `off` -- der Abstand zum Ziel, 0 ist perfekt. Das ist die
    physische Wahrheit der Runde. Was auf dem Schirm als Punktzahl steht, ist
    eine monotone Umrechnung davon; sie darf sich aendern, ohne dass die
    Datenbank falsch wird, und `ORDER BY off ASC` bleibt in jedem Fall richtig.
    """

    def __init__(self, path=DB_PATH):
        self.con = sqlite3.connect(path)
        self.con.execute("""CREATE TABLE IF NOT EXISTS runs (
                                ts    TEXT DEFAULT (datetime('now')),
                                name  TEXT NOT NULL,
                                off   INT  NOT NULL,
                                goal  INT,
                                total INT)""")
        # Umzug der alten Tabelle, einmalig. Umbenennen statt DROP: es sind nur
        # 16 Testzeilen, aber eine Migration, die Daten wegwirft, will man beim
        # zweiten Mal nicht neu schreiben muessen.
        if self.con.execute("SELECT 1 FROM sqlite_master WHERE name='scores'"
                            ).fetchone():
            self.con.execute("INSERT INTO runs (name, off) "
                             "SELECT name, score FROM scores")
            self.con.execute("ALTER TABLE scores RENAME TO scores_v1")
        self.con.commit()

    def add(self, name, off, goal=None, total=None):
        self.con.execute("INSERT INTO runs (name, off, goal, total) "
                         "VALUES (?, ?, ?, ?)", (name, off, goal, total))
        self.con.commit()

    def top(self, n=TOP_N):
        # MIN() macht die uebrigen Spalten zu „bare columns": SQLite nimmt sie
        # dann aus genau der Zeile, die das Minimum geliefert hat. Deshalb ist
        # rowid hier der Zeitpunkt des *besten* Laufs und taugt als Tiebreak --
        # bei Gleichstand steht vorn, wer ihn zuerst geschafft hat.
        return self.con.execute(
            "SELECT name, MIN(off) AS best FROM runs GROUP BY name "
            "ORDER BY best ASC, rowid ASC LIMIT ?", (n,)
        ).fetchall()

    def best(self, name):
        """Bisheriger Bestwert dieses Namens, oder None. Fuer die Rueckfrage."""
        row = self.con.execute("SELECT MIN(off) FROM runs WHERE name = ?",
                               (name,)).fetchone()
        return row[0]

    def attempts(self, name):
        return self.con.execute("SELECT COUNT(*) FROM runs WHERE name = ?",
                                (name,)).fetchone()[0]

    def qualifies(self, off):
        t = self.top()
        return len(t) < TOP_N or off < t[-1][1]


if __name__ == "__main__":
    db = DB(":memory:")
    for n, s in [("AAA", 30), ("BBB", 5), ("CCC", 12)]:
        db.add(n, s)
    assert [r[0] for r in db.top(3)] == ["BBB", "CCC", "AAA"], db.top(3)

    # Derselbe Name am naechsten Tag: der bessere Lauf zaehlt, der alte bleibt.
    db.add("AAA", 2, goal=180, total=178)
    assert db.top(1) == [("AAA", 2)], db.top(1)
    assert db.attempts("AAA") == 2
    assert db.best("AAA") == 2 and db.best("ZZZ") is None
    # ... und ein schlechterer Lauf verschlechtert den Namen nicht.
    db.add("AAA", 99)
    assert db.best("AAA") == 2 and db.attempts("AAA") == 3
    assert len(db.top()) == 3, "je Name genau eine Zeile in der Liste"

    # Gleichstand: wer zuerst da war, steht vorn.
    db.add("DDD", 5)
    assert [r[0] for r in db.top()][:3] == ["AAA", "BBB", "DDD"], db.top()

    assert db.qualifies(999)                      # Liste noch nicht voll
    for i in range(TOP_N):
        db.add(f"X{i:02d}", i)
    assert not db.qualifies(999)                  # jetzt voll, 999 faellt raus
    assert db.qualifies(0)

    # Migration: eine alte scores-Tabelle wandert vollstaendig mit.
    import os, tempfile
    path = os.path.join(tempfile.mkdtemp(), "old.db")
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE scores (name TEXT, score INT)")
    con.executemany("INSERT INTO scores VALUES (?, ?)", [("OLD", 7), ("OLD", 3)])
    con.commit()
    con.close()
    m = DB(path)
    assert m.top() == [("OLD", 3)], m.top()
    assert m.attempts("OLD") == 2
    m.con.close()
    DB(path).con.close()          # zweiter Start migriert nicht noch einmal
    assert DB(path).attempts("OLD") == 2, "Migration lief zweimal"
    print("ok")
