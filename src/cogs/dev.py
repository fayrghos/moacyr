"""Developer-only debug commands."""

from discord.ext.commands import Context, Cog, command
from src.bot import CustomBot
from typing import Optional

import discord
import src.utils as utils
import platform
import textwrap


class DevCog(Cog):

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

    def cog_check(self, ctx: Context) -> bool:
        if self.bot.application:
            return ctx.author.id == self.bot.application.owner.id
        return False

    @command(
        aliases=["kill"],
        hidden=True
    )
    async def shutdown(self, ctx: Context) -> None:
        """Ragequits."""
        await ctx.message.add_reaction("💤")
        await self.bot.close()

    @command(
        aliases=["del"],
        hidden=True
    )
    async def delmsg(self, ctx: Context, req_msg: int, req_chan: Optional[int]) -> None:
        """Deletes a message using message and channel IDs."""
        try:
            if not req_chan:
                req_chan = ctx.channel.id

            channel = self.bot.get_channel(req_chan)
            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(req_msg)
                await message.delete()
                await ctx.message.add_reaction("🖌️")

        except Exception:
            await ctx.message.add_reaction("❔")

    @command(
        hidden=True
    )
    async def guildperms(self, ctx: Context) -> None:
        """Prints all guild permissions."""
        if not ctx.guild:
            return

        perm_str = ""
        for perm, value in sorted(ctx.guild.me.guild_permissions):
            perm_str += f"{'🟢' if value else '🔴'} {perm.capitalize()}\n"

        embed = discord.Embed(title="Permissões (Guilda)", description=perm_str, color=utils.COLOR_DEBUG)
        await ctx.send(embed=embed)

    @command(
        hidden=True
    )
    async def channelperms(self, ctx: Context) -> None:
        """Prints all channel permissions."""
        if not ctx.guild or not isinstance(ctx.me, discord.Member):
            return

        perm_str = ""
        for perm, value in sorted(ctx.channel.permissions_for(ctx.me)):
            perm_str += f"{'🟢' if value else '🔴'} {perm.capitalize()}\n"

        embed = discord.Embed(title="Permissões (Canal)", description=perm_str, color=utils.COLOR_DEBUG)
        await ctx.send(embed=embed)

    @command(
        hidden=True
    )
    async def info(self, ctx: Context) -> None:
        """Prints some system information."""
        system = platform.system()
        embed = discord.Embed(color=utils.COLOR_DEBUG)

        os_desc = textwrap.dedent(f"""
            Platform: {system or "???"}
            Arch: {platform.machine() or "???"}
        """)
        embed.add_field(name="OS", value=os_desc, inline=False)

        py_desc = textwrap.dedent(f"""
            Version: {platform.python_version() or "???"}
            Compiler: {platform.python_implementation() or "???"}
            Discord.py: {discord.__version__}
        """)
        embed.add_field(name="PYTHON", value=py_desc, inline=False)

        if system == "Linux":
            distro_info = platform.freedesktop_os_release()
            distro_desc = textwrap.dedent(f"""
                Name: {distro_info.get("NAME", "???")}
                Edition: {distro_info.get("VERSION_ID", "???")}
            """)
            embed.add_field(name="DISTRO", value=distro_desc, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: CustomBot) -> None:
    await bot.add_cog(DevCog(bot))
