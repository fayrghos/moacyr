from core.bot import CustomBot

from .commands import BindCog


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(BindCog(bot))
