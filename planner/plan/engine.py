"""Planning engine.

Inputs: a parsed GameState (current trends + current date + unlocks + planted crops)
        plus the static Catalog (crops/items/recipes).

Outputs: a Plan dataclass with:
  - resolved current-week trend lists with status flags
  - cook list = trending recipes the player has unlocked + can profitably make
  - brew list = same for drinks
  - plant list = crops to plant THIS WEEK (best-season + currently trending)
  - 4-week calendar = each upcoming week with trends + plant-by-deadlines
  - missing ingredients = trending recipes the player has unlocked but lacks ingredients for

Game timing rules (from Trends.cs + CustomerInfo.cs + Crop.cs):
  - Trends rotate every Monday. allTrendsSave[0] is the CURRENT week.
  - One in-game season = 4 weeks. One week = 7 days.
  - A crop with daysToGrow=N planted today is harvestable in N days.
  - To have a crop ready for trend week W (W=0..3 starting from current),
    plant by:  daysUntilWeek(W) - daysToGrow + (current.day_of_week)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from planner.catalog import (
    Catalog, Crop, Recipe, Item,
    SPRING, SUMMER, AUTUMN, WINTER, SEASON_BITS,
)
from planner.i18n import Translator, DEFAULT_LANG
from planner.parser.saves import GameState, TrendSet, SEASON_NAMES


# Trend mechanics: trending = +20% sale price (Trends.trendPriceMultiplier = 0.2)
TREND_PRICE_MULTIPLIER = 0.2

# How many days until the start of the upcoming Monday for trend week W (0..3).
# allTrendsSave[0] is the current week. The current week's "Monday" already passed
# at game-day index 0; if today is e.g. Wed (day=2), then days_to_next_monday = 5.
def days_to_week_start(state: GameState, w: int) -> int:
    if w == 0:
        return 0  # current week, already in effect
    # use the save's countdown for week 1 if available, else compute from day-of-week
    base_to_next_monday = state.days_to_next_trend
    if base_to_next_monday <= 0:
        base_to_next_monday = (7 - state.current_date.day) % 7 or 7
    return base_to_next_monday + (w - 1) * 7


def season_for_offset(state: GameState, days: int) -> int:
    """Which season index we'll be in after `days` in-game days."""
    # 1 season = 4 weeks = 28 days. (Confirmed by Trends.numOfWeeks == 4.)
    # current week index inside the season is currentTime.week (1..4).
    cur_season = state.current_date.season
    cur_week_in_season = max(1, state.current_date.week)
    cur_day_in_week = state.current_date.day  # 0..6
    days_into_season = (cur_week_in_season - 1) * 7 + cur_day_in_week
    total_days = days_into_season + days
    season_offset = total_days // 28
    return (cur_season + season_offset) % 4


def season_bit(season_idx: int) -> int:
    return SEASON_BITS[season_idx % 4]


# ---- helpers ---------------------------------------------------------------

def resolve_items(ids: list[int], cat: Catalog) -> list[Item]:
    return [cat.items_by_id[i] for i in ids if i in cat.items_by_id]


def crop_grows_in(crop: Crop, season_idx: int) -> bool:
    return bool(crop.available_seasons & season_bit(season_idx))


def crop_is_best_in(crop: Crop, season_idx: int) -> bool:
    return bool(crop.best_seasons & season_bit(season_idx))


def find_crop_for_item(item_id: int, cat: Catalog) -> Crop | None:
    return cat.crops_by_harvest_item_id.get(item_id)


def recipes_producing(item_id: int, cat: Catalog) -> list[Recipe]:
    return cat.recipes_by_output_item_id.get(item_id, [])


# ---- recommendation builders -----------------------------------------------

@dataclass
class TrendItem:
    item_id: int
    name: str
    is_food: bool
    contains_alcohol: bool
    grow_crop_id: int | None         # if it's an ingredient with a crop
    grow_crop_name: str | None
    grow_in_season_now: bool          # plantable in current season
    grow_best_season_now: bool        # AND it's the best season
    is_planted: bool                  # at least one already in the ground
    planted_count: int
    recipe_ids: list[int]             # recipes that produce this item (if any)
    unlocked_recipe_ids: list[int]    # subset the player has unlocked


@dataclass
class CookSuggestion:
    recipe_id: int
    recipe_name: str
    output_item_id: int
    output_name: str
    profit_per_craft: int
    profit_per_hour: float
    base_profit_with_trend: int       # +20% on output sale, ingredients constant
    time_hours: float
    fuel: int
    ingredients: list[tuple[int, int, str]]   # (item_id, amount, name)
    missing_ingredients: list[str]    # names of ingredients not in catalog/items_by_id
    why: list[str]                    # human reasons


@dataclass
class PlantSuggestion:
    crop_id: int
    crop_name: str
    days_to_grow: int
    reusable: bool
    days_until_new_harvest: int
    available_seasons: list[str]
    best_seasons: list[str]
    is_best_now: bool
    yield_per_harvest: int
    target_for_trend_week: int        # 0..3
    plant_by_day: int                 # day offset from now
    why: list[str]


