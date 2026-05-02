"""Validation helpers and errors for binds."""

from typing import Union

from discord import Member, User

from cogs.bind.manager import BindManager
from core.models.bind import Bind
from core.utils import MoacyrException

TITLE_MAX = 18


class BindError(MoacyrException):
    pass


class BindValidator:
    """Centralized validation logic for bind operations."""

    def __init__(self, manager: BindManager) -> None:
        self.manager = manager

    def req_bind_exists(self, title: str, guild: int) -> Bind:
        """Require the bind to previously exists."""
        bind = self.manager.single(title, guild)
        if not bind:
            raise BindError("Nenhuma bind possui esse título.")
        return bind

    def req_bind_not_exists(self, title: str, guild: int) -> None:
        """Require that no bind exists with the same title."""
        if self.manager.single(title, guild):
            raise BindError("Já existe outra bind com esse título.")

    def req_edit_perm(self, user: Union[Member, User], bind: Bind) -> None:
        """Require the user having permission to edit."""
        if user.id != bind.author:
            raise BindError("Você não é o dono dessa bind.")

    def req_delete_perm(
        self, user: Union[Member, User], bind: Bind, is_admin: bool
    ) -> None:
        """Require the user having permission to delete."""
        if user.id != bind.author and not is_admin:
            raise BindError("Você não tem permissão para deletar essa bind.")

    def req_valid_title(self, title: str) -> None:
        """Require a bind title to be valid."""
        if len(title) > TITLE_MAX:
            raise BindError(
                f"O título da bind não pode ser maior que {TITLE_MAX} caracteres!"
            )
        if not title.isalnum():
            raise BindError("O título da bind só pode ter letras e números!")

    def purge_text(self, text: str) -> str:
        """Sanitize global mentions to prevent abuse."""
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
        return text
