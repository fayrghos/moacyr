"""Outdated pip packages checking."""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


REQ_FILE_PATH = Path("requirements.txt")


def is_outdated(cur_version: str, min_version: str) -> bool:
    """Compares two versions and returns if `cur` is older than `min`."""
    return [int(seg) for seg in cur_version.split(".")] < [int(seg) for seg in min_version.split(".")]


def check_packages() -> None:
    """Checks if environment packages are older than requirements.txt ones."""
    with open(REQ_FILE_PATH, "r") as file:
        lines: list[str] = file.readlines()

        for line in lines:
            match = re.search(r"(.*)==([0-9]+.[0-9]+.[0-9]+)", line)
            if not match:
                continue

            package, txt_version = match.groups()
            try:
                if not is_outdated(version(package), txt_version):
                    continue

            except PackageNotFoundError:
                print(f"Package '{package}' is missing from the environment. Ignoring...")
                continue

            print("Some installed pip packages are outdated.")
            print("Please, reinstall requirements.txt to proceed.")
            exit()