@dataclass
class WeekPlan:
    week_offset: int                  # 0=current, 1..3=upcoming
    days_until_start: int
    season_at_start: str
    food_trends: list[TrendItem]
    drink_trends: list[TrendItem]
    ingredient_trends: list[TrendItem]


@dataclass
class Plan:
    state: dict                       # GameState as dict for the UI
    today: dict                       # quick summary
    cook_now: list[CookSuggestion]
    brew_now: list[CookSuggestion]
    plant_now: list[PlantSuggestion]
    calendar: list[WeekPlan]          # 4 weeks
    money_silver: float


# ---- main builder ----------------------------------------------------------

def _trend_item(item_id: int, cat: Catalog, state: GameState, season_idx: int,
                tr: Translator) -> TrendItem:
    item = cat.items_by_id.get(item_id)
    name = tr.item(item_id, item.name_id if item else None,
                   fallback=item.name if item else f"?{item_id}")
    crop = find_crop_for_item(item_id, cat)
    grow_now = crop_grows_in(crop, season_idx) if crop else False
    best_now = crop_is_best_in(crop, season_idx) if crop else False
    planted = state.planted_crop_counts.get(crop.crop_id, 0) if crop else 0
    recs = recipes_producing(item_id, cat)
    unlocked = [r.recipe_id for r in recs if r.recipe_id in state.unlocked_recipe_ids and r.active]
    crop_name_localized = None
    if crop:
        crop_name_localized = tr.crop(crop.name_id, crop.harvest_item_id, crop.name)
    return TrendItem(
        item_id=item_id,
        name=name,
        is_food=item.is_food if item else False,
        contains_alcohol=item.contains_alcohol if item else False,
        grow_crop_id=crop.crop_id if crop else None,
        grow_crop_name=crop_name_localized,
        grow_in_season_now=grow_now,
        grow_best_season_now=best_now,
        is_planted=planted > 0,
        planted_count=planted,
        recipe_ids=[r.recipe_id for r in recs if r.active],
        unlocked_recipe_ids=unlocked,
    )


def _cook_suggestion(recipe: Recipe, cat: Catalog, tr: Translator, why: list[str]) -> CookSuggestion:
    base = recipe.profit_per_craft
    # +20% on the output sale (not ingredient cost) when trending
    output_with_trend = int(recipe.output_sell_copper * (1 + TREND_PRICE_MULTIPLIER))
    boosted = output_with_trend - recipe.ingredient_buy_copper
    ings = []
    missing = []
    for iid, amt in recipe.ingredients:
        it = cat.items_by_id.get(iid)
        loc_name = tr.item(iid, it.name_id if it else None, fallback=it.name if it else f"?{iid}")
        ings.append((iid, amt, loc_name))
        if not it:
            missing.append(loc_name)
    out_item_obj = cat.items_by_id.get(recipe.output_item_id) if recipe.output_item_id else None
    output_name = tr.recipe(recipe.output_item_id, fallback=recipe.name,
                            output_name_id=out_item_obj.name_id if out_item_obj else None)
    return CookSuggestion(
        recipe_id=recipe.recipe_id,
        recipe_name=output_name,
        output_item_id=recipe.output_item_id or 0,
        output_name=output_name,
        profit_per_craft=base,
        profit_per_hour=recipe.profit_per_hour,
        base_profit_with_trend=boosted,
        time_hours=recipe.time_hours,
        fuel=recipe.fuel,
        ingredients=ings,
        missing_ingredients=missing,
        why=why,
    )


def _plant_suggestion(crop: Crop, target_week: int, days_until_week: int,
                      is_best: bool, tr: Translator, why: list[str]) -> PlantSuggestion:
    plant_by = max(0, days_until_week - crop.days_to_grow)
    name = tr.crop(crop.name_id, crop.harvest_item_id, crop.name)
    return PlantSuggestion(
        crop_id=crop.crop_id,
        crop_name=name,
        days_to_grow=crop.days_to_grow,
        reusable=crop.reusable,
        days_until_new_harvest=crop.days_until_new_harvest,
        available_seasons=[SEASON_NAMES[i] for i in range(4) if crop.available_seasons & SEASON_BITS[i]],
        best_seasons=[SEASON_NAMES[i] for i in range(4) if crop.best_seasons & SEASON_BITS[i]],
        is_best_now=is_best,
        yield_per_harvest=crop.amount_best_season if is_best else max(1, crop.amount_best_season - 1),
        target_for_trend_week=target_week,
        plant_by_day=plant_by,
        why=why,
    )


