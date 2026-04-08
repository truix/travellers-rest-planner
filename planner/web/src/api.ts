import { Plan, SaveSlot, Language } from "./types";

// In dev, vite proxies /api → :8765. In prod the FastAPI server serves the
// built files itself, so relative URLs work either way.
const API = "";

export async function fetchSaves(): Promise<SaveSlot[]> {
  const r = await fetch(`${API}/api/saves`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchLanguages(): Promise<Language[]> {
  const r = await fetch(`${API}/api/languages`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchPlan(slot: string, lang: string): Promise<Plan> {
  const params = new URLSearchParams();
  if (slot) params.set("slot", slot);
  if (lang) params.set("lang", lang);
  const r = await fetch(`${API}/api/plan?${params}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
