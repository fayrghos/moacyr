"""Uncategorized commands."""

from random import randint, sample, shuffle
from textwrap import dedent
from time import time

from discord import Embed, Interaction
from discord.app_commands import command
from discord.ext.commands import Cog

import src.utils as utils
from src.bot import CustomBot


DICE_LIMIT = 50_000


def clean_entries(names: list[str]) -> list[str]:
    """Strips each raffle entry and removes empty ones."""
    final_names: list[str] = []
    for name in names:
        name = name.strip()
        if name:
            final_names.append(name)
    return final_names


class GeneralCog(Cog):

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

    @command()
    async def say(self, inter: Interaction, message: str) -> None:
        """Faz o bot falar alguma bobagem.

        Args:
            message: A mensagem a ser dita. Menções são convertidas em texto.
        """
        await inter.response.defer()
        message = await utils.remove_mentions(message, inter)
        await inter.followup.send(message)

    @command()
    async def raffle(self, inter: Interaction, entries: str, winners: int) -> None:
        """Realiza um sorteio simples.

        Args:
            entries: O nome de cada entrada, separadas por vírgula.
            winners: A quantidade de sorteados.
        """
        await inter.response.defer()

        if winners < 1:
            embed = utils.error_embed("É necessário pelo menos 1 vencedor.")
            await inter.followup.send(embed=embed)
            return

        entry_list: list[str] = clean_entries(entries.split(","))
        if not entry_list:
            embed = utils.error_embed("Nenhum participante foi encontrado.")
            await inter.followup.send(embed=embed)
            return

        entry_count: int = len(entry_list)
        if winners > entry_count:
            embed = utils.error_embed("A quantidade de vencedores é maior que a de entradas.")
            await inter.followup.send(embed=embed)
            return

        shuffle(entry_list)
        winner_list: list[str] = sample(entry_list, winners)
        winner_str: str = "\n".join(f"• {winner.capitalize()}" for winner in winner_list)

        main_desc: str = dedent(f"""
            Entradas: **{entry_count}**
            Sorteados: **{winners}**
        """)

        embed = Embed(description=main_desc,
                      color=utils.COLOR_DEF)
        embed.add_field(name="Vencedores", value=winner_str)
        await inter.followup.send(embed=embed)

    @command()
    async def dice(self,
                   inter: Interaction,
                   sides: int = 6,
                   amount: int = 1,
                   modifier: int = 0) -> None:
        """Lança um ou mais dados personalizáveis.

        Args:
            sides: A quantidade de lados por dado. Opcional.
            amount: A quantidade de dados a serem roletados. Opcional.
            modifier: Um modificador para aplicar no resultado. Opcional.
        """
        await inter.response.defer()

        if amount < 1:
            embed = utils.error_embed("É necessário lançar pelo menos 1 dado.")
            await inter.followup.send(embed=embed)
            return

        if sides < 2:
            embed = utils.error_embed("Cada dado deve conter pelo menos 2 lados.")
            await inter.followup.send(embed=embed)
            return

        if sides + amount + modifier > DICE_LIMIT:
            embed = utils.error_embed("Valores muito grandes foram inseridos.")
            await inter.followup.send(embed=embed)
            return

        modifier_signal: str = ""
        if modifier != 0:
            modifier_signal = f"+{modifier}" if modifier > 0 else str(modifier)

        number: int = randint(1, (sides * amount)) + modifier
        dice_note: str = f"{amount}d{sides}{modifier_signal}"

        embed = Embed(description=f"Um **{dice_note}** foi lançado e o resultado foi **{number}**.",
                      color=utils.COLOR_DEF)
        await inter.followup.send(embed=embed)

    @command()
    async def ping(self, inter: Interaction) -> None:
        """Verifica o tempo de atraso das respostas do bot."""
        dir_time: float = time()
        await inter.response.defer()
        defer_time: float = time()

        inter_time: float = inter.created_at.timestamp()

        diff_dir: int = int((dir_time - inter_time) * 1000)
        diff_defer: int = int((defer_time - inter_time) * 1000)

        desc_str: str = dedent(f"""
            Latência Direta: **{diff_dir}ms**
            Latência Adiada: **{diff_defer}ms**
        """)

        embed = Embed(description=desc_str,
                      color=utils.COLOR_DEF)
        await inter.followup.send(embed=embed)


async def setup(bot: CustomBot) -> None:
    await bot.add_cog(GeneralCog(bot))
