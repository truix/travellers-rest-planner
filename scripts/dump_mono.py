"""Dump MonoBehaviour ScriptableObject data using TypeTreeGenerator."""
import json, os, sys, collections
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
MANAGED = os.path.join(GAME, "Managed")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dumps", "mono")
TARGETS = {
    # Core item / recipe / crop graph
    "Item","Food","Seed","SproutSeed","Crop","Recipe","RecipeList",
    "MaterialTypeItem","IngredientGroup","ShopItem","ShopRecipe",

    # Living things
    "Animal","AnimalBreeds","AnimalRelationship","Fish","Tree","Bush",
    "BushHarvest","BeersWant",
    "Harvestable","MiscellaneousHarvest","MiscItemHarvest","Herb",

    # Player progression
    "Perk","Talent","TalentAdditions","Tool",

    # World content
    "Quest","Shop","FishingSpot","RegionData","ReputationInfo",
    "GameEvent","Mission","MissionBase","MissionTalkWith","MissionActionDone",
    "ActionDoneQuest","CraftItemTypeQuest","ServeCustomerQuest",
    "UnlockContentQuest","ChristmasTreeQuest","FarmCropQuest","RandomOrderQuestInfo",
    "QuestDatabaseAccessor",

    # Database accessors (master lists)
    "CropDatabaseAccessor","RecipeDatabaseAccessor","ItemDatabaseAccessor",
    "FoodDatabaseAccessor","ShopDatabaseAccessor","PerksDatabaseAccessor",
    "TalentDatabaseAccessor","MissionsDatabaseAccessor","ReputationDBAccessor",
    "ShopDatabase","PerksDatabase","TalentDatabase","MissionsDatabase",

    # Localization
    "LanguageSourceAsset",
}

UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"
os.makedirs(OUT, exist_ok=True)

gen = TypeTreeGenerator("2022.3.0")
gen.load_local_dll_folder(MANAGED)

def get_dict_nodes(t):
    candidates = [t]
    # try common namespaced variants
    if "." not in t:
        candidates += [f"I2.Loc.{t}"]
    for asm in ("Assembly-CSharp-firstpass", "Assembly-CSharp"):
        for full in candidates:
            try:
                return json.loads(gen.get_nodes_as_json(asm, full))
            except Exception:
                pass
    return None

# preload nodes for targets (as dicts → from_list builds correct tree)
node_cache = {}
for t in TARGETS:
    n = get_dict_nodes(t)
    if n: node_cache[t] = n
    else: print(f"no nodes for {t}", file=sys.stderr)

def safe(x, depth=0):
    if depth > 30: return "<deep>"
    if isinstance(x, dict): return {str(k): safe(v, depth+1) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [safe(v, depth+1) for v in x]
    if isinstance(x, (bytes, bytearray)): return f"<bytes len={len(x)}>"
    try: json.dumps(x); return x
    except TypeError: return repr(x)

files = []
for r,_,fs in os.walk(GAME):
    for f in fs:
        if f.endswith(".assets") or f.startswith("level") or f.startswith("sharedassets") or f == "resources.assets":
            files.append(os.path.join(r,f))

count = collections.Counter()
errs = collections.Counter()
print(f"scanning {len(files)} files for {len(node_cache)} target classes", file=sys.stderr)

for path in files:
    try:
        env = UnityPy.load(path)
    except Exception as e:
        print(f"load fail {path}: {e}", file=sys.stderr); continue
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour": continue
        try:
            d = obj.read(check_read=False)
            sc = d.m_Script
            if sc is None: continue
            cn = sc.read().m_ClassName
        except Exception:
            continue
        # Allow dynamic discovery of quest/mission subclasses (Q300_*, etc.)
        if cn not in node_cache:
            if cn.startswith(("Q", "M")) and any(c.isdigit() for c in cn[:5]):
                n = get_dict_nodes(cn)
                if n:
                    node_cache[cn] = n
                else:
                    continue
            else:
                continue
        try:
            tree = obj.read_typetree(node_cache[cn])
        except Exception as e:
            errs[cn] += 1
            continue
        name = tree.get("m_Name") or f"id{obj.path_id}"
        d_out = os.path.join(OUT, cn)
        os.makedirs(d_out, exist_ok=True)
        sn = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))[:80] or f"id{obj.path_id}"
        with open(os.path.join(d_out, f"{sn}__{obj.path_id}.json"), "w", encoding="utf8") as fh:
            json.dump(safe(tree), fh, indent=2, ensure_ascii=False)
        count[cn] += 1

print("=== counts ===")
for k,v in count.most_common(): print(f"{v:6d} {k}")
print("=== errors ===", file=sys.stderr)
for k,v in errs.most_common(): print(f"{v:6d} {k}", file=sys.stderr)
