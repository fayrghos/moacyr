"""A handler for the database."""

from contextlib import contextmanager
from os import makedirs, path
from pathlib import Path
from sqlite3 import Connection, Cursor, connect
from typing import Generator

from src.config import BotConfig


cfg = BotConfig()
cfg.parse_section("General", {
    "dbdir": "data/",
})


DBDIR = Path(cfg.get("General", "dbdir"))

if not path.exists(DBDIR):
    makedirs(DBDIR)


@contextmanager
def call_database() -> Generator[tuple[Connection, Cursor], None, None]:
    """Creates a temporary connection for the database."""
    conn = connect(path.join(DBDIR, "master.db"))
    cursor = conn.cursor()

    try:
        yield conn, cursor

    finally:
        cursor.close()
        conn.close()
