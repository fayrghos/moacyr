"""The Discord interface to the compile command."""

from discord import Interaction
from discord.app_commands import command
from discord.ext.commands import Cog

from cogs.compile.complete import compile_complete
from cogs.compile.manager import CompilerManager
from cogs.compile.modal import CompileModal
from core.bot import Moacyr
from core.utils import Errbed


class CompileCog(Cog):
    def __init__(self, bot: Moacyr, manager: CompilerManager) -> None:
        self.bot = bot
        self.manager = manager
        self.completer = compile_complete(manager)

        self.cm_compile.autocomplete("language")(self.completer)

    @command(name="compile")
    async def cm_compile(self, inter: Interaction, language: str) -> None:
        """Executa código em diversas linguagens de programação.

        Args:
            language: A linguagem a ser executada.
        """
        compilers = self.manager.get_compilers(language)
        if not compilers:
            await inter.response.send_message(
                embed=Errbed(f"Não existe nenhuma linguagem '{language}' cadastrada.")
            )
            return

        await inter.response.send_modal(CompileModal(compilers))
