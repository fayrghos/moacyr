"""The heart of the bot."""

from logging import WARNING, getLogger

import discord

from core.bot import Moacyr
from core.config import config


def main() -> None:
    discord.utils.setup_logging()
    discord.VoiceClient.warn_nacl = False
    discord.VoiceClient.warn_dave = False
    getLogger("httpx").setLevel(WARNING)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = Moacyr(command_prefix="./", intents=intents, help_command=None)
    bot.run(config.bot_token, log_handler=None)


if __name__ == "__main__":
    main()
