"""A handle for config parsing."""

from configparser import ConfigParser
from pathlib import Path


CONFIG_PATH = Path("settings.ini")


class BotConfig(ConfigParser):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.read(CONFIG_PATH)

    def parse_section(self, name: str, def_values: dict) -> None:
        """Adds a section into the .ini if it not exists."""
        if not self.has_section(name):
            self[name] = def_values

        for key, value in def_values.items():
            if not self.has_option(name, key):
                self[name][key] = str(value)

        with open(CONFIG_PATH, "w") as file:
            self.write(file)
