import sqlite3

import pytest

from service.sqlite_store import SQLiteStore

def test_transaction_commits_on_success(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")

    with store.transaction() as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO items (name) VALUES (?)", ("one",))

    with store.connect() as conn:
        row = conn.execute("SELECT name FROM items WHERE id = 1").fetchone()

    assert row["name"] == "one"


def test_transaction_rolls_back_on_error(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")

    with store.transaction() as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    with pytest.raises(sqlite3.Error):
        with store.transaction() as conn:
            conn.execute("INSERT INTO items (name) VALUES (?)", ("one",))
            conn.execute("INSERT INTO missing_table (name) VALUES (?)", ("bad",))

    with store.connect() as conn:
        rows = conn.execute("SELECT name FROM items").fetchall()

    assert rows == []


def test_connect_enables_foreign_keys(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")

    with store.connect() as conn:
        row = conn.execute("PRAGMA foreign_keys").fetchone()

    assert row[0] == 1