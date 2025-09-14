"""Steam-related commands."""

import asyncio
import re
from textwrap import dedent, shorten
from typing import Any, Optional, Self

import httpx
from discord import Colour, Embed, Interaction
from discord.app_commands import Group, command, rename
from httpx import Response

from src.bot import CustomBot
from src.envs import STEAM_KEY
from src.utils import Timestamp, err_embed, to_timestamp


CONST_ID64 = 0x0110000100000000
PRIV_TEXT = "[Privado]"
COLOR_STEAM = Colour.from_rgb(40, 71, 101)
MAX_DESC_LEN = 500


class SteamAPI:
    """A class to interact with the Steam API."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

        self.__validate_key()

    def __validate_key(self) -> None:
        """Simply checks if the API key is valid."""
        response = httpx.get(f"https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1/?key={self.api_key}",
                             timeout=10)
        if response.status_code == 200 and response.json()["apilist"]["interfaces"]:
            return

        raise InvalidSteamKey("The provided Steam key could not be validated.")

    @staticmethod
    def __kwargs_to_query(kwargs: dict[str, Any]) -> str:
        """Converts kwargs to query strings."""
        kwargs_out: str = ""
        for key, value in kwargs.items():
            # "stuffs=[123, 321]"
            if isinstance(value, list):
                values: list[tuple[int, Any]] = list(enumerate(value))
                for pair in values:
                    kwargs_out += f"&{key}[{pair[0]}]={pair[1]}"
                continue

            # "stuff=123"
            kwargs_out += f"&{key}={value}"

        return kwargs_out

    async def get(self, interface: str, version: int, **kwargs) -> Response:
        """Sends a async GET request to the Steam API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.steampowered.com/{interface}/v{version}/?key={self.api_key}" +
                                        self.__kwargs_to_query(kwargs))
        return response


class SteamID:
    """A class to handle SteamID conversions."""

    # Useful SteamID conversion info can be found at:
    # https://developer.valvesoftware.com/wiki/SteamID

    @classmethod
    async def from_guess(cls, input_str: str) -> Self:
        """Tries to convert any input to a 64bit SteamID."""
        # ID 2
        if match := re.search(r"STEAM_1:([0-1]):([0-9]+)$", input_str):
            return cls((int(match.group(2)) * 2) + CONST_ID64 + int(match.group(1)))

        # ID 3
        if match := re.search(r"\[U:1:([0-9]{1,10})\]$", input_str):
            return cls(int(match.group(1)) + CONST_ID64)

        # ID 64
        if match := re.search(r"([0-9]{17})/?$", input_str):
            return cls(int(match.group(1)))

        # ID 32
        if match := re.search(r"([0-9]{1,10})/?$", input_str):
            return cls(int(match.group(1)) + CONST_ID64)

        # Vanity
        if match := re.search(r"([a-zA-Z-0-9_\-]+)/?$", input_str):
            response = await api.get("ISteamUser/ResolveVanityURL", 1, vanityurl=match.group(1))
            data: dict[str, Any] = response.json()
            if response.status_code == 200 and data["response"]["success"] == 1:
                return cls(int(data["response"]["steamid"]))

        raise IdNotFound

    def __init__(self, id64: int) -> None:
        """Consider using the class method `guess` to create an instance."""
        self.id64 = id64
        self.id32 = self.__to_32()
        self.steam2 = self.__to_steam2()
        self.steam3 = self.__to_steam3()

    def __to_32(self) -> int:
        return self.id64 - CONST_ID64

    def __to_steam2(self) -> str:
        weird_bit: int = int(bin(self.id64)[-1])
        return f"STEAM_1:{weird_bit}:{(self.id64 - CONST_ID64 - weird_bit) // 2}"

    def __to_steam3(self) -> str:
        return f"[U:1:{self.id64 - CONST_ID64}]"


