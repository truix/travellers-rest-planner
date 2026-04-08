"""Save file discovery, parsing, and extraction.

Travellers Rest stores saves under
   %USERPROFILE%/AppData/LocalLow/Louqou/TravellersRest/GameSaves/

Each save slot is a folder named like `File_1`, `File_2`, ... containing one or
more `SaveFile-<date>.save` files (the most recent is the live one) plus a
`Save.backup`. Saves are .NET BinaryFormatter streams of the SaveData class
(see dumps/Save.cs:423 — `bf.Serialize(tempFile, data)`).
"""
from __future__ import annotations

import glob
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pypdn.nrbf import NRBF


SEASON_NAMES = ["Spring", "Summer", "Autumn", "Winter"]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def saves_root() -> str:
    return os.path.expandvars(
        r"%USERPROFILE%\AppData\LocalLow\Louqou\TravellersRest\GameSaves"
    )


@dataclass
class SaveSlot:
    slot_id: str           # e.g. "File_1"
    folder: str            # absolute path
    latest_file: str       # path to most recent .save
    mtime: float           # mtime of latest_file
    label: str             # human label for the dropdown


def discover_slots(root: str | None = None) -> list[SaveSlot]:
    root = root or saves_root()
    if not os.path.isdir(root):
        return []
    slots: list[SaveSlot] = []
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if not os.path.isdir(full) or not entry.startswith("File_"):
            continue
        saves = glob.glob(os.path.join(full, "SaveFile*.save"))
        if not saves:
            continue
        latest = max(saves, key=os.path.getmtime)
        mt = os.path.getmtime(latest)
        when = datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M")
        slots.append(SaveSlot(
            slot_id=entry,
            folder=full,
            latest_file=latest,
            mtime=mt,
            label=f"{entry}  ·  {when}",
        ))
    # newest slot first
    slots.sort(key=lambda s: s.mtime, reverse=True)
    return slots


def get_slot(slot_id: str | None = None) -> SaveSlot | None:
    slots = discover_slots()
    if not slots:
        return None
    if slot_id:
        for s in slots:
            if s.slot_id == slot_id:
                return s
    return slots[0]  # default = newest


def latest_save_in_folder(folder: str) -> str | None:
    saves = glob.glob(os.path.join(folder, "SaveFile*.save"))
    return max(saves, key=os.path.getmtime) if saves else None


def parse_save(path: str) -> Any:
    """Return the deserialized SaveData root object."""
    n = NRBF(filename=path)
    n.resolveReferences()
    return n.getRoot()


# ---------- Extraction --------------------------------------------------------

def _enum_int(v) -> int | None:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    return getattr(v, "value__", None)


def _attr(o, name, default=None):
    return getattr(o, name, default)


@dataclass
class GameDate:
    year: int
    season: int
    season_name: str
    week: int   # 1..4 within season
    day: int    # 0..6
    day_name: str
    hour: int
    minute: int

    def __str__(self):
        return f"Y{self.year} {self.season_name} W{self.week} {self.day_name} {self.hour:02d}:{self.minute:02d}"


@dataclass
class TrendSet:
    food_ids: list[int]
    drink_ids: list[int]
    ingredient_ids: list[int]


@dataclass
class CropPlanted:
    crop_id: int
    pos: tuple[float, float]
    grow_stage: int
    is_harvestable: bool
    days_to_grow: int
    days_until_new_harvest: int
    reusable_count: int
    is_dead: bool
    days_planted: int


@dataclass
class GameState:
    slot_id: str
    save_path: str
    save_mtime: float
    money_copper: int
    tavern_rep: int
    days_to_next_trend: int
    current_date: GameDate
    trends: list[TrendSet]            # 4 weeks; index 0 = current
    unlocked_recipe_ids: set[int]
    planted_crops: list[CropPlanted]
    planted_crop_counts: dict[int, int]   # cropID -> count
    tavern_name: str = ""
    player_name: str = ""
    quests_done: set[int] = field(default_factory=set)
    quests_active: dict[int, int] = field(default_factory=dict)  # qid -> progress


def extract(root, slot_id: str = "", save_path: str = "", save_mtime: float = 0.0) -> GameState:
    ct = root.currentTime
    season_idx = _enum_int(ct.season) or 0
    day_idx = _enum_int(ct.day) or 0
    date = GameDate(
        year=ct.year,
        season=season_idx,
        season_name=SEASON_NAMES[season_idx % 4],
        week=ct.week,
        day=day_idx,
        day_name=DAY_NAMES[day_idx % 7],
        hour=ct.hour,
        minute=ct.min,
    )

    trends: list[TrendSet] = []
    for ts in (root.allTrendsSave or []):
        trends.append(TrendSet(
            food_ids=list(_attr(ts, "foodTrends", []) or []),
            drink_ids=list(_attr(ts, "drinkTrends", []) or []),
            ingredient_ids=list(_attr(ts, "ingredientTrends", []) or []),
        ))

    crops: list[CropPlanted] = []
    counts: dict[int, int] = {}
    for c in (root.cropSaves or []):
        cp = CropPlanted(
            crop_id=c.cropID,
            pos=(c.position.x, c.position.y),
            grow_stage=c.growstage,
            is_harvestable=bool(c.isHarvestable),
            days_to_grow=c.daysToGrow,
            days_until_new_harvest=c.daysUntilNewHarvest,
            reusable_count=c.reusableCount,
            is_dead=bool(c.isDead),
            days_planted=c.daysPlanted,
        )
        crops.append(cp)
        counts[cp.crop_id] = counts.get(cp.crop_id, 0) + 1

    # tavern + player name from characterSave
    tavern_name = ""
    player_name = ""
    cs = getattr(root, "characterSave", None)
    if cs is not None:
        tavern_name = getattr(cs, "tavernName", "") or ""
        player_name = getattr(cs, "name", "") or ""

    # quest state
    quests_done: set[int] = set()
    for q in (getattr(root, "questsDoneSave", None) or []):
        try:
            quests_done.add(int(q))
        except Exception:
            pass
    quests_active: dict[int, int] = {}
    for q in (getattr(root, "questSaves", None) or []):
        try:
            quests_active[int(getattr(q, "questID"))] = int(getattr(q, "questProgress", 0))
        except Exception:
            pass

    return GameState(
        slot_id=slot_id,
        save_path=save_path,
        save_mtime=save_mtime,
        money_copper=int(root.money),
        tavern_rep=int(root.tavernRep),
        days_to_next_trend=int(root.daysToNextTrend),
        current_date=date,
        trends=trends,
        unlocked_recipe_ids=set(int(r) for r in (root.unlockedRecipes or [])),
        planted_crops=crops,
        planted_crop_counts=counts,
        tavern_name=tavern_name,
        player_name=player_name,
        quests_done=quests_done,
        quests_active=quests_active,
    )


def load_state(slot_id: str | None = None) -> GameState | None:
    slot = get_slot(slot_id)
    if slot is None:
        return None
    root = parse_save(slot.latest_file)
    return extract(root, slot_id=slot.slot_id, save_path=slot.latest_file, save_mtime=slot.mtime)
