from discord import Interaction
from discord.app_commands import Choice

from cogs.bind.manager import BindManager

MAX_OPTIONS = 6


class BindCompleter:
    """Title arguments autocompleters."""

    def __init__(self, manager: BindManager) -> None:
        self.manager = manager

    async def author_complete(self, inter: Interaction, cur: str) -> list[Choice[str]]:
        """Displays only binds created by the user."""
        assert inter.guild

        results = self.manager.many_author(
            inter.user.id, inter.guild.id, cur, MAX_OPTIONS
        )
        out: list[Choice[str]] = [
            Choice(name=item.title.capitalize(), value=item.title) for item in results
        ]

        return out

    async def server_complete(self, inter: Interaction, cur: str) -> list[Choice[str]]:
        """Displays all binds inthe server."""
        assert inter.guild

        results = self.manager.many_server(inter.guild.id, cur, MAX_OPTIONS)
        out: list[Choice[str]] = [
            Choice(name=item.title.capitalize(), value=item.title) for item in results
        ]

        return out
