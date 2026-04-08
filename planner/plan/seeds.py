"""Seeds / crops reference view.

Builds a sortable, locale-aware list of every crop in the catalog. Joins with
the current GameState's `planted_crop_counts` so the UI can highlight what
the player already has in the ground.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

from planner.catalog import Catalog, Crop, SEASON_BITS
from planner.i18n import Translator
from planner.parser.saves import GameState, SEASON_NAMES


def _seasons(flag: int) -> list[str]:
    return [SEASON_NAMES[i] for i in range(4) if flag & SEASON_BITS[i]]


@dataclass
class SeedRow:
    crop_id: int
    name: str
    seed_name: str | None
    seed_item_id: int | None
    seed_buy_copper: int
    harvest_item_id: int | None
    harvest_name: str
    harvest_sell_copper: int          # raw item sell price (no recipe / no trend)
    available_seasons: list[str]
    best_seasons: list[str]
    days_to_grow: int
    reusable: bool
    days_until_new_harvest: int
    yield_normal: int
    yield_best_season: int
    profit_per_day_normal: float      # rough: (sell × yield) / days_to_grow
    profit_per_day_best: float
    is_in_season_now: bool
    is_best_now: bool
    planted_count: int
    is_obtainable: bool                # has a real seed item


def build_seed_table(state: GameState | None, cat: Catalog,
                     language: str = "English") -> list[dict]:
    tr = Translator(language)
    cur_season = state.current_date.season if state else 0
    rows: list[SeedRow] = []
    for crop in cat.crops_by_id.values():
        seed_item = cat.items_by_id.get(crop.seed_item_id) if crop.seed_item_id else None
        harvest_item = cat.items_by_id.get(crop.harvest_item_id) if crop.harvest_item_id else None
        seed_name = (tr.item(seed_item.item_id, seed_item.name_id, seed_item.name)
                     if seed_item else None)
        harvest_name = (tr.item(harvest_item.item_id, harvest_item.name_id, harvest_item.name)
                        if harvest_item
                        else tr.crop(crop.name_id, crop.harvest_item_id, crop.name))
        crop_name = tr.crop(crop.name_id, crop.harvest_item_id, crop.name)
        avail = _seasons(crop.available_seasons)
        best = _seasons(crop.best_seasons)
        is_now = SEASON_NAMES[cur_season] in avail if state else False
        is_best_now = SEASON_NAMES[cur_season] in best if state else False
        planted = state.planted_crop_counts.get(crop.crop_id, 0) if state else 0
        sell = harvest_item.sell_copper if harvest_item else 0
        y_norm = max(1, crop.amount_best_season - 1)
        y_best = crop.amount_best_season
        days = max(1, crop.days_to_grow)
        # For perennials we approximate "per day" using regrow days for stable rate
        if crop.reusable and crop.days_until_new_harvest > 0:
            cycle = crop.days_until_new_harvest
        else:
            cycle = days
        ppd_norm = round((sell * y_norm) / cycle, 1) if cycle else 0
        ppd_best = round((sell * y_best) / cycle, 1) if cycle else 0
        rows.append(SeedRow(
            crop_id=crop.crop_id,
            name=crop_name,
            seed_name=seed_name,
            seed_item_id=seed_item.item_id if seed_item else None,
            seed_buy_copper=seed_item.buy_copper if seed_item else 0,
            harvest_item_id=harvest_item.item_id if harvest_item else None,
            harvest_name=harvest_name,
            harvest_sell_copper=sell,
            available_seasons=avail,
            best_seasons=best,
            days_to_grow=crop.days_to_grow,
            reusable=crop.reusable,
            days_until_new_harvest=crop.days_until_new_harvest,
            yield_normal=y_norm,
            yield_best_season=y_best,
            profit_per_day_normal=ppd_norm,
            profit_per_day_best=ppd_best,
            is_in_season_now=is_now,
            is_best_now=is_best_now,
            planted_count=planted,
            is_obtainable=seed_item is not None,
        ))
    rows.sort(key=lambda r: (not r.is_best_now, not r.is_in_season_now,
                             -r.profit_per_day_best, r.crop_id))
    return [asdict(r) for r in rows]
