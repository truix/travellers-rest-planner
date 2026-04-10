"""Catalog loader smoke tests — make sure the static dumps load and key
joins work."""
from planner.catalog import load_catalog


def test_catalog_loads():
    cat = load_catalog()
    assert len(cat.items_by_id) > 1000, "items master table should be large"
    assert len(cat.crops_by_id) >= 90
    assert len(cat.recipes_by_id) >= 400
    assert len(cat.shops) >= 19
    assert len(cat.player_perks) > 30
    assert len(cat.employee_perks) > 30
    assert len(cat.fishes) >= 50


def test_blueberry_crop():
    """Blueberry is the canonical example we've been using all along."""
    cat = load_catalog()
    blueberry = cat.crops_by_id.get(15)
    assert blueberry is not None
    assert "Blueberry" in blueberry.name
    assert blueberry.reusable is True
    assert blueberry.days_to_grow == 4
    assert blueberry.amount_best_season == 3


def test_banana_seed_loaded():
    """Banana uses SproutSeed (not Seed). Regression test for the fix."""
    cat = load_catalog()
    banana = cat.crops_by_id.get(12)
    assert banana is not None
    assert banana.seed_item_id is not None
    seed_item = cat.items_by_id[banana.seed_item_id]
    assert "Banana Sprout" in seed_item.name


def test_food_aging_flag():
    """canBeAged should be loaded correctly — only ~9 foods qualify, not all of them."""
    cat = load_catalog()
    agable = [i for i in cat.items_by_id.values() if i.has_to_be_aged_meal]
    assert 5 <= len(agable) <= 30, f"agable foods should be a small set, got {len(agable)}"


def test_recipe_resolves_ingredients():
    cat = load_catalog()
    # Steamed Eggplants — recipe id 413
    r = cat.recipes_by_id.get(413)
    assert r is not None
    assert r.output_qty == 20
    assert len(r.raw_ingredients) > 0


def test_ingredient_groups_loaded():
    cat = load_catalog()
    assert len(cat.groups_by_path_id) > 30
    # At least some groups should have resolved members (some are placeholders)
    populated = [g for g in cat.groups_by_path_id.values() if g.possible_items]
    assert len(populated) > 20
