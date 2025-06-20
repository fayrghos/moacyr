"""Image-related commands."""

from discord import Attachment, Interaction, File, Embed, Message
from discord.app_commands import Group, CheckFailure, command, context_menu
from requests.exceptions import MissingSchema
from typing import Any, Optional, cast
from PIL import Image
from pathlib import Path
from src.bot import CustomBot
from src.config import BotConfig
from tempfile import _TemporaryFileWrapper, NamedTemporaryFile
from io import BytesIO
from os import unlink
from urllib.parse import quote

import textwrap
import requests
import src.utils as utils


cfg = BotConfig()
cfg.parse_section("Images", {
    "enabled": "yes",
    "maxscale": 2.0,
    "minscale": 0.5,
})

MAX_FILESIZE = 1e7

IMGS_ENABLED = cfg.getboolean("Images", "enabled")
MAX_SCALE = cfg.getfloat("Images", "maxscale")
MIN_SCALE = cfg.getfloat("Images", "minscale")

allowed_conts: tuple[str, ...] = (
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/webp",
)


class RequestedFile:
    """A handler for file downloading."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.response = requests.get(self.url)

        if self.response.status_code == 200:
            self.content = self.response.content
            self.content_type = self.response.headers.get("Content-Type")
            self.size = len(self.content)


class FileSizeExceeded(Exception):
    pass


class ImageTooSmall(Exception):
    pass


class ImageTooBig(Exception):
    pass


TITLE_LANGS: dict[str, str] = {
    "english": ":flag_gb:",
    "native": ":flag_jp:",
    "romaji": ":pencil:",
}


async def call_anime_api(img_url: str) -> Embed:
    """Returns a Discord embed containing info about an anime frame."""
    response = requests.get(f"https://api.trace.moe/search?url={img_url}&anilistInfo")

    if response.status_code == 200:
        data: dict[str, Any] = response.json()["result"][0]

        if data["anilist"]["isAdult"]:
            return utils.error_embed("O melhor palpite encontrou conteúdo adulto.")

        embed = Embed(
            title="Melhor Palpite",
            description=f"[Ver informações do anime no AniList](<https://anilist.co/anime/{data['anilist']['id']}>)",
            color=utils.COLOR_DEF
        )

        titles = data["anilist"]["title"]
        name_text = "\n".join(f"{flag} {title}" for lang, flag in TITLE_LANGS.items() if (title := titles[lang]))
        embed.add_field(name="Nome", value=name_text)

        minutes, seconds = divmod(int(data["from"]), 60)
        info_text = textwrap.dedent(f"""\
            Episódio: **{data.get("episode", "N/A")}**
            Minuto: **{minutes:02d}:{seconds:02d}**
            Similaridade: **{round(data["similarity"] * 100, 1)}%**
        """)
        embed.add_field(name="Dados", value=info_text)

        embed.set_image(url=data["image"] + "&size=l")

    elif response.status_code == 400:
        embed = utils.error_embed("A API não conseguiu decodificar a imagem enviada.",
                                  title="Erro na Decodificação")

    elif response.status_code == 404:
        embed = utils.error_embed("A API não conseguiu coletar imagens do URL enviado.",
                                  title="Erro na Solicitação")

    else:
        embed = utils.error_embed("Algo deu errado.")

    return embed


def save_gif(tmpfile: _TemporaryFileWrapper, imgbytes: BytesIO, scale: Optional[float] = None) -> Path:
    """Converts a image BytesIO to a GIF then saves it."""
    with Image.open(imgbytes) as file:
        if scale:
            size = file.size
            newsize = (int(size[0] * scale), int(size[1] * scale))

            if min(newsize) < 64:
                raise ImageTooSmall
            if max(newsize) > 2048:
                raise ImageTooBig

            file = file.resize(newsize)
        file.save(tmpfile.name, "GIF")
    return Path(tmpfile.name)

class ImgGroup(Group):

    def __init__(self, bot: CustomBot) -> None:
        super().__init__(name="image",
                         description="Comandos relacionados a interações com imagens.")
        self.bot = bot

    async def interaction_check(self, inter: Interaction) -> bool:
        return IMGS_ENABLED

    async def on_error(self, inter: Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure):
            embed = utils.error_embed("Os comandos de imagem estão desativados no momento")
            await inter.response.send_message(embed=embed)

    @command(
        name="make-gif",
    )
    async def makegif(self,
                      inter: Interaction,
                      url: Optional[str],
                      file: Optional[Attachment],
                      scale: float = 1.0) -> None:
        """Transforma uma imagem em um GIF estático.

        Args:
            url: O URL de alguma imagem da internet.
            file: Um arquivo do seu dispositivo.
            scale: A escala para redimensionar o GIF. Opcional.
        """
        await inter.response.defer()

        if not file and not url:
            embed = utils.error_embed("Nenhum parâmetro foi fornecido.")
            await inter.followup.send(embed=embed)
            return

        if scale > MAX_SCALE or scale < MIN_SCALE:
            embed = utils.error_embed(f"A escala só pode ir de {MIN_SCALE} até {MAX_SCALE}.")
            await inter.followup.send(embed=embed)
            return

        try:
            # Casting because, for some reason, the type checker says that both file and url can be null
            image = file or RequestedFile(cast(str, url))
            if image.size > MAX_FILESIZE:
                raise FileSizeExceeded

            elif image.content_type == "image/gif" or image.url.startswith("https://tenor.com/"):
                embed = utils.error_embed("Bem... isso já parece ser um GIF.")
                await inter.followup.send(embed=embed)
                return

            if image.content_type in allowed_conts:
                img_bytes = BytesIO(await image.read()) if isinstance(image, Attachment) else BytesIO(image.content)
                tmpfile = NamedTemporaryFile(suffix=".gif", delete=False)
                path = save_gif(tmpfile, img_bytes, scale)

                await inter.followup.send(file=File(path))
                tmpfile.close()
                unlink(path)

            else:
                embed = utils.error_embed("Formato de arquivo incompatível.")
                await inter.followup.send(embed=embed)

        except FileSizeExceeded:
            embed = utils.error_embed("Este arquivo é pesado demais.")
            await inter.followup.send(embed=embed)

        except ImageTooBig:
            embed = utils.error_embed("A imagem resultante é grande demais.")
            await inter.followup.send(embed=embed)

        except ImageTooSmall:
            embed = utils.error_embed("A imagem resultante é pequena demais.")
            await inter.followup.send(embed=embed)

        except MissingSchema:
            embed = utils.error_embed("Insira um URL válido.")
            await inter.followup.send(embed=embed)

        except:
            embed = utils.error_embed("Algo deu errado.")
            await inter.followup.send(embed=embed)

    @command(
        name="find-anime",
    )
    async def findanime(self,
                        inter: Interaction,
                        url: Optional[str],
                        file: Optional[Attachment]) -> None:
        """Descubra o nome de um anime usando um frame dele.

        Args:
            url: O URL de alguma imagem da internet.
            file: Um arquivo do seu dispositivo.
        """
        await inter.response.defer()

        if not file and not url:
            embed = utils.error_embed("Nenhum parâmetro foi fornecido.")
            await inter.followup.send(embed=embed)
            return

        elif url:
            if url.startswith("http:") or url.startswith("https:"):
                embed = await call_anime_api(url)
                await inter.followup.send(embed=embed)

        elif file:
            embed = await call_anime_api(quote(file.url))
            await inter.followup.send(embed=embed)


# For some reason, this doesn't work inside the image group
@context_menu(name="Encontrar Anime")
async def findanime_menu(inter: Interaction, message: Message) -> None:
    await inter.response.defer()

    image = utils.get_image_from_message(message, ignore_url=True)
    if image and not image.startswith("https://api.trace.moe"):
        embed = await call_anime_api(image)
        await inter.followup.send(embed=embed)

    else:
        embed = utils.error_embed("Nenhuma imagem foi encontrada na mensagem.")
        await inter.followup.send(embed=embed)


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(ImgGroup(bot))
    bot.tree.add_command(findanime_menu)
