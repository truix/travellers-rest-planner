"""Generic recipe lookup — for ANY craftable item, not just drinks.

Reuses the brewing chain walker so a Foie Gras dish or a Plank or a Wine all
get the same multi-stage breakdown with localized ingredients.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from planner.catalog import Catalog, Recipe
from planner.i18n import Translator
from planner.plan.brewing import _walk_recipe, AGING_PRICE_MULT, AGING_HOURS_TO_REACH


GROUP_NAMES = {0: "Material", 1: "Food", 2: "Drink", 3: "Other"}


def list_craftables(cat: Catalog, tr: Translator,
                    unlocked: set[int] | None = None,
                    query: str = "",
                    group_filter: int | None = None) -> list[dict]:
    """Return a thin list of every active recipe — id, name, group, output,
    sell, time, unlocked. For the "search" UI."""
    out: list[dict] = []
    q = (query or "").strip().lower()
    for r in cat.recipes_by_id.values():
        if not r.active:
            continue
        if group_filter is not None and r.group != group_filter:
            continue
        out_item = cat.items_by_id.get(r.output_item_id) if r.output_item_id else None
        out_name = tr.recipe(r.output_item_id, fallback=r.name,
                             output_name_id=out_item.name_id if out_item else None)
        if q and q not in out_name.lower() and q not in r.name.lower():
            continue
        # Resolve ingredient names for menu planner
        ings = []
        for iid, amt in r.ingredients:
            ing_item = cat.items_by_id.get(iid)
            ings.append({
                "item_id": iid,
                "name": tr.item(ing_item.item_id, ing_item.name_id, ing_item.name) if ing_item else f"#{iid}",
                "amount": amt,
                "buy_copper": ing_item.buy_copper if ing_item else 0,
                "sell_copper": ing_item.sell_copper if ing_item else 0,
            })
        out.append({
            "recipe_id": r.recipe_id,
            "name": out_name,
            "group": GROUP_NAMES.get(r.group, str(r.group)),
            "output_item_id": r.output_item_id,
            "output_qty": r.output_qty,
            "per_unit_sell": (out_item.sell_copper if out_item else 0),
            "batch_sell": r.output_sell_copper,
            "ingredient_buy_cost": r.ingredient_buy_copper,
            "profit_per_craft": r.profit_per_craft,
            "time_hours": r.time_hours,
            "fuel": r.fuel,
            "is_unlocked": (unlocked is None or r.recipe_id in unlocked),
            # Drinks (group 2) all benefit from aging in a barrel; foods only
            # if they're explicitly flagged hasToBeAgedMeal (cheeses, hams).
            "can_be_aged": bool(r.group == 2 or (out_item and out_item.has_to_be_aged_meal)),
            "ingredients": ings,
        })
    out.sort(key=lambda x: (not x["is_unlocked"], -x["profit_per_craft"]))
    return out


def get_recipe_detail(recipe_id: int, cat: Catalog, tr: Translator,
                      unlocked: set[int] | None = None) -> Optional[dict]:
    r = cat.recipes_by_id.get(recipe_id)
    if r is None or not r.active:
        return None
    chain = _walk_recipe(r, cat, tr, set())
    out_item = cat.items_by_id.get(r.output_item_id) if r.output_item_id else None
    qty = max(1, r.output_qty)
    per_unit = (out_item.sell_copper if out_item else 0) or (r.output_sell_copper // qty)

    # Drinks (group 2) all use the AgingBarrel; foods only if hasToBeAgedMeal.
    can_age = bool(r.group == 2 or (out_item and out_item.has_to_be_aged_meal))

    aged_sell = {rk: int(qty * per_unit * AGING_PRICE_MULT[rk]) for rk in range(5)} if can_age else {}
    aged_sell_per_unit = {rk: int(per_unit * AGING_PRICE_MULT[rk]) for rk in range(5)} if can_age else {}
    profit = {rk: aged_sell[rk] - chain.cumulative_cost_copper for rk in aged_sell}
    profit_per_unit = {rk: aged_sell_per_unit[rk] - (chain.cumulative_cost_copper // qty) for rk in aged_sell_per_unit}

    # asdict the chain manually because BrewStage is a dataclass
    from dataclasses import asdict as _asdict
    return {
        "recipe_id": r.recipe_id,
        "name": tr.recipe(r.output_item_id, fallback=r.name,
                          output_name_id=out_item.name_id if out_item else None),
        "group": GROUP_NAMES.get(r.group, str(r.group)),
        "output_item_id": r.output_item_id,
        "output_qty": qty,
        "per_unit_sell": per_unit,
        "batch_sell": qty * per_unit,
        "ingredient_buy_cost": chain.cumulative_cost_copper,
        "total_time_hours": chain.cumulative_time_hours,
        "active_cook_hours": r.time_hours,
        "fuel": r.fuel,
        "is_unlocked": (unlocked is None or r.recipe_id in unlocked),
        "chain": _asdict(chain),
        "can_age": can_age,
        "aging_hours_per_rank": AGING_HOURS_TO_REACH if can_age else {},
        "aged_sell_per_unit": aged_sell_per_unit,
        "aged_sell_batch": aged_sell,
        "profit_per_rank_per_unit": profit_per_unit,
        "profit_per_rank_batch": profit,
    }
