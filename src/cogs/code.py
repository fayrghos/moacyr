"""Code running commands."""

from dataclasses import dataclass
from textwrap import dedent
from typing import Any

import discord
import httpx
from discord import ButtonStyle, Interaction, TextStyle
from discord.app_commands import Choice, autocomplete, command
from discord.ext.commands import Cog
from discord.ui import Button, Modal, TextInput, View, button

import src.utils as utils
from src.bot import CustomBot


MAX_OUTPUT_WIDTH = 600


def get_compiler_list() -> list[dict[str, Any]]:
    """Gets the list of available compilers from WandBox API."""
    try:
        request = httpx.get("https://wandbox.org/api/list.json", timeout=10)
        response: list[dict[str, Any]] = request.json()

        # Head compilers don't work
        functional_compilers = [
            compiler for compiler in response
            if "head" not in compiler.get("name", "").lower()
        ]
        return functional_compilers

    except Exception as err:
        print(f"Cannot connect to WandBox. ({err})")
        return []


def get_minimal_list() -> list[Choice]:
    """The list used in the empty autocomplete field."""
    min_choice_list: list[Choice] = []
    unique_languages: list[str] = []

    for item in compiler_list:
        if len(min_choice_list) >= utils.MAX_COMPLETE_OPTS:
            break

        language = item.get("language", "???")
        compiler = item.get("name", "")

        if compiler and language not in unique_languages:
            unique_languages.append(language)
            min_choice_list.append(Choice(name=language, value=compiler))
    return min_choice_list


async def compiler_complete(inter: Interaction, current: str) -> list[Choice]:
    """The autocomplete for the code run command."""
    if not current:
        return minimal_compiler_list

    max_choice_list: list[Choice] = []
    for item in compiler_list:
        if len(max_choice_list) >= utils.MAX_COMPLETE_OPTS:
            break

        compiler = item.get("name", "")
        language = item.get("language", "???")
        if current.lower() not in language.lower():
            continue

        if compiler and current.lower() in language.lower():
            max_choice_list.append(Choice(name=f"{language} @ {compiler}", value=compiler))
    return max_choice_list


compiler_list = get_compiler_list()
minimal_compiler_list = get_minimal_list()


@dataclass
class CodeLanguage:
    """Represents a code language supported by Wandbox."""

    display: str
    version: str
    compiler: str


class CodeModal(Modal):
    """Modal used in code eval commands."""

    code_field: TextInput = TextInput(
        label="Código Desejado",
        placeholder="O código a ser compilado e executado.",
        required=True,
        style=TextStyle.paragraph
    )

    stdin_field: TextInput = TextInput(
        label="Entrada de Teclado",
        placeholder="Entradas para input(), scanf(), Scanner() e derivados, separadas por quebras de linha.",
        required=False,
        style=TextStyle.paragraph
    )

    def __init__(self, lang_obj: CodeLanguage) -> None:
        super().__init__(title=f"Executar {lang_obj.display}")
        self.lang_obj = lang_obj

    async def on_submit(self, inter: Interaction) -> None:
        await inter.response.defer(thinking=True)
        code: str = self.code_field.value
        stdin: str = self.stdin_field.value

        async with httpx.AsyncClient() as client:
            response = await client.post("https://wandbox.org/api/compile.json", json={
                "code": code,
                "compiler": self.lang_obj.compiler,
                "stdin": stdin
            })

        if response.status_code == 500:
            await inter.followup.send(embed=utils.err_embed("O servidor não foi capaz de processar esse código."))
            return

        elif response.status_code != 200:
            await inter.followup.send(embed=utils.err_embed("Ocorreu um erro inesperado ao processar esse código."))
            return

        data: dict[str, str] = response.json()
        prog_message: str = data.get("program_message") or data.get("compiler_message") or "<NENHUMA>"
        status: str = data.get("status") or data.get("signal") or "Desconhecido"

        desc = dedent(f"""\
            Status: **{status}**
            Compilador: **{self.lang_obj.compiler}**
            ```{utils.cooler_shorten(prog_message, MAX_OUTPUT_WIDTH)}```
        """)

        embed = discord.Embed(title=f"{self.lang_obj.display}",
                              description=desc,
                              color=utils.COLOR_DEBUG)
        await inter.followup.send(embed=embed, view=DisplayCodeView(inter, self.lang_obj, code))


class DisplayCodeView(View):

    def __init__(self, inter: Interaction, lang: CodeLanguage, code: str) -> None:
        super().__init__(timeout=120)
        self.inter = inter
        self.code = code
        self.lang = lang

    async def on_timeout(self) -> None:
        """Deletes all buttons after the timeout."""
        message = await self.inter.original_response()
        if message:
            await message.edit(view=None)

    @button(label="Ver Código", style=ButtonStyle.secondary)
    async def display_code(self, inter: Interaction, button: Button) -> None:
        await inter.response.send_message(f"```{self.lang.display}\n{self.code}```", ephemeral=True)


class RunCog(Cog):

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

    @command(
        name="code",
    )
    @autocomplete(language=compiler_complete)
    async def runcode(self, inter: Interaction, language: str) -> None:
        """Execute código em diversas linguagens de programação populares.

        Args:
            language: A linguagem desejada. Digite para ver mais linguagens e compiladores.
        """
        requested_lang = language.split(" ")[-1].lower()
        for compiler in compiler_list:
            if requested_lang == compiler.get("name", "").lower():
                compiler = CodeLanguage(
                    compiler.get("language", "???"),
                    compiler.get("version", "???"),
                    requested_lang
                )
                modal = CodeModal(compiler)
                await inter.response.send_modal(modal)
                return

        await inter.response.send_message(embed=utils.err_embed("Nenhum compilador foi encontrado."))


async def setup(bot: CustomBot) -> None:
    await bot.add_cog(RunCog(bot))
