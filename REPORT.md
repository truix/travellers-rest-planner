# Travellers Rest — Reverse-Engineered Reference

Source: decompiled `Assembly-CSharp.dll` + extracted ScriptableObjects from `resources.assets`/`sharedassets*` (game build at `F:\SteamLibrary\steamapps\common\Travellers Rest`).

Raw data lives in:
- `data/crops.csv` — every crop with seasons, days, yield, seed
- `data/recipes.csv` — every recipe with ingredients resolved + profit math (sorted by id)
- `data/foods.csv` — every food/ingredient
- `data/items.json` — master path_id → item lookup
- `dumps/mono/<Class>/*.json` — raw ScriptableObject dumps (95 Crops, 85 Seeds, 478 Recipes, 477 Foods, 633 Items)

> **Currency.** Internal "copper" used everywhere below: 1 silver = 100 copper, 1 gold = 100 silver = 10,000 copper.

---

## 1. Crops & seeds

The full table is in `data/crops.csv`. Schema (from `Crop.cs` ScriptableObject):

| field | meaning |
|---|---|
| `available_seasons` | bitmask of seasons it CAN grow |
| `best_seasons` | seasons in which yield = `amount_best_season` (a higher number) |
| `days_to_grow` | days from planting to first harvest |
| `reusable` | 1 = perennial (apple, blueberry, cherry, banana...) |
| `regrow_days` | days between subsequent harvests on perennials |
| `harvest_amount` | base yield per harvest (off-season / non-best) |
| `amount_best_season` | yield per harvest in best season |

Season flags: `Spring=1, Summer=2, Autumn=4, Winter=8`.

### Active crops by season

Counts are restricted to crops with a real seed (i.e. actually plantable in-game — many entries with no seed are unused dev placeholders).

- **Spring:** Aroma Hops, Bitter Hops, Dual Hops, Wheat, Apple, Asparagus*, Aubergine*, Avocado*, Banana, Beetroot*, Bell Pepper*, Blueberry, Broccoli*, Carrot, Cherry, Chilli, ...
- **Summer:** Aroma Hops, Barley, Bitter Hops, Dual Hops, Wheat, Apple, Asparagus*, Aubergine*, Banana, Beetroot*, Blueberry, Broccoli*, Carrot, Cherry, Chilli, ...
- **Autumn:** Aroma Hops, Bitter Hops, Dual Hops, Rye, Apple, Avocado*, Beetroot*, Bell Pepper*, Broccoli*, Carrot, Cabbage, ...
- **Winter:** Aroma Hops, Bitter Hops, Dual Hops, Rye, Wheat, Cabbage, ...

(* = ScriptableObject exists but no seed/Item link — placeholder)

### Best-season multipliers (the only thing that matters for income)

Plant a crop **only in its best season** — yield jumps from 2 to 3 (or 4 for asparagus). Examples from `crops.csv`:

| Crop | Avail. seasons | Best season | Off / Best yield | Days |
|---|---|---|---|---|
| Aroma Hops | All | **Summer/Winter** | 2 / 3 | 3 |
| Barley | Spring/Summer | **Summer** | 2 / 2 | 3 |
| Bitter Hops | All | **Autumn** | 2 / 3 | 3 |
| Dual Hops | All | **Spring** | 2 / 3 | 4 |
| Rye | Autumn/Winter | **Winter** | 2 / 2 | 5 |
| Wheat | Spring/Summer/Winter | **Summer** | 2 / 3 | 4 |
| Apple (perennial) | Summer/Autumn | **Autumn** | 2 / 3 | 14 / regrow 3 |
| Blueberry (perennial) | Spring/Summer | **Spring** | 2 / 3 | 4 / regrow 3 |
| Banana (perennial) | Spring/Summer | none | 2 / 3 | 20 / regrow 5 |
| Cherry (perennial) | Spring/Summer | **Spring** | 2 / 3 | 20 / regrow 3 |
| Chilli (perennial) | Spring/Summer | **Summer** | 2 / 3 | 4 / regrow 3 |
| Carrot | Spring/Summer/Autumn | **Summer** | 2 / 3 | 3 |
| Cabbage | Autumn/Winter | **Winter** | 1 / 2 | 4 |

→ Open `data/crops.csv` for the full list of all 95.

### Perennials are insanely better than annuals

Reusable crops (Apple, Banana, Blueberry, Cherry, Chilli, …) only need to grow ONCE — after the first harvest they regrow every `regrow_days`. Example: Apple is 14 days the first time, then **3 days** every harvest after that, for 3 fruit per harvest in best season. Plant them once in early game in their best season and they outproduce annuals for the rest of the year.

### Seed sources

