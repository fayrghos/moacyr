"""Steam-related commands."""

# This code is a mess and has too much spaghetti
# TODO: Rewrite this from scratch! ...and please nuke the requests lib!

from discord import Interaction
from discord.app_commands import Group, command, rename
from requests import HTTPError
from src.bot import CustomBot
from steam.steamid import SteamID, from_url, from_csgo_friend_code
from steam.webapi import WebAPI
from requests.exceptions import ConnectionError
from src.config import BotConfig
from src.envs import STEAM_KEY
from typing import Any

import discord
import src.utils as utils
import re
import textwrap
import asyncio


cfg = BotConfig()
cfg.parse_section("Steam", {
    "desclen": 350,
})

FAVICON: str = (
    "https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/"
    "753/1d0167575d746dadea7706685c0f3c01c8aeb6d8.jpg"
)
MAX_DESC_LENGTH = cfg.getint("Steam", "desclen")
PRIV_TEXT = "[PRIVADO]"

COLOR_STEAM = discord.Colour.from_rgb(40, 71, 101)

if STEAM_KEY:
    api = WebAPI(key=STEAM_KEY, http_timeout=10)


async def parse_steamid(inputid: str) -> SteamID:
    """Tries to converts its arg to a SteamID64."""
    userid = SteamID(inputid)
    if userid:
        return userid

    userid = from_url(f"https://steamcommunity.com/id/{inputid}")
    if userid:
        return userid

    userid = from_url(inputid)
    if userid:
        return userid

    userid = from_csgo_friend_code(inputid)
    if userid:
        return userid

    raise UnknownSteamID


class UnknownSteamID(Exception):
    pass


class SteamUser:
    """Represents a Steam user."""

    def __init__(self, steamid: SteamID) -> None:
        self.id = steamid
        self.summary: dict[str, Any] = api.call("ISteamUser.GetPlayerSummaries", steamids=self.id)["response"]["players"][0]

        self._bans = None
        self._friendnum = None

    @property
    def bans(self) -> dict[str, Any]:
        if not self._bans:
            self._bans = api.call("ISteamUser.GetPlayerBans", steamids=self.id)["players"][0]
        return self._bans

    @property
    def friendnum(self) -> int | str:
        if not self._friendnum:
            try:
                self._friendnum = len(api.call("ISteamUser.GetFriendList", steamid=self.id)["friendslist"]["friends"])
            except HTTPError:
                self._friendnum = PRIV_TEXT
        return self._friendnum

    @property
    def avatar(self) -> str:
        return self.summary["avatarfull"]

    @property
    def name(self) -> str:
        return self.summary["personaname"]

    @property
    def join_date(self) -> str:
        return utils.to_timestamp(self.summary.get("timecreated"), utils.Timestamp.ShortDate) or PRIV_TEXT

    @property
    def seen_date(self) -> str:
        return utils.to_timestamp(self.summary.get("lastlogoff"), utils.Timestamp.Relative) or PRIV_TEXT

    @property
    def vacbanned(self) -> bool:
        return self.bans["VACBanned"]

    @property
    def vacban_num(self) -> int:
        return self.bans["NumberOfVACBans"]

    @property
    def commbanned(self) -> bool:
        return self.bans["CommunityBanned"]

    @property
    def gamebanned(self) -> bool:
        return self.bans["NumberOfGameBans"] != 0

    @property
    def gameban_num(self) -> int:
        return self.bans["NumberOfGameBans"]

    @property
    def tradebanned(self) -> bool:
        return self.bans["EconomyBan"] != "none"


class WorkshopItem:
    """Represents a Steam Workshop item."""

    def __init__(self, info: dict[str, Any]) -> None:
        self.name: str = info["title"]
        self.preview: str = info["preview_url"]
        self.description: str = self._normalize_desc(info["description"])

        self.view_count: str = format(info["views"], ",")
        self.sub_count: str = format(info["subscriptions"], ",")
        self.fav_count: str = format(info["favorited"], ",")
        self.life_sub_count: str = format(info["lifetime_subscriptions"], ",")
        self.life_fav_count: str = format(info["lifetime_favorited"], ",")

        self.file_size: float = round(int(info["file_size"]) / (2**20), 2)
        self.create_date: str = utils.to_timestamp(info["time_created"])
        self.update_date: str = utils.to_timestamp(info["time_updated"])

    def _normalize_desc(self, desc: str) -> str:
        """Removes html tags, hyperlinks and shorten the description."""
        new_desc = re.sub(r"\[/?[^\]]+\]", "", desc)
        new_desc = re.sub(r"https?://\S+", "", new_desc)
        new_desc = textwrap.shorten(new_desc, MAX_DESC_LENGTH)
        return new_desc


