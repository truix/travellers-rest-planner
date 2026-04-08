"""Render per-scene tilemap PNGs.

For each level scene, find every Tilemap component, walk its tile placements,
look up the tile sprites via the level's external file references, and
composite into a per-scene PNG.

Tilemap typetree (Unity 2022 / Travellers Rest):
  m_Tiles[]:           tuples of (Vector3Int position, TileChangeData)
  m_TileSpriteArray[]: list of {m_RefCount, m_Data:{m_FileID, m_PathID}}
  m_TileMatrixArray[]: list of {m_RefCount, m_Data: 4x4 matrix}
  m_TileColorArray[]:  list of {m_RefCount, m_Data: rgba}
"""
from __future__ import annotations

import json
import os
import sys
from PIL import Image

import UnityPy
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "maps")
META = os.path.join(ROOT, "data", "maps.json")
os.makedirs(OUT, exist_ok=True)

PPU = 16
MAX_OUTPUT_DIM = 4096


def split_tile(entry):
    if isinstance(entry, tuple) and len(entry) == 2:
        return entry[0], entry[1]
    if isinstance(entry, dict):
        return entry.get("first"), entry.get("second", entry)
    return None, None


def load_sprite_image(obj):
    try:
        d = obj.read()
        img = d.image
        if img is None:
            return None
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        return img
    except Exception:
        return None


