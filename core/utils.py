"""Multipurpose variables and functions."""

from enum import Enum

from discord import Colour, Embed

COLOR_DEF = Colour.from_rgb(147, 112, 219)
COLOR_ERR = Colour.from_rgb(225, 80, 80)
COLOR_CRIT = Colour.from_rgb(45, 25, 25)
COLOR_DEBUG = Colour.from_rgb(25, 25, 25)

MAX_COMPLETE_OPTS = 25


class Timestamp(Enum):
    """Discord timestamp converters."""

    Default = ""
    ShortTime = ":t"
    LongTime = ":T"
    ShortDate = ":d"
    LongDate = ":D"
    ShortDateTime = ":f"
    LongDateTime = ":F"
    Relative = ":R"


class Genbed(Embed):
    """Abreviation for generic embeds"""

    def __init__(self, desc: str, *args, **kwargs) -> None:
        super().__init__(
            *args,
            description=desc,
            **kwargs,
            color=COLOR_DEF,
        )


class Errbed(Embed):
    """Abreviation for generic embeds"""

    def __init__(self, desc: str, *args, crit: bool = False, **kwargs) -> None:
        super().__init__(
            *args,
            description=desc,
            color=COLOR_ERR if not crit else COLOR_CRIT,
            **kwargs,
        )


class MoacyrException(Exception):
    """Intentional exceptions."""

    def embed(self) -> Errbed:
        return Errbed(str(self))


def stampify(time: int, stamp: Timestamp = Timestamp.Default) -> str:
    """Transform an integer in a valid Discord timestamp."""
    return f"<t:{time}{stamp.value}>" if time else ""


def cooler_shorten(text: str, max_width: int) -> str:
    """An alternative to textwrap.shorten that actually breaks words."""
    text = " ".join(text.split())
    text_len: int = len(text)

    if text_len <= max_width:
        return text

    place: str = f" <+{text_len - max_width}>"
    place_len: int = len(place)

    if max_width <= place_len:
        raise ValueError("The placeholder is hiding the entire text.")

    return text[: max_width - place_len] + place
