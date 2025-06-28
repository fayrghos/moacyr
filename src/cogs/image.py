"""Image-related commands."""

from discord import Attachment, Interaction, File, Embed, Message
from discord.app_commands import Group, CheckFailure, command, context_menu
from httpx import UnsupportedProtocol
from typing import Any, Optional, Self
from PIL import Image
from pathlib import Path
from src.bot import CustomBot
from src.config import BotConfig
from tempfile import _TemporaryFileWrapper, NamedTemporaryFile
from io import BytesIO
from os import unlink
from urllib.parse import quote

import httpx
import textwrap
import src.utils as utils


cfg = BotConfig()
cfg.parse_section("Images", {
    "enabled": "yes",
    "maxscale": 3.0,
    "minscale": 0.2,
})

MAX_FILESIZE = 1e7
IMGS_ENABLED = cfg.getboolean("Images", "enabled")
MAX_SCALE = cfg.getfloat("Images", "maxscale")
MIN_SCALE = cfg.getfloat("Images", "minscale")

ALLOWED_MIMES: tuple[str, ...] = (
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/webp",
)

TITLE_LANGS: dict[str, str] = {
    "english": ":flag_gb:",
    "native": ":flag_jp:",
    "romaji": ":pencil:",
}


class ImageHandler:
    """A wrapper for padronizing Attachments and pure URLs."""

    @classmethod
    async def from_attachment(cls, attach: Attachment) -> Self:
        return cls(
            url=attach.url,
            content=await attach.read(),
            mime=attach.content_type,
            size=attach.size
        )

    @classmethod
    async def from_url(cls, url: str) -> Self:
        async with httpx.AsyncClient() as client:
            # Just for checking the content size first
            head = await client.head(url)
            if int(head.headers.get("Content-Length", 0)) > MAX_FILESIZE:
                raise FileSizeExceeded

            # Actual request
            response = await client.get(url)

        if response.status_code == 200:
            return cls(
                url=url,
                content=response.content,
                mime=response.headers.get("Content-Type"),
                size=len(response.content)
            )
        raise ValueError("For some reason, the image is None.")

    def __init__(self,
                 url: str,
                 content: bytes,
                 mime: Optional[str],
                 size: int) -> None:
        self.url = url
        self.content = BytesIO(content)
        self.mime = mime or "application/octet-stream"
        self.size = size

        if self.size > MAX_FILESIZE:
            raise FileSizeExceeded


async def call_anime_api(img_url: str) -> Embed:
    """Returns a Discord embed containing info about an anime frame."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.trace.moe/search?url={img_url}&anilistInfo")

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
        return embed

    else:
        match response.status_code:
            case 400:
                return utils.error_embed("A API não foi capaz de decodificar a imagem enviada.")

            case 403 | 404:
                return utils.error_embed("A API não conseguiu extrair imagens do URL enviado.")

            case 405:
                return utils.error_embed("A API relatou que o método HTTP usado foi incorreto.")

            case 500:
                return utils.error_embed("O servidor da API relatou um erro interno.")

            case 503:
                return utils.error_embed("O banco de dados da API não está respondendo.")

            case 504:
                return utils.error_embed("O servidor da API está sobrecarregado.")

            case _:
                return utils.error_embed("Algo deu errado.")


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


def normalize_mime(mime: str) -> str:
    """Normalize MIME types. It also removes semicolons because HTML files are goofy."""
    return mime.split("/")[-1].split(";")[0].upper()


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
            embed = utils.error_embed("Você precisa fornecer pelo menos um URL ou Arquivo.")
            await inter.followup.send(embed=embed)
            return

        if scale > MAX_SCALE or scale < MIN_SCALE:
            embed = utils.error_embed(f"A escala só pode ir de {MIN_SCALE}x até {MAX_SCALE}x.")
            await inter.followup.send(embed=embed)
            return

        image: Optional[ImageHandler] = None

        try:
            if file:
                image = await ImageHandler.from_attachment(file)
            elif url:
                image = await ImageHandler.from_url(url)
            assert image

            if image.mime == "image/gif" or image.url.startswith("https://tenor.com/"):
                embed = utils.error_embed("Bem... isso já parece ser um GIF.")
                await inter.followup.send(embed=embed)
                return

            elif image.mime not in ALLOWED_MIMES:
                embed = utils.error_embed(textwrap.dedent(f"""\
                    O seu arquivo é do tipo inválido \"**{normalize_mime(image.mime)}**\".

                    Tipos suportados:
                    {"\n".join(list(map(lambda x: f"• **{normalize_mime(x)}**", ALLOWED_MIMES)))}
                """))
                await inter.followup.send(embed=embed)
                return

            temp_file = NamedTemporaryFile(suffix=".gif", delete=False)
            path = save_gif(temp_file, image.content, scale)

            await inter.followup.send(file=File(path))
            temp_file.close()
            unlink(path)

        except FileSizeExceeded:
            embed = utils.error_embed("O arquivo enviado é pesado demais para ser processado.")
            await inter.followup.send(embed=embed)

        except ImageTooBig:
            embed = utils.error_embed("A imagem redimensionada é grande demais.")
            await inter.followup.send(embed=embed)

        except ImageTooSmall:
            embed = utils.error_embed("A imagem redimensionada é pequena demais.")
            await inter.followup.send(embed=embed)

        except UnsupportedProtocol:
            embed = utils.error_embed("O URL enviado não é válido.")
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


class FileSizeExceeded(Exception):
    pass


class ImageTooSmall(Exception):
    pass


class ImageTooBig(Exception):
    pass


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(ImgGroup(bot))
    bot.tree.add_command(findanime_menu)
