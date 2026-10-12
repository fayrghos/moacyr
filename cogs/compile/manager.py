"""WebAPI access layer for the compile command."""

from logging import getLogger
from typing import Self

import httpx
from discord.app_commands import Choice
from httpx import RequestError, TimeoutException
from pydantic import ValidationError

from core.schemas.compile import Compiler, CompileRequest, CompileResponse, CompilerList

logger = getLogger(__name__)


class CompilerManager:
    """Manages all things related to Wandbox compilers."""

    @classmethod
    async def start(cls) -> Self:
        return cls(await cls.fetch_compilers())

    @staticmethod
    async def fetch_compilers() -> list[Compiler]:
        """Gets an updated list of compilers available in Wandbox."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://wandbox.org/api/list.json", timeout=10
                )
                response.raise_for_status()
            except TimeoutException:
                logger.warning("A timeout happened while connecting to Wandbox.")
                return []
            except RequestError:
                logger.warning("An unknown error happened while connecting to Wandbox.")
                return []

            try:
                list = CompilerList(response.json()).root
            except ValidationError:
                logger.warning("Failed to validate the Wandbox response.")
                return []

            # For some reason, 'head' compilers are buggy
            return [
                compiler for compiler in list if "head" not in compiler.name.lower()
            ]

    @staticmethod
    async def send_compile(request: CompileRequest) -> CompileResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://wandbox.org/api/compile.json",
                timeout=10,
                json=request.model_dump(),
            )
            response.raise_for_status()
        return CompileResponse(**response.json())

    def __init__(self, compilers: list[Compiler]) -> None:
        self.compilers = compilers
        self.choices = self._choicefy_compilers(compilers)

    def get_compiler(self, language: str) -> Compiler | None:
        """Gets a specific compiler from the compiler list."""
        for compiler in self.compilers:
            if compiler.language.lower() == language.lower():
                return compiler
        return None

    def _choicefy_compilers(self, compilers: list[Compiler]) -> list[Choice[str]]:
        """Returns a minimal version of the compiler list which only contains one entry per language."""
        output: list[Choice[str]] = []
        existing_langs: list[str] = []

        for compiler in compilers:
            if compiler.language not in existing_langs:
                existing_langs.append(compiler.language)
                output.append(compiler.choicefy())

        return output