class SteamGroup(Group):

    def __init__(self, bot: CustomBot) -> None:
        super().__init__(name="steam", description="Comandos relacionados ao Steam.")
        self.bot = bot

    @command(name="userid")
    @rename(req_userid="user")
    async def getid(self, inter: Interaction, req_userid: str) -> None:
        """Exibe uma lista dos IDs de um usuário Steam.

        Args:
            req_userid: Qualquer SteamID ou URL.
        """
        await inter.response.defer()
        for _ in range(3):
            try:
                user = SteamUser(await parse_steamid(req_userid))

                general_info = textwrap.dedent(f"""\
                    **Criação:** {user.join_date}
                    **Visto:** {user.seen_date}
                    **Amigos:** {user.friendnum}
                """)

                id_info = textwrap.dedent(f"""\
                    **ID:** {user.id.as_steam2}
                    **ID3:** {user.id.as_steam3}
                    **ID32:** {user.id.as_32}
                    **ID64:** {user.id}
                    **CS2:** {user.id.as_csgo_friend_code}
                    **Add:** {user.id.invite_url}
                """)

                ban_info = ""
                if user.vacbanned:
                    ban_info += f"⛔ VAC ({user.vacban_num})\n"
                if user.gamebanned:
                    ban_info += f"⛔ Game ({user.gameban_num})\n"
                if user.commbanned:
                    ban_info += "⛔ Community\n"
                if user.tradebanned:
                    ban_info += "⛔ Trade\n"
                if not ban_info:
                    ban_info = "🟢 Nenhum"
                ban_info.strip()

                embed = discord.Embed(title=user.name.upper(),
                                      description=general_info,
                                      url=f"https://steamcommunity.com/profiles/{user.id}",
                                      color=COLOR_STEAM)
                embed.set_thumbnail(url=user.avatar)
                embed.add_field(name="Identificadores", value=id_info)
                embed.add_field(name="Banimentos", value=ban_info)
                embed.set_footer(text="Steam Community", icon_url=FAVICON)

                await inter.followup.send(embed=embed)
                return

            except ConnectionError:
                await asyncio.sleep(1)

            except UnknownSteamID:
                embed = utils.error_embed("Não foi possível obter informações desse usuário.\nEsse comando aceita apenas SteamIDs e URLs.")
                await inter.followup.send(embed=embed)
                return

            except Exception:
                embed = utils.error_embed("Algo deu errado.")
                await inter.followup.send(embed=embed)
                return

        # This will only be called if the connection fails
        embed = utils.error_embed("A conexão com a API do Steam falhou após 3 tentativas.")
        await inter.followup.send(embed=embed)

    @command()
    @rename(req_workid="item")
    async def workshop(self, inter: Interaction, req_workid: str) -> None:
        """Exibe informações sobre um item na Oficina Steam

        Args:
            req_workid: ID ou URL do item.
        """
        await inter.response.defer()

        workshop_id = re.sub(r"\D+", "", req_workid)
        if not workshop_id:
            embed = utils.error_embed("Você inseriu um ID/URL inválido.")
            await inter.followup.send(embed=embed)
            return

        for _ in range(3):
            try:
                request = api.call("ISteamRemoteStorage.GetPublishedFileDetails",
                                   itemcount=1,
                                   publishedfileids=[workshop_id])
                item = WorkshopItem(request["response"]["publishedfiledetails"][0])

                info_field = textwrap.dedent(f"""
                    **Tamanho:** {item.file_size} MB
                    **Postado:** {item.create_date}
                    **Atualizado:** {item.update_date}
                """)

                stat_field = textwrap.dedent(f"""
                    👁️ {item.view_count}
                    📥 {item.sub_count} ({item.life_sub_count} únicos)
                    ⭐ {item.fav_count} ({item.life_fav_count} únicos)
                """)

                embed = discord.Embed(title=item.name.upper(),
                                      description=item.description,
                                      url=f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}",
                                      color=COLOR_STEAM)
                embed.set_thumbnail(url=item.preview)
                embed.add_field(name="Propriedades", value=info_field)
                embed.add_field(name="Estatísticas", value=stat_field)
                embed.set_footer(text=f"Steam Workshop • {workshop_id}", icon_url=FAVICON)

                await inter.followup.send(embed=embed)
                return

            except ConnectionError:
                await asyncio.sleep(1)

            except Exception:
                embed = utils.error_embed("Não foi possível obter informações sobre esse item.")
                await inter.followup.send(embed=embed)
                return

        # This will only be called if the connection fails
        embed = utils.error_embed("A conexão com a API do Steam falhou após 3 tentativas.")
        await inter.followup.send(embed=embed)


async def setup(bot: CustomBot) -> None:
    if not STEAM_KEY:
        print("Cannot find a Steam API key. Skipping Steam related commands...")
        return
    bot.tree.add_command(SteamGroup(bot))
