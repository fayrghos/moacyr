from core.bot import CustomBot

from .commands import BindGroup


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(BindGroup(bot))