def render_scene(env, scene_name, all_objs_by_pid) -> dict | None:
    """env is the FULL game env (so externals resolve). all_objs_by_pid is
    a global path_id index for fast lookup."""
    # Locate the level's SerializedFile inside the env
    level_sf = None
    for cab, sf in env.files.items():
        if scene_name in str(cab):
            level_sf = sf
            break
    if level_sf is None:
        return None

    # SerializedFile.objects is already dict[path_id, ObjectReader]
    level_objs = level_sf.objects

    # The external file list is on the SerializedFile. file_id N (1-indexed)
    # maps to externals[N-1].path which we then look up in env.files.
    externals = getattr(level_sf, "externals", []) or []
    ext_files = []
    for ext in externals:
        # ext.path is like "archive:/CAB-xxxx/sharedassets1.assets"
        # We need to find the matching env.files entry
        ext_name = (getattr(ext, "name", None) or getattr(ext, "path", "") or "").split("/")[-1]
        match = None
        for cab, sf in env.files.items():
            if ext_name and ext_name in str(cab):
                match = sf
                break
        ext_files.append(match)

    def resolve_ref(file_id, path_id):
        if not path_id:
            return None
        if file_id == 0:
            return level_objs.get(path_id)
        idx = file_id - 1
        if idx < 0 or idx >= len(ext_files):
            return None
        sf = ext_files[idx]
        if sf is None:
            return None
        return sf.objects.get(path_id)

    # Walk tilemaps
    tilemaps = []
    for o in level_sf.objects.values():
        if o.type.name != "Tilemap":
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not t.get("m_Tiles"):
            continue
        tilemaps.append((o, t))

    if not tilemaps:
        return None

    # Compute global bounds
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    total = 0
    for _, t in tilemaps:
        for entry in (t.get("m_Tiles") or []):
            pos, _data = split_tile(entry)
            if not isinstance(pos, dict):
                continue
            x = pos.get("x", 0)
            y = pos.get("y", 0)
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            total += 1
    if total == 0 or min_x > max_x:
        return None

    width_t = max_x - min_x + 1
    height_t = max_y - min_y + 1
    pixel_w = min(MAX_OUTPUT_DIM, width_t * PPU)
    pixel_h = min(MAX_OUTPUT_DIM, height_t * PPU)
    if pixel_w * pixel_h > 60_000_000:
        # Scale down by halving the PPU until under budget
        ppu = PPU
        while ppu > 2 and pixel_w * pixel_h > 60_000_000:
            ppu //= 2
            pixel_w = min(MAX_OUTPUT_DIM, width_t * ppu)
            pixel_h = min(MAX_OUTPUT_DIM, height_t * ppu)
    else:
        ppu = PPU

    canvas = Image.new("RGBA", (pixel_w, pixel_h), (0, 0, 0, 0))
    sprite_cache: dict[tuple, Image.Image | None] = {}
    drawn = 0

    for tm_idx, (tm_obj, tm) in enumerate(tilemaps):
        sprite_array = tm.get("m_TileSpriteArray") or []
        # Pre-decode sprites that this tilemap uses
        decoded = []
        for ref_wrap in sprite_array:
            data = ref_wrap.get("m_Data") if isinstance(ref_wrap, dict) else None
            if not data:
                decoded.append(None)
                continue
            fid = data.get("m_FileID", 0)
            pid = data.get("m_PathID", 0)
            key = (fid, pid)
            if key in sprite_cache:
                decoded.append(sprite_cache[key])
                continue
            obj = resolve_ref(fid, pid)
            if obj is None or obj.type.name != "Sprite":
                sprite_cache[key] = None
                decoded.append(None)
                continue
            img = load_sprite_image(obj)
            sprite_cache[key] = img
            decoded.append(img)

        for entry in (tm.get("m_Tiles") or []):
            pos, data = split_tile(entry)
            if not isinstance(pos, dict) or not isinstance(data, dict):
                continue
            si = data.get("m_TileSpriteIndex", -1)
            if si < 0 or si >= len(decoded):
                continue
            img = decoded[si]
            if img is None:
                continue
            tx = pos.get("x", 0) - min_x
            ty = pos.get("y", 0) - min_y
            px = tx * ppu
            py = (height_t - ty - 1) * ppu
            if px < 0 or py < 0 or px + img.width > pixel_w or py + img.height > pixel_h:
                continue
            try:
                # Scale sprite if our ppu is reduced
                if ppu != img.width and img.width > ppu:
                    img2 = img.resize((ppu, ppu), Image.NEAREST)
                else:
                    img2 = img
                canvas.alpha_composite(img2, (int(px), int(py)))
                drawn += 1
            except Exception:
                pass

    if drawn == 0:
        return None

    out_path = os.path.join(OUT, f"{scene_name}.png")
    canvas.save(out_path, "PNG", optimize=True)
    return {
        "scene": scene_name,
        "width": pixel_w,
        "height": pixel_h,
        "ppu": ppu,
        "world_min_x": min_x,
        "world_min_y": min_y,
        "world_max_x": max_x,
        "world_max_y": max_y,
        "drawn_tiles": drawn,
    }


def main():
    hotspots_path = os.path.join(ROOT, "data", "hotspots.json")
    target = set()
    if os.path.exists(hotspots_path):
        with open(hotspots_path, encoding="utf8") as f:
            h = json.load(f)
        for k in ("trees", "foraging", "fishing", "vendors"):
            for x in (h.get(k) or []):
                target.add(x["scene"])
    if not target:
        target = {f"level{i}" for i in range(28)}

    print(f"[maps] loading full game env...", file=sys.stderr)
    env = UnityPy.load(GAME)
    print(f"[maps] {len(env.files)} files loaded", file=sys.stderr)

    metas = {}
    for scene in sorted(target):
        try:
            meta = render_scene(env, scene, None)
        except Exception as e:
            print(f"  fail {scene}: {e}", file=sys.stderr)
            continue
        if meta:
            metas[scene] = meta
            print(f"  ✓ {scene}: {meta['width']}x{meta['height']} ppu={meta['ppu']} ({meta['drawn_tiles']} tiles)", file=sys.stderr)
        else:
            print(f"  · {scene}: empty", file=sys.stderr)

    with open(META, "w", encoding="utf8") as f:
        json.dump(metas, f, indent=2)
    print(f"[maps] wrote {len(metas)} maps", file=sys.stderr)


if __name__ == "__main__":
    main()
