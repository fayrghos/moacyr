"""A handler for the database."""

from logging import getLogger
from os import makedirs
from os.path import exists
from pathlib import Path

from sqlmodel import create_engine

from core.models.bind import Bind

logger = getLogger(__name__)

DB_PATH = Path("./data/")
if not exists(DB_PATH):
    logger.info(f"Creating a '{DB_PATH}' directory.")
    makedirs(DB_PATH)

dbengine = create_engine(f"sqlite:///{DB_PATH}/main.db")

Bind.metadata.create_all(dbengine)
