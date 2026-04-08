<div align="center">

# Travellers Rest Planner

**A research, strategy, and live save-reading tool for [Travellers Rest](https://store.steampowered.com/app/1139980/Travellers_Rest/) — the cozy tavern-management game by Isolated games.**

*A better wiki, a brewing dashboard, a menu planner, a world map, and a live game-state reader — all in one self-hosted page.*

[Features](#features) · [Quick start](#quick-start) · [Architecture](#architecture) · [Data extraction](#data-extraction) · [Contributing](#contributing) · [Legal](#legal)

</div>

---

## Why?

The official wiki is sparse and out of date. The in-game UI doesn't tell you which crops will be trending in 3 weeks, which hops give the best margin on a Pilsner, when to start brewing for a rank-4 aged batch to hit Monday's trend rotation, or where in the world that one specific NPC actually stands.

This tool reads your **live save file** every time the game autosaves and joins it with everything we could extract from the game's own asset bundles to answer those questions directly.

## Features

### Live save reading
- Watches your save folder via `watchdog`. The instant the game autosaves, the UI re-renders.
- Reads the .NET BinaryFormatter save via `pypdn`, no game modification or runtime hooking required.
- Supports multiple save slots — pick from a dropdown in the header.
- Reads your tavern name, character name, money, reputation, planted crops, current season/week/day, completed and active quests, days until next trend rotation, and the next 4 weeks of trend lists.

### Plan tab
- Today's snapshot bar (date, money, rep, crops planted, recipes known)
- **Plant now** action cards — exactly which crops to plant today and which day each must be planted by to be ready for an upcoming trend
- **Cook now / brew now** — your unlocked, currently-trending recipes ranked by trend-boosted profit
- **4-week trend almanac** — every food, drink and ingredient that will trend across the next month, with badges for "best season now", "in season", "growing N", "unlocked", "locked"

### Brew planner
For each of the 4 upcoming trend weeks: top trending drinks, the cheapest valid combination of ingredients for each recipe (with **trending ingredients automatically picked** so you also benefit from selling them at +20%), the exact day to start brewing, projected profit at rank 4 + trend bonus, and total time including aging.

### Brewing tab
- Every drink (41) with its full multi-stage chain (mill → mash → ferment), each ingredient slot showing accepted alternatives and per-unit prices
- 5-rank aging grid showing per-unit AND batch prices, profit, and cumulative aging time per rank
- **Punnett-style ingredient combinatorics grid** for any recipe with two `IngredientGroup` slots (e.g. Lager = Pale Malt × Pale Hops) — cheapest combo highlighted in green, most expensive in red
- Currently-trending drinks get a glowing badge

### Menu planner
Tick recipes to add to your tavern menu. Live aggregate stats: total fuel, total cost, total sell value (with +20% trend bonus auto-applied to trending dishes), unique-bar-items bonus computation, drinks count, foods count, trending count.

### Seeds tab
- All 95 crops in a sortable filterable ledger table
- **Color-coded season chips** with the best season highlighted (★)
- Days to grow, perennial regrow days, yield (normal vs best), sell-each, copper/day yield (normal and best), seed cost, currently-planted count
- Gold rows for crops at their best season RIGHT NOW

### Recipes tab
- Every recipe (293 active) — search-as-you-type, group filter, sortable columns
- Per-unit price (skill-stable) AND batch price columns
- **Click a row to expand the full crafting chain**, including aging rank grid for agable recipes (drinks + cheeses + pickles)

### Vendors tab
- All 19 vendor NPCs with their full stock lists
- ★ marker for always-in-stock items
- **Vendor location pill** showing which scene each vendor lives in
- Filter by vendor name or item

### Map tab
- Real **rendered tilemap backgrounds** for 10 scenes (composited from the game's own Tilemap data — `level10`, `level12`, `level20`, etc.)
- Hotspot dots for **607 trees, 333 foraging spots, 122 fishing spots, 56 vendor NPCs, 9 animal spawners**
- Layer toggle (all / trees / foraging / fishing / vendors / animals) and scene picker
- Vendor names labeled inline on the map

### Quests tab
- All 42 quests with description, requirements, reward
- **State badge** read from your save: ✓ done, active, available
- Filter by state and search

### Perks tab
- 56 player perks + 77 employee perks, grouped by tree (Resources, Cooking, Brewing, Crafting, Management, …)
- Localized names and descriptions

### Fish / Foraging / Reputation tabs
- 58 fish species, 8 foraging spots, 56 reputation milestones
- Foraging entries show the season(s) they spawn in and the harvest amount range

### Global fuzzy search
- Header search box indexes everything: recipes, crops, vendors, vendor items, quests, fish, bushes, drinks, perks
- Click a result to jump to that tab and pre-fill its filter

### Localization
- Pulls strings directly from the game's I2 Localization asset (8278 terms × 30 languages)
- Live language switcher in the header — works for every tab

### Currency
- Real **gold / silver / copper sprites** extracted from the game, rendered inline next to every number
- Tabular monospace numerals for clean alignment

### Aesthetic
- Designed as a "warm sunny parchment" tavern ledger book × dense data terminal
- Hand-set typography: IM Fell English (1672 type revival), EB Garamond, JetBrains Mono
- Wooden-frame icon plates, ink-rule section dividers, fleuron ornaments
- Bright daylight palette — *no generic AI dashboard greys*

## Quick start

### Prerequisites
- **Travellers Rest** installed locally (Steam, GOG, or any other source)
- **Python 3.10+**
- A recent .NET runtime (for `ilspycmd` if you want to re-decompile any classes; not required at runtime)

### Install

```bash
git clone https://github.com/YOUR-USERNAME/travellers-rest-planner.git
cd travellers-rest-planner
pip install -r requirements.txt
```

### Extract game data (one-time, ~5 minutes)

The repository ships **no game assets** for legal reasons. The extraction scripts read your local Travellers Rest install and produce the planner's data files.

```bash
python scripts/dump_mono.py      # ScriptableObjects: items, recipes, crops, etc.
python scripts/dump_i2l.py       # Localization terms (30 languages)
python scripts/dump_icons.py     # Item sprites → data/icons/<id>.png
python scripts/dump_coins.py     # Coin sprites for the currency formatter
python scripts/dump_hotspots.py  # Walks scene files for tree/bush/NPC positions
python scripts/dump_maps.py      # Renders scene tilemap PNG backgrounds (~7 MB)
python scripts/synthesize.py     # Builds csv summary tables
```

The scripts **auto-detect** your Steam install on Windows / macOS / Linux. If you have it somewhere unusual, set:

```bash
# Windows
set TR_GAME_DIR=F:\Games\SteamLibrary\steamapps\common\Travellers Rest\Windows\TravellersRest_Data

# macOS
export TR_GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Travellers Rest/Windows/TravellersRest_Data"

# Linux
export TR_GAME_DIR="$HOME/.steam/steam/steamapps/common/Travellers Rest/Windows/TravellersRest_Data"
```

### Run

```bash
python -m planner
```

Then open <http://127.0.0.1:8765/>.

The planner watches `%AppData%/LocalLow/Louqou/TravellersRest/GameSaves/` (or the OS equivalent). Every time the game autosaves, the UI auto-refreshes.

### Run the tests

```bash
pytest -q
```

## Architecture

```
travellers-rest-planner/
│
├── planner/                  ← Python package
│   ├── __main__.py           ← `python -m planner` entry
│   ├── gamepath.py           ← Steam install auto-detect
│   ├── catalog.py            ← Static catalog: items, recipes, crops, shops, perks, etc.
│   ├── i18n.py               ← I2 Localization translator
│   ├── parser/
│   │   ├── saves.py          ← Save file discovery + pypdn deserialization + extract
│   │   └── odin.py           ← (legacy, unused — saves use BinaryFormatter not Odin)
│   ├── plan/
│   │   ├── engine.py         ← Plan tab — today, plant/cook/brew, 4-week calendar
│   │   ├── brewing.py        ← Brewing chain walker + aging math + Punnett combinatorics
│   │   ├── brew_planner.py   ← Per-week brew recommendations
│   │   ├── recipes.py        ← Generic recipe lookup
│   │   └── seeds.py          ← Seeds reference table
│   └── server/
│       ├── app.py            ← FastAPI app + WebSocket + watchdog auto-reload
│       └── static.py         ← Single-file vanilla HTML/JS UI (the whole frontend)
│
├── scripts/                  ← One-shot extractors (run once after install or game patch)
│   ├── dump_mono.py          ← ScriptableObjects via UnityPy + TypeTreeGenerator
│   ├── dump_i2l.py           ← Localization terms (custom binary walker)
│   ├── dump_icons.py         ← Item sprites (file_id-aware, transparent PNGs)
│   ├── dump_coins.py         ← The 3 coin sprites for the formatter
│   ├── dump_hotspots.py      ← Scene-walks every level for placed objects
│   ├── dump_maps.py          ← Composites Tilemap data into per-scene background PNGs
│   └── synthesize.py         ← Joins extracted JSON into csv/json summaries
│
├── tests/                    ← pytest suite (35 tests)
│   ├── test_catalog.py
│   ├── test_currency.py
│   ├── test_brewing.py
│   ├── test_api.py
│   └── test_save_parser.py
│
├── data/                     ← Generated by extractors (gitignored)
├── dumps/                    ← Generated by extractors (gitignored)
├── REPORT.md                 ← Initial reverse-engineering writeup
├── requirements.txt
├── LICENSE                   ← MIT
└── README.md
```

### How the data flows

```
        Travellers Rest install
                │
       ┌────────┴────────┐
       │                 │
  scripts/dump_*       %AppData%/LocalLow/Louqou/.../*.save
       │                 │
       │                 │  watchdog
       ▼                 ▼
   data/, dumps/    parser/saves.py (pypdn → SaveData)
       │                 │
       └────────┬────────┘
                ▼
          planner/catalog.py
                │
                ▼
          planner/plan/* (engine, brewing, brew_planner, recipes, seeds)
                │
                ▼
          planner/server/app.py  (FastAPI + WebSocket)
                │
                ▼
   planner/server/static.py  (single-file HTML/JS UI)
```

### Key reverse-engineering findings

- **Save format**: `System.Runtime.Serialization.Formatters.Binary.BinaryFormatter` (NOT Sirenix Odin Serializer as we initially guessed). Parsed via [`pypdn`](https://pypi.org/project/pypdn/).
- **Trend mechanics** (`Trends.cs:64`): `trendPriceMultiplier = 0.2f` — flat **+20%** sale price for trending items. Trends rotate every Monday. The save stores **4 weeks of trends ahead**, which is what makes plant-by deadlines computable.
- **Aging math** (`AgingBarrel.cs:950`): 24h per rank step, 48h for the rank 3→4 step. Total **5 in-game days** for max rank. Price multipliers from `Money.cs:418-426`: rank 2 +10%, rank 3 +20%, rank 4 +30%.
- **Currency** (`Price.cs:467`): `1 silver = 100 copper`, `1 gold = 100 silver = 10,000 copper`.
- **Customer satisfaction** (`Customer.cs:292`): the satisfaction score (`EEJPHDIFEHG` after Beebyte obfuscation) is multiplied directly into the final price paid. A 0.5-satisfaction customer literally pays half.
- **Unique bar items bonus** (`Money.cs:435`): `+3 copper per unique bar item × every drink sold`. This is why menu variety beats menu depth.
- **Customer info** (`CustomerInfo.cs`): every penalty constant (table dirty, floor dirty, low light, rowdy customer, no food at bar, etc.) extracted into [REPORT.md](./REPORT.md).
- **Obfuscator**: the game's `Assembly-CSharp.dll` is hit with Beebyte Obfuscator 3.12.0 — class names like `Crop`, `Recipe`, `Trends`, `CustomerInfo` survive (those are the public surface), but most method names are random alphabet soup. The data extraction works against the field names, which are stable.

See [REPORT.md](./REPORT.md) for the full writeup.

## Data extraction

| Script | Output | Time | Source |
|---|---|---:|---|
| `dump_mono.py` | `dumps/mono/<Class>/*.json` (~3000 ScriptableObjects: items, recipes, crops, shops, talents, fish, quests, …) | ~30s | `resources.assets`, `sharedassets*` |
| `dump_i2l.py` | `data/i18n.json` (8278 terms × 30 languages) | ~5s | `resources.assets` (LanguageSourceAsset) |
| `dump_icons.py` | `data/icons/<item_id>.png` (~1100 PNGs, file_id-aware to avoid PathID collisions) | ~60s | All asset files |
| `dump_coins.py` | `data/icons/_gold.png`, `_silver.png`, `_copper.png` | ~1s | `resources.assets` |
| `dump_hotspots.py` | `data/hotspots.json` (Tree/Bush/Fish/Vendor positions across scenes) | ~30s | `level0`–`level27` |
| `dump_maps.py` | `data/maps/<scene>.png` (composited Tilemap backgrounds) + `data/maps.json` | ~3 minutes | Full game env |
| `synthesize.py` | `data/items.json`, `data/recipes.csv`, `data/crops.csv`, `data/foods.csv` | ~1s | `dumps/mono/` |

Re-run any of these after a game patch.

## Contributing

PRs welcome. The code is intentionally small and Python-only (no JS build step, no compile steps).

### Areas that could use help
- **More scene tilemap renders** — `level0`, `level2`, etc. use SpriteRenderers instead of Tilemaps and need a different compositor.
- **Crop chain walker** — like the brewing chain walker but for foods (e.g. Pizza → Dough → Flour → Mill Wheat → Wheat).
- **NPC dialogue extraction** — the I2L file has dialog trees we don't surface yet.
- **Translation key mapping for reputation milestones** — they currently show codenames like `BrewAndCook` because no localized titles exist for them in the I2L table.
- **A "what changed since last save" diff view** for tracking progress between gameplay sessions.

### Running tests

```bash
pytest -q          # 35 tests, ~3 seconds
pytest -v          # verbose
```

## Legal

This is a **fan-made tool** for a game I love. It is not affiliated with, endorsed by, or sponsored by Isolated games.

The repository contains **only my own code**. No game assets — sprites, localization strings, ScriptableObject contents, scene art — are bundled. Every extraction script reads from a local copy of the game that the user already owns. The `data/` and `dumps/` folders are generated locally and **gitignored**.

If you are a Louqou employee and would like this tool taken down or modified, please open an issue.

The decompiled C# files in `dumps/*.cs` are gitignored — they're produced by [`ilspycmd`](https://github.com/icsharpcode/ILSpy) against a local copy of `Assembly-CSharp.dll` and are useful only for development reference.

[Travellers Rest on Steam](https://store.steampowered.com/app/1139980/Travellers_Rest/) · [Louqou's website](https://louqou.com/)

## License

[MIT](./LICENSE) — do whatever you want with the code.
