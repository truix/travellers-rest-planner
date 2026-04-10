"""FastAPI backend for the Travellers Rest planner.

Endpoints:
  GET  /api/saves                 list available save slots
  GET  /api/state?slot=&lang=     return current GameState (raw)
  GET  /api/plan?slot=&lang=      return computed Plan (the main payload)
  GET  /api/languages             list available locales
  WS   /ws                        push 'updated' messages when a watched
                                  save file changes on disk

Static UI is served from planner/web/dist/ at /. In dev you can run the
React+Vite frontend separately on :5173 and it will hit /api/* via proxy.
"""
from __future__ import annotations

import asyncio
import json as _json_mod
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from planner.catalog import load_catalog
from planner.i18n import available_languages, DEFAULT_LANG
from planner.parser.saves import (
    discover_slots, get_slot, parse_save, extract, saves_root, latest_save_in_folder,
)
from planner.plan.engine import build_plan, plan_to_dict
from planner.plan.brewing import all_brew_plans, build_brew_plan
from planner.plan.brew_planner import build_brew_plan_view
from planner.plan.seeds import build_seed_table
from planner.plan.recipes import list_craftables, get_recipe_detail
from planner.plan.itemdb import item_detail
from planner.i18n import Translator
from dataclasses import asdict, is_dataclass


# ---------- WebSocket connection manager ------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        text = json.dumps(msg)
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------- Watchdog observer ------------------------------------------------

