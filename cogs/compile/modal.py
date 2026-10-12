"""The modal used in the compile command."""

from textwrap import dedent
from typing import override

from discord import Embed, Interaction, TextStyle
from discord.ui import Label, Modal, TextInput
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

    stdin_field = Label(
        text="Entrada Padrão",
        description="Conteúdo para input(), scanf() e derivados, separado por linhas.",
        component=TextInput(
            style=TextStyle.long,
            required=False,
        ),
    )

    def __init__(self, compiler: Compiler) -> None:
        super().__init__(title=f"Rodar {compiler.language}")
        self.compiler = compiler

    @override
    async def on_submit(self, inter: Interaction) -> None:
        await inter.response.defer(thinking=True)
        assert isinstance(self.code_field.component, TextInput)
        assert isinstance(self.stdin_field.component, TextInput)

        try:
            response = await CompilerManager.send_compile(
                CompileRequest(
                    compiler=self.compiler.name,
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
                embed=Errbed("Não foi possível validar as entradas da compilação.")
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
                title=self.compiler.language,
                color=COLOR_DEBUG,
                description=dedent(f"""
                    Saída: **{response.status}**
                    Compilador: **{self.compiler.name}**
                    ```
                    {cooler_shorten(response.output, MAX_OUTPUT)}
                    ```
                """),
            )
        )
