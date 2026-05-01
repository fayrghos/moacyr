"""Bind-related commands."""

from core.bot import Moacyr

from .commands import BindGroup


async def setup(bot: Moacyr) -> None:
    bot.tree.add_command(BindGroup(bot))
