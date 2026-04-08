"""Brew planner — for each of the 4 upcoming trend weeks, recommend which
drinks to brew (and which exact ingredient choices to use).

Output structure (returned from /api/brew-plan):
  weeks: [
    {
      week_offset: int (0..3),
      season: str,
      days_until: int,
      trending_drink_ids: [int],
      trending_ingredient_ids: [int],
      picks: [
        {
          drink_item_id, drink_name, recipe_id,
          is_unlocked, is_trending,
          base_per_unit_sell, trended_per_unit_sell,
          total_cook_hours,
          best_combo: { ingredients: [{label, item_id, item_name, mod_name?, buy_cost, sell, slot_amount}], total_cost },
          start_brewing_by_day: int,
          profit_per_craft_aged4: int,   # rank 4 + trend
          profit_per_hour: float,
          why: [str],
        }, ...
      ]
    }
  ]
"""
from __future__ import annotations

from dataclasses import asdict
from itertools import product

from planner.catalog import Catalog
from planner.i18n import Translator
from planner.parser.saves import GameState, SEASON_NAMES
from planner.plan.brewing import (
    build_brew_plan, AGING_PRICE_MULT, AGING_HOURS_TO_REACH, TREND_BONUS,
)


def _days_to_week(state: GameState, w: int) -> int:
    """Days from current in-game day to the start of trend week W (0-indexed)."""
    if w == 0:
        return 0
    base = state.days_to_next_trend
    if base <= 0:
        base = (7 - state.current_date.day) % 7 or 7
    return base + (w - 1) * 7


def _season_for(state: GameState, days_offset: int) -> int:
    cur_season = state.current_date.season
    week_in_season = max(1, state.current_date.week)
    day_in_week = state.current_date.day
    days_into_season = (week_in_season - 1) * 7 + day_in_week
    return (cur_season + (days_into_season + days_offset) // 28) % 4


def _best_combo_for(plan, trending_ing_ids: set[int]):
    """Pick the best (item per slot) combo for a brew plan.

    Strategy:
    - For each IngredientGroup slot, prefer a TRENDING ingredient (more variety
      lets you sell trending raw later) — but the actual brew price isn't
      affected by which choice you pick, only the COST is. So tied between
      "cheapest" (best margin) and "trending" (player wants to use up trending
      stock). Default = cheapest unless `prefer_trending` is True.
    - For non-group slots, the choice is fixed.
    """
    chain = plan.chain
    slots = chain.slots
    combo_items = []
    total_cost = chain.cumulative_cost_copper
    # We rebuild the cost from scratch with the chosen items
    rebuilt_cost = 0
    for s in slots:
        if not s.choices:
            # Unresolved slot
            rebuilt_cost += s.cheapest_cost
            combo_items.append({
                "label": s.label,
                "item_id": None,
                "item_name": s.label,
                "mod_name": None,
                "buy_cost": s.cheapest_cost,
                "sell": s.raw_sell_value,
                "slot_amount": s.amount,
                "is_trending": False,
            })
            continue
        # Pick: cheapest by default, but if any choice is trending, prefer that
        chosen = s.choices[0]
        for c in s.choices:
            if c.item_id in trending_ing_ids:
                chosen = c
                break
        cost = chosen.buy_cost_copper * s.amount
        rebuilt_cost += cost
        combo_items.append({
            "label": s.label,
            "item_id": chosen.item_id,
            "item_name": chosen.item_name,
            "mod_name": chosen.mod_name,
            "buy_cost": cost,
            "sell": chosen.sell_copper * s.amount,
            "slot_amount": s.amount,
            "is_trending": chosen.item_id in trending_ing_ids,
        })
    return combo_items, rebuilt_cost


def build_brew_plan_view(state: GameState, cat: Catalog, tr: Translator) -> dict:
    if not state.trends:
        return {"weeks": []}

    # Build all brew plans once
    from planner.plan.brewing import all_brew_plans
    plans = all_brew_plans(cat, tr, state.unlocked_recipe_ids)
    plans_by_item = {p.drink_item_id: p for p in plans if p.drink_item_id}

    weeks_out = []
    for w in range(min(4, len(state.trends))):
        ts = state.trends[w]
        days_until = _days_to_week(state, w)
        season_idx = _season_for(state, days_until)
        trending_drink_ids = set(ts.drink_ids)
        trending_ingredient_ids = set(ts.ingredient_ids)

        picks = []
        for did in trending_drink_ids:
            p = plans_by_item.get(did)
            if not p:
                continue
            combo, total_cost = _best_combo_for(p, trending_ingredient_ids)
            # Trended per-unit sale price (rank 0 + trend)
            base_pu = p.per_unit_sell
            trended_pu = int(base_pu * (1 + TREND_BONUS))
            # Aged rank-4 + trend per craft (full batch)
            r4_batch = int(p.aged_sell[4] * (1 + TREND_BONUS))
            profit_aged4 = r4_batch - total_cost

            # When to start brewing? brew time + (5 days aging if you want rank 4)
            #   To be ready for week W (in `days_until` days), start by:
            brew_h = p.total_brewing_hours
            aging_h = AGING_HOURS_TO_REACH[4]  # 120h = 5 days for full max
            total_h = brew_h + aging_h
            total_d = total_h / 24
            start_by = max(0, days_until - int(total_d))

            why = []
            if combo and any(x["is_trending"] for x in combo):
                why.append("uses a trending ingredient (no price impact, but lets you sell off stock)")
            if w == 0:
                why.append("trending RIGHT NOW — brew immediately to sell at +20%")
            else:
                why.append(f"trending in {days_until}d — start brewing by day {start_by}")
            if not p.is_unlocked:
                why.append("RECIPE LOCKED — unlock first")

            picks.append({
                "drink_item_id": p.drink_item_id,
                "drink_name": p.drink_name,
                "recipe_id": p.chain.recipe_id,
                "is_unlocked": p.is_unlocked,
                "is_trending": True,
                "base_per_unit_sell": base_pu,
                "trended_per_unit_sell": trended_pu,
                "trended_batch_sell": int(p.aged_sell[0] * (1 + TREND_BONUS)),
                "trended_aged_batch": r4_batch,
                "ingredient_cost": total_cost,
                "profit_per_craft_aged4": profit_aged4,
                "profit_per_hour": round(profit_aged4 / max(brew_h, 0.01), 1),
                "total_cook_hours": brew_h,
                "total_with_aging_hours": total_h,
                "start_brewing_by_day": start_by,
                "best_combo": combo,
                "why": why,
                "is_wine": p.is_wine,
            })

        # Sort: unlocked first, then by aged rank-4 profit
        picks.sort(key=lambda x: (not x["is_unlocked"], -x["profit_per_craft_aged4"]))

        # Resolve trending ingredient names
        ing_names = []
        for iid in trending_ingredient_ids:
            it = cat.items_by_id.get(iid)
            if it:
                ing_names.append({
                    "item_id": iid,
                    "name": tr.item(iid, it.name_id, it.name),
                    "buy_copper": it.buy_copper,
                    "sell_copper": it.sell_copper,
                    "trended_sell_copper": int(it.sell_copper * (1 + TREND_BONUS)),
                })

        weeks_out.append({
            "week_offset": w,
            "season": SEASON_NAMES[season_idx],
            "days_until": days_until,
            "trending_drink_ids": list(trending_drink_ids),
            "trending_ingredients": ing_names,
            "picks": picks,
        })

    return {"weeks": weeks_out}
