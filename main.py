"""The heart of the bot."""

import discord

from src.bot import CustomBot
from src.envs import BOT_TOKEN


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = CustomBot(command_prefix="./", intents=intents, help_command=None)


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
