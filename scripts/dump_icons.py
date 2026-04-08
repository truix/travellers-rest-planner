"""Extract item icons as transparent PNGs.

Strategy: we already have all the items dumped as JSON in dumps/mono/. Each
JSON file lives in a path that includes the source asset file as a side-channel
(via __path_id). Walk the dumps to learn (item_id, source_pid) pairs. Then for
each Sprite/Texture2D in the asset bundles, save it as data/icons/<item_id>.png
ONLY if its path_id matches the item's icon ref AND the item lives in the same
asset file (file_id=0 means same-file).

Since we don't track which source file each item JSON came from, we use this
two-pass approach:
1. Walk asset files. For each file, build a map of items found in this file
   (item_id -> icon_pid + icon_fileid).
2. Within the same file, look up sprites by path_id and save them.

This guarantees no PathID collisions across files.
"""
from __future__ import annotations

import os
import sys
import json

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "icons")
os.makedirs(OUT, exist_ok=True)

ITEM_CLASSES = ("Item", "Food", "Seed", "SproutSeed", "Fish")


def make_generator():
    g = TypeTreeGenerator("2022.3.0")
    g.load_local_dll_folder(os.path.join(GAME, "Managed"))
    cache = {}
    for cls in ITEM_CLASSES:
        try:
            cache[cls] = json.loads(g.get_nodes_as_json("Assembly-CSharp", cls))
        except Exception as e:
            print(f"  no nodes for {cls}: {e}", file=sys.stderr)
    return cache


def fix_dict_nodes(nodes):
    # The dict-list form is what UnityPy's read_typetree(nodes) accepts.
    return nodes


def asset_files():
    files = []
    for r, _, fs in os.walk(GAME):
        for f in fs:
            if f.endswith(".resS"):
                continue
            if (f.endswith(".assets")
                    or f.startswith("level")
                    or f.startswith("sharedassets")
                    or f == "resources.assets"):
                files.append(os.path.join(r, f))
    return files


def save_sprite(obj, item_id: int) -> bool:
    out = os.path.join(OUT, f"{item_id}.png")
    try:
        data = obj.read()
        img = data.image
        if img is None:
            return False
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        # If alpha channel is uniformly opaque AND the corner is pure black,
        # treat the texture as a "black-keyed" image and turn black to alpha.
        px = img.load()
        w, h = img.size
        c00 = px[0, 0]
        if len(c00) == 4 and c00[3] == 255 and c00[:3] == (0, 0, 0):
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if r < 4 and g < 4 and b < 4:
                        px[x, y] = (0, 0, 0, 0)
        img.save(out, "PNG")
        return True
    except Exception as e:
        print(f"  fail item={item_id} pid={obj.path_id}: {e}", file=sys.stderr)
        return False


def extract():
    nodes_cache = make_generator()
    files = asset_files()
    print(f"[icons] scanning {len(files)} asset files", file=sys.stderr)

    saved = 0
    skipped = 0
    by_class: dict[str, int] = {}

    for path in files:
        try:
            env = UnityPy.load(path)
        except Exception:
            continue

        objs_by_pid = {o.path_id: o for o in env.objects}

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                d = obj.read(check_read=False)
                cn = d.m_Script.read().m_ClassName
            except Exception:
                continue
            if cn not in nodes_cache:
                continue
            try:
                tree = obj.read_typetree(nodes_cache[cn])
            except Exception:
                continue
            iid = tree.get("id")
            icon_ref = tree.get("icon") or {}
            ipid = icon_ref.get("m_PathID", 0)
            ifid = icon_ref.get("m_FileID", 0)
            if iid is None or not ipid or ifid != 0:
                skipped += 1
                continue
            out_path = os.path.join(OUT, f"{iid}.png")
            if os.path.exists(out_path):
                continue
            target = objs_by_pid.get(ipid)
            if target is None or target.type.name != "Sprite":
                continue
            if save_sprite(target, iid):
                saved += 1
                by_class[cn] = by_class.get(cn, 0) + 1

    print(f"[icons] saved {saved} icons (skipped {skipped})", file=sys.stderr)
    for k, v in sorted(by_class.items(), key=lambda x: -x[1]):
        print(f"  {v:5} {k}", file=sys.stderr)


if __name__ == "__main__":
    extract()
