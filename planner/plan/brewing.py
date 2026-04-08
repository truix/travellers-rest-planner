"""Brewing / drink chain walker.

For any drink the player has unlocked, walks back through the producing
recipes to compute:

  - The full multi-stage chain (Mill → Brew → Age, etc.)
  - Total active time across all stages (sum of cook times)
  - Total raw ingredient cost using the cheapest fulfillment for each
    IngredientGroup slot
  - Sale price at every aging rank, with the trend bonus baked in optionally
  - "Start by day X to be ready by day Y" reverse calculator

Aging math (from dumps/AgingBarrel.cs):
  rank 0 → 1: 24h (1 day)        no price bonus
  rank 1 → 2: 24h (1 day)        +10%   (Money.cs:418-426)
  rank 2 → 3: 24h (1 day)        +20%
  rank 3 → 4: 48h (2 days)       +30%
  TOTAL: 5 in-game days to reach max rank.

Wine ingredient_type==7 uses ~1 in-game year per rank instead, but we model
that with the same rank multipliers (player rarely waits a year for it).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from planner.catalog import Catalog, Recipe, Item, IngredientGroup
from planner.i18n import Translator


# Aging rank → price multiplier (1.0 + bonus). From Money.CalculatePriceWithModifiers
# (dumps/Money.cs:418-426): rank 2 +10%, rank 3 +20%, rank 4 +30%.
AGING_PRICE_MULT = {0: 1.0, 1: 1.0, 2: 1.10, 3: 1.20, 4: 1.30}

# Per AgingBarrel.StartTimer (dumps/AgingBarrel.cs:950): 24h between each rank,
# except 48h for the rank 3 → rank 4 step. The same applies to wine — there is
# no special slow-wine path in the live timer (the year-long branch in
# CLFCJNFCPMP is obfuscator dead code).
AGING_HOURS_TO_REACH = {0: 0, 1: 24, 2: 48, 3: 72, 4: 120}

# Trend price bonus (Trends.cs trendPriceMultiplier)
TREND_BONUS = 0.20


@dataclass
class IngredientChoice:
    """One way to fulfill an ingredient slot — either a concrete item or one
    pick from an IngredientGroup."""
    item_id: int
    item_name: str
    mod_name: Optional[str]            # the grain/flavor variant if applicable
    buy_cost_copper: int               # market buy price for this item
    sell_copper: int                   # market sell price (raw, no recipe/trend)
    is_from_group: bool                # was this slot a group?
    group_name: Optional[str]


@dataclass
class IngredientSlot:
    """One ingredient line in a recipe stage. May be a concrete item or a
    group with multiple choices."""
    label: str                         # display name (item or group)
    amount: int
    is_group: bool
    choices: list[IngredientChoice]    # if not a group, length 1
    cheapest_cost: int                 # amount × cheapest choice's buy price
    raw_sell_value: int                # amount × cheapest choice's sell price
    sub_stage: Optional["BrewStage"] = None   # if produced by another recipe


@dataclass
class BrewStage:
    """One step in a brewing chain (e.g., Mill, Brew, etc.)."""
    recipe_id: int
    recipe_name: str                   # localized
    output_name: str                   # localized
    output_qty: int
    time_hours: float
    fuel: int
    slots: list[IngredientSlot]
    direct_cost_copper: int            # raw cost of this stage's leaf ingredients
    cumulative_cost_copper: int        # incl. sub-stages
    cumulative_time_hours: float       # incl. sub-stages (longest path)


@dataclass
class BrewPlan:
    drink_item_id: int
    drink_name: str                    # localized
    is_unlocked: bool
    contains_alcohol: bool
    chain: BrewStage                   # top-level (the brew recipe itself)
    output_qty: int                    # units produced per craft (a "batch")
    per_unit_sell: int                 # sell price for ONE unit at rank 0 (skill-stable)
    raw_sell_copper: int               # batch sell price at rank 0, NO trend
    aged_sell: dict[int, int]          # rank → batch sale copper
    aged_sell_per_unit: dict[int, int] # rank → per-unit sale copper
    profit_per_rank: dict[int, int]    # rank → batch profit (sale − cumulative cost)
    profit_per_rank_per_unit: dict[int, int]  # rank → per-unit profit
    total_brewing_hours: float         # without aging
    aging_hours_per_rank: dict[int, int]  # rank → cumulative aging hours
    is_wine: bool                      # purely for UI labelling now


# ---- helpers ---------------------------------------------------------------

def _localized_item(item: Item | None, fallback_name: str, tr: Translator) -> str:
    if item is None:
        return fallback_name
    return tr.item(item.item_id, item.name_id, fallback=item.name)


def _resolve_slot(raw: dict, cat: Catalog, tr: Translator) -> IngredientSlot:
    """Turn one raw_ingredient entry into an IngredientSlot, including
    expanding IngredientGroups."""
    pid = raw["path_id"]
    mpid = raw["mod_path_id"]
    amount = raw["amount"]

    grp = cat.groups_by_path_id.get(pid)
    if grp is not None:
        choices = []
        for ipid, mod_pid in grp.possible_items:
            it = cat.items_by_path_id.get(ipid)
            if not it:
                continue
            mod_item = cat.items_by_path_id.get(mod_pid) if mod_pid else None
            mod_name = _localized_item(mod_item, "", tr) if mod_item else None
            choices.append(IngredientChoice(
                item_id=it.item_id,
                item_name=_localized_item(it, it.name, tr),
                mod_name=mod_name,
                buy_cost_copper=it.buy_copper,
                sell_copper=it.sell_copper,
                is_from_group=True,
                group_name=grp.name,
            ))
        # Sort by cost
        choices.sort(key=lambda c: c.buy_cost_copper)
        cheapest = (choices[0].buy_cost_copper * amount) if choices else 0
        cheapest_sell = (choices[0].sell_copper * amount) if choices else 0
        # Localized group label — IngredientGroups use Items/item_name_<negative_id>
        glabel = tr.get(f"Items/item_name_{grp.group_id}")
        if not glabel:
            glabel = grp.name
            if " - " in glabel:
                glabel = glabel.split(" - ", 1)[1]
        return IngredientSlot(
            label=glabel,
            amount=amount,
            is_group=True,
            choices=choices,
            cheapest_cost=cheapest,
            raw_sell_value=cheapest_sell,
        )

    it = cat.items_by_path_id.get(pid)
    if it is None:
        return IngredientSlot(
            label=f"?{pid}",
            amount=amount,
            is_group=False,
            choices=[],
            cheapest_cost=0,
            raw_sell_value=0,
        )

    mod_item = cat.items_by_path_id.get(mpid) if mpid else None
    mod_name = _localized_item(mod_item, "", tr) if mod_item else None
    name = _localized_item(it, it.name, tr)
    if mod_name:
        name = f"{name} ({mod_name})"
    choice = IngredientChoice(
        item_id=it.item_id,
        item_name=name,
        mod_name=mod_name,
        buy_cost_copper=it.buy_copper,
        sell_copper=it.sell_copper,
        is_from_group=False,
        group_name=None,
    )
    return IngredientSlot(
        label=name,
        amount=amount,
        is_group=False,
        choices=[choice],
        cheapest_cost=it.buy_copper * amount,
        raw_sell_value=it.sell_copper * amount,
    )


def _walk_recipe(recipe: Recipe, cat: Catalog, tr: Translator,
                 visited: set[int], depth: int = 0) -> BrewStage:
    """Build a BrewStage for `recipe`, recursively walking back into any
    intermediate ingredients (mill stages, etc.)."""
    visited.add(recipe.recipe_id)
    slots: list[IngredientSlot] = []
    direct_cost = 0
    sub_time = 0.0
    sub_cost = 0
    for raw in recipe.raw_ingredients:
        slot = _resolve_slot(raw, cat, tr)
        # Check whether the chosen item itself has a producing recipe (only
        # follow into ACTIVE ones, and only if not already visited).
        producing: Optional[Recipe] = None
        if not slot.is_group and slot.choices:
            iid = slot.choices[0].item_id
            for r in cat.recipes_by_output_item_id.get(iid, []):
                if r.active and r.recipe_id not in visited and depth < 4:
                    # only follow if recipe time > 0 — skip trivial passes
                    if r.time_hours > 0:
                        producing = r
                        break
        if producing is not None:
            sub = _walk_recipe(producing, cat, tr, visited, depth + 1)
            slot.sub_stage = sub
            # cost from the sub-stage (per-output amortised)
            per_out = sub.cumulative_cost_copper / max(sub.output_qty, 1)
            slot.cheapest_cost = int(per_out * slot.amount)
            sub_cost += slot.cheapest_cost
            sub_time = max(sub_time, sub.cumulative_time_hours)
        else:
            direct_cost += slot.cheapest_cost
        slots.append(slot)

    cum_cost = direct_cost + sub_cost
    cum_time = recipe.time_hours + sub_time

    out_item = cat.items_by_id.get(recipe.output_item_id) if recipe.output_item_id else None
    out_name_id = out_item.name_id if out_item else None
    nice_name = tr.recipe(recipe.output_item_id, fallback=recipe.name,
                          output_name_id=out_name_id)

    return BrewStage(
        recipe_id=recipe.recipe_id,
        recipe_name=nice_name,
        output_name=nice_name,
        output_qty=recipe.output_qty,
        time_hours=recipe.time_hours,
        fuel=recipe.fuel,
        slots=slots,
        direct_cost_copper=direct_cost,
        cumulative_cost_copper=cum_cost,
        cumulative_time_hours=cum_time,
    )


def build_brew_plan(drink_recipe: Recipe, cat: Catalog, tr: Translator,
                    is_unlocked: bool) -> BrewPlan:
    chain = _walk_recipe(drink_recipe, cat, tr, set())
    out_item = cat.items_by_id.get(drink_recipe.output_item_id) if drink_recipe.output_item_id else None
    is_wine = bool(out_item and "wine" in (out_item.name or "").lower())
    qty = max(1, drink_recipe.output_qty)
    # Per-unit sell price is the stable comparison — perks change yield/craft.
    per_unit = (out_item.sell_copper if out_item else 0) or (drink_recipe.output_sell_copper // qty)
    sale_base_batch = per_unit * qty
    aged_sell = {r: int(sale_base_batch * AGING_PRICE_MULT[r]) for r in range(5)}
    aged_sell_per_unit = {r: int(per_unit * AGING_PRICE_MULT[r]) for r in range(5)}
    profit = {r: aged_sell[r] - chain.cumulative_cost_copper for r in range(5)}
    profit_per_unit = {
        r: aged_sell_per_unit[r] - (chain.cumulative_cost_copper // qty)
        for r in range(5)
    }
    return BrewPlan(
        drink_item_id=drink_recipe.output_item_id or 0,
        drink_name=chain.output_name,
        is_unlocked=is_unlocked,
        contains_alcohol=out_item.contains_alcohol if out_item else False,
        chain=chain,
        output_qty=qty,
        per_unit_sell=per_unit,
        raw_sell_copper=sale_base_batch,
        aged_sell=aged_sell,
        aged_sell_per_unit=aged_sell_per_unit,
        profit_per_rank=profit,
        profit_per_rank_per_unit=profit_per_unit,
        total_brewing_hours=chain.cumulative_time_hours,
        aging_hours_per_rank=AGING_HOURS_TO_REACH,
        is_wine=is_wine,
    )


def all_brew_plans(cat: Catalog, tr: Translator,
                   unlocked_recipe_ids: set[int]) -> list[BrewPlan]:
    out: list[BrewPlan] = []
    seen = set()
    for r in cat.recipes_by_id.values():
        if not r.active or r.group != 2:  # 2 = Drink
            continue
        if r.recipe_id in seen:
            continue
        seen.add(r.recipe_id)
        out.append(build_brew_plan(r, cat, tr,
                                   is_unlocked=r.recipe_id in unlocked_recipe_ids))
    # Sort: unlocked first, then by max-rank profit
    out.sort(key=lambda p: (not p.is_unlocked, -p.profit_per_rank[4]))
    return out
