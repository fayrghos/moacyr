"""Environment variables handling."""

from os import getenv
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", "")
STEAM_KEY = getenv("STEAM_KEY", "")
LOG_GUILD = getenv("LOG_GUILD", "")
LOG_CHANNEL = getenv("LOG_CHANNEL", "")
