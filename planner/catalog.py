"""Static game catalog: crops, recipes, items, foods.

Loaded once from the JSON dumps under dumps/mono/ and indexed for fast lookup
by item-id (the human-numbered Item.id, NOT the Unity path_id).

This is the bridge between save-file references (which use item.id) and
our extracted data.
"""
from __future__ import annotations

import csv
import glob
import json
import os
from dataclasses import dataclass, field
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONO = os.path.join(ROOT, "dumps", "mono")
DATA = os.path.join(ROOT, "data")

# Season flag bits (from CropSeason enum)
SPRING, SUMMER, AUTUMN, WINTER = 1, 2, 4, 8
SEASON_BITS = [SPRING, SUMMER, AUTUMN, WINTER]


@dataclass
class Crop:
    crop_id: int                  # Crop.id
    name: str
    name_id: str
    seed_path_id: int             # PathID of the seed Item
    seed_item_id: int | None      # Item.id of the seed (resolved later)
    available_seasons: int        # bitmask
    best_seasons: int             # bitmask
    days_to_grow: int
    reusable: bool
    days_until_new_harvest: int
    amount_best_season: int
    harvest_path_id: int          # PathID of harvested item
    harvest_item_id: int | None
    harvest_amount: int


@dataclass
class Recipe:
    recipe_id: int
    name: str
    group: int                    # 0=Material 1=Food 2=Drink
    active: bool
    output_path_id: int
    output_item_id: int | None
    output_qty: int
    output_sell_copper: int
    ingredient_buy_copper: int
    profit_per_craft: int
    profit_per_hour: float
    fuel: int
    time_hours: float
    ingredients: list[tuple[int, int]]   # list of (item_id, amount) for resolved items only
    raw_ingredients: list[dict]          # full list incl. groups: {path_id, mod_path_id, amount}


@dataclass
class Item:
    item_id: int                  # Item.id (the small human number)
    path_id: int                  # Unity PathID
    name: str
    name_id: str
    buy_copper: int
    sell_copper: int
    is_food: bool
    food_type: int | None
    contains_alcohol: bool
    has_to_be_aged_meal: bool   # cheese, ham, etc. — items that age into a "meal"
    excluded_from_trends: bool


@dataclass
class IngredientGroup:
    """A category like 'Pale Malt' that recipes can require, with the list of
    specific (item, modifier) pairs that can fulfill it."""
    group_id: int                            # negative ids like -36
    path_id: int
    name: str                                # raw asset name
    name_id: str
    possible_items: list[tuple[int, int]]    # list of (item_path_id, mod_path_id_or_0)


@dataclass
class Shop:
    shop_id: int
    name: str               # vendor name (e.g. "Wilson", "Lia")
    shop_type: int
    items: list[dict]       # raw shopItems entries (item_pid, weight, min, max, unlimited)


@dataclass
class Talent:
    talent_id: int
    name: str
    name_id: str
    description: str
    raw: dict               # everything else for the UI


@dataclass
class FishKind:
    fish_id: int
    name: str
    name_id: str
    raw: dict


@dataclass
class BushHarvest:
    bush_id: int
    name: str
    raw: dict


@dataclass
class Quest:
    quest_id: int
    name_id: str
    description: str
    required_amount: int
    reward: dict | None
    recipes_unlocked: list[int]   # path_ids
    linked_quests: list[int]
    only_on_halloween: bool
    only_on_christmas: bool
    is_repeatable: bool
    raw: dict


@dataclass
class ReputationMilestone:
    rep_id: int
    name: str
    name_id: str
    raw: dict


@dataclass
class PerkLine:
    """A row in the player perks tree (PerksDatabase.playerPerksLines)."""
    perk_id: int
    name: str
    description: str
    perk_tree: str          # category like "Recursos", "Cocina"
    raw: dict


