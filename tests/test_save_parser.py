"""Save file parser tests — only run if a real save exists."""
import os
import pytest

from planner.parser.saves import discover_slots, load_state


@pytest.fixture(scope="module")
def state():
    slots = discover_slots()
    if not slots:
        pytest.skip("no save slots present")
    return load_state()


def test_save_parses(state):
    assert state.money_copper >= 0
    assert state.tavern_rep >= 0
    assert state.current_date.season in (0, 1, 2, 3)
    assert state.current_date.day in range(7)
    assert len(state.trends) == 4, "should have 4 weeks of trend lookahead"


def test_trends_populated(state):
    for w, ts in enumerate(state.trends):
        assert isinstance(ts.food_ids, list)
        assert isinstance(ts.drink_ids, list)
        assert isinstance(ts.ingredient_ids, list)


def test_player_and_tavern_name(state):
    assert isinstance(state.tavern_name, str)
    assert isinstance(state.player_name, str)


def test_quests(state):
    assert isinstance(state.quests_done, set)
    # Quest IDs are positive integers
    assert all(isinstance(q, int) for q in state.quests_done)
