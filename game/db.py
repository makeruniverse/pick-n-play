import sqlite3

from balance import points
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

    Gespeichert wird die *physische Wahrheit* der Runde und nicht die
    Punktzahl: `off` (Abstand zum Ziel am Ende), `dist` (Abstand bei
    Rundenbeginn) und `secs` (Restzeit). Die Punktzahl ist eine Funktion
    dieser drei, sie steht in balance.points(), und sie darf sich aendern,
    ohne dass die Datenbank falsch wird -- eine alte Runde wird dann nach der
    neuen Formel gewertet, was richtiger ist als ein eingefrorener Wert.

    Der Preis dafuer: die Bestenliste laesst sich nicht mehr in SQL sortieren,
    weil die Punktzahl ein Verhaeltnis ist. `top()` liest deshalb alle Zeilen
    und rechnet in Python.
    """

    def __init__(self, path=DB_PATH):
        self.con = sqlite3.connect(path)
        self.con.execute("""CREATE TABLE IF NOT EXISTS runs (
                                ts    TEXT DEFAULT (datetime('now')),
                                name  TEXT NOT NULL,
                                off   INT  NOT NULL,
                                goal  INT,
                                total INT,
                                dist  INT,
                                secs  REAL)""")
        # Spalten nachziehen, falls die Tabelle aus der Zeit vor der Wertung
        # stammt. ALTER TABLE ADD COLUMN kennt kein IF NOT EXISTS, also gegen
        # den vorhandenen Bestand geprueft statt gegen einen Fehler gefangen.
        have = {r[1] for r in self.con.execute("PRAGMA table_info(runs)")}
        for col, typ in (("dist", "INT"), ("secs", "REAL")):
            if col not in have:
                self.con.execute(f"ALTER TABLE runs ADD COLUMN {col} {typ}")
        # Umzug der alten Tabelle, einmalig. Umbenennen statt DROP: es sind nur
        # 16 Testzeilen, aber eine Migration, die Daten wegwirft, will man beim
        # zweiten Mal nicht neu schreiben muessen.
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
        """(name, punkte) je Runde, in Einfuegereihenfolge.

        Zeilen ohne `dist` sind aus der Zeit vor der Wertung und haben keine
        vergleichbare Punktzahl. Sie bleiben in der Tabelle -- die CSV fuer die
        OeA soll vollstaendig sein -- aber sie stehen in keiner Bestenliste.
        """
        return [(name, points(off, dist, secs or 0.0)) for name, off, dist, secs
                in self.con.execute("SELECT name, off, dist, secs FROM runs "
                                    "WHERE dist IS NOT NULL ORDER BY rowid")]

    def top(self, n=TOP_N):
        """Je Name der beste Lauf, absteigend. Hoch ist gut.

        ponytail: linearer Scan ueber alle Runden. Ein Messetag sind ein paar
        hundert Zeilen; ein Index lohnt ab dem Tag, an dem die Tabelle einen
        Messetag ueberlebt.
        """
        best = {}
        for name, pts in self._scored():
            # Strikt groesser, und die Zeilen kommen in rowid-Reihenfolge:
            # bei Gleichstand bleibt der fruehere Lauf stehen. Damit steht bei
            # gleicher Punktzahl vorn, wer sie zuerst geschafft hat.
            if pts > best.get(name, -1):
                best[name] = pts
        return sorted(best.items(), key=lambda kv: -kv[1])[:n]

    def best(self, name):
        """Bisherige Bestpunktzahl dieses Namens, oder None. Fuer die Rueckfrage."""
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
    # Drei Runden mit derselben Startdistanz: dann ordnet allein `off`.
    for n, off in [("AAA", 30), ("BBB", 5), ("CCC", 12)]:
        db.add(n, off, dist=50)
    assert [r[0] for r in db.top(3)] == ["BBB", "CCC", "AAA"], db.top(3)
    assert db.top(1)[0][1] == points(5, 50), db.top(1)

    # Derselbe Name am naechsten Tag: der bessere Lauf zaehlt, der alte bleibt.
    db.add("AAA", 2, goal=180, total=178, dist=50)
    assert db.top(1) == [("AAA", points(2, 50))], db.top(1)
    assert db.attempts("AAA") == 2
    assert db.best("AAA") == points(2, 50) and db.best("ZZZ") is None
    # ... und ein schlechterer Lauf verschlechtert den Namen nicht.
    db.add("AAA", 49, dist=50)
    assert db.best("AAA") == points(2, 50) and db.attempts("AAA") == 3
    assert len(db.top()) == 3, "je Name genau eine Zeile in der Liste"

    # Gleichstand: wer zuerst da war, steht vorn.
    db.add("DDD", 5, dist=50)
    assert [r[0] for r in db.top()][:3] == ["AAA", "BBB", "DDD"], db.top()

    # Die Restzeit entscheidet nur unter Perfekten -- und dort entscheidet sie.
    db.add("FAST", 0, dist=50, secs=span)
    db.add("SLOW", 0, dist=50, secs=0.0)
    assert db.top(1) == [("FAST", 1000)], db.top(1)
    assert db.best("SLOW") < db.best("FAST")

    # Gleicher Abstand, groessere Startdistanz -> mehr Punkte. Das ist der
    # Grund, warum Gleichstaende selten sind: gewertet wird der Anteil.
    db.add("NAH", 3, dist=30)
    db.add("WEIT", 3, dist=90)
    assert db.best("WEIT") > db.best("NAH")

    assert db.qualifies(1000)                     # Liste noch nicht voll
    for i in range(TOP_N):
        db.add(f"X{i:02d}", i, dist=50)
    assert not db.qualifies(1), "Liste voll, eine Zeile mit 1 Punkt faellt raus"
    assert db.qualifies(1000)

    # Migration: eine alte scores-Tabelle wandert vollstaendig mit. Ihre Zeilen
    # haben kein `dist` und damit keine vergleichbare Punktzahl -- sie stehen
    # in der CSV, aber in keiner Bestenliste.
    import os, tempfile
    path = os.path.join(tempfile.mkdtemp(), "old.db")
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE scores (name TEXT, score INT)")
    con.executemany("INSERT INTO scores VALUES (?, ?)", [("OLD", 7), ("OLD", 3)])
    con.commit()
    con.close()
    m = DB(path)
    assert m.top() == [], m.top()
    assert m.attempts("OLD") == 2, "Zeilen sind da, nur nicht wertbar"
    assert m.best("OLD") is None
    m.add("NEU", 4, dist=40)
    assert [r[0] for r in m.top()] == ["NEU"], m.top()
    m.con.close()
    DB(path).con.close()          # zweiter Start migriert nicht noch einmal
    assert DB(path).attempts("OLD") == 2, "Migration lief zweimal"

    # Und eine Tabelle aus der Zeit vor dieser Sitzung bekommt die Spalten,
    # ohne dass jemand sie von Hand nachzieht.
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