@dataclass
class Catalog:
    crops_by_id: dict[int, Crop] = field(default_factory=dict)
    crops_by_harvest_item_id: dict[int, Crop] = field(default_factory=dict)
    recipes_by_id: dict[int, Recipe] = field(default_factory=dict)
    recipes_by_output_item_id: dict[int, list[Recipe]] = field(default_factory=dict)
    items_by_id: dict[int, Item] = field(default_factory=dict)
    items_by_path_id: dict[int, Item] = field(default_factory=dict)
    groups_by_path_id: dict[int, IngredientGroup] = field(default_factory=dict)
    shops: list[Shop] = field(default_factory=list)
    talents: list[Talent] = field(default_factory=list)
    fishes: list[FishKind] = field(default_factory=list)
    bushes: list[BushHarvest] = field(default_factory=list)
    quests: list[Quest] = field(default_factory=list)
    reputations: list[ReputationMilestone] = field(default_factory=list)
    player_perks: list[PerkLine] = field(default_factory=list)
    employee_perks: list[PerkLine] = field(default_factory=list)


def _load_dir(name: str) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for p in glob.glob(os.path.join(MONO, name, "*.json")):
        try:
            with open(p, encoding="utf8") as f:
                d = json.load(f)
        except Exception:
            continue
        try:
            pid = int(os.path.basename(p).rsplit("__", 1)[1].split(".")[0])
        except Exception:
            continue
        d["__path_id"] = pid
        out[pid] = d
    return out


def _price(p) -> int:
    if not p:
        return 0
    # Confirmed in Price.cs:467 — 1 silver = 100 copper, 1 gold = 10,000 copper
    return p.get("gold", 0) * 10000 + p.get("silver", 0) * 100 + p.get("copper", 0)


