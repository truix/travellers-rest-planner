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

import pypdn.nrbf as _nrbf_mod

# Monkey-patch pypdn to handle new Dictionary types in game updates.
# The game added Dictionary<int,...> fields that pypdn's NRBF parser
# can't resolve (missing KeyValuePairs attribute).
#
# The dispatch table at line ~742 of nrbf.py holds a direct reference
# to the original function, so patching the class method isn't enough.
# We patch the original function object in-place via its code object.
_orig_resolve = _nrbf_mod.NRBF._resolveDictReference

def _safe_resolve_dict_ref(self, reference):
    try:
        originalObj = reference.originalObj
        if not hasattr(originalObj, 'KeyValuePairs'):
            return  # skip unsupported dictionary types
        return _orig_resolve(self, reference)
    except (AttributeError, TypeError):
        return

# Replace the class method AND rebuild the dispatch tuple
_nrbf_mod.NRBF._resolveDictReference = _safe_resolve_dict_ref
_nrbf_mod.NRBF._collectionResolvers = tuple(
    (name, _safe_resolve_dict_ref) if 'Dict' in name else (name, func)
    for name, func in _nrbf_mod.NRBF._collectionResolvers
)

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
    shop_stock: dict[int, dict[int, int]] = field(default_factory=dict)  # shop_id -> {item_id: amount}


def extract(root, slot_id: str = "", save_path: str = "", save_mtime: float = 0.0) -> GameState:
    """Extract game state from the parsed save root. Every field access is
    wrapped in try/except so a single changed/missing field doesn't crash
    the whole parser — we just get a default value for that field."""

    # Current date
    try:
        ct = root.currentTime
        season_idx = _enum_int(ct.season) or 0
        day_idx = _enum_int(ct.day) or 0
        date = GameDate(
            year=getattr(ct, "year", 1),
            season=season_idx,
            season_name=SEASON_NAMES[season_idx % 4],
            week=getattr(ct, "week", 1),
            day=day_idx,
            day_name=DAY_NAMES[day_idx % 7],
            hour=getattr(ct, "hour", 6),
            minute=getattr(ct, "min", 0),
        )
    except Exception:
        date = GameDate(1, 0, "Spring", 1, 0, "Mon", 6, 0)

    # Trends
    trends: list[TrendSet] = []
    try:
        for ts in (getattr(root, "allTrendsSave", None) or []):
            trends.append(TrendSet(
                food_ids=[int(x) for x in (_attr(ts, "foodTrends", []) or [])],
                drink_ids=[int(x) for x in (_attr(ts, "drinkTrends", []) or [])],
                ingredient_ids=[int(x) for x in (_attr(ts, "ingredientTrends", []) or [])],
            ))
    except Exception:
        pass

    # Planted crops
    crops: list[CropPlanted] = []
    counts: dict[int, int] = {}
    try:
        for c in (getattr(root, "cropSaves", None) or []):
            try:
                pos = getattr(c, "position", None)
                cp = CropPlanted(
                    crop_id=int(getattr(c, "cropID", 0)),
                    pos=(getattr(pos, "x", 0), getattr(pos, "y", 0)) if pos else (0, 0),
                    grow_stage=int(getattr(c, "growstage", 0)),
                    is_harvestable=bool(getattr(c, "isHarvestable", False)),
                    days_to_grow=int(getattr(c, "daysToGrow", 0)),
                    days_until_new_harvest=int(getattr(c, "daysUntilNewHarvest", 0)),
                    reusable_count=int(getattr(c, "reusableCount", 0)),
                    is_dead=bool(getattr(c, "isDead", False)),
                    days_planted=int(getattr(c, "daysPlanted", 0)),
                )
                crops.append(cp)
                counts[cp.crop_id] = counts.get(cp.crop_id, 0) + 1
            except Exception:
                continue
    except Exception:
        pass

    # Tavern + player name
    tavern_name = ""
    player_name = ""
    try:
        cs = getattr(root, "characterSave", None)
        if cs is not None:
            tavern_name = str(getattr(cs, "tavernName", "") or "")
            player_name = str(getattr(cs, "name", "") or "")
    except Exception:
        pass

    # Quest state
    quests_done: set[int] = set()
    try:
        for q in (getattr(root, "questsDoneSave", None) or []):
            try:
                quests_done.add(int(q))
            except Exception:
                pass
    except Exception:
        pass

    quests_active: dict[int, int] = {}
    try:
        for q in (getattr(root, "questSaves", None) or []):
            try:
                quests_active[int(getattr(q, "questID"))] = int(getattr(q, "questProgress", 0))
            except Exception:
                pass
    except Exception:
        pass

    # Unlocked recipes
    unlocked: set[int] = set()
    try:
        for r in (getattr(root, "unlockedRecipes", None) or []):
            try:
                unlocked.add(int(r))
            except Exception:
                pass
    except Exception:
        pass

    # Shop stock — what vendors are currently selling today
    shop_stock: dict[int, dict[int, int]] = {}
    try:
        for shop_save in (getattr(root, "shopsSaves", None) or []):
            try:
                sid = int(getattr(shop_save, "id", 0))
                items_save = getattr(shop_save, "itemsAmountSave", []) or []
                stock = {}
                for item_save in items_save:
                    try:
                        iid = int(getattr(item_save, "id", 0))
                        amt = int(getattr(item_save, "amount", 0))
                        if iid:
                            stock[iid] = amt
                    except Exception:
                        pass
                if stock:
                    shop_stock[sid] = stock
            except Exception:
                pass
    except Exception:
        pass

    return GameState(
        slot_id=slot_id,
        save_path=save_path,
        save_mtime=save_mtime,
        money_copper=int(getattr(root, "money", 0)),
        tavern_rep=int(getattr(root, "tavernRep", 0)),
        days_to_next_trend=int(getattr(root, "daysToNextTrend", 0)),
        current_date=date,
        trends=trends,
        unlocked_recipe_ids=unlocked,
        planted_crops=crops,
        planted_crop_counts=counts,
        tavern_name=tavern_name,
        player_name=player_name,
        quests_done=quests_done,
        quests_active=quests_active,
        shop_stock=shop_stock,
    )


def load_state(slot_id: str | None = None) -> GameState | None:
    slot = get_slot(slot_id)
    if slot is None:
        return None
    root = parse_save(slot.latest_file)
    return extract(root, slot_id=slot.slot_id, save_path=slot.latest_file, save_mtime=slot.mtime)
