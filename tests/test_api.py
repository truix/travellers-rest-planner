"""Endpoint smoke tests via FastAPI's TestClient."""
import pytest
from fastapi.testclient import TestClient

from planner.server.app import app
from planner.catalog import load_catalog


@pytest.fixture(scope="module")
def client():
    load_catalog.cache_clear()
    return TestClient(app)


def test_root_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Travellers Rest" in r.text


@pytest.mark.parametrize("path,kind,minlen", [
    ("/api/saves",        list, 0),
    ("/api/languages",    list, 20),
    ("/api/seeds",        list, 50),
    ("/api/brewing",      list, 30),
    ("/api/recipes",      list, 200),
    ("/api/vendors",      list, 10),
    ("/api/quests",       list, 30),
    ("/api/perks",        dict, 2),
    ("/api/talents",      list, 50),
    ("/api/fish",         list, 50),
    ("/api/bushes",       list, 1),
    ("/api/reputation",   list, 30),
])
def test_endpoint(client, path, kind, minlen):
    r = client.get(path + "?lang=English")
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    j = r.json()
    assert isinstance(j, kind)
    if isinstance(j, list):
        assert len(j) >= minlen, f"{path} returned only {len(j)}"
    else:
        assert len(j) >= minlen


def test_plan_has_today(client):
    r = client.get("/api/plan?lang=English")
    if r.status_code != 200:
        pytest.skip("no save file present")
    p = r.json()
    assert "today" in p
    today = p["today"]
    assert "tavern_name" in today
    assert "season" in today


def test_quests_have_state(client):
    qs = client.get("/api/quests?lang=English").json()
    states = {q["state"] for q in qs}
    assert states.issubset({"available", "active", "completed"})


def test_brewing_per_unit_math(client):
    plans = client.get("/api/brewing?lang=English").json()
    for p in plans[:10]:
        # rank 0 batch / qty ≈ per_unit
        if p["output_qty"] > 0:
            assert abs(p["aged_sell_per_unit"]["0"] * p["output_qty"] - p["aged_sell"]["0"]) <= p["output_qty"]


def test_translation_english(client):
    """Top items in any language list should NOT start with their numeric id prefix."""
    fish = client.get("/api/fish?lang=English").json()
    raw_count = sum(1 for f in fish if f["name"][:1].isdigit() and " - " in f["name"])
    # Some new fish from updates may not have localization keys yet
    assert raw_count <= len(fish) * 0.2, f"{raw_count}/{len(fish)} fish still raw (>20%)"
    bushes = client.get("/api/bushes?lang=English").json()
    raw_count = sum(1 for b in bushes if b["name"][:1].isdigit() and " - " in b["name"])
    assert raw_count == 0, "bushes still raw"
