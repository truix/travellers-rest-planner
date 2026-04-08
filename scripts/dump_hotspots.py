"""Walk every Unity scene file looking for spawned game objects with positions.

Outputs data/hotspots.json with shape:
  {
    "scenes": ["level0", "level1", ...],
    "trees":   [{"scene": "...", "x": ..., "y": ..., "kind": "Apple", "item_id": 205}],
    "bushes":  [{"scene": "...", "x": ..., "y": ..., "kind": "Wild Berries", "item_id": 3073}],
    "fishingSpots": [...],
    "ores":    [...]
  }

Approach: for each scene file, find every MonoBehaviour of class
Tree / OnlineTree / OnlineCropTree / BushHarvest / OnlineBushHarvest /
FishingSpot / FishPoolObject. For each, find its parent GameObject's Transform
and read the position. Walk the Transform parent chain until we hit a root,
which gives us the world position (Unity stores local positions).

We can't easily resolve the kind (apple vs cherry) without joining with the
prefab data — for now we just record the type/scene/x/y.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import UnityPy
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "hotspots.json")

# class -> bucket name in the output
CLASS_BUCKETS = {
    "Tree":                  "trees",
    "OnlineTree":            "trees",
    "OnlineCropTree":        "trees",
    "BushHarvest":           "foraging",
    "OnlineBushHarvest":     "foraging",
    "MiscellaneousHarvest":  "foraging",
    "OnlineMiscellaneousHarvest": "foraging",
    "MiscItemHarvest":       "foraging",
    "Harvestable":           "foraging",
    "MushroomsSpawner":      "foraging",
    "Herb":                  "foraging",
    "FishingSpot":           "fishing",
    "FishPoolObject":        "fishing",
    "FishThrowSpawner":      "fishing",
    "AnimalsSpawner":        "animals",
    "OnlineAnimal":          "animals",
    "AnimalsPetShop":        "vendors",
    "ShopBaseUI":            "vendors",
    "OpenShop":              "vendors",
    "NPCSpawner":            "npcs",
}


def get_world_position(transform_obj, env_objects_by_pid):
    """Walk Transform parent chain summing local positions."""
    x, y = 0.0, 0.0
    cur = transform_obj
    seen = set()
    while cur is not None and cur.path_id not in seen:
        seen.add(cur.path_id)
        try:
            d = cur.read_typetree()
        except Exception:
            try:
                d = cur.read()
                d = vars(d)
            except Exception:
                break
        pos = d.get("m_LocalPosition") or {}
        x += pos.get("x", 0)
        y += pos.get("y", 0)
        father = d.get("m_Father") or {}
        fpid = father.get("m_PathID", 0)
        if not fpid:
            break
        cur = env_objects_by_pid.get(fpid)
    return x, y


def find_transform_for_gameobject(go_obj):
    """A GameObject has a m_Component list of components; find the Transform."""
    try:
        d = go_obj.read_typetree()
    except Exception:
        return None
    for comp in d.get("m_Component", []) or []:
        c = comp.get("component") or comp
        pid = c.get("m_PathID", 0) if isinstance(c, dict) else 0
        if not pid:
            continue
        # Look it up later — we don't know type here without reading
        return pid
    return None


def extract():
    out = defaultdict(list)
    scene_count = 0
    for entry in sorted(os.listdir(GAME)):
        full = os.path.join(GAME, entry)
        if not os.path.isfile(full):
            continue
        # Only the level files (scenes) — not sharedassets
        if not (entry.startswith("level") and not entry.endswith(".resS")):
            continue
        if "." in entry:  # skip level0.assets etc.
            continue
        try:
            env = UnityPy.load(full)
        except Exception as e:
            print(f"  load fail {entry}: {e}", file=sys.stderr)
            continue
        scene_count += 1

        # Index objects by path_id for parent-walking
        objects_by_pid = {o.path_id: o for o in env.objects}

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                d = obj.read(check_read=False)
                cn = d.m_Script.read().m_ClassName
            except Exception:
                continue
            bucket = CLASS_BUCKETS.get(cn)
            # Catch any class ending in NPC and not the generic base classes
            if bucket is None and cn.endswith("NPC") and cn not in (
                "OnlineBaseNPC", "OnlineDialogueNPC", "HumanNPC",
                "SimpleDialogueNPC", "SimpleTavernDialogueNPC",
                "GuardNPC", "ChickenNPC", "CowNPC", "SheepNPC", "OxNPC",
                "CorgiNPC", "CrabNPC", "TurkeyNPC", "MonsterNPC", "AnimalNPC",
            ):
                bucket = "vendors"
            if bucket is None:
                continue
            # Walk to the GameObject -> Transform
            try:
                go_pid = d.m_GameObject.path_id if d.m_GameObject else 0
            except Exception:
                go_pid = 0
            if not go_pid:
                continue
            go = objects_by_pid.get(go_pid)
            if go is None:
                continue
            # Find the Transform component on this GameObject
            try:
                go_data = go.read_typetree()
            except Exception:
                continue
            transform_pid = 0
            for comp in (go_data.get("m_Component") or []):
                cref = (comp.get("component") if isinstance(comp, dict) else None) or {}
                pid = cref.get("m_PathID", 0)
                if not pid:
                    continue
                child = objects_by_pid.get(pid)
                if child is None:
                    continue
                if child.type.name == "Transform" or child.type.name == "RectTransform":
                    transform_pid = pid
                    break
            if not transform_pid:
                continue
            transform = objects_by_pid.get(transform_pid)
            if transform is None:
                continue
            x, y = get_world_position(transform, objects_by_pid)
            entry_data = {
                "scene": entry,
                "x": round(x, 2),
                "y": round(y, 2),
                "class": cn,
            }
            # For named NPC vendors, store the npc name (strip "NPC" suffix)
            if bucket == "vendors":
                entry_data["name"] = cn[:-3] if cn.endswith("NPC") else cn
            out[bucket].append(entry_data)

    result = {"scenes": [f"level{i}" for i in range(28)], **out}
    counts = {k: len(v) for k, v in out.items()}
    print(f"[hotspots] {scene_count} scenes, counts: {counts}", file=sys.stderr)
    with open(OUT, "w", encoding="utf8") as f:
        json.dump(result, f, indent=2)
    print(f"[hotspots] wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    extract()
