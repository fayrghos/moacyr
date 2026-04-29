"""A handler for the database."""

from logging import getLogger
from os import makedirs
from os.path import exists
from pathlib import Path

from sqlmodel import SQLModel, create_engine

from core.config import config
from core.models import bind as bind

logger = getLogger(__name__)

DB_PATH = Path(config.db_path)
if not exists(DB_PATH):
    logger.info(f"Creating a '{DB_PATH}' directory.")
    makedirs(DB_PATH)

dbengine = create_engine(f"sqlite:///{DB_PATH}/main.db")

SQLModel.metadata.create_all(dbengine)
