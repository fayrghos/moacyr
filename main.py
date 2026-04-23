"""The heart of the bot."""

import discord

from core.bot import CustomBot
from core.envs import BOT_TOKEN


def main() -> None:
    discord.utils.setup_logging()
    discord.VoiceClient.warn_nacl = False
    discord.VoiceClient.warn_dave = False

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = CustomBot(command_prefix="./", intents=intents, help_command=None)
    bot.run(BOT_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
