"""Pydantic models for compile commands."""

from typing import Annotated

from discord import SelectOption
from discord.app_commands import Choice
from pydantic import AfterValidator, BaseModel, Field, RootModel


class Compiler(BaseModel):
    """Code compilers inside list requests."""

    name: str
    version: str
    language: str

    command: str = Field(alias="display-compile-command")
    has_runtime: bool = Field(alias="runtime-option-raw")
    has_compiler: bool = Field(alias="compiler-option-raw")

    def choicefy(self) -> Choice[str]:
        """Converts this compiler into a Discord app choice."""
        return Choice(name=self.language, value=self.language.lower())

    def selectify(self) -> SelectOption:
        """Converts this compiler into a Discord app select option."""
        return SelectOption(label=self.name, value=self.name)


class CompilerList(RootModel[list[Compiler]]):
    """Compiler list GET request response."""


class CompileRequest(BaseModel):
    """Code compile POST request parameters."""

    code: str
    compiler: str
    stdin: str = Field(default="")


class CompileResponse(BaseModel):
    """Code compile POST request response."""

    status: Annotated[str, AfterValidator(lambda x: x or "?")]

    program_message: str
    compiler_message: str

    @property
    def output(self) -> str:
        return self.program_message or self.compiler_message or "<Vazio>"
