"""Create (or reset) the SQLite sample used to exercise the DB viewer.

    conda run -n myenv python scripts/make_test_db.py
    → data/test_viewer.db
"""

from __future__ import annotations

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_viewer.db")

SCHEMA = """
DROP VIEW IF EXISTS user_totals;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

CREATE TABLE users (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    email   TEXT UNIQUE,
    active  INTEGER NOT NULL DEFAULT 1,
    score   REAL DEFAULT 0
);

CREATE TABLE orders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    item       TEXT NOT NULL,
    amount     REAL NOT NULL,
    status     TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- no explicit PK: exercises the rowid fallback path
CREATE TABLE notes (
    title TEXT,
    body  TEXT,
    tags  TEXT
);

CREATE VIEW user_totals AS
    SELECT u.name, COUNT(o.id) AS orders, COALESCE(SUM(o.amount), 0) AS total
    FROM users u LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id;
"""

USERS = [
    ("Ada Lovelace", "ada@example.com", 1, 91.5),
    ("Grace Hopper", "grace@example.com", 1, 97.0),
    ("Alan Turing", "alan@example.com", 0, 88.25),
    ("Katherine Johnson", "katherine@example.com", 1, 95.75),
]
ORDERS = [
    (1, "Keyboard", 79.99, "paid"),
    (1, "Monitor", 249.0, "paid"),
    (2, "USB hub", 34.5, "shipped"),
    (3, "Notebook", 4.25, "new"),
    (4, "Desk lamp", 42.0, "cancelled"),
]
NOTES = [
    ("Try CRUD", "Double-click a cell to edit it.", "demo,sqlite"),
    ("Rowid table", "notes has no primary key, so edits use rowid.", "demo"),
    ("Blob test", "BLOBs stay read-only in the grid.", "demo"),
]


def main() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO users (name, email, active, score) VALUES (?, ?, ?, ?)", USERS)
        conn.executemany("INSERT INTO orders (user_id, item, amount, status) VALUES (?, ?, ?, ?)", ORDERS)
        conn.executemany("INSERT INTO notes (title, body, tags) VALUES (?, ?, ?)", NOTES)
        conn.execute("UPDATE notes SET body = CAST(body AS BLOB) WHERE title = 'Blob test'")
        conn.commit()
    print(f"created {DB_PATH}")


if __name__ == "__main__":
    main()