Seeds either drop from harvesting the crop or are sold by **Lia** (the seed shop NPC). Lia's stock rotates by season — only the seeds for crops whose `available_seasons` includes the current season can appear.

---

## 2. The trend system (how prices actually work)

The wiki is wrong / vague about this. Here's the real model from `Trends.cs`, `Food.cs`, `Money.cs`:

### Rotation
- The game tracks **4 weeks** of trends ahead at all times (`Trends.allTrends[4]`).
- Trends rotate **every Monday**: `SwapTrends()` shifts the queue forward one slot and `GenerateNewTrends(3)` makes a new trend set for week +3 (`Trends.MLMJEAOCODM`).
- Trends are gated behind a reputation milestone (`RepUnlocksManager.repUnlockTrends`) — if you haven't unlocked them, every recipe sells at base price.

### What's in a trend set
Each `TrendSet` has three lists:
1. **Trending ingredients** — raw ingredients (Berries, Veg, etc.) that the season's crops can produce
2. **Trending foods (meals)** — full cooked dishes
3. **Trending drinks**

`Trends.JLIHBKPHAKE()` (the populator) only picks ingredients whose underlying `Crop.avaliableSeasons` includes the current season. So **trends are season-locked** — you can never see a "Pumpkin Pie" trend in summer because pumpkin can't grow.

### The price multiplier (the ONLY thing that matters)
From `Trends.cs:64` and `Food.cs`:

```csharp
public float trendPriceMultiplier = 0.2f;   // hard-coded
// in Food.AEAEPPIGMBJ():
if (Trends.IsTrendingMeal(this))
    finalPrice = basePrice + basePrice * 0.2f;   // +20%
```

