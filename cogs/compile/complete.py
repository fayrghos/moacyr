"""Autocomplete handler for the compile commands."""

from collections.abc import Callable, Coroutine

from discord import Interaction
from discord.app_commands import Choice

from cogs.compile.manager import CompilerManager
from core.utils import MAX_COMPLETE_OPTS


def compile_complete(
    manager: CompilerManager,
) -> Callable[[Interaction, str], Coroutine]:
    """Autocomplete function for the compile command."""

    async def inner_complete(inter: Interaction, partial: str) -> list[Choice]:
        """Do these things even have docs?"""
        if not partial:
            return manager.choices[:MAX_COMPLETE_OPTS]

        output: list[Choice] = []
        for choice in manager.choices:
            if len(output) >= MAX_COMPLETE_OPTS:
                break
            if partial.lower() in choice.name.lower():
                output.append(choice)
        return output

    return inner_complete