class SaveWatcher(FileSystemEventHandler):
    """Watches the GameSaves root and broadcasts whenever a .save file changes."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self._last_emit_at = 0.0

    def _emit(self, path: str):
        # Debounce: the game writes save files in bursts
        import time
        now = time.time()
        if now - self._last_emit_at < 0.5:
            return
        self._last_emit_at = now
        coro = manager.broadcast({"type": "save_changed", "path": path})
        try:
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        except Exception:
            pass

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".save"):
            self._emit(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".save"):
            self._emit(event.src_path)


_observer: Observer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _observer
    loop = asyncio.get_running_loop()
    root = saves_root()
    if os.path.isdir(root):
        _observer = Observer()
        _observer.schedule(SaveWatcher(loop), root, recursive=True)
        _observer.start()
        print(f"[planner] watching {root}", flush=True)
    yield
    if _observer:
        _observer.stop()
        _observer.join()


app = FastAPI(title="Travellers Rest Planner", lifespan=lifespan)

# Allow Vite dev server (5173) to hit the API in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Routes -----------------------------------------------------------

@app.get("/api/saves")
def api_saves():
    slots = discover_slots()
    return [
        {
            "slot_id": s.slot_id,
            "label": s.label,
            "mtime": s.mtime,
            "latest_file": s.latest_file,
        }
        for s in slots
    ]


@app.get("/api/languages")
def api_languages():
    return [{"name": l["name"], "code": l["code"]} for l in available_languages()]


def _load_state_for(slot_id: str | None):
    slot = get_slot(slot_id)
    if not slot:
        return None
    # Re-discover the latest save in the slot folder so we always pick up the freshest
    latest = latest_save_in_folder(slot.folder) or slot.latest_file
    mt = os.path.getmtime(latest)
    try:
        root = parse_save(latest)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
    try:
        return extract(root, slot_id=slot.slot_id, save_path=latest, save_mtime=mt)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


@app.get("/api/state")
def api_state(slot: str | None = Query(default=None)):
    state = _load_state_for(slot)
    if state is None:
        return JSONResponse({"error": "no save"}, status_code=404)
    return {
        "slot_id": state.slot_id,
        "save_path": state.save_path,
        "save_mtime": state.save_mtime,
        "money_copper": state.money_copper,
        "tavern_rep": state.tavern_rep,
        "days_to_next_trend": state.days_to_next_trend,
        "current_date": vars(state.current_date),
        "trends": [
            {
                "food_ids": t.food_ids,
                "drink_ids": t.drink_ids,
                "ingredient_ids": t.ingredient_ids,
            } for t in state.trends
        ],
        "unlocked_recipe_ids": list(state.unlocked_recipe_ids),
        "planted_crop_counts": state.planted_crop_counts,
    }


@app.get("/api/plan")
def api_plan(
    slot: str | None = Query(default=None),
    lang: str = Query(default=DEFAULT_LANG),
):
    try:
        state = _load_state_for(slot)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"save parse failed: {e}"}, status_code=500)
    if state is None:
        return JSONResponse({"error": "no save"}, status_code=404)
    try:
        cat = load_catalog()
        plan = build_plan(state, cat, language=lang)
        return plan_to_dict(plan)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"plan build failed: {e}"}, status_code=500)


def _to_jsonable(obj):
    if is_dataclass(obj):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


@app.get("/api/seeds")
def api_seeds(slot: str | None = Query(default=None),
              lang: str = Query(default=DEFAULT_LANG)):
    state = _load_state_for(slot)
    cat = load_catalog()
    return build_seed_table(state, cat, language=lang)


def _vendor_locations() -> dict[str, list[dict]]:
    """Map vendor name -> list of {scene, x, y} from hotspots."""
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hotspots.json"))
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf8") as f:
        h = json.load(f)
    out: dict[str, list[dict]] = {}
    for v in (h.get("vendors") or []):
        nm = (v.get("name") or "").lower()
        if not nm:
            continue
        out.setdefault(nm, []).append({"scene": v["scene"], "x": v["x"], "y": v["y"]})
    return out


@app.get("/api/vendors")
def api_vendors(slot: str | None = Query(default=None),
                lang: str = Query(default=DEFAULT_LANG)):
    """Every vendor with the items they sell, localized."""
    cat = load_catalog()
    tr = Translator(lang)
    locs = _vendor_locations()
    out = []
    for s in cat.shops:
        items = []
        for entry in s.items:
            ipid = (entry.get("item") or {}).get("m_PathID", 0)
            it = cat.items_by_path_id.get(ipid)
            if not it:
                continue
            items.append({
                "item_id": it.item_id,
                "name": tr.item(it.item_id, it.name_id, it.name),
                "buy_copper": it.buy_copper,
                "sell_copper": it.sell_copper,
                "weight": entry.get("weight", 1),
                "always": bool(entry.get("alwaysAppear", 0)),
                "min": entry.get("min", 0),
                "max": entry.get("max", 0),
                "unlimited": bool(entry.get("unlimited", 0)),
            })
        loc = locs.get(s.name.lower(), [])
        out.append({
            "shop_id": s.shop_id,
            "vendor": s.name,
            "shop_type": s.shop_type,
            "item_count": len(items),
            "items": items,
            "locations": loc,
        })
    return out


@app.get("/api/quests")
def api_quests(slot: str | None = Query(default=None),
               lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    state = _load_state_for(slot)
    completed_ids = state.quests_done if state else set()
    active_ids = set(state.quests_active.keys()) if state else set()
    out = []
    for q in cat.quests:
        # Quest nameId is the literal i18n key (e.g. "questNamePorridge")
        name = tr.get(q.name_id) or q.name_id or f"quest #{q.quest_id}"
        desc = tr.get(q.description) or q.description
        state_label = "completed" if q.quest_id in completed_ids else (
                      "active" if q.quest_id in active_ids else "available")
        out.append({
            "quest_id": q.quest_id,
            "name": name,
            "description": desc,
            "required_amount": q.required_amount,
            "is_repeatable": q.is_repeatable,
            "only_halloween": q.only_on_halloween,
            "only_christmas": q.only_on_christmas,
            "recipes_unlocked": q.recipes_unlocked,
            "state": state_label,
        })
    return out


# Perk tree categories: the data file holds the Spanish names. Map to the
# English/i18n keys observed in the I2L term table.
PERK_TREE_KEY = {
    "Recursos": "Resources",
    "Cocina": "Cooking",
    "Servicio": "Service",
    "Granja": "Farming",
    "Cervecería": "Brewing",
    "Cerveceria": "Brewing",
    "Ganadería": "Livestock",
    "Ganaderia": "Livestock",
    "Crianza": "Livestock",
    "Personalidad": "Personality",
    "Comportamiento": "Behaviour",
    "Habilidad": "Ability",
    "Fabricación": "Crafting",
    "Fabricacion": "Crafting",
    "Gestión": "Management",
    "Gestion": "Management",
    "Habilidades": "Skills",
}


@app.get("/api/perks")
def api_perks(lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    def _conv(perks, key_prefix):
        out = []
        for p in perks:
            n = tr.get(f"Perks/{key_prefix}_name_{p.perk_id}") or p.name
            d = tr.get(f"Perks/{key_prefix}_description_{p.perk_id}") or p.description
            tree_key = PERK_TREE_KEY.get(p.perk_tree, p.perk_tree)
            tree_loc = tr.get(tree_key) or tree_key
            out.append({
                "perk_id": p.perk_id,
                "name": n,
                "description": d,
                "tree": tree_loc,
            })
        return out
    return {
        "player": _conv(cat.player_perks, "playerPerk"),
        "employee": _conv(cat.employee_perks, "perk"),
    }


@app.get("/api/talents")
def api_talents(lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    return [{
        "talent_id": t.talent_id,
        "name": tr.get(t.name_id) or t.name,
        "description": tr.get(t.name_id and f"talentDesc_{t.name_id}") or t.description,
    } for t in cat.talents]


@app.get("/api/fish")
def api_fish(lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    out = []
    for f in cat.fishes:
        # Fish IS-A Item — its localization key is Items/item_name_<id>
        name = tr.item(f.fish_id, f.name_id, f.name)
        out.append({
            "fish_id": f.fish_id,
            "name": name,
        })
    return out


SEASON_FLAG = {1: "Spring", 2: "Summer", 4: "Autumn", 8: "Winter"}

@app.get("/api/bushes")
def api_bushes(lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    seen: dict[int, dict] = {}
    for b in cat.bushes:
        d = b.raw
        # harvestedItems is either a single dict {item:{m_PathID}, amount} (Misc*),
        # or a list of those dicts, or just a {m_PathID} (BushHarvest).
        h = d.get("harvestedItems") or d.get("harvestedItem")
        candidates: list[tuple[int, int]] = []  # (item_pid, amount)
        if isinstance(h, dict):
            inner = h.get("item") or h
            ipid = inner.get("m_PathID", 0) if isinstance(inner, dict) else 0
            if ipid:
                candidates.append((ipid, h.get("amount", 1)))
        elif isinstance(h, list):
            for entry in h:
                if isinstance(entry, dict):
                    inner = entry.get("item") or entry
                    ipid = inner.get("m_PathID", 0) if isinstance(inner, dict) else 0
                    if ipid:
                        candidates.append((ipid, entry.get("amount", 1)))

        for ipid, amt in candidates:
            h_item = cat.items_by_path_id.get(ipid)
            if not h_item:
                continue
            name = tr.item(h_item.item_id, h_item.name_id, h_item.name)
            seasons = [SEASON_FLAG[bit] for bit in (1, 2, 4, 8)
                       if d.get("avaliableSeasons", 0) & bit]
            cls = d.get("_class", "BushHarvest")
            rec = {
                "bush_id": h_item.item_id,
                "name": name,
                "harvest_amount_min": d.get("amountMin", amt),
                "harvest_amount_max": d.get("amountMax", amt),
                "days_to_grow": d.get("daysToGrow", 0),
                "probability": d.get("probability", 0),
                "seasons": seasons,
                "kind": cls,
            }
            if h_item.item_id in seen:
                ex = seen[h_item.item_id]
                ex["seasons"] = sorted(set(ex["seasons"]) | set(seasons),
                                       key=lambda s: ["Spring","Summer","Autumn","Winter"].index(s))
                ex["harvest_amount_min"] = min(ex["harvest_amount_min"], rec["harvest_amount_min"])
                ex["harvest_amount_max"] = max(ex["harvest_amount_max"], rec["harvest_amount_max"])
            else:
                seen[h_item.item_id] = rec
    return sorted(seen.values(), key=lambda x: x["name"])


@app.get("/api/hotspots")
def api_hotspots():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hotspots.json"))
    if not os.path.exists(p):
        return JSONResponse({"error": "hotspots not extracted — run scripts/dump_hotspots.py"}, status_code=404)
    with open(p, encoding="utf8") as f:
        return json.load(f)


@app.get("/api/reputation")
def api_reputation(lang: str = Query(default=DEFAULT_LANG)):
    cat = load_catalog()
    tr = Translator(lang)
    out = []
    for r in cat.reputations:
        rep_num = r.raw.get("repNumber", 0)
        title = r.raw.get("title", "") or ""
        # Try common i18n key patterns
        name = tr.get(title) or tr.get(f"reputationLevel_{rep_num}") or title or r.name
        # Strip the "N - " prefix on raw fallback
        if name and " - " in name and name.split(" - ", 1)[0].isdigit():
            name = name.split(" - ", 1)[1]
        out.append({
            "rep_id": rep_num,
            "name": name,
            "customers_capacity": r.raw.get("customersCapacity", 0),
            "floor": r.raw.get("floorDisponible", 0),
            "dining_zones": r.raw.get("diningZonesNumber", 0),
            "crafting_zones": r.raw.get("craftingZonesNumber", 0),
            "rented_rooms": r.raw.get("rentedRoomsNumber", 0),
        })
    out.sort(key=lambda x: x["rep_id"])
    return out


@app.get("/api/item/{item_id}")
def api_item(item_id: int, lang: str = Query(default=DEFAULT_LANG)):
    """Full dossier on any item — sources, uses, vendors, crops, recipes."""
    cat = load_catalog()
    tr = Translator(lang)
    detail = item_detail(item_id, cat, tr)
    if not detail:
        return JSONResponse({"error": "item not found"}, status_code=404)
    return detail


@app.get("/api/items")
def api_items(lang: str = Query(default=DEFAULT_LANG), q: str = Query(default="")):
    """Search all items by name."""
    cat = load_catalog()
    tr = Translator(lang)
    query = q.strip().lower()
    results = []
    for item in cat.items_by_id.values():
        name = tr.item(item.item_id, item.name_id, item.name)
        if query and query not in name.lower():
            continue
        results.append({
            "item_id": item.item_id,
            "name": name,
            "buy_copper": item.buy_copper,
            "sell_copper": item.sell_copper,
            "is_food": item.is_food,
        })
    results.sort(key=lambda x: x["name"])
    return results


@app.get("/api/recipes")
def api_recipes(slot: str | None = Query(default=None),
                lang: str = Query(default=DEFAULT_LANG),
                q: str = Query(default=""),
                group: int | None = Query(default=None)):
    state = _load_state_for(slot)
    cat = load_catalog()
    tr = Translator(lang)
    unlocked = state.unlocked_recipe_ids if state else None
    return list_craftables(cat, tr, unlocked=unlocked, query=q, group_filter=group)


@app.get("/api/recipe/{recipe_id}")
def api_recipe_detail(recipe_id: int,
                      slot: str | None = Query(default=None),
                      lang: str = Query(default=DEFAULT_LANG)):
    state = _load_state_for(slot)
    cat = load_catalog()
    tr = Translator(lang)
    unlocked = state.unlocked_recipe_ids if state else None
    detail = get_recipe_detail(recipe_id, cat, tr, unlocked=unlocked)
    if detail is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return _to_jsonable(detail)


@app.get("/api/brew-plan")
def api_brew_plan(slot: str | None = Query(default=None),
                  lang: str = Query(default=DEFAULT_LANG)):
    state = _load_state_for(slot)
    if state is None:
        return JSONResponse({"weeks": []}, status_code=200)
    cat = load_catalog()
    tr = Translator(lang)
    return build_brew_plan_view(state, cat, tr)


@app.get("/api/brewing")
def api_brewing(slot: str | None = Query(default=None),
                lang: str = Query(default=DEFAULT_LANG)):
    state = _load_state_for(slot)
    cat = load_catalog()
    tr = Translator(lang)
    unlocked = state.unlocked_recipe_ids if state else set()
    plans = all_brew_plans(cat, tr, unlocked)
    return _to_jsonable(plans)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # ignore inbound, just keep it alive
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# ---------- Static UI -------------------------------------------------------
# Prefer the built React app if it exists; otherwise serve a vanilla HTML fallback.

from fastapi.responses import HTMLResponse
from planner.server.static import INDEX_HTML

ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "icons"))
if os.path.isdir(ICONS_DIR):
    app.mount("/icons", StaticFiles(directory=ICONS_DIR), name="icons")

MAPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "maps"))
if os.path.isdir(MAPS_DIR):
    app.mount("/maps", StaticFiles(directory=MAPS_DIR), name="maps")


@app.get("/api/maps")
def api_maps():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "maps.json"))
    if not os.path.exists(p):
        return JSONResponse({}, status_code=200)
    with open(p, encoding="utf8") as f:
        return json.load(f)

WEB_DIST = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
WEB_DIST = os.path.abspath(WEB_DIST)
if os.path.isdir(WEB_DIST) and os.path.isdir(os.path.join(WEB_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST, "assets")), name="assets")

    @app.get("/")
    def index_react():
        return FileResponse(os.path.join(WEB_DIST, "index.html"))
else:
    @app.get("/", response_class=HTMLResponse)
    def index_vanilla():
        return INDEX_HTML


# ---------- entry ------------------------------------------------------------

def main():
    import uvicorn
    uvicorn.run("planner.server.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
