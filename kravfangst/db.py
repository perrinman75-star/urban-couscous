import json
import sqlite3
from datetime import datetime

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS arende (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT NOT NULL,
    tjanst TEXT,
    data TEXT NOT NULL DEFAULT '{}',
    skapad TEXT NOT NULL,
    uppdaterad TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS strategiskt_mal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    namn TEXT NOT NULL,
    vikt REAL NOT NULL
);
"""

DEFAULT_GOALS = [("Strategiskt mål 1", 40), ("Strategiskt mål 2", 35), ("Strategiskt mål 3", 25)]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM strategiskt_mal").fetchone()[0] == 0:
        db.executemany("INSERT INTO strategiskt_mal (namn, vikt) VALUES (?, ?)", DEFAULT_GOALS)
    db.commit()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _case(row):
    if row is None:
        return None
    return {"id": row["id"], "titel": row["titel"], "tjanst": row["tjanst"],
            "data": json.loads(row["data"]), "skapad": row["skapad"],
            "uppdaterad": row["uppdaterad"]}


def list_cases():
    rows = get_db().execute("SELECT * FROM arende ORDER BY uppdaterad DESC").fetchall()
    return [_case(r) for r in rows]


def get_case(case_id):
    return _case(get_db().execute("SELECT * FROM arende WHERE id = ?", (case_id,)).fetchone())


def create_case(data):
    db = get_db()
    now = _now()
    cur = db.execute(
        "INSERT INTO arende (titel, data, skapad, uppdaterad) VALUES (?, ?, ?, ?)",
        (data.get("titel", ""), json.dumps(data, ensure_ascii=False), now, now))
    db.commit()
    return cur.lastrowid


def save_case(case_id, data, service):
    db = get_db()
    db.execute(
        "UPDATE arende SET titel = ?, tjanst = ?, data = ?, uppdaterad = ? WHERE id = ?",
        (data.get("titel", ""), service, json.dumps(data, ensure_ascii=False), _now(), case_id))
    db.commit()


def delete_case(case_id):
    db = get_db()
    db.execute("DELETE FROM arende WHERE id = ?", (case_id,))
    db.commit()


def list_goals():
    rows = get_db().execute("SELECT * FROM strategiskt_mal ORDER BY id").fetchall()
    return [{"id": r["id"], "name": r["namn"], "weight": r["vikt"]} for r in rows]


def save_goals(goals):
    """Ersätter målen. goals: lista av dict med id (eller None), name, weight."""
    db = get_db()
    keep = [g_["id"] for g_ in goals if g_.get("id")]
    placeholders = ",".join("?" * len(keep)) or "NULL"
    db.execute(f"DELETE FROM strategiskt_mal WHERE id NOT IN ({placeholders})", keep)
    for goal in goals:
        if goal.get("id"):
            db.execute("UPDATE strategiskt_mal SET namn = ?, vikt = ? WHERE id = ?",
                       (goal["name"], goal["weight"], goal["id"]))
        else:
            db.execute("INSERT INTO strategiskt_mal (namn, vikt) VALUES (?, ?)",
                       (goal["name"], goal["weight"]))
    db.commit()
