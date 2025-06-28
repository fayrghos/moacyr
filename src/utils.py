"""Multipurpose variables and functions."""

from enum import Enum
from discord import Colour, Embed, Interaction, Permissions, ButtonStyle
from discord.ext.commands import Context
from discord.ui import View, button, Button
from typing import Any, Union, Optional

import re


COLOR_DEF = Colour.from_rgb(147, 112, 219)
COLOR_ERROR = Colour.from_rgb(225, 80, 80)
COLOR_DEBUG = Colour.from_rgb(25, 25, 25)

MAX_COMPLETE_OPTS = 25


class Timestamp(Enum):
    Default = ""
    ShortTime = ":t"
    LongTime = ":T"
    ShortDate = ":d"
    LongDate = ":D"
    ShortDateTime = ":f"
    LongDateTime = ":F"
    Relative = ":R"


def error_embed(error_desc: Union[str, Exception], *, title: Optional[str] = None) -> Embed:
    """Returns a generic error embed."""
    return Embed(title=title, description=error_desc, color=COLOR_ERROR)


async def remove_mentions(message: str, via: Union[Context, Interaction]) -> str:
    """Removes user, roles, @everyone and @here mentions from a string."""
    bot = via.client if isinstance(via, Interaction) else via.bot
    guild = via.guild

    mentions = re.findall(r"<@(\d+)>", message)
    roles = re.findall(r"<@&(\d+)>", message)

    message = message.replace("@here", "@\u200bhere")
    message = message.replace("@everyone", "@\u200beveryone")

    for user_id in mentions:
        user = await bot.fetch_user(int(user_id))
        message = message.replace(f"<@{user_id}>", f"@\u200b{user.display_name}")

    if not guild:
        return message

    for role_id in roles:
        role = guild.get_role(int(role_id))
        if not role:
            break
        message = message.replace(f"<@&{role_id}>", f"@\u200b{role.name}")
    return message


def to_timestamp(time: Any, stamp: Timestamp = Timestamp.Default) -> str:
    """Tries to format the param to a Discord timestamp."""
    return f"<t:{time}{stamp.value}>" if time else ""


def check_permissions(need_perms: list[str], perms: Permissions) -> bool:
    """Checks if all the need_perms are True inside perms."""
    exist_perms = dir(perms)
    for perm in need_perms:
        if perm not in exist_perms:
            return False
        continue
    return True


def cooler_shorten(text: str, max_width: int) -> str:
    """An alternative to textwrap.shorten that actually breaks words."""
    text = " ".join(text.split())
    text_len: int = len(text)

    if text_len <= max_width:
        return text

    place: str = f" <+{text_len - max_width}>"
    place_len: int = len(place)

    if max_width <= place_len:
        raise ValueError("The placeholder is hiding the entire text.")

    return text[:max_width - place_len] + place


class EmbScroller(View):
    """A view to scroll through multiple embeds."""

    def __init__(self, inter: Interaction, embeds: list[Embed], *, timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.inter = inter
        self.embeds = embeds

        self.index = 0
        self.update_label()

        if len(embeds) <= 1:
            self.forward.disabled = True

    async def on_timeout(self) -> None:
        """Deletes all buttons after the timeout."""
        message = await self.inter.original_response()
        if message:
            await message.edit(view=None)

    async def interaction_check(self, new_inter: Interaction) -> bool:
        return new_inter.user.id == self.inter.user.id

    def update_label(self) -> None:
        """Updates the jump button label."""
        self.jump.label = f"{self.index + 1} de {len(self.embeds)}"

    def set_index(self, new_index: int) -> None:
        """Updates the current index and adjusts buttons."""
        self.index = new_index

        self.back.disabled = False
        if self.index <= 0:
            self.back.disabled = True

        self.forward.disabled = False
        if self.index >= len(self.embeds) - 1:
            self.forward.disabled = True

        self.update_label()

    @button(label="◀", style=ButtonStyle.secondary, disabled=True)
    async def back(self, inter: Interaction, button: Button) -> None:
        self.set_index(self.index - 1)
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @button(label="", style=ButtonStyle.secondary, disabled=True)
    async def jump(self, inter: Interaction, button: Button) -> None:
        pass

    @button(label="▶", style=ButtonStyle.secondary)
    async def forward(self, inter: Interaction, button: Button) -> None:
        self.set_index(self.index + 1)
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)
