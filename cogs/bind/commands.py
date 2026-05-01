from discord import AllowedMentions, Embed, Interaction, TextStyle
from discord.app_commands import Group, allowed_contexts, autocomplete, command
from discord.ui import Label, Modal, TextInput

from cogs.bind.complete import BindCompleter
from cogs.bind.manager import BindManager
from cogs.bind.validator import BindError, BindValidator
from core.bot import CustomBot
from core.models.bind import Bind
from core.utils import COLOR_DEF

manager = BindManager()
validator = BindValidator(manager)
completer = BindCompleter(manager)

TEXT_MAX = 1000


class BindAddModal(Modal):
    """Bind insertion modal."""

    text_row = Label(
        text="Texto",
        component=TextInput(
            max_length=TEXT_MAX,
            placeholder="Se hoje eu sou estrela, amanhã já se apagou...",
            style=TextStyle.long,
        ),
    )

    def __init__(self, title: str) -> None:
        super().__init__(title="Adicionar Bind")
        self.btitle = title

    async def on_submit(self, inter: Interaction) -> None:
        assert isinstance(self.text_row.component, TextInput)
        assert inter.guild

        text = validator.purge_text(self.text_row.component.value)
        bind = Bind(
            title=self.btitle,
            text=text,
            author=inter.user.id,
            guild=inter.guild.id,
        )
        manager.add(bind)

        await inter.response.send_message(
            embed=Embed(
                description=f"A bind **{self.btitle.capitalize()}** foi registrada!",
                color=COLOR_DEF,
            ),
        )


class BindEditModal(Modal):
    """Bind edition modal."""

    text_row = Label(
        text="Texto",
        component=TextInput(
            max_length=TEXT_MAX,
            placeholder="Se hoje eu te odeio amanhã lhe tenho amor...",
            style=TextStyle.long,
        ),
    )

    def __init__(self, bind: Bind) -> None:
        super().__init__(title="Editar Bind")
        assert isinstance(self.text_row.component, TextInput)

        self.bind = bind
        self.text_row.component.default = bind.text

    async def on_submit(self, inter: Interaction) -> None:
        assert isinstance(self.text_row.component, TextInput)
        assert inter.guild

        text = validator.purge_text(self.text_row.component.value)
        if text == self.bind.text:
            await inter.response.send_message(
                embed=Embed(
                    description="Bem... você não alterou nada.", color=COLOR_DEF
                )
            )
            return
        self.bind.text = text
        manager.edit(self.bind)

        await inter.response.send_message(
            embed=Embed(
                description=f"A bind **{self.bind.title.capitalize()}** foi editada!",
                color=COLOR_DEF,
            ),
        )


@allowed_contexts(guilds=True, dms=False)
class BindGroup(Group):
    """Bind-related commands."""

    def __init__(self, bot: CustomBot) -> None:
        super().__init__(name="bind", description="Comandos relacionados a binds.")
        self.bot = bot

    @command(name="print")
    @autocomplete(title=completer.server_complete)
    async def b_print(self, inter: Interaction, title: str) -> None:
        """Imprime o texto de uma bind.

        Args:
            title: O título da bind.
        """
        assert inter.guild
        title = title.lower()

        try:
            bind = validator.req_bind_exists(title, inter.guild.id)
        except BindError as err:
            await inter.response.send_message(embed=err.embed())
            return

        await inter.response.send_message(
            bind.text, allowed_mentions=AllowedMentions.none()
        )

    @command(name="add")
    async def b_add(self, inter: Interaction, title: str) -> None:
        """Registra uma nova bind em seu nome.

        Args:
            title: O título da bind.
        """
        assert inter.guild
        title = title.lower()

        try:
            validator.req_valid_title(title)
            validator.req_bind_not_exists(title, inter.guild.id)
        except BindError as err:
            await inter.response.send_message(embed=err.embed())
            return

        await inter.response.send_modal(BindAddModal(title))

    @command(name="edit")
    @autocomplete(title=completer.author_complete)
    async def b_edit(self, inter: Interaction, title: str) -> None:
        """Edita uma de suas binds.

        Args:
            title: O título da bind.
        """
        assert inter.guild
        title = title.lower()

        try:
            bind = validator.req_bind_exists(title, inter.guild.id)
            validator.req_edit_perm(inter.user, bind)
        except BindError as err:
            await inter.response.send_message(embed=err.embed())
            return

        await inter.response.send_modal(BindEditModal(bind))

    @command(name="delete")
    @autocomplete(title=completer.author_complete)
    async def b_delete(self, inter: Interaction, title: str) -> None:
        """Delete uma de suas binds.

        Args:
            title: O título da bind.
        """
        assert inter.guild
        title = title.lower()

        try:
            bind = validator.req_bind_exists(title, inter.guild.id)
            validator.req_delete_perm(
                inter.user, bind, inter.permissions.manage_messages
            )
        except BindError as err:
            await inter.response.send_message(embed=err.embed())
            return

        manager.delete(bind)
        await inter.response.send_message(
            embed=Embed(
                description=f"A bind `{bind.title}` foi deletada.", color=COLOR_DEF
            )
        )
