"""Brewing chain walker tests."""
from planner.catalog import load_catalog
from planner.i18n import Translator
from planner.plan.brewing import all_brew_plans, build_brew_plan, AGING_PRICE_MULT


def test_brew_plans_load():
    cat = load_catalog()
    tr = Translator("English")
    plans = all_brew_plans(cat, tr, set())
    assert len(plans) >= 30, "should have lots of drink recipes"
    # All chains have at least one slot
    for p in plans:
        assert p.chain.slots, f"empty chain for {p.drink_name}"


def test_rank_grid_math():
    cat = load_catalog()
    tr = Translator("English")
    plans = all_brew_plans(cat, tr, set())
    p = next(p for p in plans if p.profit_per_rank[0] > 0)
    # Rank 4 should be ~1.3× rank 0 sale (approximately, integer rounding)
    expected_r4 = int(p.aged_sell[0] * 1.30)
    assert abs(p.aged_sell[4] - expected_r4) <= 2
    # Per-unit × output_qty == batch
    assert p.aged_sell_per_unit[0] * p.output_qty == p.aged_sell[0] or \
           abs(p.aged_sell_per_unit[0] * p.output_qty - p.aged_sell[0]) <= p.output_qty


def test_chain_walks_substages():
    """Whiskey should walk into a Mill substage for the malt."""
    cat = load_catalog()
    tr = Translator("English")
    whiskey = cat.recipes_by_id.get(534)  # Whisky
    assert whiskey is not None
    plan = build_brew_plan(whiskey, cat, tr, is_unlocked=True)
    has_substage = any(s.sub_stage is not None for s in plan.chain.slots)
    assert has_substage, "whiskey chain should walk into mill substage"