class SteamUser:
    """Represents a Steam user."""

    @classmethod
    async def from_steamid(cls, steamid: SteamID) -> Self:
        """Fetches Steam user details using a SteamID."""
        summ, bans, friends, level, customs = await asyncio.gather(
            api.get("ISteamUser/GetPlayerSummaries", 2, steamids=steamid.id64),
            api.get("ISteamUser/GetPlayerBans", 1, steamids=steamid.id64),
            api.get("ISteamUser/GetFriendList", 1, steamid=steamid.id64),
            api.get("IPlayerService/GetSteamLevel", 1, steamid=steamid.id64),
            api.get("IPlayerService/GetProfileItemsEquipped", 1, steamid=steamid.id64)
        )

        summ = summ.raise_for_status().json()["response"]["players"][0]
        bans = bans.raise_for_status().json()["players"][0]
        friends = friends.raise_for_status().json()["friendslist"]["friends"] if friends.status_code == 200 else None
        level = level.raise_for_status().json()["response"]
        customs = customs.raise_for_status().json()["response"]

        return cls(steamid, summ, bans, friends, level, customs)

    def __init__(self,
                 steamid: SteamID,
                 summary: dict[str, Any],
                 bans: dict[str, Any],
                 friends: Optional[list[dict[str, Any]]],
                 level: dict[str, Any],
                 customs: dict[str, dict[str, Any]]) -> None:
        """Should not be called directly, use `from_steamid` instead."""
        self.id = steamid
        self.r_summary = summary
        self.r_bans = bans
        self.r_friends = friends
        self.r_level = level
        self.r_customs = customs

        self.name: str = self.r_summary["personaname"]
        self.avatar: str = self.r_summary["avatarfull"]
        self.url = f"https://steamcommunity.com/profiles/{self.id.id64}"
        self.level: Optional[int] = self.r_level.get("player_level", None)

        self.vacban_amount: int = self.r_bans["NumberOfVACBans"]
        self.gameban_amount: int = self.r_bans["NumberOfGameBans"]
        self.days_no_ban: int = self.r_bans["DaysSinceLastBan"]

        self.vacban_status: bool = self.r_bans["VACBanned"]
        self.gameban_status: bool = self.r_bans["NumberOfGameBans"] > 0
        self.commban_status: bool = self.r_bans["CommunityBanned"]
        self.tradeban_status: bool = self.r_bans["EconomyBan"] != "none"

        self.join: Optional[int] = self.r_summary.get("timecreated")
        self.seen: Optional[int] = self.r_summary.get("lastlogoff")

    @property
    def friend_amount(self) -> Optional[int]:
        if self.r_friends:
            return len(self.r_friends)
        return None

    @property
    def country(self) -> Optional[str]:
        country: Optional[str] = self.r_summary.get("loccountrycode")
        if country:
            return f":flag_{country.lower()}:"
        return None

    @property
    def background(self) -> str:
        url: Optional[str] = self.r_customs["profile_background"].get("image_large")
        if url:
            return f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/{url}"
        return "https://steamcommunity-a.akamaihd.net/public/images/profile/2020/bg_dots.png"


class SteamWorkItem:
    """Represents a Steam Workshop item."""

    @classmethod
    async def from_url(cls, url: str) -> Self:
        """Fetches a Steam Workshop item using its URL or ID."""
        if match := re.search(r"([0-9]+)$", url):
            response = await api.get("IPublishedFileService/GetDetails",
                                     1,
                                     itemcount=1,
                                     publishedfileids=[match.group(1)])
            data: dict[str, Any] = response.json()
            if response.status_code == 200 and data["response"]["publishedfiledetails"][0]["result"] == 1:
                return cls(match.group(1), data["response"]["publishedfiledetails"][0])

        raise IdNotFound

    def __init__(self,
                 workid: str,
                 details: dict[str, Any]) -> None:
        """Should not be called directly, use `from_url` instead."""
        self.r_details = details
        self.id = workid

        self.title: str = self.r_details["title"]
        self.preview: str = self.r_details["preview_url"]
        self.url: str = f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.id}"
        self.tags: str = ", ".join([tag["display_name"] for tag in self.r_details["tags"]])

        self.view_amount: int = self.r_details["views"]
        self.sub_amount: int = self.r_details["subscriptions"]
        self.sub_amount_life: int = self.r_details["lifetime_subscriptions"]
        self.fav_amount: int = self.r_details["favorited"]
        self.fav_amount_life: int = self.r_details["lifetime_favorited"]

        self.file_size: int = int(details["file_size"])
        self.create_date: int = self.r_details["time_created"]
        self.update_date: int = self.r_details["time_updated"]

    @property
    def description(self) -> str:
        return re.sub(r"(\[/?[^\]]+\])|(https?://\S+)", "", self.r_details["file_description"])


