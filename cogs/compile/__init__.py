"""Compile command."""

from cogs.compile.manager import CompilerManager
from core.bot import Moacyr

from .commands import CompileCog


async def setup(bot: Moacyr) -> None:
    await bot.add_cog(CompileCog(bot, await CompilerManager.start()))
