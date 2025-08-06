"""Image-related commands."""

import textwrap
from io import BytesIO
from os import unlink
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Any, Optional, Self

import httpx
from discord import Attachment, Embed, File, Interaction
from discord.app_commands import CheckFailure, Group, command
from httpx import UnsupportedProtocol
from PIL import Image

import src.utils as utils
from src.bot import CustomBot
from src.config import BotConfig


cfg = BotConfig()
cfg.parse_section("Images", {
    "enabled": "yes",
    "maxscale": 3.0,
    "minscale": 0.2,
})

IMGS_ENABLED = cfg.getboolean("Images", "enabled")

MAX_FILESIZE = 1e7

MAX_SCALE = 3.0
MIN_SCALE = 0.2

ALLOWED_MIMES: tuple[str, ...] = (
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/webp",
    "image/gif"
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
        if attach.size > MAX_FILESIZE:
            raise FileSizeExceeded

        return cls(
            url=attach.url,
            content=await attach.read(),
            mime=attach.content_type,
            size=attach.size
        )

    @classmethod
    async def from_url(cls, url: str) -> Self:
        if url.startswith("https://tenor.com/") and not url.endswith(".gif"):
            url += ".gif"

        async with httpx.AsyncClient() as client:
            # Just for checking the content first
            head = await client.head(url, follow_redirects=True)
            if int(head.headers.get("Content-Length", 0)) > MAX_FILESIZE:
                raise FileSizeExceeded

            # Actual request
            response = await client.get(head.url)

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

        if self.mime not in ALLOWED_MIMES:
            raise NotAllowedMime(self.mime)


async def call_anime_api(image: ImageHandler) -> Embed:
    """Returns a Discord embed containing info about an anime frame."""
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.trace.moe/search?anilistInfo",
                                     files={"image": image.content})

    if response.status_code == 200:
        data: dict[str, Any] = response.json()["result"][0]

        if data["anilist"]["isAdult"]:
            return utils.error_embed("O melhor palpite não pode ser exibido pois encontrou conteúdo adulto.")

        similarity: int = round(data["similarity"] * 100, 1)
        desc: str = f"[Clique para conhecer o anime.](<https://anilist.co/anime/{data["anilist"]["id"]}>)"

        if similarity < 90:
            desc += "\n\n⚠️ Similaridades abaixo de **90%** geralmente exibem erros."

        embed = Embed(
            title="Melhor Palpite",
            description=desc,
            color=utils.COLOR_DEF
        )

        titles = data["anilist"]["title"]
        titles_text = "\n".join(f"{flag} {title}" for lang, flag in TITLE_LANGS.items() if (title := titles[lang]))
        embed.add_field(name="Nome", value=titles_text)

        minutes, seconds = divmod(int(data["from"]), 60)
        info_text = textwrap.dedent(f"""\
            Episódio: **{data.get("episode", "N/A")}**
            Minuto: **{minutes:02d}:{seconds:02d}**
            Similaridade: **{similarity}%**
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
                return utils.error_embed("Ocorreu um erro HTTP com status não catalogado.")


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


def handle_shared_errors(error: Exception) -> Embed:
    """Handles common errors that can occur in image commands."""
    match error:
        case FileSizeExceeded():
            return utils.error_embed("O arquivo enviado é pesado demais para ser processado.")

        case ImageTooBig():
            return utils.error_embed("A imagem resultante é grande demais.")

        case ImageTooSmall():
            return utils.error_embed("A imagem resultante é pequena demais.")

        case UnsupportedProtocol():
            return utils.error_embed("O URL enviado não é válido.")

        case NotAllowedMime() as err:
            return utils.error_embed(textwrap.dedent(f"""\
                O seu arquivo é do tipo inválido \"**{normalize_mime(err.mime)}**\".

                Tipos suportados:
                {"\n".join(list(map(lambda x: f"• **{normalize_mime(x)}**", ALLOWED_MIMES)))}
            """))
        case _:
            return utils.error_embed("Algo deu errado.")


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

            if image.mime == "image/gif":
                embed = utils.error_embed("Bem... isso já parece ser um GIF.")
                await inter.followup.send(embed=embed)
                return

            temp_file = NamedTemporaryFile(suffix=".gif", delete=False)
            path = save_gif(temp_file, image.content, scale)

            await inter.followup.send(file=File(path))
            temp_file.close()
            unlink(path)

        except Exception as err:
            await inter.followup.send(embed=handle_shared_errors(err))

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
            embed = utils.error_embed("Você precisa fornecer pelo menos um URL ou Arquivo.")
            await inter.followup.send(embed=embed)
            return

        try:
            if file:
                embed = await call_anime_api(await ImageHandler.from_attachment(file))
                await inter.followup.send(embed=embed)

            elif url:
                embed = await call_anime_api(await ImageHandler.from_url(url))
                await inter.followup.send(embed=embed)

        except Exception as err:
            await inter.followup.send(embed=handle_shared_errors(err))


class FileSizeExceeded(Exception):
    pass


class ImageTooSmall(Exception):
    pass


class ImageTooBig(Exception):
    pass


class NotAllowedMime(Exception):
    def __init__(self, mime: str) -> None:
        self.mime = mime


async def setup(bot: CustomBot) -> None:
    bot.tree.add_command(ImgGroup(bot))
