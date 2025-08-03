"""A handler for the database."""

import sqlite3
from contextlib import contextmanager
from os import makedirs, path
from pathlib import Path
from typing import Generator

from src.config import BotConfig


cfg = BotConfig()
cfg.parse_section("General", {
    "dbdir": "data/",
})


DBDIR = Path(cfg.get("General", "dbdir"))

if not path.exists(DBDIR):
    makedirs(DBDIR)


class BaseDB:
    """Represents a generic SQLite database manipulator."""
    db = sqlite3.connect(path.join(DBDIR, "master.db"))

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Creates a cursor for this database."""
        cursor = self.db.cursor()

        try:
            yield cursor

        finally:
            cursor.close()

    def _commit(self) -> None:
        """Updates the database. Should be called after every operation."""
        self.db.commit()
