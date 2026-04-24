"""A handler for the database."""

from contextlib import contextmanager
from os import makedirs, path
from pathlib import Path
from sqlite3 import Connection, Cursor, connect
from typing import Generator

from core.config import config

DB_DIR = Path(config.db_path)
if not path.exists(DB_DIR):
    makedirs(DB_DIR)


@contextmanager
def call_database() -> Generator[tuple[Connection, Cursor], None, None]:
    """Creates a temporary connection for the database."""
    conn = connect(path.join(DB_DIR, "main.db"))
    cursor = conn.cursor()

    try:
        yield conn, cursor

    finally:
        cursor.close()
        conn.close()