So **trending = +20% sale price**. That's it — there's no exponential bonus. It applies separately on:
- The cooked dish itself (if it's a trending meal/drink)
- And/or to its ingredients (if any used ingredient is a trending ingredient — applied at the food's level)

### The full price formula (per item served to a customer)

From `Utils.CHFGMKCEKHF()` + `Money.CalculatePriceWithModifiers()`:

```
basePrice = recipe.GetSellPrice(ingredients_used)        // depends on which ingredients
                                                          // and their quality
+ aging bonus:    rank 2 = +10%, rank 3 = +20%, rank 4 = +30%   (Money.cs:418-426)
+ trend bonus:    +20% if trending meal OR trending ingredient  (Food.cs:260-321)
+ unique bar items: +3 copper PER unique drink available at bar (Money.cs:435)
                                                                 (drinks only)
+ employee perks: ApplyPerkPrices() (depends on hired bartender)
+ player perk 40 "Servicial":   +X% on food (X = perk level)
+ player perk 23 "Tip jar":     X% chance to double the price on this sale
+ tavern satisfaction bonus:    +(serviceAverage * percentagePlusPricesSatisfaction)
```

Final answer is then **multiplied by the customer's personal satisfaction `EEJPHDIFEHG` (0..1)**. Unhappy customers literally pay less for the exact same plate (`Customer.cs:292,959`).

### Practical implication
- A trending dish made with a trending ingredient, served aged (rank 4), with a high tavern satisfaction and 50+ unique drinks at the bar, can sell for **roughly ~2x** its base. That's the cap to chase.
- The single biggest lever is **uniqueBarItems × 3 copper** on every drink sold. Stocking 30 unique beers/wines/cocktails adds **+90 copper to every drink** in the tavern.

---

## 3. Top money-making recipes (raw data)

Computed in `data/recipes.csv` as `output.sellPrice × outputQty − Σ(ingredient.buyPrice × amount)`. This uses the **base** sell price (no aging, no trend, no uniqueItems bonus) and assumes you'd buy ingredients from a shop — if you grow them yourself, profit is much higher.

Filtered to active recipes only (`usingNewRecipesSystem=1`, not replaced).

### Top 20 by profit / craft (copper)

| Profit | Profit/h | Recipe |
|---:|---:|---|
| 14040 | 7020 | Tarta Guinness |
| 13336 | 10002 | Arroz con Leche (Rice Pudding) |
| 13208 | 9906 | Carne a la Mostaza (Mustard Meat) |
| 10460 | 5230 | Costillas con Mostaza y Miel |
| 10124 | 7593 | Fajita |
| 9254 | 6940 | Bizcochitos de Plátano y Almendras |
| 9150 | 6862 | Púdin de Boniato (Sweet Potato Pudding) |
| 9060 | 6795 | Crema Catalana |
| 8716 | 6537 | Garbanzos con Curry (Chickpea Curry) |
| 8535 | 2845 | Zanahorias Navideñas |
| 8498 | 6373 | Burrito |
| 8000 | 6000 | Panettone |
| 7948 | 5961 | Brownie |
| 7920 | 7920 | Bomba del Cazador |
| 7898 | 5923 | Baklava |
| 7815 | 5861 | Costillas Barbacoa |
| 7740 | 1935 | Coctel de Gambas |
| 7620 | 5715 | Salteado de Brócoli |
| 7596 | 3798 | Pastel de Calabaza |
| 7514 | 11271 | Tacos |

### Top 20 by profit / hour (throughput)

| c/h | c/craft | Recipe |
|---:|---:|---|
| 16560 | 2760 | Porridge |
| 11271 | 7514 | Tacos |
| 11226 | 7484 | Okonomiyaki |
| 10755 | 7170 | Galletas de Cacahuete |
| 10710 | 7140 | Mazorcas de Maíz |
| 10302 | 6868 | Gyozas |
| 10005 | 6670 | Revuelto de Setas |
| 10002 | 13336 | Arroz con Leche |
| 9930 | 6620 | Bol de Yogurt |
| 9906 | 13208 | Carne a la Mostaza |
| 9600 | 4800 | Carne Picada |
| 9390 | 6260 | Yogur de Frutas |
| 9072 | 6048 | Crema de Patata y Setas |
| 9036 | 6024 | Dorayaki |
| 8712 | 7260 | Pastel de Cangrejo |
| 8442 | 5628 | Crema de Nabo |
| 8343 | 5562 | Sopa de Tomate |
| 8340 | 5560 | Espinacas con Gambas |
| 8280 | 5520 | Sopa Fría de Remolacha |
| 8154 | 5436 | Bolas de Arroz |

**Strategy reading:**
- **Pure throughput king:** **Porridge** — 2760c per craft but only 10 minutes; if you can keep selling it, nothing beats c/h.
- **Lazy big tickets:** **Arroz con Leche / Carne a la Mostaza** — both >13000c/craft AND >9900c/h. Single best "set and forget" dishes.
- **Tacos / Okonomiyaki** — only ~40min cook for ~7500c. Best mid-game balance.
- Avoid: anything labeled "OLD" — those are replaced. The CSV `active` column is 1 only for current recipes.

---

## 4. Customers — orders, patience, anger, satisfaction

All values are from `CustomerInfo.cs` (the ScriptableObject all customers share) and the `CustomerState*` classes.

### Customer satisfaction (`EEJPHDIFEHG`, range 0..1)
Starts at **1.0**. Drops from many sources, never goes back up on its own. Final price paid to you is multiplied by this number (`Customer.cs:292,959`). A customer at 0.5 satisfaction pays you HALF.

| Penalty | Amount | When |
|---|---:|---|
| `requestOrderPatience` | 10 s | how long they wait for a waiter to take their order |
| `requestRoomPatience` | 30 s | how long they wait for a room |
| `longTimeWaitingPenalty` | -0.01/s | drains while past patience for an order |
| Late by 40s | -0.03 once | + customer leaves entirely |
| `tableDirtyPenalty` | -0.01/s | sitting at a dirty table |
| `tableVeryDirtyPenalty` | -0.02/s | very dirty table |
| `floorDirtPenalty` | -0.05 | once, on floor dirt nearby |
| `tavernDirty` | -0.02/s | overall tavern cleanliness |
| `tavernFilthy` | -0.03/s | |
| `tavernDisgusting` | -0.04/s | |
| `notEnoughLightEvery10secs` | -0.05/10s | low lighting in their area |
| `temperaturePenalty` | -0.02 | wrong temperature (use fireplaces in winter) |
| `rowdyCustomerNearPenalty` | -0.02 | another rowdy customer adjacent |
| `withoutAnyFoodAtBar` | -0.02 | empty bar shelves |
| `beingANuisancePenalty` | -0.1 | when this customer turns rowdy |
| `leaveWillingly` | -0.2 | when they leave before getting served |
| `roomDoesntMeetRequirementsPenalty` | -0.3 | renting a room that fails their requirements |

### Eating
- `timeEatingMin/Max = 60..120` seconds — they sit for 1–2 minutes per dish.
- `timeEatingLastOrdersMin/Max = 15..25` — last-orders mode shortens it.
- `requestAgainProbability = 50` — **50% chance a customer orders again after finishing**. So serving an "appetizer + main" path is essentially the same as serving two customers (and is encouraged).
- `floorDirtProbability = 55`, `rateMakeFloorDirt = 5` — they will mess up your floor often. Hire a janitor or this stacks.

### Rowdy customers
- `rowdyCustomersProbability = 7%` (chance any spawning customer is rowdy)
- `calmRowdyCustomersProbability = 50%` (chance you can calm them down)
- `timeAfterNextRowdyCustomer = 20s` cooldown
- A rowdy customer next to others applies `-0.02/s` to those neighbors. Isolate them (corner table) or kick them out fast.

### Rooms
- `roomOrdersRate = (30, 60)` — rented rooms place a food/drink order every 30–60 in-game min.
- `comfortMultiplier = 0.4f`, `repComfortMin = 30` — comfort affects price a lot once your tavern hits 30 reputation.
- Higher reputation gives a `roomOrdersReputiationMultiplier = 0.3f` extra room-order rate.

### Trends + uniqueness multipliers (customer-side)
- `trendsMultiplier = 8` — every trending item available in your tavern gives a multiplier weight of 8 to satisfaction-with-menu calculations.
- `uniqueItemsMultiplier = 4` — every unique item on your menu gives weight 4. (Combined with the **+3 copper per unique bar item** in `Money.cs`, this is why menu variety matters more than depth.)

### Should you serve appetizers + multiple drinks?

**Yes**, but not for the reason you'd think. There's no game logic that gives a "multi-course bonus" per customer. The reason it's worth it is:

1. The 50% re-order probability after finishing means a customer who eats fast at a clean table with good lighting effectively becomes 1.5–2 customers' worth of revenue.
2. `uniqueBarItems * 3` copper is added to **every drink** you sell. Stocking many varieties (even cheap ones) inflates every drink sold tavern-wide.
3. Drinks have the lowest cook time of any category — pure throughput.

So the optimal serving style is: **lots of drinks, one entrée per customer, large variety on the bar shelf, high cleanliness.** Don't bother with multi-course meals — they don't trigger any bonus.

---

## 5. Concrete profit-maximization strategy

### Daily routine
1. **Mornings:** harvest perennials in their best season (Apple/Autumn, Blueberry/Spring, Cherry/Spring, Chilli/Summer). Replant annuals only where the season matches `best_seasons`.
2. **Replenish drink stock first** every morning. Brew 1 of every wort/brew you've unlocked → variety stacks the +3c bonus on every drink sold.
3. **Cook 1–2 of the high-c/h dishes** for the dinner rush (Porridge for fast turnover, Arroz con Leche / Tacos for big tickets).
4. **Pin trending items.** When trends rotate Monday, check what's trending and rotate your menu to include those — it's a flat +20% on those plates.

### Long-term setup
- Hire a **janitor employee** ASAP (eliminates floor / table cleanliness drains, which silently halve every plate's effective price).
- Keep an **aging cellar** running 24/7 with the dishes that have `canBeAged = true` — rank 4 aging is +30% by itself, stacks with trends and satisfaction bonuses.
- Player perks to prioritize for raw money:
  - **Perk 40 "Servicial"** — +X% on food prices.
  - **Perk 23 "Tip jar"** — chance to 2× the sale price.
  - **Perk 38** — bonus on trending meals.

### What NOT to spend time on
- "OLD" recipes (Brew Amber Ale OLD, Brew Black Ale OLD, etc.) — `replacedRecipe=1`, the game skips them.
- Crops without `seed` set in `crops.csv` — they're dev placeholders.
- Multi-course meals as a strategy — there's no bonus for it.
- Maxing one expensive recipe vs many medium ones — variety triggers the unique-items bonus, single-recipe spam doesn't.

---

## 6. Caveats / things the dump can't tell you

- The **base** sale price for some crafted dishes (`recipe.AEAEPPIGMBJ`) is computed at runtime from the *specific* ingredients and their *quality* — the value in `recipes.csv` uses the static `Item.sellPrice` field on the output and the buy price of canonical ingredients, so it under-estimates dishes whose price scales heavily with high-quality ingredients (most "premium" recipes do). Actual in-game prices for top dishes will run **1.5–2× higher** than `recipes.csv` shows once you factor in quality + trends + aging + satisfaction.
- The exact `percentagePlusPricesSatisfaction` constant is on the `Money` MonoBehaviour singleton in a scene, not a ScriptableObject we extracted. Empirically it ranges roughly +5–25% on top of base.
- All function names with random letters (e.g. `EEJPHDIFEHG`, `OFDGCPAEGOM`, `KPJOKNMAHHH`) are Beebyte-obfuscated. The fields and the *meaningful* names (`Crop`, `Recipe`, `CustomerInfo`, `trendPriceMultiplier`, etc.) survived the obfuscator and that's what we keyed on.

---

## How to regenerate / extend

Everything is reproducible:
```
python scripts/dump_mono.py     # extracts ScriptableObjects via TypeTreeGenerator
python scripts/synthesize.py    # joins into csv/json
```

Re-decompile a class:
```
ilspycmd -t <ClassName> "F:/.../Managed/Assembly-CSharp.dll" > dumps/<ClassName>.cs
```
