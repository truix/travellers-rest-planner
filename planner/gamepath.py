"""Locate the Travellers Rest install directory.

Resolution order:
  1. $TR_GAME_DIR environment variable (full path to ...TravellersRest_Data)
  2. Steam's libraryfolders.vdf parsed for the game's library
  3. Common Steam install paths on Windows / macOS / Linux
  4. Every drive letter on Windows scanned for "SteamLibrary/steamapps/common/Travellers Rest"

Always returns a path that exists, or raises FileNotFoundError with a helpful
message describing how to set TR_GAME_DIR.
"""
from __future__ import annotations

import os
import re
import string
import sys
from functools import lru_cache
from pathlib import Path

GAME_FOLDER  = "Travellers Rest"
DATA_SUBPATH = os.path.join("Windows", "TravellersRest_Data")
SENTINEL     = "globalgamemanagers"  # always present in TravellersRest_Data


def _is_valid_data_dir(p: Path) -> bool:
    return p.is_dir() and (p / SENTINEL).exists()


def _candidates_from_env() -> list[Path]:
    val = os.environ.get("TR_GAME_DIR")
    if not val:
        return []
    p = Path(val).expanduser().resolve()
    # Allow either the data dir directly, or the install root
    return [p, p / DATA_SUBPATH, p / GAME_FOLDER / DATA_SUBPATH]


def _candidates_from_libraryfolders() -> list[Path]:
    """Parse Steam's libraryfolders.vdf to find every Steam library on disk."""
    out: list[Path] = []
    vdf_paths = []

    if sys.platform == "win32":
        for env in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(env)
            if base:
                vdf_paths.append(Path(base) / "Steam" / "steamapps" / "libraryfolders.vdf")
    elif sys.platform == "darwin":
        vdf_paths.append(Path.home() / "Library/Application Support/Steam/steamapps/libraryfolders.vdf")
    else:
        for sub in (".steam/steam", ".local/share/Steam", ".steam/root"):
            vdf_paths.append(Path.home() / sub / "steamapps/libraryfolders.vdf")

    for vdf in vdf_paths:
        if not vdf.is_file():
            continue
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Match every "path" "..." line — works on both old and new vdf formats
        for m in re.finditer(r'"path"\s*"([^"]+)"', text):
            lib = Path(m.group(1).replace("\\\\", "\\"))
            out.append(lib / "steamapps/common" / GAME_FOLDER / DATA_SUBPATH)
    return out


def _candidates_from_default_locations() -> list[Path]:
    out: list[Path] = []
    if sys.platform == "win32":
        for env in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(env)
            if base:
                out.append(Path(base) / "Steam/steamapps/common" / GAME_FOLDER / DATA_SUBPATH)
        # Walk every drive letter for SteamLibrary/...
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:/")
            if not root.exists():
                continue
            for steamlib in (root / "SteamLibrary",
                             root / "Games/SteamLibrary",
                             root / "Steam"):
                out.append(steamlib / "steamapps/common" / GAME_FOLDER / DATA_SUBPATH)
    elif sys.platform == "darwin":
        out.append(Path.home() / "Library/Application Support/Steam/steamapps/common"
                   / GAME_FOLDER / DATA_SUBPATH)
    else:
        for sub in (".steam/steam", ".local/share/Steam", ".steam/root"):
            out.append(Path.home() / sub / "steamapps/common" / GAME_FOLDER / DATA_SUBPATH)
    return out


@lru_cache(maxsize=1)
def find_game_data_dir() -> str:
    """Return the absolute path to TravellersRest_Data, or raise."""
    seen = []
    for source in (_candidates_from_env(),
                   _candidates_from_libraryfolders(),
                   _candidates_from_default_locations()):
        for cand in source:
            if cand in seen:
                continue
            seen.add(cand) if isinstance(seen, set) else seen.append(cand)
            if _is_valid_data_dir(cand):
                return str(cand)

    msg = (
        "Could not find Travellers Rest install. Set the TR_GAME_DIR environment\n"
        "variable to the path of the TravellersRest_Data folder, e.g.:\n"
        "  Windows:  set TR_GAME_DIR=F:\\SteamLibrary\\steamapps\\common\\Travellers Rest\\Windows\\TravellersRest_Data\n"
        "  macOS:    export TR_GAME_DIR=\"$HOME/Library/Application Support/Steam/steamapps/common/Travellers Rest/Windows/TravellersRest_Data\"\n"
        "  Linux:    export TR_GAME_DIR=\"$HOME/.steam/steam/steamapps/common/Travellers Rest/Windows/TravellersRest_Data\"\n"
        f"Tried {len(seen)} candidate path(s)."
    )
    raise FileNotFoundError(msg)


def managed_dir() -> str:
    """Path to the Managed/ folder (where Assembly-CSharp.dll lives)."""
    return os.path.join(find_game_data_dir(), "Managed")
