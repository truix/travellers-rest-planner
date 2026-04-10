"""Item database — for any item, returns everything: sources, uses, vendors,
drops, recipes that produce it, recipes that consume it, crops, fish, etc.

This is the "click any item and see everything" endpoint.
"""
from __future__ import annotations

from planner.catalog import Catalog
from planner.i18n import Translator


def _find_uses(item_id: int, cat: Catalog, tr: Translator) -> list[dict]:
    uses = []
    for r in cat.recipes_by_id.values():
        if not r.active:
            continue
        for iid, amt in r.ingredients:
            if iid == item_id:
                out = cat.items_by_id.get(r.output_item_id)
                out_name_id = out.name_id if out else None
                uses.append({
                    "type": "recipe_ingredient",
                    "recipe_id": r.recipe_id,
                    "name": tr.recipe(r.output_item_id, fallback=r.name,
                                      output_name_id=out_name_id),
                    "output_item_id": r.output_item_id,
                    "amount_needed": amt,
                    "group": ["Material","Food","Drink","Other"][r.group] if r.group < 4 else str(r.group),
                })
                break
    for c in cat.crops_by_id.values():
        if c.seed_item_id == item_id:
            uses.append({
                "type": "planting",
                "crop_id": c.crop_id,
                "crop_name": tr.crop(c.name_id, c.harvest_item_id, c.name),
                "harvest_id": c.harvest_item_id,
                "harvest_name": tr.item(c.harvest_item_id, None, c.name) if c.harvest_item_id else None,
            })
    for gid, grp in cat.groups_by_path_id.items():
        for ipid, mpid in grp.possible_items:
            it = cat.items_by_path_id.get(ipid)
            if it and it.item_id == item_id:
                glabel = tr.get(f"Items/item_name_{grp.group_id}")
                if not glabel:
                    glabel = grp.name.split(" - ", 1)[1] if " - " in grp.name else grp.name
                uses.append({
                    "type": "ingredient_group",
                    "group_name": glabel,
                    "group_id": grp.group_id,
                })
                break
    return uses


def item_detail(item_id: int, cat: Catalog, tr: Translator) -> dict | None:
    """Build a complete dossier on a single item."""
    item = cat.items_by_id.get(item_id)
    if not item:
        # Fish and some other items aren't in items_by_id but exist in the fish catalog
        for f in cat.fishes:
            if f.fish_id == item_id:
                d = f.raw
                sp = d.get("sellPrice") or {}
                sell = sp.get("gold",0)*10000 + sp.get("silver",0)*100 + sp.get("copper",0)
                bp = d.get("price") or {}
                buy = bp.get("gold",0)*10000 + bp.get("silver",0)*100 + bp.get("copper",0)
                name = tr.item(item_id, f.name_id, f.name)
                seasons = ["Spring","Summer","Autumn","Winter"]
                sf = d.get("season", 15)
                return {
                    "item_id": item_id,
                    "name": name,
                    "buy_copper": buy,
                    "sell_copper": sell,
                    "is_food": True,
                    "food_type": d.get("foodType"),
                    "contains_alcohol": False,
                    "has_to_be_aged_meal": False,
                    "sources": [{
                        "type": "fish",
                        "name": name,
                        "difficulty": d.get("difficulty", 0),
                        "fishing_method": d.get("fishingMethod", 0),
                        "water_type": d.get("waterType", 0),
                        "season_flags": sf,
                    }],
                    "uses": (u := _find_uses(item_id, cat, tr)),
                    "source_count": 1,
                    "use_count": len(u),
                }
        return None

    name = tr.item(item.item_id, item.name_id, item.name)

    # === SOURCES: how do you get this item? ===
    sources = []

    # 1. Recipes that PRODUCE this item
    for r in cat.recipes_by_output_item_id.get(item_id, []):
        if not r.active:
            continue
        out_name = tr.recipe(r.output_item_id, fallback=r.name,
                             output_name_id=item.name_id)
        ings = []
        for iid, amt in r.ingredients:
            ing = cat.items_by_id.get(iid)
            ings.append({
                "item_id": iid,
                "name": tr.item(ing.item_id, ing.name_id, ing.name) if ing else f"#{iid}",
                "amount": amt,
            })
        sources.append({
            "type": "recipe",
            "recipe_id": r.recipe_id,
            "name": out_name,
            "output_qty": r.output_qty,
            "time_hours": r.time_hours,
            "ingredients": ings,
        })

    # 2. Crops that harvest into this item
    crop = cat.crops_by_harvest_item_id.get(item_id)
    if crop:
        seed = cat.items_by_id.get(crop.seed_item_id)
        sources.append({
            "type": "crop",
            "crop_id": crop.crop_id,
            "name": tr.crop(crop.name_id, crop.harvest_item_id, crop.name),
            "seed": tr.item(seed.item_id, seed.name_id, seed.name) if seed else None,
            "seed_id": crop.seed_item_id,
            "days_to_grow": crop.days_to_grow,
            "reusable": crop.reusable,
            "regrow_days": crop.days_until_new_harvest,
            "available_seasons": [s for i, s in enumerate(["Spring","Summer","Autumn","Winter"])
                                  if crop.available_seasons & (1 << i)],
            "best_seasons": [s for i, s in enumerate(["Spring","Summer","Autumn","Winter"])
                             if crop.best_seasons & (1 << i)],
            "yield_normal": max(1, crop.amount_best_season - 1),
            "yield_best": crop.amount_best_season,
        })

    # 3. Vendors that sell this item
    for shop in cat.shops:
        for si in shop.items:
            si_pid = (si.get("item") or {}).get("m_PathID", 0)
            si_item = cat.items_by_path_id.get(si_pid)
            if si_item and si_item.item_id == item_id:
                sources.append({
                    "type": "vendor",
                    "vendor": shop.name,
                    "shop_id": shop.shop_id,
                    "buy_copper": si_item.buy_copper,
                    "always_stocked": bool(si.get("alwaysAppear", 0)),
                })

    # 4. Bush/foraging that drops this item
    for bush in cat.bushes:
        h = bush.raw.get("harvestedItems") or {}
        h_pid = 0
        if isinstance(h, dict):
            inner = h.get("item") or h
            h_pid = inner.get("m_PathID", 0) if isinstance(inner, dict) else 0
        h_item = cat.items_by_path_id.get(h_pid)
        if h_item and h_item.item_id == item_id:
            sources.append({
                "type": "foraging",
                "name": tr.item(h_item.item_id, h_item.name_id, h_item.name),
                "amount_min": bush.raw.get("amountMin", 0),
                "amount_max": bush.raw.get("amountMax", 0),
            })

    # 5. Is it a fish?
    for fish in cat.fishes:
        if fish.fish_id == item_id:
            d = fish.raw
            sources.append({
                "type": "fish",
                "difficulty": d.get("difficulty", 0),
                "fishing_method": d.get("fishingMethod", 0),
                "water_type": d.get("waterType", 0),
                "season_flags": d.get("season", 15),
            })

    # === USES: what is this item used for? ===
    uses = _find_uses(item_id, cat, tr)

    return {
        "item_id": item_id,
        "name": name,
        "buy_copper": item.buy_copper,
        "sell_copper": item.sell_copper,
        "is_food": item.is_food,
        "food_type": item.food_type,
        "contains_alcohol": item.contains_alcohol,
        "has_to_be_aged_meal": item.has_to_be_aged_meal,
        "sources": sources,
        "uses": uses,
        "source_count": len(sources),
        "use_count": len(uses),
    }