def build_plan(state: GameState, cat: Catalog, language: str = DEFAULT_LANG) -> Plan:
    cur_season = state.current_date.season
    tr = Translator(language)

    # Build the 4-week calendar
    calendar: list[WeekPlan] = []
    for w, ts in enumerate(state.trends[:4]):
        days_to = days_to_week_start(state, w)
        season_then = season_for_offset(state, days_to)
        calendar.append(WeekPlan(
            week_offset=w,
            days_until_start=days_to,
            season_at_start=SEASON_NAMES[season_then],
            food_trends=[_trend_item(i, cat, state, season_then, tr) for i in ts.food_ids],
            drink_trends=[_trend_item(i, cat, state, season_then, tr) for i in ts.drink_ids],
            ingredient_trends=[_trend_item(i, cat, state, season_then, tr) for i in ts.ingredient_ids],
        ))

    # ---- COOK NOW: trending food (current week) that the player has unlocked
    cook_now: list[CookSuggestion] = []
    cur = calendar[0]
    seen_recipes = set()
    for ti in cur.food_trends:
        for rid in ti.unlocked_recipe_ids:
            if rid in seen_recipes:
                continue
            seen_recipes.add(rid)
            r = cat.recipes_by_id[rid]
            why = [f"trending this week → +{int(TREND_PRICE_MULTIPLIER*100)}% sale price",
                   f"unlocks {ti.name}"]
            cook_now.append(_cook_suggestion(r, cat, tr, why))

    # ---- BREW NOW: same for drink trends
    brew_now: list[CookSuggestion] = []
    seen_drinks = set()
    for ti in cur.drink_trends:
        for rid in ti.unlocked_recipe_ids:
            if rid in seen_drinks:
                continue
            seen_drinks.add(rid)
            r = cat.recipes_by_id[rid]
            why = [f"trending drink → +{int(TREND_PRICE_MULTIPLIER*100)}% sale price",
                   f"unlocks {ti.name}"]
            brew_now.append(_cook_suggestion(r, cat, tr, why))

    # ---- PLANT NOW: ingredients trending in any of the next 4 weeks whose crop
    # could be ready in time AND is in (or close to) its best season then.
    plant_now: list[PlantSuggestion] = []
    seen_crops: set[int] = set()
    for w, wk in enumerate(calendar):
        for ti in wk.ingredient_trends + wk.food_trends:
            crop_id = ti.grow_crop_id
            if crop_id is None or crop_id in seen_crops:
                continue
            crop = cat.crops_by_id.get(crop_id)
            if crop is None:
                continue
            target_season = SEASON_NAMES.index(wk.season_at_start)
            if not crop_grows_in(crop, target_season):
                continue
            is_best = crop_is_best_in(crop, target_season)
            # Can the crop be ready in time? Plant-by must be >= 0
            days_to_week = wk.days_until_start
            if crop.days_to_grow > days_to_week + 7:
                # too slow even if planted today and the trend lasts a week
                continue
            why = [
                f"will be trending in week {w} ({wk.season_at_start})",
                f"{crop.days_to_grow}d to grow vs {days_to_week}d until that week",
            ]
            if is_best:
                why.append("BEST season → +1 yield per harvest")
            if state.planted_crop_counts.get(crop_id, 0):
                why.append(f"already growing {state.planted_crop_counts[crop_id]}")
            plant_now.append(_plant_suggestion(crop, w, days_to_week, is_best, tr, why))
            seen_crops.add(crop_id)

    # Sort plant suggestions: best season first, then by urgency (lowest plant_by_day)
    plant_now.sort(key=lambda p: (not p.is_best_now, p.plant_by_day, p.target_for_trend_week))
    # Sort cook suggestions by trend-boosted profit per hour
    cook_now.sort(key=lambda c: -(c.base_profit_with_trend / max(c.time_hours, 0.01)))
    brew_now.sort(key=lambda c: -(c.base_profit_with_trend / max(c.time_hours, 0.01)))

    today_summary = {
        "date": str(state.current_date),
        "season": state.current_date.season_name,
        "year": state.current_date.year,
        "week_in_season": state.current_date.week,
        "day_of_week": state.current_date.day_name,
        "next_trend_rotation_in_days": days_to_week_start(state, 1),
        "money_copper": state.money_copper,
        "money_silver": round(state.money_copper / 100, 2),
        "tavern_rep": state.tavern_rep,
        "planted_count": sum(state.planted_crop_counts.values()),
        "unique_planted": len(state.planted_crop_counts),
        "unlocked_recipes": len(state.unlocked_recipe_ids),
        "tavern_name": state.tavern_name,
        "player_name": state.player_name,
    }

    # Convert state to a serializable dict
    state_dict = {
        "slot_id": state.slot_id,
        "save_path": state.save_path,
        "save_mtime": state.save_mtime,
    }

    return Plan(
        state=state_dict,
        today=today_summary,
        cook_now=cook_now,
        brew_now=brew_now,
        plant_now=plant_now,
        calendar=calendar,
        money_silver=round(state.money_copper / 100, 2),
    )


def plan_to_dict(plan: Plan) -> dict[str, Any]:
    """Walk dataclasses → dicts for JSON output."""
    def conv(o):
        if hasattr(o, "__dataclass_fields__"):
            return {k: conv(v) for k, v in asdict(o).items()}
        if isinstance(o, (list, tuple)):
            return [conv(v) for v in o]
        if isinstance(o, dict):
            return {k: conv(v) for k, v in o.items()}
        if isinstance(o, set):
            return list(o)
        return o
    return conv(plan)
