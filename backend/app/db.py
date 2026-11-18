import os, sqlite3
from pathlib import Path
DB_PATH = os.environ.get("EVENTS_DB", str(Path(__file__).resolve().parent.parent / "events.db"))

def conn():
    c = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init():
    c = conn()
    c.executescript((Path(__file__).parent / "schema.sql").read_text())
    for i, r in enumerate(["ADMIN", "ORGANIZER", "STUDENT"], 1):
        c.execute("INSERT OR IGNORE INTO roles(id,name) VALUES(?,?)", (i, r))
    c.close()

def q(c, sql, args=()):
    return [dict(r) for r in c.execute(sql, args).fetchall()]

def q1(c, sql, args=()):
    r = c.execute(sql, args).fetchone()
    return dict(r) if r else None
