import { useEffect, useMemo, useRef, useState } from "react";
import { fetchSaves, fetchLanguages, fetchPlan } from "./api";
import {
  Plan, SaveSlot, Language, CookSuggestion, PlantSuggestion, WeekPlan, TrendItem,
} from "./types";

function fmtMoney(copper: number): string {
  // Per Price.cs:467: 1 silver = 100 copper, 1 gold = 10,000 copper
  const g = Math.floor(copper / 10000);
  const s = Math.floor((copper % 10000) / 100);
  const c = copper % 100;
  const parts = [];
  if (g) parts.push(`${g}g`);
  if (s || g) parts.push(`${s}s`);
  parts.push(`${c}c`);
  return parts.join(" ");
}

function Today({ today }: { today: Plan["today"] }) {
  return (
    <section className="today">
      <div className="stat">
        <div className="label">Date</div>
        <div className="value">{today.season} W{today.week_in_season}</div>
        <div className="label">{today.day_of_week} · year {today.year}</div>
      </div>
      <div className="stat">
        <div className="label">Trend rotates</div>
        <div className="value">in {today.next_trend_rotation_in_days}d</div>
      </div>
      <div className="stat">
        <div className="label">Money</div>
        <div className="value">{fmtMoney(today.money_copper)}</div>
      </div>
      <div className="stat">
        <div className="label">Tavern Rep</div>
        <div className="value">{today.tavern_rep}</div>
      </div>
      <div className="stat">
        <div className="label">Crops planted</div>
        <div className="value">{today.planted_count}</div>
        <div className="label">{today.unique_planted} unique</div>
      </div>
      <div className="stat">
        <div className="label">Recipes unlocked</div>
        <div className="value">{today.unlocked_recipes}</div>
      </div>
    </section>
  );
}

function CookCard({ s }: { s: CookSuggestion }) {
  return (
    <div className="card">
      <div className="title">
        <span className="name">{s.recipe_name}</span>
        <span className="profit">+{fmtMoney(s.base_profit_with_trend - s.profit_per_craft)} · {fmtMoney(s.base_profit_with_trend)} total</span>
      </div>
      <div className="meta">
        {s.time_hours}h cook · fuel {s.fuel} · {Math.round(s.base_profit_with_trend / Math.max(s.time_hours, 0.01))}c/h
      </div>
      <div className="meta">
        ingredients: {s.ingredients.map(([_, a, n]) => `${a}× ${n}`).join(" + ")}
      </div>
      {s.why.length > 0 && <div className="why">{s.why.join(" · ")}</div>}
    </div>
  );
}

function PlantCard({ s }: { s: PlantSuggestion }) {
  return (
    <div className="card">
      <div className="title">
        <span className="name">
          {s.crop_name} {s.is_best_now && <span className="badge best">BEST</span>}
        </span>
        <span className="profit">
          {s.plant_by_day === 0 ? "plant TODAY" : `plant within ${s.plant_by_day}d`}
        </span>
      </div>
      <div className="meta">
        {s.days_to_grow}d to grow
        {s.reusable && ` · perennial (regrow ${s.days_until_new_harvest}d)`}
        {" · "}{s.yield_per_harvest}/harvest
        {" · target trend wk+"}{s.target_for_trend_week}
      </div>
      <div className="meta">
        seasons: {s.available_seasons.join(", ")} (best: {s.best_seasons.join(", ") || "none"})
      </div>
      <div className="why">{s.why.join(" · ")}</div>
    </div>
  );
}

function TrendItemRow({ t }: { t: TrendItem }) {
  let badge: { cls: string; text: string } | null = null;
  if (t.unlocked_recipe_ids.length > 0) badge = { cls: "ok", text: "unlocked" };
  else if (t.recipe_ids.length > 0) badge = { cls: "bad", text: "locked" };
  if (t.grow_crop_id) {
    if (t.grow_best_season_now) badge = { cls: "best", text: "BEST now" };
    else if (t.grow_in_season_now) badge = { cls: "ok", text: "in season" };
    else badge = { cls: "warn", text: "off-season" };
    if (t.is_planted) badge = { cls: "ok", text: `growing ${t.planted_count}` };
  }
  return (
    <div className="item">
      <span>{t.name}</span>
      {badge && <span className={`badge ${badge.cls}`}>{badge.text}</span>}
    </div>
  );
}

