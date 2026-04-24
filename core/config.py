"""A handle for config parsing."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    bot_token: str = Field(...)
    db_path: str = Field(default="./data/")

    steam_key: Optional[str] = Field(default=None)
    log_guild: Optional[int] = Field(default=None)
    log_channel: Optional[int] = Field(default=None)

    model_config = SettingsConfigDict(env_file=".env")


config = Config()
