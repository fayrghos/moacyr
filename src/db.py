"""A handler for the database."""

import sqlite3
from os import makedirs, path
from pathlib import Path

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
    DB = sqlite3.connect(path.join(DBDIR, "master.db"))

    def get_cursor(self) -> sqlite3.Cursor:
        """Creates a cursor for this database."""
        return self.DB.cursor()

    def _save(self) -> None:
        """Updates the database. Should be called after every operation."""
        self.DB.commit()
