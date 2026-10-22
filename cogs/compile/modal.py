"""The modal used in the compile command."""

from textwrap import dedent
from typing import override

from discord import Embed, Interaction, TextStyle
from discord.ui import Label, Modal, Select, TextInput
from httpx import HTTPStatusError, RequestError, TimeoutException
from pydantic import ValidationError

from cogs.compile.manager import CompilerManager
from core.schemas.compile import Compiler, CompileRequest
from core.utils import COLOR_DEBUG, Errbed, cooler_shorten

MAX_OUTPUT = 600


class CompileModal(Modal):
    code_field = Label(
        text="Código",
        component=TextInput(
            style=TextStyle.long,
            required=True,
        ),
    )

    compiler_field = Label(
        text="Compilador",
        component=Select(placeholder="Automático", required=False),
    )

    stdin_field = Label(
        text="Entrada Padrão",
        description="Conteúdo para input(), scanf() e derivados, separado por linhas.",
        component=TextInput(
            style=TextStyle.long,
            required=False,
        ),
    )

    def __init__(self, compilers: list[Compiler]) -> None:
        self.compilers = compilers
        super().__init__(title=f"Rodar {self.language_name}")

        assert isinstance(self.compiler_field.component, Select)
        self.compiler_field.component.options = [
            compiler.selectify() for compiler in self.compilers
        ]

    @property
    def language_name(self) -> str:
        """Returns the name of the language that is being used."""
        return self.compilers[0].language

    @property
    def compiler_name(self) -> str:
        """Returns the name of the compiler that is being used."""
        assert isinstance(self.compiler_field.component, Select)
        return (
            self.compiler_field.component.values[0]
            if self.compiler_field.component.values
            else self.compilers[0].name
        )

    @override
    async def on_submit(self, inter: Interaction) -> None:
        await inter.response.defer(thinking=True)
        assert isinstance(self.code_field.component, TextInput)
        assert isinstance(self.stdin_field.component, TextInput)

        try:
            response = await CompilerManager.send_compile(
                CompileRequest(
                    compiler=self.compiler_name,
                    code=self.code_field.component.value,
                    stdin=self.stdin_field.component.value,
                )
            )
        except HTTPStatusError:
            await inter.followup.send(
                embed=Errbed("O Wandbox retornou uma resposta inválida.")
            )
            return
        except ValidationError:
            await inter.followup.send(
                embed=Errbed("Não foi possível validar a resposta da compilação.")
            )
            return
        except TimeoutException:
            await inter.followup.send(
                embed=Errbed("O Wandbox demorou muito tempo para responder.")
            )
            return
        except RequestError:
            await inter.followup.send(
                embed=Errbed("Houve um erro desconhecido na conexão com o Wandbox.")
            )
            return

        await inter.followup.send(
            embed=Embed(
                title=self.language_name,
                color=COLOR_DEBUG,
                description=dedent(f"""
                    Saída: **{response.status}**
                    Compilador: **{self.compiler_name}**
                    ```
                    {cooler_shorten(response.output, MAX_OUTPUT)}
                    ```
                """),
            )
        )