class SteamGroup(Group):

    def __init__(self, bot: CustomBot) -> None:
        super().__init__(name="steam", description="Comandos relacionados ao Steam.")
        self.bot = bot

    @command()
    @rename(given_id="id")
    async def user(self, inter: Interaction, given_id: str) -> None:
        """Exibe informações sobre algum usuário Steam.

        Args:
            given_id: Qualquer SteamID ou URL do perfil.
        """
        await inter.response.defer()
        try:
            userid = await SteamID.from_guess(given_id)
            user = await SteamUser.from_steamid(userid)

            desc: str = dedent(f"""
                Nível: **{user.level if user.level is not None else PRIV_TEXT}**
                Criado: **{to_timestamp(user.join, Timestamp.LongDate) if user.join else PRIV_TEXT}**
                Visto: **{to_timestamp(user.seen, Timestamp.LongDate) if user.seen else PRIV_TEXT}**
                Amigos: **{user.friend_amount or PRIV_TEXT}**
                País: **{user.country or PRIV_TEXT}**
            """)

            ids_field: str = dedent(f"""
                ID2: **{user.id.steam2}**
                ID3: **{user.id.steam3}**
                ID32: **{user.id.id32}**
                ID64: **{user.id.id64}**
            """)

            bans: list[str] = []
            if user.vacban_status:
                bans.append(f"⛔ VACs ({user.vacban_amount})")
            if user.gameban_status:
                bans.append(f"⛔ Jogos ({user.gameban_amount})")
            if user.commban_status:
                bans.append("⛔ Comunidade")
            if user.tradeban_status:
                bans.append("⛔ Trocas")
            if not bans:
                bans.append("🟢 Nenhum")
            bans_field: str = "\n".join(bans)

            embed = Embed(description=desc,
                          color=COLOR_STEAM,
                          title=user.name.upper(),
                          url=user.url)
            embed.set_thumbnail(url=user.avatar)
            embed.add_field(name="Banimentos", value=bans_field, inline=False)
            embed.add_field(name="Steam IDs", value=ids_field, inline=False)
            embed.set_image(url=user.background)
            await inter.followup.send(embed=embed)

        except IdNotFound:
            embed = err_embed("Nenhum jogador foi encontrado.\n" +
                              "Esse comando aceita URLs de perfil e qualquer formato de SteamID.")
            await inter.followup.send(embed=embed)

        except:
            embed = err_embed("Algo deu errado.")
            await inter.followup.send(embed=embed)

    @command()
    @rename(given_id="id")
    async def workshop(self, inter: Interaction, given_id: str) -> None:
        """Exibe informações sobre um item da Oficina Steam.

        Args:
            given_id: O ID ou o URL de um item na oficina.
        """
        await inter.response.defer()
        try:
            item = await SteamWorkItem.from_url(given_id)

            data_field: str = dedent(f"""
                ID: **{item.id}**
                Tamanho: **{round(item.file_size / (2**20), 2)} MiB**
                Postado: **{to_timestamp(item.create_date, Timestamp.ShortDate)}**
                Atualizado: **{to_timestamp(item.update_date, Timestamp.ShortDate)}**
            """)

            stats_field: str = dedent(f"""
                👁️ {format(item.view_amount, ",")}
                📥 {format(item.sub_amount, ",")} ({format(item.sub_amount_life, ",")} no total)
                ⭐ {format(item.fav_amount, ",")} ({format(item.fav_amount_life, ",")} no total)
            """)

            embed = Embed(description=shorten(item.description, MAX_DESC_LEN),
                          title=item.title.upper(),
                          url=item.url,
                          color=COLOR_STEAM)
            embed.add_field(name="Dados", value=data_field)
            embed.add_field(name="Estatísticas", value=stats_field)
            embed.add_field(name="Tags", value=item.tags, inline=False)
            embed.set_thumbnail(url=item.preview)
            await inter.followup.send(embed=embed)

        except IdNotFound:
            embed = err_embed("Nenhum item na oficina foi encontrado.\n" +
                              "Esse comando aceita IDs de item ou sua respectiva URL.")
            await inter.followup.send(embed=embed)

        except:
            embed = err_embed("Algo deu errado.")
            await inter.followup.send(embed=embed)


class IdNotFound(Exception):
    pass


class InvalidSteamKey(Exception):
    pass


async def setup(bot: CustomBot) -> None:
    global api

    if not STEAM_KEY:
        print("The Steam key is blank. Skipping Steam commands...")
        return

    api = SteamAPI(STEAM_KEY)
    bot.tree.add_command(SteamGroup(bot))
