"""List unique MonoBehaviour script class names with counts."""
import os, sys, collections
import UnityPy
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0f1"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
counts = collections.Counter()
files = []
for r,_,fs in os.walk(GAME):
    for f in fs:
        if f.endswith(".assets") or f.startswith("level") or f.startswith("sharedassets") or f == "resources.assets":
            files.append(os.path.join(r,f))

for p in files:
    try:
        env = UnityPy.load(p)
    except Exception:
        continue
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour": continue
        try:
            d = obj.read()
            sc = d.m_Script
            if sc is None: continue
            s = sc.read()
            cn = getattr(s,"m_ClassName",None) or getattr(s,"name","?")
            counts[cn] += 1
        except Exception as e:
            counts[f"<err:{type(e).__name__}>"] += 1

for k,v in counts.most_common(200):
    print(f"{v:6d} {k}")
