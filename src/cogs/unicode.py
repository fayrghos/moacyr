from enum import Enum, auto
from typing import Optional

from discord import Interaction
from discord.app_commands import command
from discord.ext.commands import Cog

from src.bot import CustomBot


UNI_A_UPPER = ord("A")
UNI_A_LOWER = ord("a")
UNI_ZERO = ord("0")


def generate_font_map(
    upper: int,
    lower: int,
    zero: Optional[int] = None,
) -> dict[str, str]:
    """
    Generates a font map based on the HEX code equivalent
    to 'a', 'A', and '0' in a certain font.

    Please prefer the Bold versions.
    """
    out: dict[str, str] = {}

    for i in range(26):
        out[chr(UNI_A_UPPER + i)] = chr(upper + i)
        out[chr(UNI_A_LOWER + i)] = chr(lower + i)

    if zero:
        for i in range(10):
            out[chr(UNI_ZERO + i)] = chr(zero + i)

    return out


class UniFont(Enum):
    Fraktur = auto()
    Monospace = auto()
    Calligraphy = auto()
    Doublestruck = auto()
    Circled = auto()
    Squared = auto()


available_fonts: dict[UniFont, dict[str, str]] = {
    UniFont.Fraktur: generate_font_map(0x1D56C, 0x1D586),
    UniFont.Monospace: generate_font_map(0x1D670, 0x1D68A, 0x1D7F6),
    UniFont.Calligraphy: generate_font_map(0x1D4D0, 0x1D4EA),
    UniFont.Doublestruck: generate_font_map(0x1D538, 0x1D552, 0x1D7D8),
    UniFont.Circled: generate_font_map(0x24B6, 0x24D0),
    UniFont.Squared: generate_font_map(0xF130, 0xF130),  # Lowercase unavailable
}


class UniCog(Cog):

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

    @command(name="unify")
    async def unify(self, inter: Interaction, input: str, font: UniFont):
        """
        Converte um texto comum em caracteres Unicode.

        Args:
            input: O texto a ser transformado.
            font: A fonte Unicode desejada.
        """
        await inter.response.defer()

        out: str = ""
        selected_font: Optional[dict[str, str]] = available_fonts.get(font)

        if not selected_font:
            raise AssertionError("An unknown unicode font has been selected.")

        for char in input:
            out += selected_font.get(char, char)

        await inter.followup.send(f"Fonte: **{font.name}**\n```{out}```")


async def setup(bot: CustomBot):
    await bot.add_cog(UniCog(bot))
