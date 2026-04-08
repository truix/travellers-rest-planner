"""Join the JSON dumps into clean tables.

Outputs to gameresearch/data/:
  items.json   -- master path_id -> {name,id,price,sellPrice,...}
  crops.csv    -- crop sheet with seasons, days, harvest, seed
  recipes.csv  -- recipe sheet with ingredients resolved + profit math
  foods.csv    -- food/ingredient sheet
"""
import json, os, csv, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONO = os.path.join(ROOT, "dumps", "mono")
OUT  = os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)

def load_dir(name):
    out = {}
    for p in glob.glob(os.path.join(MONO, name, "*.json")):
        with open(p, encoding="utf8") as f:
            d = json.load(f)
        # path_id from filename suffix
        pid = int(os.path.basename(p).rsplit("__",1)[1].split(".")[0])
        d["__path_id"] = pid
        out[pid] = d
    return out

items   = load_dir("Item")
crops   = load_dir("Crop")
seeds   = load_dir("Seed")
recipes = load_dir("Recipe")
foods   = load_dir("Food")

print(f"items={len(items)} crops={len(crops)} seeds={len(seeds)} recipes={len(recipes)} foods={len(foods)}")

# Master name resolver: PathID -> display name
name_of = {}
for pid, it in items.items():
    name_of[pid] = it.get("m_Name", f"item{pid}")
for pid, f in foods.items():
    name_of.setdefault(pid, f.get("m_Name", f"food{pid}"))
for pid, c in crops.items():
    name_of.setdefault(pid, c.get("m_Name", f"crop{pid}"))
for pid, s in seeds.items():
    name_of.setdefault(pid, s.get("m_Name", f"seed{pid}"))

def resolve(ptr):
    if not isinstance(ptr, dict): return None
    pid = ptr.get("m_PathID", 0)
    if pid == 0: return None
    return name_of.get(pid, f"?{pid}")

def price_to_copper(p):
    if not p: return 0
    # Confirmed in Price.cs:467 — 1 silver = 100 copper, 1 gold = 10,000 copper
    return p.get("gold",0)*10000 + p.get("silver",0)*100 + p.get("copper",0)

# CropSeason flags
SEASONS = [(1,"Spring"),(2,"Summer"),(4,"Autumn"),(8,"Winter")]
def seasons(flag):
    if flag is None: return ""
    return "|".join(n for b,n in SEASONS if flag & b) or "None"

# ---------- items.json (master) ----------
master = {}
for src in (items, foods):
    for pid, it in src.items():
        master[pid] = {
            "path_id": pid,
            "id": it.get("id"),
            "name": it.get("m_Name"),
            "nameId": it.get("nameId"),
            "buy_copper":  price_to_copper(it.get("price")),
            "sell_copper": price_to_copper(it.get("sellPrice")),
            "category": it.get("category"),
            "shop": it.get("shop"),
            "excludedFromTrends": it.get("excludedFromTrends"),
            "foodType": it.get("foodType"),
            "ingredientType": it.get("ingredientType"),
            "containsAlcohol": it.get("containsAlcohol"),
        }
with open(os.path.join(OUT,"items.json"),"w",encoding="utf8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

# ---------- crops.csv ----------
with open(os.path.join(OUT,"crops.csv"),"w",newline="",encoding="utf8") as f:
    w = csv.writer(f)
    w.writerow(["id","name","nameId","seed","available_seasons","best_seasons",
                "days_to_grow","reusable","regrow_days","amount_best_season",
                "harvest_item","harvest_amount"])
    for pid, c in sorted(crops.items(), key=lambda kv: kv[1].get("id",0)):
        seed_n = resolve(c.get("seed"))
        h = (c.get("harvestedItems") or [{}])[0]
        hi = resolve(h.get("item")) if h else None
        ha = h.get("amount") if h else None
        w.writerow([
            c.get("id"), c.get("m_Name"), c.get("nameId"), seed_n,
            seasons(c.get("avaliableSeasons")), seasons(c.get("bestSeasons")),
            c.get("daysToGrow"), c.get("reusable"), c.get("daysUntilNewHarvest"),
            c.get("amountBestSeason"), hi, ha,
        ])

# ---------- foods.csv ----------
with open(os.path.join(OUT,"foods.csv"),"w",newline="",encoding="utf8") as f:
    w = csv.writer(f)
    w.writerow(["path_id","name","foodType","ingredientType","containsAlcohol","canBeAged","canBeSold","seed"])
    for pid, fd in foods.items():
        w.writerow([pid, fd.get("m_Name"), fd.get("foodType"), fd.get("ingredientType"),
                    fd.get("containsAlcohol"), fd.get("canBeAged"), fd.get("canBeSold"),
                    resolve(fd.get("seed"))])

# ---------- recipes.csv ----------
def fmt_ing(ing):
    parts = []
    for x in ing or []:
        nm = resolve(x.get("item")) or "?"
        amt = x.get("amount",1)
        mod = resolve(x.get("mod"))
        parts.append(f"{amt}x {nm}" + (f"[{mod}]" if mod else ""))
    return " + ".join(parts)

GROUPS = {0:"Material",1:"Food",2:"Drink",3:"Other"}
with open(os.path.join(OUT,"recipes.csv"),"w",newline="",encoding="utf8") as f:
    w = csv.writer(f)
    w.writerow(["id","name","group","active","output","output_qty","output_sell_copper",
                "ing_cost_buy_copper","profit_per_craft","profit_per_hour",
                "fuel","time_hours","ingredients"])
    for pid, r in sorted(recipes.items(), key=lambda kv: kv[1].get("id",0)):
        out = r.get("output") or {}
        out_pid = (out.get("item") or {}).get("m_PathID",0)
        out_name = resolve(out.get("item"))
        out_qty = out.get("amount",1)
        out_item = master.get(out_pid, {})
        sell = out_item.get("sell_copper",0) * out_qty
        ing_cost = 0
        for ing in r.get("ingredientsNeeded") or []:
            ipid = (ing.get("item") or {}).get("m_PathID",0)
            ing_cost += master.get(ipid,{}).get("buy_copper",0) * ing.get("amount",1)
        t = r.get("time") or {}
        hours = (t.get("years",0)*365*24 + t.get("weeks",0)*7*24 +
                 t.get("days",0)*24 + t.get("hours",0) + t.get("mins",0)/60)
        active = r.get("usingNewRecipesSystem",1) and not r.get("replacedRecipe",0)
        pph = round((sell-ing_cost)/hours,1) if hours>0 else (sell-ing_cost)
        w.writerow([
            r.get("id"), r.get("m_Name"),
            GROUPS.get(r.get("recipeGroup"), r.get("recipeGroup")),
            int(bool(active)),
            out_name, out_qty, sell, ing_cost, sell-ing_cost, pph,
            r.get("fuel"), round(hours,2),
            fmt_ing(r.get("ingredientsNeeded")),
        ])

print("wrote", os.listdir(OUT))
