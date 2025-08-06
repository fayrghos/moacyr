"""A subclass for customizing the bot."""

import asyncio
import random
from typing import NoReturn

import discord
from discord import Interaction
from discord.app_commands import AppCommandError
from discord.ext.commands import (
    Bot,
    CheckFailure,
    CommandError,
    Context,
    ExtensionError,
)

import src.utils as utils
from src.envs import LOG_CHANNEL, LOG_GUILD


ACTIV_TIME = 180


module_list: tuple[str, ...] = (
    "general",
    "dev",
    "bind",
    "steam",
    "image",
    "code",
)

status_list: list[str] = [
    "Train",
    "Vertigo",
    "Ancient",
    "Overpass",
    "Mirage",
    "Inferno",
    "Nuke",
    "Anubis",
    "Dust II",
    "Office",
    "Italy",
    "Pool Day",
    "Bind",
    "Haven",
    "Split",
    "Ascent",
    "Icebox",
    "Breeze",
    "Fracture",
    "Pearl",
    "Lotus",
    "Sunset",
    "Abyss",
]


class CustomBot(Bot):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.activity_index: int = 0
        self.activity_cycletime: int = ACTIV_TIME
        self.activities: list[str] = status_list

        self.tree.error(self.on_slash_error)

    async def on_ready(self) -> None:
        if self.activities:
            self.loop.create_task(self.cycle_activities())

        await self.init_cogs()
        await self.sync_cogs()

        print("Let's roll.")

    async def on_slash_error(self, inter: Interaction, error: AppCommandError) -> None:
        if isinstance(error, CheckFailure):
            return

        # Should always be the last
        elif self.application and self.application.owner.id == inter.user.id and LOG_CHANNEL:
            channel = await self.fetch_channel(int(LOG_CHANNEL))
            if isinstance(channel, discord.TextChannel):
                embed = utils.error_embed(error, title=error.__class__.__name__)
                await channel.send(self.application.owner.mention, embed=embed)

    # Just silencing legacy prefixed commands
    async def on_command_error(self, context: Context, error: CommandError) -> None:
        pass

    async def init_cogs(self) -> None:
        """Initializes all bot commands in the given modules."""
        for module_name in module_list:
            try:
                await self.load_extension("src.cogs." + module_name)

            except ExtensionError as error:
                print(f"Cannot import cog '{module_name}' ({error}).")

    async def sync_cogs(self) -> None:
        """Syncs the slash commands to Discord."""
        await self.tree.sync()
        if LOG_GUILD:
            await self.tree.sync(guild=discord.Object(int(LOG_GUILD)))

    async def cycle_activities(self) -> NoReturn:
        """Toggles between activities periodically."""
        random.shuffle(self.activities)
        while True:
            activity = discord.Game(name=self.activities[self.activity_index])

            await self.change_presence(activity=activity)
            self.activity_index += 1
            if self.activity_index % len(self.activities) == 0:
                random.shuffle(self.activities)
                self.activity_index = 0

            await asyncio.sleep(self.activity_cycletime)
