"""A handle for config parsing."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    bot_token: str = Field(...)
    db_path: str = Field(default="./data/")
    steam_key: str | None = Field(default=None)

    model_config = SettingsConfigDict(env_file=".env")


config = Config()
