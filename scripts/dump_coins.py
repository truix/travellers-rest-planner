"""Extract the GoldCoin / SilverCoin / CopperCoin sprites for the currency formatter."""
import os, sys
import UnityPy
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "icons")
os.makedirs(OUT, exist_ok=True)

WANT = {"GoldCoin": "_gold.png", "SilverCoin": "_silver.png", "CopperCoin": "_copper.png"}
saved = {}

env = UnityPy.load(os.path.join(GAME, "resources.assets"))
for obj in env.objects:
    if obj.type.name != "Sprite":
        continue
    try:
        d = obj.read()
        nm = getattr(d, "m_Name", "") or ""
    except Exception:
        continue
    if nm in WANT and nm not in saved:
        try:
            img = d.image
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            out = os.path.join(OUT, WANT[nm])
            img.save(out, "PNG")
            saved[nm] = out
            print(f"  saved {nm} -> {out}  ({img.size})", file=sys.stderr)
        except Exception as e:
            print(f"  fail {nm}: {e}", file=sys.stderr)

if len(saved) < 3:
    print(f"only {len(saved)}/3 coins extracted", file=sys.stderr)
