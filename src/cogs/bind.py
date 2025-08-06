"""Bind-related bot commands."""

import textwrap
import time
from dataclasses import dataclass

from discord import Embed, Guild, TextStyle
from discord.app_commands import (
    CheckFailure,
    Choice,
    Group,
    allowed_contexts,
    autocomplete,
    command,
)
from discord.interactions import Interaction
from discord.ui import Modal, TextInput

import src.utils as utils
from src.bot import CustomBot
from src.config import BotConfig
from src.db import BaseDB


cfg = BotConfig()
cfg.parse_section("Binds", {
    "enabled": "yes",
})

BIND_ENABLED = cfg.getboolean("Binds", "enabled")

MIN_NAME_LEN = 2
MAX_NAME_LEN = 25

MIN_TEXT_LEN = 3
MAX_TEXT_LEN = 600

TEXT_PLACEHOLDER = "De acordo com todas as conhecidas leis da aviação..."


@dataclass
class Bind:
    """Represents a Bind."""

    name: str
    text: str
    author: int
    guild: int
    time: int


class BindManager(BaseDB):
    """Represents the Bind Manager system."""

    def __init__(self) -> None:
        super().__init__()
        if BIND_ENABLED:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS binds (
                        "name" TEXT,
                        "text" TEXT,
                        "author" INTEGER,
                        "guild" INTEGER,
                        "time" INTEGER,
                        UNIQUE("guild","name")
                    )
                """)
        self.complete_cache: dict[tuple[int, int], list[Bind]] = {}

    def get_bind(self, name: str, guild: int) -> Bind | None:
        """Returns a Bind from the database."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM binds WHERE name=? AND guild=?",
                           [name.lower(), guild])
            bind = cursor.fetchone()

            if bind:
                return Bind(*bind)
            return None

    def get_all_binds(self, author: int, guild: int) -> list[Bind]:
        """Returns many Binds from the database."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM binds WHERE author=? AND guild=?",
                           [author, guild])
            binds = cursor.fetchall()

        if binds:
            return [Bind(*bind) for bind in binds]
        return []

    def add_bind(self,
                 name: str,
                 text: str,
                 author: int,
                 guild: int,
                 timestamp: float) -> None:
        """Register a Bind into the database."""
        with self.get_cursor() as cursor:
            cursor.execute("INSERT INTO binds VALUES (?, ?, ?, ?, ?)",
                           [name.lower(), text, author, guild, timestamp])
            self._commit()

    def edit_bind(self, bind: Bind, new_text: str) -> None:
        """Edits a Bind from the database."""
        with self.get_cursor() as cursor:
            cursor.execute("UPDATE binds SET text=? WHERE name=? AND guild=?",
                           [new_text, bind.name, bind.guild])
            self._commit()

    def delete_bind(self, bind: Bind) -> None:
        """Deletes a Bind from the database."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM binds WHERE name=? AND guild=?",
                           [bind.name, bind.guild])
            self._commit()

    def nuke_server_binds(self, guild: int) -> None:
        """Deletes all binds from a server."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM binds WHERE guild=?",
                           [guild])
            self._commit()

    def _commit(self) -> None:
        super()._commit()
        self.complete_cache.clear()


class BindRegisterModal(Modal):
    """Modal used in the bind registration command."""

    textfield: TextInput = TextInput(
        label="Texto desejado",
        placeholder=TEXT_PLACEHOLDER,
        required=True,
        min_length=MIN_TEXT_LEN,
        max_length=MAX_TEXT_LEN,
        style=TextStyle.paragraph
    )

    def __init__(self, name: str) -> None:
        super().__init__(title="Registrar Bind")
        self.name = name

    async def on_submit(self, inter: Interaction) -> None:
        assert inter.guild
        await inter.response.defer()

        text = self.textfield.value
        text = await cleanse_text(text, inter)

        bind_manager.add_bind(self.name, text, inter.user.id, inter.guild.id, int(time.time()))

        embed = Embed(description=f"Você registrou uma bind com o nome de \"**{self.name.capitalize()}**\"!",
                      color=utils.COLOR_DEF)
        await inter.followup.send(embed=embed)


class BindModifyModal(Modal):
    """Modal used in the bind modification command."""

    textfield: TextInput = TextInput(
        label="Novo texto desejado",
        placeholder=TEXT_PLACEHOLDER,
        required=True,
        min_length=MIN_TEXT_LEN,
        max_length=MAX_TEXT_LEN,
        style=TextStyle.paragraph
    )

    def __init__(self, bind: Bind) -> None:
        super().__init__(title="Modificar Bind")
        self.bind = bind

    async def on_submit(self, inter: Interaction) -> None:
        await inter.response.defer()

        text = self.textfield.value
        text = await cleanse_text(text, inter)

        bind_manager.edit_bind(self.bind, text)
        embed = Embed(description=f"Você editou o texto da bind com o nome de \"**{self.bind.name.capitalize()}**\"!",
                      color=utils.COLOR_DEF)
        await inter.followup.send(embed=embed)


async def bind_complete(inter: Interaction, current: str) -> list[Choice]:
    """The autocomplete for the bind commands."""
    assert inter.user
    assert inter.guild

    # Cache cuz calling the database each time is bad
    user_tuple = (inter.user.id, inter.guild.id)
    if not bind_manager.complete_cache.get(user_tuple):
        bind_manager.complete_cache[user_tuple] = bind_manager.get_all_binds(inter.user.id, inter.guild.id)

    if not current:
        return [
            Choice(name=bind.name.capitalize(), value=bind.name)
            for bind in bind_manager.complete_cache[user_tuple][:utils.MAX_COMPLETE_OPTS]
        ]

    return [
        Choice(name=bind.name.capitalize(), value=bind.name)
        for bind in bind_manager.complete_cache[user_tuple][:utils.MAX_COMPLETE_OPTS]
        if current in bind.name
    ]


async def cleanse_text(text: str, inter: Interaction) -> str:
    """Cleanses the text to be used in a bind."""
    new_text = await utils.remove_mentions(text, inter)
    new_text = new_text.replace("*DEAD*", "\\*DEAD\\*") # TF2 binds
    return new_text

def split_binds(binds: list[Bind], *, group_size: int = 15) -> list[list[Bind]]:
    """Splits a list of binds. Should be used to create pages."""
    final_list: list[list[Bind]] = []
    for _ in binds:
        if not binds:
            break
        final_list.append(binds[:group_size])
        binds = binds[group_size:]
    return final_list

def bind_groups_to_embeds(binds: list[list[Bind]]) -> list[Embed]:
    """Converts a splitted list of bind groups into a list of embeds."""
    final_binds: list[Embed] = []
    for group in binds:
        bind_str = "\n".join(f"- {bind.name.capitalize()}" for bind in group)

        embed = (Embed(title="Suas binds:",
                       description=bind_str,
                       color=utils.COLOR_DEF))
        embed.set_footer(text="Válidas somente nesse servidor.")

        final_binds.append(embed)
    return final_binds


def existing_bind_emb(name: str) -> Embed:
    return Embed(description=f"Uma bind nomeada \"**{name.capitalize()}**\" já existe.",
                 color=utils.COLOR_ERROR)


def non_existing_bind_emb() -> Embed:
    return Embed(description=f"Não existe nenhuma bind registrada com esse nome.",
                 color=utils.COLOR_ERROR)


def non_bind_own_emb() -> Embed:
    return Embed(description="Você não é o autor dessa bind.",
                 color=utils.COLOR_ERROR)


bind_manager = BindManager()


@allowed_contexts(guilds=True, dms=False)
class BindGroup(Group):

    def __init__(self, bot: CustomBot) -> None:
        super().__init__(name="bind",
                         description="Comandos relacionados a Binds.")
        self.bot = bot

        self.bot.add_listener(self.server_leave_deleter, "on_guild_remove")

    async def interaction_check(self, inter: Interaction) -> bool:
        return BIND_ENABLED and inter.guild is not None

    async def on_error(self, inter: Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure):
            embed = utils.error_embed("As binds não podem ser usadas no momento.")
            await inter.response.send_message(embed=embed)

    async def server_leave_deleter(self, guild: Guild) -> None:
        """Deletes all binds from a server when the bot leaves it."""
        bind_manager.nuke_server_binds(guild.id)

    @command(
        name="say",
    )
    @autocomplete(name=bind_complete)
    async def say(self, inter: Interaction, name: str) -> None:
        """Imprime uma determinada bind no chat.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild
        await inter.response.defer()

        bind = bind_manager.get_bind(name, inter.guild.id)
        if not bind:
            await inter.followup.send(embed=non_existing_bind_emb())
            return

        await inter.followup.send(bind.text)

    @command(
        name="register",
    )
    async def register(self, inter: Interaction, name: str) -> None:
        """Cria uma bind com um determinado nome.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild

        bind = bind_manager.get_bind(name, inter.guild.id)
        if bind:
            await inter.response.send_message(embed=existing_bind_emb(bind.name), ephemeral=True)
            return

        if not name.isalnum():
            embed = utils.error_embed("O nome da sua bind deve conter apenas letras e números.")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        if len(name) > MAX_NAME_LEN or len(name) < MIN_NAME_LEN:
            embed = utils.error_embed(f"O nome da sua bind deve ter entre {MIN_NAME_LEN} e {MAX_NAME_LEN} caracteres.")
            await inter.response.send_message(embed=embed, ephemeral=True)

        modal = BindRegisterModal(name)
        await inter.response.send_modal(modal)

    @command(
        name="delete",
    )
    @autocomplete(name=bind_complete)
    async def delete(self, inter: Interaction, name: str) -> None:
        """Deleta uma bind criada por você.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild
        await inter.response.defer(ephemeral=True)

        bind = bind_manager.get_bind(name, inter.guild.id)
        if not bind:
            await inter.followup.send(embed=non_existing_bind_emb())
            return

        if bind.author != inter.user.id and not inter.permissions.manage_messages:
            await inter.followup.send(embed=non_bind_own_emb())
            return

        bind_manager.delete_bind(bind)
        embed = Embed(description=f"Você deletou a bind com o nome de \"**{bind.name.capitalize()}**\"!",
                      color=utils.COLOR_DEF)
        await inter.followup.send(embed=embed)

    @command(
        name="modify",
    )
    @autocomplete(name=bind_complete)
    async def modify(self, inter: Interaction, name: str) -> None:
        """Altera o texto de uma bind criada por você.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild

        bind = bind_manager.get_bind(name, inter.guild.id)
        if not bind:
            await inter.response.send_message(embed=non_existing_bind_emb(), ephemeral=True)
            return

        if bind.author != inter.user.id:
            await inter.response.send_message(embed=non_bind_own_emb(), ephemeral=True)
            return

        modal = BindModifyModal(bind)
        modal.textfield.default = bind.text[:MAX_TEXT_LEN]
        await inter.response.send_modal(modal)

    @command(
        name="list-mine",
    )
    async def listmine(self, inter: Interaction) -> None:
        """Exibe uma lista das binds criadas por você.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild
        await inter.response.defer(ephemeral=True)

        binds = bind_manager.get_all_binds(inter.user.id, inter.guild.id)
        if not binds:
            embed = Embed(description="Você ainda não registrou nenhuma bind nesse servidor.",
                          color=utils.COLOR_ERROR)
            await inter.followup.send(embed=embed)
            return

        splitted_binds = split_binds(binds)
        embeds = bind_groups_to_embeds(splitted_binds)

        await inter.followup.send(embed=embeds[0], view=utils.EmbScroller(inter, embeds))

    @command(
        name="info",
    )
    @autocomplete(name=bind_complete)
    async def info(self, inter: Interaction, name: str) -> None:
        """Exibe informações úteis sobre uma bind.

        Args:
            name: Nome usado para chamar a bind.
        """
        assert inter.guild
        await inter.response.defer(ephemeral=True)

        bind = bind_manager.get_bind(name, inter.guild.id)
        if not bind:
            await inter.followup.send(embed=non_existing_bind_emb(), ephemeral=True)
            return

        author = await self.bot.fetch_user(bind.author)
        desc = textwrap.dedent(f"""\
            **Autor:** {author.mention} ({author.name})
            **Criada:** {utils.to_timestamp(bind.time, utils.Timestamp.Relative)}
            ```
            {bind.text}
            ```
        """)

        embed = Embed(description=desc,
                      color=utils.COLOR_DEF,
                      title=bind.name.capitalize())
        embed.set_footer(text="Válida somente nesse servidor.")
        await inter.followup.send(embed=embed)


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(BindGroup(bot))