function CalendarWeek({ w }: { w: WeekPlan }) {
  return (
    <div className={"week" + (w.week_offset === 0 ? " current" : "")}>
      <h3>
        Week +{w.week_offset}
        <span className="when">{w.season_at_start} · in {w.days_until_start}d</span>
      </h3>
      <div className="group">
        <div className="label">Foods</div>
        {w.food_trends.map((t) => <TrendItemRow key={"f"+t.item_id} t={t} />)}
      </div>
      <div className="group">
        <div className="label">Drinks</div>
        {w.drink_trends.map((t) => <TrendItemRow key={"d"+t.item_id} t={t} />)}
      </div>
      <div className="group">
        <div className="label">Ingredients</div>
        {w.ingredient_trends.map((t) => <TrendItemRow key={"i"+t.item_id} t={t} />)}
      </div>
    </div>
  );
}

export default function App() {
  const [saves, setSaves] = useState<SaveSlot[]>([]);
  const [langs, setLangs] = useState<Language[]>([]);
  const [slot, setSlot] = useState<string>("");
  const [lang, setLang] = useState<string>("English");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [wsLive, setWsLive] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // initial load
  useEffect(() => {
    fetchSaves().then((s) => {
      setSaves(s);
      if (s.length && !slot) setSlot(s[0].slot_id);
    }).catch((e) => setError(String(e)));
    fetchLanguages().then(setLangs).catch(() => {});
  }, []);

  // load plan whenever slot/lang changes
  const reload = async () => {
    if (!slot) return;
    try {
      const p = await fetchPlan(slot, lang);
      setPlan(p);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  };
  useEffect(() => { reload(); }, [slot, lang]);

  // websocket — auto-reload on save change
  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    // In dev (vite proxy) connect via the same origin; vite proxies /ws.
    const url = `${proto}://${location.host}/ws`;
    let alive = true;
    const open = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => setWsLive(true);
      ws.onclose = () => {
        setWsLive(false);
        if (alive) setTimeout(open, 2000);
      };
      ws.onmessage = (ev) => {
        try {
          const m = JSON.parse(ev.data);
          if (m.type === "save_changed") {
            // small debounce so the file finishes writing
            setTimeout(reload, 500);
          }
        } catch {}
      };
    };
    open();
    return () => { alive = false; wsRef.current?.close(); };
  }, [slot, lang]);

  return (
    <>
      <header className="top">
        <h1>TRAVELLERS REST PLANNER</h1>
        <select value={slot} onChange={(e) => setSlot(e.target.value)}>
          {saves.map((s) => (
            <option key={s.slot_id} value={s.slot_id}>{s.label}</option>
          ))}
        </select>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          {langs.map((l) => (
            <option key={l.code} value={l.name}>{l.name}</option>
          ))}
        </select>
        <span className={"ws-status " + (wsLive ? "live" : "dead")}>
          {wsLive ? "live" : "offline"}
        </span>
      </header>

      <main>
        {error && <div className="card" style={{ borderColor: "var(--bad)", color: "var(--bad)" }}>{error}</div>}
        {!plan && !error && <div className="empty">loading…</div>}
        {plan && (
          <>
            <Today today={plan.today} />

            <h2 className="section">Plant now</h2>
            {plan.plant_now.length === 0
              ? <div className="empty">Nothing trending that you can plant in time.</div>
              : <div className="row">
                  <div>{plan.plant_now.filter((_, i) => i % 2 === 0).map((s) => <PlantCard key={s.crop_id} s={s} />)}</div>
                  <div>{plan.plant_now.filter((_, i) => i % 2 === 1).map((s) => <PlantCard key={s.crop_id} s={s} />)}</div>
                </div>}

            <h2 className="section">Cook now (trending food, unlocked)</h2>
            {plan.cook_now.length === 0
              ? <div className="empty">No trending food recipes unlocked.</div>
              : plan.cook_now.map((s) => <CookCard key={s.recipe_id} s={s} />)}

            <h2 className="section">Brew now (trending drinks, unlocked)</h2>
            {plan.brew_now.length === 0
              ? <div className="empty">No trending drinks unlocked.</div>
              : plan.brew_now.map((s) => <CookCard key={s.recipe_id} s={s} />)}

            <h2 className="section">4-week trend calendar</h2>
            <div className="calendar">
              {plan.calendar.map((w) => <CalendarWeek key={w.week_offset} w={w} />)}
            </div>
          </>
        )}
      </main>
    </>
  );
}
