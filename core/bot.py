"""The main bot implementation."""

from asyncio import sleep
from logging import getLogger
from os import listdir
from random import shuffle

from discord import Game, Interaction
from discord.app_commands import CheckFailure
from discord.ext.commands import Bot, Context, ExtensionAlreadyLoaded, ExtensionNotFound

from core.utils import Errbed

logger = getLogger(__name__)

ACTIVS: tuple[str, ...] = (
    "Italy",
    "Office",
    "Ancient",
    "Cache",
    "Dust II",
    "Inferno",
    "Mirage",
    "Nuke",
    "Overpass",
    "Train",
    "Vertigo",
)

ACTIVS_TIME = 300


class Moacyr(Bot):
    """The right coolness in the wrong place."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.activs = [Game(name=activ) for activ in ACTIVS]

    async def on_ready(self) -> None:
        await self.load_cogs()
        await self.cycle_ativs()
        logger.info("Wake up and smell the ashes.")

    async def load_cogs(self) -> None:
        """Load and sync all available cogs."""
        cogs: list[str] = [
            item.replace(".py", "")
            for item in listdir("cogs")
            if not item.startswith("_")
        ]

        for cog in cogs:
            try:
                await self.load_extension(f"cogs.{cog}")
            except ExtensionAlreadyLoaded:
                logger.error(f"Multiple cogs named '{cog}' found!")
            except ExtensionNotFound:
                logger.error(f"No cogs named '{cog}' were found!")

        await self.tree.sync()

    async def cycle_ativs(self) -> None:
        """Rotate the bot activities periodically."""
        while True:
            shuffle(self.activs)
            for activ in self.activs:
                await self.change_presence(activity=activ)
                await sleep(ACTIVS_TIME)

    async def on_command_error(self, ctx: Context, err: Exception) -> None:
        """Prefix commands."""

    async def on_slash_command_error(self, inter: Interaction, err: Exception) -> None:
        """Slash commands."""
        if isinstance(err, CheckFailure):
            return

        logger.exception("Unknown Exception.", exc_info=err)
        if not inter.response.is_done():
            await inter.response.send_message(
                embed=Errbed("Ocorreu um erro não catalogado.", crit=True)
            )