@lru_cache(maxsize=1)
def load_catalog() -> Catalog:
    items_raw = _load_dir("Item")
    foods_raw = _load_dir("Food")
    seeds_raw = _load_dir("Seed")
    sprout_seeds_raw = _load_dir("SproutSeed")
    crops_raw = _load_dir("Crop")
    recipes_raw = _load_dir("Recipe")
    groups_raw = _load_dir("IngredientGroup")

    cat = Catalog()

    # Items + Foods + Seeds + SproutSeeds all inherit from Item base
    for src, is_food in ((items_raw, False), (foods_raw, True),
                         (seeds_raw, True), (sprout_seeds_raw, True)):
        for pid, d in src.items():
            iid = d.get("id")
            if iid is None:
                continue
            it = Item(
                item_id=int(iid),
                path_id=pid,
                name=d.get("m_Name", ""),
                name_id=d.get("nameId", "") or "",
                buy_copper=_price(d.get("price")),
                sell_copper=_price(d.get("sellPrice")),
                is_food=is_food,
                food_type=d.get("foodType"),
                contains_alcohol=bool(d.get("containsAlcohol", 0)),
                # Item.hasToBeAgedMeal — explicit flag set on cheeses, hams, etc.
                # (Food.canBeAged defaults to true on every food so it's not a useful filter.)
                has_to_be_aged_meal=bool(d.get("hasToBeAgedMeal", 0)),
                excluded_from_trends=bool(d.get("excludedFromTrends", 0)),
            )
            cat.items_by_id[it.item_id] = it
            cat.items_by_path_id[pid] = it

    # Crops
    for pid, d in crops_raw.items():
        cid = d.get("id")
        if cid is None:
            continue
        seed_pid = (d.get("seed") or {}).get("m_PathID", 0)
        h = (d.get("harvestedItems") or [{}])[0] or {}
        h_pid = (h.get("item") or {}).get("m_PathID", 0)
        seed_item = cat.items_by_path_id.get(seed_pid)
        h_item = cat.items_by_path_id.get(h_pid)
        crop = Crop(
            crop_id=int(cid),
            name=d.get("m_Name", ""),
            name_id=d.get("nameId", "") or "",
            seed_path_id=seed_pid,
            seed_item_id=seed_item.item_id if seed_item else None,
            available_seasons=int(d.get("avaliableSeasons", 0)),
            best_seasons=int(d.get("bestSeasons", 0)),
            days_to_grow=int(d.get("daysToGrow", 1)),
            reusable=bool(d.get("reusable", 0)),
            days_until_new_harvest=int(d.get("daysUntilNewHarvest", 0)),
            amount_best_season=int(d.get("amountBestSeason", 0)),
            harvest_path_id=h_pid,
            harvest_item_id=h_item.item_id if h_item else None,
            harvest_amount=int(h.get("amount", 0)),
        )
        cat.crops_by_id[crop.crop_id] = crop
        if crop.harvest_item_id is not None:
            cat.crops_by_harvest_item_id[crop.harvest_item_id] = crop

    # Recipes
    for pid, d in recipes_raw.items():
        rid = d.get("id")
        if rid is None:
            continue
        out_p = (d.get("output") or {}).get("item") or {}
        out_pid = out_p.get("m_PathID", 0)
        out_item = cat.items_by_path_id.get(out_pid)
        out_qty = (d.get("output") or {}).get("amount", 1)
        sell = (out_item.sell_copper * out_qty) if out_item else 0
        ing_cost = 0
        ings: list[tuple[int, int]] = []
        raw_ings: list[dict] = []
        for ing in d.get("ingredientsNeeded") or []:
            ipid = (ing.get("item") or {}).get("m_PathID", 0)
            mpid = (ing.get("mod") or {}).get("m_PathID", 0)
            amt = ing.get("amount", 1)
            raw_ings.append({"path_id": ipid, "mod_path_id": mpid, "amount": amt})
            it = cat.items_by_path_id.get(ipid)
            if it:
                ing_cost += it.buy_copper * amt
                ings.append((it.item_id, amt))
        t = d.get("time") or {}
        hours = (t.get("years", 0) * 365 * 24
                 + t.get("weeks", 0) * 7 * 24
                 + t.get("days", 0) * 24
                 + t.get("hours", 0)
                 + t.get("mins", 0) / 60)
        active = bool(d.get("usingNewRecipesSystem", 1)) and not bool(d.get("replacedRecipe", 0))
        profit = sell - ing_cost
        pph = (profit / hours) if hours > 0 else float(profit)
        rec = Recipe(
            recipe_id=int(rid),
            name=d.get("m_Name", ""),
            group=int(d.get("recipeGroup", 1)),
            active=active,
            output_path_id=out_pid,
            output_item_id=out_item.item_id if out_item else None,
            output_qty=out_qty,
            output_sell_copper=sell,
            ingredient_buy_copper=ing_cost,
            profit_per_craft=profit,
            profit_per_hour=round(pph, 1),
            fuel=int(d.get("fuel", 0)),
            time_hours=round(hours, 2),
            ingredients=ings,
            raw_ingredients=raw_ings,
        )
        cat.recipes_by_id[rec.recipe_id] = rec
        if rec.output_item_id is not None:
            cat.recipes_by_output_item_id.setdefault(rec.output_item_id, []).append(rec)

    # IngredientGroups (Pale Malt, Dark Hops, ...) — recipes use these as
    # placeholder slots; the player picks one of `possible_items`.
    for pid, d in groups_raw.items():
        gid = d.get("id")
        if gid is None:
            continue
        possible: list[tuple[int, int]] = []
        for entry in (d.get("possibleItems") or []):
            ipid = (entry.get("item") or {}).get("m_PathID", 0)
            mpid = (entry.get("mod") or {}).get("m_PathID", 0)
            possible.append((ipid, mpid))
        grp = IngredientGroup(
            group_id=int(gid),
            path_id=pid,
            name=d.get("m_Name", ""),
            name_id=d.get("nameId", "") or "",
            possible_items=possible,
        )
        cat.groups_by_path_id[pid] = grp

    # ----- Shops -----
    for pid, d in _load_dir("Shop").items():
        # m_Name like "10 - Wilson"
        nm = d.get("m_Name", "")
        vendor = nm.split(" - ", 1)[1] if " - " in nm else nm
        cat.shops.append(Shop(
            shop_id=int(d.get("id", 0)),
            name=vendor,
            shop_type=int(d.get("shopType", 0)),
            items=d.get("shopItems") or [],
        ))
    cat.shops.sort(key=lambda s: s.shop_id)

    # ----- Talents -----
    for pid, d in _load_dir("Talent").items():
        cat.talents.append(Talent(
            talent_id=int(d.get("id", 0)),
            name=d.get("m_Name", ""),
            name_id=d.get("nameId", "") or "",
            description=d.get("description", "") or "",
            raw=d,
        ))
    cat.talents.sort(key=lambda t: t.talent_id)

    # ----- Fish -----
    for pid, d in _load_dir("Fish").items():
        cat.fishes.append(FishKind(
            fish_id=int(d.get("id", 0)),
            name=d.get("m_Name", ""),
            name_id=d.get("nameId", "") or "",
            raw=d,
        ))
    cat.fishes.sort(key=lambda f: f.fish_id)

    # ----- Foraging spots — unify BushHarvest, MiscellaneousHarvest, MiscItemHarvest -----
    for cls in ("BushHarvest", "MiscellaneousHarvest", "MiscItemHarvest"):
        for pid, d in _load_dir(cls).items():
            cat.bushes.append(BushHarvest(
                bush_id=int(d.get("id", 0) or 0),
                name=d.get("m_Name", "") or cls,
                raw={**d, "_class": cls},
            ))
    cat.bushes.sort(key=lambda b: b.bush_id)

    # ----- Quests (multiple subclass dirs) -----
    quest_dirs = ["ActionDoneQuest", "MissionTalkWith", "MissionActionDone",
                  "CraftItemTypeQuest", "ServeCustomerQuest", "UnlockContentQuest",
                  "ChristmasTreeQuest"]
    for d_name in quest_dirs:
        for pid, d in _load_dir(d_name).items():
            cat.quests.append(Quest(
                quest_id=int(d.get("id", 0)),
                name_id=d.get("nameId", "") or "",
                description=d.get("description", "") or "",
                required_amount=int(d.get("requiredAmount", 1)),
                reward=d.get("reward"),
                recipes_unlocked=[r.get("m_PathID", 0) for r in (d.get("recipesUnlocked") or [])],
                linked_quests=[q.get("m_PathID", 0) for q in (d.get("linkedQuests") or [])],
                only_on_halloween=bool(d.get("onlyOnHalloween", 0)),
                only_on_christmas=bool(d.get("onlyOnChristmas", 0)),
                is_repeatable=bool(d.get("isRepeatable", 0)),
                raw=d,
            ))
    cat.quests.sort(key=lambda q: q.quest_id)

    # ----- ReputationInfo -----
    for pid, d in _load_dir("ReputationInfo").items():
        cat.reputations.append(ReputationMilestone(
            rep_id=int(d.get("id", 0) or 0),
            name=d.get("m_Name", ""),
            name_id=d.get("nameId", "") or "",
            raw=d,
        ))
    cat.reputations.sort(key=lambda r: r.rep_id)

    # ----- PerkLines from PerksDatabase (single file) -----
    perk_db_dir = os.path.join(MONO, "PerksDatabase")
    if os.path.isdir(perk_db_dir):
        for fname in os.listdir(perk_db_dir):
            with open(os.path.join(perk_db_dir, fname), encoding="utf8") as f:
                pd = json.load(f)
            for entry in pd.get("playerPerksLines", []):
                cat.player_perks.append(PerkLine(
                    perk_id=int(entry.get("id", 0)),
                    name=entry.get("name", ""),
                    description=entry.get("description", ""),
                    perk_tree=entry.get("perkTree", ""),
                    raw=entry,
                ))
            for entry in pd.get("employeePerksLines", []):
                cat.employee_perks.append(PerkLine(
                    perk_id=int(entry.get("id", 0)),
                    name=entry.get("name", ""),
                    description=entry.get("description", ""),
                    perk_tree=entry.get("perkTree", ""),
                    raw=entry,
                ))
    cat.player_perks.sort(key=lambda p: p.perk_id)
    cat.employee_perks.sort(key=lambda p: p.perk_id)

    return cat
