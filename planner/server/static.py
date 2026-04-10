"""Single-file vanilla HTML/JS UI — the Tavernkeeper's Daylight Ledger.

Aesthetic: warm sunny parchment × hand-bound tavern almanac. Bright, cheery,
pixel-friendly. Typography: IM Fell English (1672 type revival) for display,
EB Garamond for body, JetBrains Mono for tabular numbers.
"""

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Travellers Rest Planner</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English+SC&family=IM+Fell+English:ital@0;1&family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* ============================================================
   THE DAYLIGHT LEDGER — DESIGN TOKENS  (bright & cheery)
   ============================================================ */
:root {
  /* warm parchment palette */
  --parch-deep:    #ead7a6;   /* aged page edge */
  --parch:         #faf2d8;   /* main page */
  --parch-soft:    #f7ecc7;   /* card */
  --parch-bright:  #fff8e1;   /* hover / highlight */
  --parch-shadow:  #d9c692;
  --rule:          #c9b478;   /* ink ruling */
  --rule-soft:     #d8c692;
  --rule-deep:     #ad9554;

  /* warm sky / midday accents */
  --sky:           #c8e0e8;
  --sky-deep:      #6c9bb1;
  --moss:          #6a9248;
  --moss-deep:     #4e7030;
  --moss-pale:     #d6e6bf;
  --burgundy:      #983d3d;
  --burgundy-deep: #6e1f1f;

  /* ink — high contrast warm brown text */
  --ink:           #1a1008;
  --ink-soft:      #2e2010;
  --ink-faded:     #5a4228;
  --ink-ghost:     #8a7050;

  /* coin colours — golden hour */
  --gold:          #b07d18;
  --gold-bright:   #d49a2a;
  --gold-deep:     #8a5e0a;
  --silver:        #6f6e62;
  --silver-deep:   #4d4c43;
  --copper:        #a85a1a;
  --copper-bright: #c97026;

  /* glows */
  --gold-glow:     rgba(208, 144, 28, 0.28);

  /* typography */
  --font-display:    'IM Fell English', 'EB Garamond', Georgia, serif;
  --font-display-sc: 'IM Fell English SC', 'IM Fell English', Georgia, serif;
  --font-body:       'EB Garamond', Georgia, serif;
  --font-mono:       'JetBrains Mono', ui-monospace, 'Cascadia Mono', monospace;
}

/* ============================================================
   RESET + GLOBAL
   ============================================================ */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--parch);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.55;
  font-weight: 500;
  font-feature-settings: "liga", "kern", "onum";
  min-height: 100vh;
  /* paper grain via SVG noise + warm vignette */
  background-image:
    radial-gradient(ellipse at 50% -10%, #fff5d8 0%, transparent 55%),
    radial-gradient(ellipse at 80% 110%, rgba(217, 198, 146, 0.5) 0%, transparent 55%),
    url("data:image/svg+xml;utf8,%3Csvg viewBox='0 0 280 280' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.6' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.42 0 0 0 0 0.32 0 0 0 0 0.18 0 0 0 0.10 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
::selection { background: var(--gold-glow); color: var(--ink); }

/* scrollbars */
::-webkit-scrollbar { width: 12px; height: 12px; }
::-webkit-scrollbar-track { background: var(--parch-shadow); }
::-webkit-scrollbar-thumb { background: var(--rule-deep); border-radius: 0; border: 2px solid var(--parch-shadow); }
::-webkit-scrollbar-thumb:hover { background: var(--gold-deep); }

/* ============================================================
   THE LEDGER SPINE — sticky header
   ============================================================ */
header.spine {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(180deg, var(--parch-bright) 0%, var(--parch) 100%);
  border-bottom: 2px double var(--rule-deep);
  box-shadow: 0 4px 16px -8px rgba(120, 85, 30, 0.3);
}
header.spine .row {
  max-width: 1640px;
  margin: 0 auto;
  padding: 14px 28px 12px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 24px;
  align-items: center;
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.brand .seal {
  font-family: var(--font-display);
  font-size: 30px;
  color: var(--gold);
  text-shadow: 0 0 12px var(--gold-glow);
  line-height: 1;
}
.brand h1 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 22px;
  letter-spacing: 0.01em;
  color: var(--ink);
}
.brand h1 em {
  font-style: italic;
  color: var(--burgundy);
}
.brand .tavern {
  font-family: var(--font-display);
  font-size: 14px;
  font-style: italic;
  color: var(--ink-faded);
  border-left: 1px solid var(--rule);
  padding-left: 12px;
  margin-left: 4px;
}
.brand .tavern .at { color: var(--ink-ghost); margin-right: 4px; }
.brand .tavern .by { color: var(--ink-ghost); margin: 0 4px; }

.controls {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}
.controls label {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.18em;
  color: var(--ink-ghost);
  text-transform: uppercase;
  margin-right: 2px;
}
.controls select, .controls input {
  background: var(--parch-bright);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--rule);
  border-radius: 0;
  cursor: pointer;
  appearance: none;
  transition: border-color .2s;
}
.controls select { padding-right: 24px;
  background-image:
    linear-gradient(45deg, transparent 50%, var(--gold-deep) 50%),
    linear-gradient(135deg, var(--gold-deep) 50%, transparent 50%);
  background-position: calc(100% - 12px) 50%, calc(100% - 8px) 50%;
  background-size: 4px 4px;
  background-repeat: no-repeat;
}
.controls select:hover, .controls input:hover { border-color: var(--gold-deep); }
.controls select:focus, .controls input:focus { outline: none; border-color: var(--gold); }

.global-search {
  position: relative;
  min-width: 220px;
}
.global-search input {
  width: 100%;
  padding-left: 30px !important;
  cursor: text;
}
.global-search::before {
  content: "❦";
  position: absolute;
  left: 10px; top: 50%;
  transform: translateY(-50%);
  font-family: var(--font-display);
  color: var(--gold-deep);
  pointer-events: none;
}
.search-results {
  position: absolute;
  top: 110%;
  right: 0;
  width: 420px;
  max-height: 480px;
  overflow-y: auto;
  background: var(--parch-bright);
  border: 1px solid var(--rule-deep);
  box-shadow: 0 12px 32px -12px rgba(80, 50, 10, 0.5);
  z-index: 200;
  display: none;
}
.search-results.open { display: block; }
.search-result {
  padding: 8px 12px;
  border-bottom: 1px solid var(--parch-shadow);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.search-result:hover { background: var(--gold-glow); }
.search-result .kind {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.16em;
  color: var(--ink-ghost);
  text-transform: uppercase;
}
.search-result .nm { color: var(--ink); flex: 1; }

.ws-pill {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 5px 10px;
  border: 1px solid var(--rule);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-faded);
  background: var(--parch-bright);
}
.ws-pill::before {
  content: "";
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--ink-ghost);
}
.ws-pill.live { color: var(--moss-deep); border-color: var(--moss-deep); background: var(--moss-pale); }
.ws-pill.live::before {
  background: var(--moss);
  box-shadow: 0 0 8px var(--moss);
  animation: pulse 2.4s ease-in-out infinite;
}
.ws-pill.dead { color: var(--burgundy); border-color: var(--burgundy); }
.ws-pill.dead::before { background: var(--burgundy); }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ============================================================
   TAB NAV
   ============================================================ */
nav.tabs {
  position: sticky;
  top: 60px;
  z-index: 90;
  background: var(--parch-soft);
  border-bottom: 1px solid var(--rule);
  overflow: visible;
}
nav.tabs .row {
  max-width: 1640px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  gap: 2px;
  overflow: visible;
}
nav.tabs button {
  background: transparent;
  border: 0;
  color: var(--ink-faded);
  font-family: var(--font-display-sc);
  font-size: 12px;
  letter-spacing: 0.14em;
  padding: 13px 16px 11px;
  cursor: pointer;
  position: relative;
  transition: color .2s;
  display: flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
  text-transform: uppercase;
}
nav.tabs button .glyph {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--ink-ghost);
  transition: color .2s, transform .3s;
}
nav.tabs button:hover { color: var(--ink); }
nav.tabs button:hover .glyph { color: var(--gold); transform: translateY(-1px); }
nav.tabs button.active { color: var(--burgundy-deep); }
nav.tabs button.active .glyph { color: var(--gold); }
nav.tabs button.active::after {
  content: "";
  position: absolute;
  left: 14px; right: 14px; bottom: -1px;
  height: 2px;
  background: var(--burgundy);
}

/* Tab dropdowns */
.tab-dropdown {
  position: relative;
}
.tab-dropdown .tab-trigger {
  background: transparent;
  border: 0;
  color: var(--ink-faded);
  font-family: var(--font-display-sc);
  font-size: 12px;
  letter-spacing: 0.14em;
  padding: 13px 16px 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
  text-transform: uppercase;
  transition: color .2s;
}
.tab-dropdown .tab-trigger .glyph {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--ink-ghost);
  transition: color .2s;
}
.tab-dropdown:hover .tab-trigger { color: var(--ink); }
.tab-dropdown:hover .tab-trigger .glyph { color: var(--gold); }
.tab-dropdown.has-active .tab-trigger { color: var(--burgundy-deep); }
.tab-dropdown.has-active .tab-trigger .glyph { color: var(--gold); }
.tab-dropdown.has-active .tab-trigger::after {
  content: "";
  position: absolute;
  left: 14px; right: 14px; bottom: -1px;
  height: 2px;
  background: var(--burgundy);
}
.tab-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--parch-bright);
  border: 1px solid var(--rule-deep);
  box-shadow: 0 8px 24px -8px rgba(60, 35, 10, 0.4);
  z-index: 80;
  min-width: 180px;
}
.tab-dropdown.open .tab-menu { display: block; }
.tab-menu button {
  display: block;
  width: 100%;
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--parch-deep);
  color: var(--ink-soft);
  font-family: var(--font-body);
  font-size: 14px;
  padding: 10px 18px;
  text-align: left;
  cursor: pointer;
  transition: background .15s, color .15s;
}
.tab-menu button:last-child { border-bottom: 0; }
.tab-menu button:hover { background: var(--gold-glow); color: var(--burgundy-deep); }
.tab-menu button.active { color: var(--burgundy-deep); font-weight: 600; }

/* ============================================================
   MAIN
   ============================================================ */
main {
  max-width: 1640px;
  margin: 0 auto;
  padding: 28px 28px 80px;
}

#err {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--burgundy);
  background: rgba(152, 61, 61, 0.08);
  border: 1px solid var(--burgundy);
  padding: 10px 14px;
  margin-bottom: 20px;
}

.tab-shell { animation: fade-up .35s ease-out; }
@keyframes fade-up {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ============================================================
   ORNAMENTAL TYPOGRAPHY
   ============================================================ */
.section-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 32px 0 14px;
  font-family: var(--font-display-sc);
  font-size: 13px;
  letter-spacing: 0.18em;
  color: var(--ink-faded);
  text-transform: uppercase;
}
.section-head::before, .section-head::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--rule-deep), transparent);
}
.section-head .ornament {
  color: var(--gold);
  font-family: var(--font-display);
  font-size: 17px;
}
.section-head:first-child { margin-top: 0; }

.empty {
  color: var(--ink-ghost);
  font-style: italic;
  font-size: 13px;
  padding: 10px 0;
}

/* ============================================================
   STAT TILES
   ============================================================ */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule-deep);
  margin-bottom: 32px;
  box-shadow: 0 8px 24px -16px rgba(120, 85, 30, 0.35);
}
.stat-tile {
  background: var(--parch-soft);
  padding: 18px 20px 16px;
  position: relative;
  overflow: hidden;
}
.stat-tile::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at top right, var(--gold-glow), transparent 70%);
  opacity: 0;
  transition: opacity .3s;
  pointer-events: none;
}
.stat-tile:hover::before { opacity: 1; }
.stat-tile .label {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--ink-ghost);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.stat-tile .value {
  font-family: var(--font-display);
  font-size: 24px;
  color: var(--ink);
  line-height: 1.05;
}
.stat-tile .value.money { font-family: var(--font-mono); font-size: 19px; font-weight: 500; }
.stat-tile .sub {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.16em;
  color: var(--ink-ghost);
  margin-top: 6px;
  text-transform: uppercase;
}

/* ============================================================
   CURRENCY
   ============================================================ */
.coin {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.95em;
}
.coin.muted { opacity: 0.65; }
.coin .unit {
  display: inline-flex;
  align-items: center;
  gap: 1px;
}
.coin .unit img {
  width: 12px;
  height: 12px;
  image-rendering: pixelated;
  vertical-align: middle;
  display: inline-block;
}
.coin .g { color: var(--gold-bright); font-weight: 600; }
.coin .s { color: var(--silver-deep); font-weight: 500; }
.coin .c { color: var(--copper-bright); font-weight: 500; }
.coin .neg { color: var(--burgundy); margin-right: 1px; }
.coin .zero { color: var(--ink-ghost); }

/* ============================================================
   ACTION CARDS
   ============================================================ */
.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
@media (max-width: 1100px) {
  .action-grid { grid-template-columns: 1fr; }
  .stat-grid { grid-template-columns: repeat(3, 1fr); }
}
.card {
  background: var(--parch-soft);
  border: 1px solid var(--rule);
  padding: 14px 16px 12px;
  position: relative;
  transition: border-color .2s, background .2s;
}
.card::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--burgundy);
  opacity: 0;
  transition: opacity .2s;
}
.card:hover { border-color: var(--rule-deep); background: var(--parch-bright); }
.card:hover::before { opacity: 1; }
.card.locked { opacity: 0.55; }
.card .head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.card .title {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 16px;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}
.card .meta {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-soft);
  margin-top: 2px;
  font-weight: 500;
}
.card .why {
  font-family: var(--font-body);
  font-size: 12px;
  font-style: italic;
  color: var(--burgundy);
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--rule);
}

/* ============================================================
   BADGES
   ============================================================ */
.badge {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 2px 8px;
  border: 1px solid currentColor;
  white-space: nowrap;
  display: inline-block;
  vertical-align: middle;
}
.badge.gold  { color: var(--gold-deep); background: rgba(208,144,28,0.12); }
.badge.gold.glow { box-shadow: 0 0 14px var(--gold-glow); animation: glow 2.4s ease-in-out infinite; }
@keyframes glow {
  0%, 100% { box-shadow: 0 0 10px var(--gold-glow); }
  50%      { box-shadow: 0 0 22px var(--gold-glow); }
}
.badge.moss   { color: var(--moss-deep); background: rgba(106,146,72,0.12); }
.badge.ember  { color: var(--copper); background: rgba(168,90,26,0.12); }
.badge.wax    { color: var(--burgundy); background: rgba(152,61,61,0.10); }
.badge.dim    { color: var(--ink-ghost); }
.badge.sky    { color: var(--sky-deep); background: rgba(108,155,177,0.14); }

/* ============================================================
   CALENDAR
   ============================================================ */
.calendar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule-deep);
}
@media (max-width: 1100px) { .calendar { grid-template-columns: repeat(2, 1fr); } }
.week {
  background: var(--parch-soft);
  padding: 14px 16px 16px;
  position: relative;
}
.week.current {
  background: linear-gradient(180deg, var(--parch-bright) 0%, #fff5d8 100%);
}
.week.current::before {
  content: "NOW";
  position: absolute;
  top: 12px; right: 14px;
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--burgundy-deep);
  background: var(--parch-bright);
  padding: 2px 6px;
  border: 1px solid var(--burgundy);
}
.week h3 {
  margin: 0 0 4px;
  font-family: var(--font-display);
  font-size: 19px;
  color: var(--burgundy-deep);
  font-weight: 400;
}
.week h3 .ord { color: var(--ink-faded); font-style: italic; margin-right: 6px; }
.week .when {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--ink-ghost);
  text-transform: uppercase;
  margin-bottom: 12px;
}
.week .group { margin-top: 12px; }
.week .group-label {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--gold-deep);
  text-transform: uppercase;
  margin-bottom: 4px;
  padding-bottom: 3px;
  border-bottom: 1px solid var(--rule);
}
.week .item {
  font-family: var(--font-body);
  font-size: 13px;
  padding: 3px 0;
  display: flex;
  justify-content: space-between;
  gap: 6px;
  color: var(--ink-soft);
  line-height: 1.3;
  align-items: center;
}
.week .item .name { flex: 1; min-width: 0; display: flex; align-items: center; gap: 6px; }

/* ============================================================
   ITEM ICON
   ============================================================ */
.icon {
  width: 100%;
  height: 100%;
  flex-shrink: 0;
  image-rendering: pixelated;
  vertical-align: middle;
  background: transparent;
  object-fit: contain;
}
.icon-frame {
  display: inline-flex;
  width: 36px; height: 36px;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 3px;
  vertical-align: middle;
  /* Wooden plank border — outer dark oak, inner warm grain, soft inset */
  background:
    radial-gradient(ellipse at 30% 30%, #fff5d8 0%, #f0e0b0 60%, #e0c98a 100%);
  border: 1px solid #5a3a1a;
  box-shadow:
    /* outer wood frame */
    0 0 0 1px #8a5a28,
    0 0 0 3px #6b4218,
    0 0 0 4px #3a2410,
    /* inner shading */
    inset 0 1px 0 rgba(255, 245, 216, 0.9),
    inset 0 -1px 0 rgba(90, 60, 26, 0.4),
    inset 1px 0 0 rgba(255, 245, 216, 0.6),
    inset -1px 0 0 rgba(90, 60, 26, 0.3),
    /* drop shadow */
    0 2px 4px -1px rgba(60, 35, 10, 0.35);
  position: relative;
}
.icon-frame::before {
  /* Faint wood-grain streaks */
  content: "";
  position: absolute;
  inset: 3px;
  background:
    repeating-linear-gradient(
      90deg,
      transparent 0px,
      rgba(120, 80, 30, 0.05) 1px,
      transparent 2px,
      transparent 5px
    );
  pointer-events: none;
  z-index: 0;
}
.icon-frame .icon { position: relative; z-index: 1; }
.icon-frame.lg { width: 52px; height: 52px; padding: 4px; }

/* ============================================================
   SEASON CHIPS
   ============================================================ */
.season-chips {
  display: inline-flex;
  gap: 3px;
  vertical-align: middle;
}
.scn {
  font-family: var(--font-display-sc);
  font-size: 8px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 6px;
  border: 1px solid currentColor;
  border-radius: 9px;
  font-weight: 500;
  opacity: 0.45;
  white-space: nowrap;
}
.scn.in { opacity: 0.95; }
.scn.best {
  opacity: 1;
  background: currentColor;
  color: var(--parch-bright) !important;
  font-weight: 700;
  box-shadow: 0 0 8px currentColor;
}
.scn.best::after { content: " ★"; }
.scn.spring { color: #c45a85; }
.scn.summer { color: #c89018; }
.scn.autumn { color: #b35a20; }
.scn.winter { color: #5a85b3; }
.scn.best.spring { background: #c45a85; color: #fff !important; }
.scn.best.summer { background: #c89018; color: #fff !important; }
.scn.best.autumn { background: #b35a20; color: #fff !important; }
.scn.best.winter { background: #5a85b3; color: #fff !important; }

/* ============================================================
   LEDGER TABLE
   ============================================================ */
.ledger-frame {
  border: 1px solid var(--rule-deep);
  background: var(--parch-soft);
  margin-top: 8px;
  box-shadow: 0 6px 24px -16px rgba(120, 85, 30, 0.35);
}
table.ledger {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-body);
  font-size: 14px;
}
table.ledger thead th {
  background: var(--parch-deep);
  color: var(--ink-soft);
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-weight: 400;
  padding: 11px 14px;
  text-align: left;
  border-bottom: 2px solid var(--rule-deep);
  cursor: pointer;
  user-select: none;
  position: sticky;
  top: 110px;
  z-index: 5;
  white-space: nowrap;
}
table.ledger thead th:hover { color: var(--burgundy-deep); }
table.ledger thead th.sorted { color: var(--burgundy-deep); }
table.ledger thead th .arrow { display: inline-block; margin-left: 4px; color: var(--gold); font-size: 9px; }
table.ledger thead th.num { text-align: right; }
table.ledger tbody td {
  padding: 8px 14px;
  border-bottom: 1px solid var(--parch-deep);
  vertical-align: middle;
  font-weight: 500;
}
table.ledger tbody td.num {
  text-align: right;
  font-family: var(--font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--ink-soft);
}
table.ledger tbody tr {
  position: relative;
  transition: background .15s;
}
table.ledger tbody tr:hover { background: var(--parch-bright); }
table.ledger tbody tr.dim { opacity: 0.5; }
table.ledger tbody tr.best {
  background: linear-gradient(90deg, rgba(208,144,28,0.14), transparent 60%);
  box-shadow: inset 3px 0 0 var(--gold);
}
table.ledger tbody tr.in-season {
  background: linear-gradient(90deg, rgba(106,146,72,0.10), transparent 70%);
}
table.ledger tbody tr.expandable { cursor: pointer; }
table.ledger .item-name { color: var(--ink); font-weight: 600; display: flex; align-items: center; gap: 8px; }
table.ledger .meta-line { color: var(--ink-faded); font-size: 11px; margin-top: 2px; }

/* ============================================================
   FILTER BAR
   ============================================================ */
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  padding: 8px 0;
}
.filter-bar .field {
  position: relative;
  flex: 1;
  max-width: 380px;
}
.filter-bar input[type=text] {
  background: var(--parch-bright);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 14px;
  padding: 8px 12px 8px 36px;
  border: 1px solid var(--rule);
  border-radius: 0;
  width: 100%;
  transition: border-color .2s, box-shadow .2s;
}
.filter-bar input[type=text]:focus {
  outline: none;
  border-color: var(--gold-deep);
  box-shadow: 0 0 0 2px var(--gold-glow);
}
.filter-bar .field::before {
  content: "❦";
  position: absolute;
  left: 12px; top: 50%;
  transform: translateY(-50%);
  font-family: var(--font-display);
  color: var(--gold-deep);
  font-size: 14px;
  pointer-events: none;
}
.pill-group {
  display: flex;
  gap: 0;
  border: 1px solid var(--rule);
}
.pill-group button {
  background: var(--parch-soft);
  color: var(--ink-faded);
  border: 0;
  border-right: 1px solid var(--rule);
  padding: 7px 14px;
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  cursor: pointer;
  transition: color .2s, background .2s;
}
.pill-group button:last-child { border-right: 0; }
.pill-group button:hover { color: var(--ink); background: var(--parch-bright); }
.pill-group button.on {
  background: var(--burgundy);
  color: var(--parch-bright);
}
.filter-bar .count {
  margin-left: auto;
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--ink-faded);
  text-transform: uppercase;
}

/* ============================================================
   BREWING CARD
   ============================================================ */
.brew-card {
  background: var(--parch-soft);
  border: 1px solid var(--rule);
  padding: 16px 20px 18px;
  margin-bottom: 14px;
  position: relative;
}
.brew-card::before {
  content: "";
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--gold), var(--gold-deep), transparent);
}
.brew-card.locked { opacity: 0.55; }
.brew-card .head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 4px;
}
.brew-card .head .name {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--burgundy-deep);
  font-weight: 400;
  display: flex;
  align-items: center;
  gap: 10px;
}
.brew-card .head .summary {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faded);
  font-variant-numeric: tabular-nums;
}
.brew-card .head .summary .key { color: var(--ink-ghost); }

.stage {
  margin-top: 10px;
  padding-left: 16px;
  border-left: 1px solid var(--rule);
  position: relative;
}
.stage::before {
  content: "";
  position: absolute;
  left: -3px; top: 8px;
  width: 5px; height: 5px;
  background: var(--gold);
  border-radius: 50%;
}
.stage .stage-head {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--ink);
  font-weight: 600;
  margin-bottom: 4px;
}
.stage .stage-head .time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-faded);
  margin-left: 8px;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
}
.slot {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  font-size: 12px;
  padding: 4px 0;
  align-items: flex-start;
  border-bottom: 1px dotted var(--parch-deep);
}
.slot:last-child { border-bottom: 0; }
.slot .label {
  color: var(--ink-soft);
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.slot .label .amt { color: var(--gold-deep); font-family: var(--font-mono); font-weight: 500; }
.slot .opts {
  display: block;
  width: 100%;
  margin-top: 3px;
  font-size: 10px;
  color: var(--ink-faded);
  line-height: 1.6;
}
.slot .opts .opt { display: inline-block; margin-right: 14px; }
.slot .cost {
  text-align: right;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink);
}
.slot .sell {
  display: block;
  color: var(--copper);
  font-size: 10px;
  margin-top: 2px;
}

.ranks {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1px;
  margin-top: 14px;
  background: var(--rule);
  border: 1px solid var(--rule-deep);
}
.rank-cell {
  background: var(--parch-bright);
  padding: 10px 12px;
  position: relative;
}
.rank-cell::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent, var(--gold-glow));
  opacity: 0;
  pointer-events: none;
  transition: opacity .25s;
}
.rank-cell:hover::after { opacity: 1; }
.rank-cell .rl {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.16em;
  color: var(--ink-ghost);
  text-transform: uppercase;
}
.rank-cell .rl .age {
  display: block;
  color: var(--gold-deep);
  font-size: 9px;
  margin-top: 1px;
}
.rank-cell .profit {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--moss-deep);
  margin-top: 6px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.rank-cell .pu {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--gold-deep);
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}
.rank-cell .batch {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--ink-ghost);
  margin-top: 1px;
  font-variant-numeric: tabular-nums;
}

.note {
  font-family: var(--font-body);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-ghost);
  margin-top: 8px;
}
.start-by {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(208,144,28,0.10);
  border: 1px solid var(--gold-deep);
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--gold-deep);
}

/* Brew Plan tab */
.bp-week {
  background: var(--parch-soft);
  border: 1px solid var(--rule);
  margin-bottom: 18px;
  padding: 14px 18px 16px;
}
.bp-week.now {
  background: linear-gradient(180deg, var(--parch-bright), #fff5d8);
  border-color: var(--burgundy);
  box-shadow: 0 0 24px rgba(208,144,28,0.15);
}
.bp-week-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 6px;
  margin-bottom: 8px;
}
.bp-week-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--burgundy-deep);
  font-weight: 400;
}
.bp-week-head h3 .ord {
  color: var(--ink-faded);
  font-style: italic;
  margin-left: 8px;
}
.bp-when {
  font-family: var(--font-display-sc);
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--gold-deep);
  text-transform: uppercase;
  background: var(--parch-bright);
  padding: 4px 10px;
  border: 1px solid var(--gold-deep);
}
.bp-ings {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--parch-deep);
}
.bp-ings-l {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--ink-ghost);
  text-transform: uppercase;
}
.ing-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--parch-bright);
  border: 1px solid var(--rule);
  padding: 2px 8px 2px 4px;
  font-size: 12px;
  color: var(--ink-soft);
}
.bp-pick {
  background: var(--parch-bright);
  border: 1px solid var(--rule);
  padding: 12px 14px;
  margin-top: 10px;
}
.bp-pick.locked { opacity: 0.55; }
.bp-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.bp-name {
  font-family: var(--font-display);
  font-size: 19px;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 10px;
}
.bp-stats {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule-deep);
  margin-bottom: 8px;
}
.bp-stat {
  background: var(--parch-soft);
  padding: 8px 10px;
}
.bp-stat .lbl {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.16em;
  color: var(--ink-ghost);
  text-transform: uppercase;
}
.bp-stat .big {
  font-family: var(--font-mono);
  font-size: 18px;
  color: var(--moss-deep);
  font-weight: 600;
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}
.bp-stat .med {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}
.bp-combo {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.bp-combo .combo {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  background: var(--parch-deep);
  border: 1px solid var(--rule);
  font-size: 11px;
  color: var(--ink-soft);
}
.bp-combo .combo.trend {
  background: rgba(208,144,28,0.18);
  border-color: var(--gold-deep);
  color: var(--gold-deep);
  box-shadow: 0 0 8px var(--gold-glow);
}
.bp-why {
  font-family: var(--font-body);
  font-style: italic;
  font-size: 11px;
  color: var(--burgundy);
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px dashed var(--rule);
}

/* Punnett-style combinatorics grid */
.punnett {
  margin-top: 12px;
  font-family: var(--font-mono);
  font-size: 10px;
  border-collapse: collapse;
  background: var(--parch-bright);
  border: 1px solid var(--rule-deep);
}
.punnett th, .punnett td {
  padding: 5px 9px;
  border: 1px solid var(--parch-deep);
  text-align: center;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.punnett th {
  background: var(--parch-deep);
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.10em;
  color: var(--ink-soft);
  font-weight: 400;
  text-transform: none;
}
.punnett th.corner { background: var(--parch); color: var(--gold-deep); }
.punnett td.cheap { background: var(--moss-pale); color: var(--moss-deep); font-weight: 600; }
.punnett td.dear  { background: rgba(196,72,72,0.08); color: var(--burgundy); }
.punnett-label {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--gold-deep);
  text-transform: uppercase;
  margin: 14px 0 0;
}
tr.detail-row td {
  background: var(--parch-deep);
  border-bottom: 2px solid var(--rule-deep);
  padding: 14px 24px 18px !important;
}
tr.detail-row .detail-title {
  font-family: var(--font-display);
  font-size: 19px;
  color: var(--burgundy-deep);
  margin-bottom: 4px;
}
tr.detail-row .detail-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faded);
  margin-bottom: 8px;
}

/* ============================================================
   VENDOR CARDS — cleaned up
   ============================================================ */
.vendor-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
@media (max-width: 1100px) { .vendor-grid { grid-template-columns: 1fr; } }
.vendor {
  background: var(--parch-soft);
  border: 1px solid var(--rule);
  padding: 0;
  display: flex;
  flex-direction: column;
}
.vendor .v-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 14px;
  padding: 14px 18px 10px;
  border-bottom: 2px double var(--rule-deep);
  background: var(--parch-bright);
}
.vendor .v-head .name {
  font-family: var(--font-display);
  font-size: 24px;
  color: var(--burgundy-deep);
}
.vendor .v-head .v-meta {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--ink-ghost);
  text-transform: uppercase;
}
.vendor .v-loc {
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--moss-deep);
  background: var(--moss-pale);
  padding: 2px 8px;
  border: 1px solid var(--moss-deep);
  text-transform: uppercase;
  white-space: nowrap;
  display: inline-block;
  margin-top: 4px;
}
.vendor .v-loc.unknown { color: var(--ink-ghost); background: var(--parch-bright); border-color: var(--rule); }
.vendor table.v-items {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.vendor table.v-items td {
  padding: 5px 12px;
  border-bottom: 1px solid var(--parch-deep);
  vertical-align: middle;
}
.vendor table.v-items tr:last-child td { border-bottom: 0; }
.vendor table.v-items tr:hover td { background: var(--parch-bright); }
.vendor table.v-items td.nm { color: var(--ink); display: flex; align-items: center; gap: 8px; }
.vendor table.v-items td.nm.always::before {
  content: "★";
  color: var(--gold);
  font-size: 12px;
}
.vendor table.v-items td.num {
  text-align: right;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  white-space: nowrap;
}

/* ============================================================
   QUEST CARDS
   ============================================================ */
.quest-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
@media (max-width: 1100px) { .quest-grid { grid-template-columns: 1fr; } }
.quest {
  background: var(--parch-soft);
  border: 1px solid var(--rule);
  padding: 14px 18px;
  position: relative;
}
.quest.completed { background: var(--moss-pale); border-color: var(--moss-deep); }
.quest.completed .q-name { color: var(--moss-deep); }
.quest.completed::after {
  content: "✓ done";
  position: absolute; top: 12px; right: 14px;
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.18em;
  color: var(--moss-deep);
  background: var(--parch-bright);
  padding: 2px 7px;
  border: 1px solid var(--moss-deep);
}
.quest.active::after {
  content: "active";
  position: absolute; top: 12px; right: 14px;
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.18em;
  color: var(--gold-deep);
  background: var(--parch-bright);
  padding: 2px 7px;
  border: 1px solid var(--gold-deep);
}
.quest .q-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 6px;
  padding-right: 56px;
}
.quest .q-name {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--ink);
}
.quest .q-id {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-ghost);
}
.quest .q-desc {
  font-size: 13px;
  color: var(--ink-soft);
  line-height: 1.55;
}
.quest .q-meta {
  margin-top: 8px;
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--ink-faded);
  text-transform: uppercase;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

/* ============================================================
   PERKS LIST
   ============================================================ */
.perk-tree {
  margin-bottom: 28px;
}
.perk-tree h3 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--burgundy-deep);
  margin: 18px 0 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--rule);
}
.perk-tree h3 .ct {
  font-family: var(--font-display-sc);
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--ink-faded);
  text-transform: uppercase;
  margin-left: 8px;
}
.perk {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--parch-deep);
}
.perk .pid {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-ghost);
  text-align: right;
  padding-top: 2px;
}
.perk .pname {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 14px;
  color: var(--ink);
}
.perk .pdesc {
  font-size: 12px;
  color: var(--ink-faded);
  margin-top: 2px;
  font-style: italic;
}

/* ============================================================
   REPUTATION TIMELINE
   ============================================================ */
.rep-track {
  position: relative;
  padding-left: 32px;
  margin-top: 8px;
}
.rep-track::before {
  content: "";
  position: absolute;
  left: 10px; top: 0; bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, var(--gold), var(--rule), var(--rule-soft));
}
.rep-node {
  position: relative;
  padding: 10px 0 10px 8px;
  display: flex;
  gap: 14px;
  align-items: baseline;
}
.rep-node::before {
  content: "";
  position: absolute;
  left: -22px; top: 16px;
  width: 9px; height: 9px;
  background: var(--gold);
  border: 1px solid var(--parch);
  box-shadow: 0 0 0 1px var(--gold-deep);
  border-radius: 50%;
}
.rep-node .rep-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--gold-deep);
  font-weight: 600;
  min-width: 32px;
}
.rep-node .rep-name {
  font-family: var(--font-display);
  color: var(--ink);
  font-size: 16px;
}
.rep-node .rep-meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-faded);
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

/* ============================================================
   FISH / FORAGING grid
   ============================================================ */
.list-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule-deep);
}
@media (max-width: 1100px) { .list-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 700px)  { .list-grid { grid-template-columns: 1fr; } }
.list-grid .entry {
  background: var(--parch-soft);
  padding: 11px 14px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--ink-soft);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.list-grid .entry .nm {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.list-grid .entry .meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-ghost);
  font-variant-numeric: tabular-nums;
}
.list-grid .entry:hover { background: var(--parch-bright); color: var(--ink); }

/* ============================================================
   MAP TAB
   ============================================================ */
.map-controls {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-family: var(--font-display-sc);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faded);
}
.legend .lg-item { display: inline-flex; align-items: center; gap: 5px; }
.legend .dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.legend .dot.tree    { background: #6a9248; }
.legend .dot.bush    { background: #983d3d; }
.legend .dot.fish    { background: #6c9bb1; }
.legend .dot.animal  { background: #d49a2a; }

.map-canvas-wrap {
  border: 1px solid var(--rule-deep);
  background: var(--parch-bright);
  padding: 0;
  position: relative;
  overflow: auto;
  max-height: 720px;
}
canvas#mapCanvas {
  display: block;
  cursor: crosshair;
  image-rendering: pixelated;
  background:
    linear-gradient(135deg, #f5e9c4 0%, #ead7a6 100%);
}
.map-stats {
  display: flex;
  gap: 18px;
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faded);
  font-variant-numeric: tabular-nums;
}

/* ============================================================
   ITEM MODAL — click any item name to see full dossier
   ============================================================ */
.cart-btn {
  background: var(--moss-pale);
  border: 1px solid var(--moss-deep);
  color: var(--moss-deep);
  font-size: 12px;
  padding: 2px 8px;
  cursor: pointer;
  border-radius: 3px;
  margin-left: 6px;
  vertical-align: middle;
}
.cart-btn:hover { background: var(--moss); color: #fff; }

.item-link {
  color: var(--burgundy-deep);
  cursor: pointer;
  text-decoration: underline;
  text-decoration-style: dotted;
  text-underline-offset: 2px;
}
.item-link:hover { color: var(--gold-deep); }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(58, 41, 24, 0.5);
  z-index: 200;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 60px 20px;
  overflow-y: auto;
}
.modal {
  background: var(--parch-bright);
  border: 2px solid var(--rule-deep);
  max-width: 800px;
  width: 100%;
  padding: 0;
  box-shadow: 0 16px 48px -16px rgba(60, 35, 10, 0.5);
  position: relative;
}
.modal-close {
  position: absolute;
  top: 12px; right: 14px;
  background: none;
  border: none;
  font-size: 22px;
  color: var(--ink-faded);
  cursor: pointer;
}
.modal-close:hover { color: var(--burgundy); }
.modal-header {
  background: var(--parch-deep);
  padding: 16px 20px;
  border-bottom: 2px solid var(--rule-deep);
  display: flex;
  align-items: center;
  gap: 14px;
}
.modal-header .name {
  font-family: var(--font-display);
  font-size: 26px;
  color: var(--burgundy-deep);
}
.modal-header .prices {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-faded);
  margin-left: auto;
}
.modal-body { padding: 16px 20px; }
.modal-section {
  margin-bottom: 18px;
}
.modal-section h3 {
  font-family: var(--font-display-sc);
  font-size: 12px;
  letter-spacing: 0.18em;
  color: var(--gold-deep);
  text-transform: uppercase;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 4px;
  margin: 0 0 8px;
}
.modal-row {
  display: flex;
  gap: 10px;
  align-items: baseline;
  padding: 5px 0;
  border-bottom: 1px solid var(--parch-deep);
  font-size: 13px;
}
.modal-row:last-child { border-bottom: 0; }
.modal-row .type-badge {
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 7px;
  border: 1px solid currentColor;
  flex-shrink: 0;
}
.modal-row .type-badge.recipe { color: var(--burgundy); }
.modal-row .type-badge.vendor { color: var(--moss-deep); }
.modal-row .type-badge.crop { color: var(--gold-deep); }
.modal-row .type-badge.fish { color: var(--sky-deep); }
.modal-row .type-badge.foraging { color: var(--copper); }
.modal-row .type-badge.group { color: var(--ink-faded); }
.modal-row .type-badge.planting { color: var(--moss); }
.modal-row .detail {
  color: var(--ink-faded);
  font-size: 11px;
  font-family: var(--font-mono);
}
.modal-empty {
  color: var(--ink-ghost);
  font-style: italic;
  font-size: 12px;
  padding: 4px 0;
}

footer.colophon {
  text-align: center;
  font-family: var(--font-display-sc);
  font-size: 9px;
  letter-spacing: 0.22em;
  color: var(--ink-ghost);
  text-transform: uppercase;
  padding: 36px 0 6px;
}
footer.colophon .orn {
  display: block;
  font-family: var(--font-display);
  color: var(--gold);
  font-size: 18px;
  margin-bottom: 8px;
}

.loading {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--burgundy-deep);
  text-align: center;
  padding: 80px 0;
  font-style: italic;
}
.loading::after {
  content: " …";
  animation: dots 1.4s steps(4) infinite;
}
@keyframes dots {
  0%, 25%   { content: " ."; }
  50%       { content: " .."; }
  75%, 100% { content: " ..."; }
}
</style>
</head>
<body>

<header class="spine">
  <div class="row">
    <div class="brand">
      <span class="seal">⚜</span>
      <h1>Travellers Rest <em>Planner</em></h1>
      <span class="tavern" id="tavernName"></span>
    </div>
    <div class="global-search">
      <input id="globalSearch" type="text" placeholder="Search anything…" autocomplete="off">
      <div id="searchResults" class="search-results"></div>
    </div>
    <div class="controls">
      <select id="slot"></select>
      <select id="lang"></select>
      <span id="ws-pill" class="ws-pill dead">offline</span>
    </div>
  </div>
</header>

<nav class="tabs">
  <div class="row">
    <button data-tab="plan" class="active"><span class="glyph">⚖</span>Plan</button>
    <div class="tab-dropdown">
      <button class="tab-trigger"><span class="glyph">⚗</span>Brewing ▾</button>
      <div class="tab-menu">
        <button data-tab="brewing">Compendium</button>
        <button data-tab="brewPlan">Brew Plan</button>
      </div>
    </div>
    <div class="tab-dropdown">
      <button class="tab-trigger"><span class="glyph">⚒</span>Crafting ▾</button>
      <div class="tab-menu">
        <button data-tab="recipes">Recipes</button>
        <button data-tab="seeds">Seeds &amp; Crops</button>
        <button data-tab="menu">Menu Planner</button>
        <button data-tab="shopping">Shopping List</button>
      </div>
    </div>
    <div class="tab-dropdown">
      <button class="tab-trigger"><span class="glyph">⚔</span>World ▾</button>
      <div class="tab-menu">
        <button data-tab="vendors">Vendors</button>
        <button data-tab="fish">Fish</button>
        <button data-tab="foraging">Foraging</button>
        <button data-tab="map">Map</button>
      </div>
    </div>
    <div class="tab-dropdown">
      <button class="tab-trigger"><span class="glyph">★</span>Progress ▾</button>
      <div class="tab-menu">
        <button data-tab="quests">Quests</button>
        <button data-tab="perks">Perks</button>
        <button data-tab="reputation">Reputation</button>
      </div>
    </div>
  </div>
</nav>

<main>
  <div id="err"></div>
  <div id="content"><div class="loading">Reading the ledger</div></div>
  <footer class="colophon">
    <span class="orn">❦ ⚜ ❦</span>
    Compiled from the keeper's records
  </footer>
</main>

<script>
"use strict";

const STATE = {
  saves: [], languages: [],
  slot: "", lang: "English",
  tab: "plan",
  data: {},
  recipeDetailCache: {},
  iconExists: new Set(),  // populated lazily as <img> elements load
  ui: {
    seeds:    { sort: null, dir: -1, filter: "" },
    recipes:  { sort: null, dir: -1, filter: "", group: null, expanded: new Set() },
    brewing:  { showLocked: false },
    vendors:  { filter: "", stock: "all" },
    quests:   { filter: "", state: "all" },
    perks:    { mode: "player" },
    fish:     { filter: "" },
    foraging: { filter: "" },
    map:      { layer: "all", scene: "all" },
    menu:     { picked: new Set(), filter: "" },
    shopping: { filter: "" },  // cart is now server-side, synced via /api/cart
  },
};

const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

/* ----- formatters ----- */
const COIN_GOLD = '<img src="/icons/_gold.png" alt="">';
const COIN_SILVER = '<img src="/icons/_silver.png" alt="">';
const COIN_COPPER = '<img src="/icons/_copper.png" alt="">';
function fmtMoney(copper) {
  if (copper == null || isNaN(copper)) return '<span class="coin"><span class="zero">—</span></span>';
  copper = Math.round(copper);
  const neg = copper < 0;
  copper = Math.abs(copper);
  const g = Math.floor(copper / 10000);
  const s = Math.floor((copper % 10000) / 100);
  const c = copper % 100;
  if (!g && !s && !c) return `<span class="coin"><span class="unit"><span class="c">0</span>${COIN_COPPER}</span></span>`;
  const parts = [];
  if (neg) parts.push('<span class="neg">−</span>');
  if (g)      parts.push(`<span class="unit"><span class="g">${g}</span>${COIN_GOLD}</span>`);
  if (s || g) parts.push(`<span class="unit"><span class="s">${s}</span>${COIN_SILVER}</span>`);
  parts.push(`<span class="unit"><span class="c">${c}</span>${COIN_COPPER}</span>`);
  return `<span class="coin">${parts.join("")}</span>`;
}
const fmtMoneyMuted = (c) => fmtMoney(c).replace('class="coin"', 'class="coin muted"');
function fmtHours(h) {
  if (h == null) return "—";
  if (h < 1)  return Math.round(h * 60) + "m";
  if (h < 24) return Number.isInteger(h) ? h + "h" : h.toFixed(1) + "h";
  const d = Math.floor(h / 24), rem = Math.round(h % 24);
  return rem ? `${d}d ${rem}h` : `${d}d`;
}

/* ----- crop_id → harvest_item_id lookup (for icons) ----- */
function _cropItemId(cropId) {
  const seeds = STATE.data.seeds || [];
  const match = seeds.find(s => s.crop_id === cropId);
  return match ? (match.harvest_item_id || match.seed_item_id || cropId) : cropId;
}

/* ----- shared shopping cart (server-synced) ----- */
let CART = [];

async function loadCart() {
  CART = await jget("/api/cart?slot=" + encodeURIComponent(STATE.slot));
}

async function addToCart(itemId, name, buyCost, vendor, qty) {
  await fetch("/api/cart", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      slot: STATE.slot, action: "add",
      item: { item_id: itemId, name: name, qty: qty || 1, buy_copper: buyCost, vendor: vendor }
    }),
  });
  // Cart will update via websocket broadcast
}

async function removeFromCart(itemId) {
  await fetch("/api/cart", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ slot: STATE.slot, action: "remove", item_id: itemId }),
  });
}

async function clearCart() {
  await fetch("/api/cart", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ slot: STATE.slot, action: "clear" }),
  });
}

function cartButton(itemId, name, buyCost, vendor) {
  return `<button class="cart-btn" onclick="event.stopPropagation(); addToCart(${itemId}, '${esc(name).replace(/'/g,"\\'")}', ${buyCost}, '${esc(vendor||"").replace(/'/g,"\\'")}', 1)" title="Add to shopping list">🛒</button>`;
}

/* ----- item link helper — makes any item name clickable ----- */
function itemLink(itemId, name, showIcon) {
  if (!itemId || !name) return esc(name || "?");
  const icon = showIcon !== false ? iconHtml(itemId) : "";
  return `${icon}<span class="item-link" onclick="openItem(${itemId})">${esc(name)}</span>`;
}

async function openItem(itemId) {
  const lang = STATE.lang || "English";
  try {
    const d = await jget("/api/item/" + itemId + "?lang=" + encodeURIComponent(lang));
    showItemModal(d);
  } catch (e) {
    console.error(e);
  }
}

function showItemModal(d) {
  const sourcesHtml = d.sources.length === 0
    ? '<div class="modal-empty">No known sources in extracted data. May drop from mine or world objects.</div>'
    : d.sources.map(s => {
        let detail = "";
        if (s.type === "recipe") {
          const ings = s.ingredients.map(i => `${i.amount}x ${itemLink(i.item_id, i.name, false)}`).join(" + ");
          detail = `<div class="detail">${s.output_qty}x · ${fmtHours(s.time_hours)} · ${ings}</div>`;
        } else if (s.type === "crop") {
          detail = `<div class="detail">${s.days_to_grow}d grow · ${s.available_seasons.join(",")} · best ${s.best_seasons.join(",") || "none"} · yield ${s.yield_normal}-${s.yield_best} · seed: ${s.seed ? itemLink(s.seed_id, s.seed, false) : "?"}</div>`;
        } else if (s.type === "vendor") {
          detail = `<div class="detail">buy ${fmtMoney(s.buy_copper)}${s.always_stocked ? " · always in stock" : ""}</div>`;
        } else if (s.type === "foraging") {
          detail = `<div class="detail">${s.amount_min}-${s.amount_max} per pick</div>`;
        } else if (s.type === "fish") {
          const seasons = ["Spring","Summer","Autumn","Winter"].filter((_,i) => s.season_flags & (1<<i));
          const water = {0:"Any",1:"Fresh",2:"Salt"}[s.water_type] || "?";
          detail = `<div class="detail">diff ${s.difficulty} · ${water} water · ${seasons.join(",")}</div>`;
        }
        return `<div class="modal-row"><span class="type-badge ${s.type}">${s.type}</span><div><div>${esc(s.name || s.vendor || "")}</div>${detail}</div></div>`;
      }).join("");

  const usesHtml = d.uses.length === 0
    ? '<div class="modal-empty">Not used in any known recipe.</div>'
    : d.uses.map(u => {
        let label = "";
        let detail = "";
        if (u.type === "recipe_ingredient") {
          label = itemLink(u.output_item_id, u.name, false);
          detail = `<div class="detail">${u.amount_needed}x needed · ${u.group}</div>`;
        } else if (u.type === "planting") {
          label = itemLink(u.harvest_id, u.crop_name, false);
          detail = `<div class="detail">harvests ${u.harvest_name || "?"}</div>`;
        } else if (u.type === "ingredient_group") {
          label = esc(u.group_name);
          detail = `<div class="detail">accepted in this ingredient group</div>`;
        }
        return `<div class="modal-row"><span class="type-badge ${u.type === "recipe_ingredient" ? "recipe" : u.type === "planting" ? "crop" : "group"}">${u.type.replace("recipe_ingredient","recipe").replace("ingredient_group","group")}</span><div><div>${label}</div>${detail}</div></div>`;
      }).join("");

  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  modal.innerHTML = `
    <div class="modal">
      <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
      <div class="modal-header">
        ${iconHtml(d.item_id, "lg")}
        <div class="name">${esc(d.name)}</div>
        <div class="prices">
          buy ${fmtMoney(d.buy_copper)} · sell ${fmtMoney(d.sell_copper)}
          ${d.has_to_be_aged_meal ? ' · <span class="badge gold">agable</span>' : ""}
          ${d.contains_alcohol ? ' · <span class="badge ember">alcohol</span>' : ""}
        </div>
      </div>
      <div class="modal-body">
        <div class="modal-section">
          <h3>Sources — how to get it (${d.source_count})</h3>
          ${sourcesHtml}
        </div>
        <div class="modal-section">
          <h3>Uses — what it's for (${d.use_count})</h3>
          ${usesHtml}
        </div>
      </div>
    </div>`;
  document.body.appendChild(modal);
}

/* ----- icon helper ----- */
function iconHtml(itemId, sizeCls) {
  if (!itemId) return "";
  const lg = sizeCls === "lg";
  return `<span class="icon-frame${lg ? ' lg' : ''}"><img class="icon" src="/icons/${itemId}.png" loading="lazy" onerror="this.parentElement.style.display='none'"></span>`;
}

/* ----- season chip helper ----- */
const SEASON_CLASS = { Spring: "spring", Summer: "summer", Autumn: "autumn", Winter: "winter" };
function seasonChips(available, best) {
  if (!available?.length) return "";
  const bestSet = new Set(best || []);
  return '<span class="season-chips">' +
    ["Spring","Summer","Autumn","Winter"].map(s => {
      if (!available.includes(s)) return "";
      const cls = SEASON_CLASS[s] + (available.includes(s) ? " in" : "") + (bestSet.has(s) ? " best" : "");
      return `<span class="scn ${cls}">${s.slice(0,3)}</span>`;
    }).filter(Boolean).join("") +
    '</span>';
}

/* ----- fetchers ----- */
async function jget(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}
function qs() {
  const p = new URLSearchParams();
  if (STATE.slot) p.set("slot", STATE.slot);
  if (STATE.lang) p.set("lang", STATE.lang);
  return p.toString();
}
async function loadAll() {
  const Q = qs();
  try {
    const [plan, seeds, brewing, brewPlan, recipes, vendors, quests, perks, fish, bushes, reputation, hotspots, maps] = await Promise.all([
      jget("/api/plan?" + Q),
      jget("/api/seeds?" + Q),
      jget("/api/brewing?" + Q),
      jget("/api/brew-plan?" + Q),
      jget("/api/recipes?" + Q),
      jget("/api/vendors?" + Q),
      jget("/api/quests?" + Q),
      jget("/api/perks?" + Q),
      jget("/api/fish?" + Q),
      jget("/api/bushes?" + Q),
      jget("/api/reputation?" + Q),
      jget("/api/hotspots").catch(() => null),
      jget("/api/maps").catch(() => ({})),
    ]);
    STATE.data = { plan, seeds, brewing, brewPlan, recipes, vendors, quests, perks, fish, bushes, reputation, hotspots, maps };
    STATE.recipeDetailCache = {};
    $("#err").innerHTML = "";
    const t = plan && plan.today;
    if (t && t.tavern_name) {
      $("#tavernName").innerHTML =
        `<span class="at">at</span> <em>${esc(t.tavern_name)}</em> <span class="by">·</span> <span style="color:var(--burgundy)">${esc(t.player_name)}</span>`;
    }
    renderTab();
  } catch (e) {
    $("#err").innerHTML = esc("⚠ " + e.message);
  }
}

/* ============================================================
   PLAN TAB
   ============================================================ */
function trendBadge(t) {
  if (t.grow_crop_id) {
    if (t.is_planted) return `<span class="badge moss">growing ${t.planted_count}</span>`;
    if (t.grow_best_season_now) return '<span class="badge gold glow">best now</span>';
    if (t.grow_in_season_now) return '<span class="badge moss">in season</span>';
    return '<span class="badge ember">off-season</span>';
  }
  if (t.unlocked_recipe_ids?.length) return '<span class="badge moss">unlocked</span>';
  if (t.recipe_ids?.length) return '<span class="badge wax">locked</span>';
  return "";
}
function renderTrendList(items) {
  if (!items?.length) return '<div class="empty">—</div>';
  return items.map(t =>
    `<div class="item"><span class="name">${itemLink(t.item_id, t.name)}</span>${trendBadge(t)}</div>`
  ).join("");
}
function renderWeek(w) {
  const ord = ["I","II","III","IV"][w.week_offset];
  return `
    <div class="week ${w.week_offset === 0 ? 'current' : ''}">
      <h3><span class="ord">${ord}</span>${esc(w.season_at_start)}</h3>
      <div class="when">in ${w.days_until_start}d</div>
      <div class="group"><div class="group-label">Foods</div>${renderTrendList(w.food_trends)}</div>
      <div class="group"><div class="group-label">Drinks</div>${renderTrendList(w.drink_trends)}</div>
      <div class="group"><div class="group-label">Ingredients</div>${renderTrendList(w.ingredient_trends)}</div>
    </div>`;
}
function renderCookCard(s) {
  const trendBonus = s.base_profit_with_trend - s.profit_per_craft;
  return `
    <div class="card">
      <div class="head">
        <div class="title">${itemLink(s.output_item_id, s.recipe_name)}</div>
        <div>${fmtMoney(s.base_profit_with_trend)}</div>
      </div>
      <div class="meta">${fmtHours(s.time_hours)} cook · fuel ${s.fuel} · trend bonus ${fmtMoney(trendBonus)}</div>
      <div class="meta">${s.ingredients.map(([id,a,n]) => `${a}× ${itemLink(id, n, false)}`).join("  +  ")}</div>
      ${s.why?.length ? `<div class="why">${esc(s.why.join(" · "))}</div>` : ""}
    </div>`;
}
function renderPlantCard(s) {
  const deadline = s.plant_by_day === 0
    ? '<span class="badge gold glow">plant TODAY</span>'
    : `<span class="badge gold">plant in ≤${s.plant_by_day}d</span>`;
  // Find the seed's vendor info for the cart button
  const vendors = STATE.data.vendors || [];
  let seedVendor = null;
  let seedBuy = 0;
  let seedName = s.crop_name + " Seeds";
  // Search vendors for this crop's seed
  for (const v of vendors) {
    for (const item of v.items) {
      if (item.name && item.name.toLowerCase().includes(s.crop_name.toLowerCase()) &&
          (item.name.toLowerCase().includes("seed") || item.name.toLowerCase().includes("sprout"))) {
        seedVendor = v.vendor;
        seedBuy = item.buy_copper;
        seedName = item.name;
        break;
      }
    }
    if (seedVendor) break;
  }
  const cartBtn = seedVendor
    ? cartButton(0, seedName, seedBuy, seedVendor)
    : '';
  return `
    <div class="card">
      <div class="head">
        <div class="title">${iconHtml(_cropItemId(s.crop_id), 'lg')}${esc(s.crop_name)} ${s.is_best_now ? '<span class="badge gold">BEST</span>' : ''} ${cartBtn}</div>
        ${deadline}
      </div>
      <div class="meta">${s.days_to_grow}d to grow${s.reusable ? ' · perennial (regrow ' + s.days_until_new_harvest + 'd)' : ''} · ${s.yield_per_harvest}/harvest · target wk +${s.target_for_trend_week}</div>
      <div class="meta">${seasonChips(s.available_seasons, s.best_seasons)}</div>
      <div class="why">${esc(s.why.join(" · "))}</div>
    </div>`;
}
function renderPlan() {
  const p = STATE.data.plan;
  if (!p) return '<div class="loading">Reading the ledger</div>';
  const t = p.today;
  const tiles = `
    <div class="stat-grid">
      <div class="stat-tile"><div class="label">Date</div><div class="value">${esc(t.season)} · W${t.week_in_season}</div><div class="sub">${esc(t.day_of_week)} · year ${t.year}</div></div>
      <div class="stat-tile"><div class="label">Trend rotates</div><div class="value">in ${t.next_trend_rotation_in_days}d</div></div>
      <div class="stat-tile"><div class="label">Coffer</div><div class="value money">${fmtMoney(t.money_copper)}</div></div>
      <div class="stat-tile"><div class="label">Tavern Rep</div><div class="value">${t.tavern_rep}</div></div>
      <div class="stat-tile"><div class="label">Crops planted</div><div class="value">${t.planted_count}</div><div class="sub">${t.unique_planted} unique</div></div>
      <div class="stat-tile"><div class="label">Recipes known</div><div class="value">${t.unlocked_recipes}</div></div>
    </div>`;
  const plant = p.plant_now.length === 0
    ? '<div class="empty">Nothing trending you can plant in time.</div>'
    : `<div class="action-grid">${p.plant_now.map(renderPlantCard).join("")}</div>`;
  const cook = p.cook_now.length === 0 ? '<div class="empty">No trending food recipes you have unlocked.</div>'
                                       : p.cook_now.map(renderCookCard).join("");
  const brew = p.brew_now.length === 0 ? '<div class="empty">No trending drinks you have unlocked.</div>'
                                       : p.brew_now.map(renderCookCard).join("");
  return tiles
    + `<h2 class="section-head"><span class="ornament">✿</span> Plant now</h2>${plant}`
    + `<h2 class="section-head"><span class="ornament">⚒</span> Cook now</h2>${cook}`
    + `<h2 class="section-head"><span class="ornament">⚗</span> Brew now</h2>${brew}`
    + `<h2 class="section-head"><span class="ornament">⚜</span> Four-week trend almanac</h2>`
    + `<div class="calendar">${p.calendar.map(renderWeek).join("")}</div>`;
}

/* ============================================================
   SEEDS TAB
   ============================================================ */
const SEED_COLS = [
  { k: "name",                  l: "Crop",         t: "str",  align: "" },
  { k: "available_seasons",     l: "Seasons",      t: "season",align: "" },
  { k: "days_to_grow",          l: "Days",         t: "num",  align: "num" },
  { k: "reusable",              l: "Perennial",    t: "bool", align: "" },
  { k: "days_until_new_harvest",l: "Regrow",       t: "num",  align: "num" },
  { k: "yield_normal",          l: "Yield",        t: "num",  align: "num" },
  { k: "yield_best_season",     l: "Yield ★",      t: "num",  align: "num" },
  { k: "harvest_sell_copper",   l: "Sell each",    t: "money",align: "num" },
  { k: "profit_per_day_normal", l: "/day",         t: "money",align: "num" },
  { k: "profit_per_day_best",   l: "/day ★",       t: "money",align: "num" },
  { k: "seed_buy_copper",       l: "Seed cost",    t: "money",align: "num" },
  { k: "planted_count",         l: "Planted",      t: "num",  align: "num" },
];
function sortRows(rows, key, dir, type) {
  if (!key) return rows;
  return [...rows].sort((a, b) => {
    let av = a[key], bv = b[key];
    if (type === "arr")  { av = (av || []).join(","); bv = (bv || []).join(","); }
    if (type === "bool") { av = av ? 1 : 0;            bv = bv ? 1 : 0; }
    if (av == null) return 1;
    if (bv == null) return -1;
    if (av < bv) return -dir;
    if (av > bv) return dir;
    return 0;
  });
}
function renderSeedsBody() {
  const u = STATE.ui.seeds;
  let rows = (STATE.data.seeds || []).filter(r => r.is_obtainable);
  const f = u.filter.trim().toLowerCase();
  if (f) rows = rows.filter(r =>
    r.name.toLowerCase().includes(f) ||
    (r.harvest_name || "").toLowerCase().includes(f) ||
    r.available_seasons.join(" ").toLowerCase().includes(f));
  if (u.sort) {
    const col = SEED_COLS.find(c => c.k === u.sort);
    rows = sortRows(rows, u.sort, u.dir, col?.t || "str");
  }
  $("#seedCount").textContent = rows.length + " crops";
  return rows.map(r => {
    const cls = r.is_best_now ? "best" : (r.is_in_season_now ? "in-season" : "dim");
    const cells = SEED_COLS.map(col => {
      const v = r[col.k];
      const c = col.align === "num" ? "num" : "";
      if (col.t === "money")  return `<td class="${c}">${fmtMoneyMuted(v)}</td>`;
      if (col.t === "num")    return `<td class="${c}">${v ?? "—"}</td>`;
      if (col.t === "bool")   return `<td>${v ? "✓" : ""}</td>`;
      if (col.t === "arr")    return `<td>${(v || []).map(x => esc(x)).join(", ")}</td>`;
      if (col.t === "season") return `<td>${seasonChips(v, r.best_seasons)}</td>`;
      if (col.k === "name")   return `<td><div class="item-name">${itemLink(r.harvest_item_id, v)}</div><div class="meta-line">${r.seed_item_id ? itemLink(r.seed_item_id, r.seed_name || "seed", false) : esc(r.harvest_name)}</div></td>`;
      return `<td>${esc(v)}</td>`;
    }).join("");
    return `<tr class="${cls}">${cells}</tr>`;
  }).join("");
}
function renderSeeds() {
  const u = STATE.ui.seeds;
  const headers = SEED_COLS.map(c =>
    `<th data-col="${c.k}" data-type="${c.t}" class="${c.align} ${u.sort === c.k ? 'sorted' : ''}">${c.l}${u.sort === c.k ? `<span class="arrow">${u.dir === 1 ? '▲' : '▼'}</span>` : ''}</th>`
  ).join("");
  return `
    <h2 class="section-head"><span class="ornament">✿</span> The seed register</h2>
    <div class="filter-bar">
      <div class="field"><input id="seedFilter" type="text" placeholder="Filter by crop, season…" value="${esc(u.filter)}"></div>
      <span class="count" id="seedCount"></span>
    </div>
    <div class="ledger-frame">
      <table class="ledger">
        <thead><tr>${headers}</tr></thead>
        <tbody id="seedBody"></tbody>
      </table>
    </div>
    <p class="note">Gold rows are at their <em>best season right now</em> — yield is +1 per harvest. Faded rows are off-season.</p>`;
}

/* ============================================================
   BREWING TAB
   ============================================================ */
function renderSlot(slot) {
  let opts = "";
  if (slot.is_group && slot.choices?.length) {
    opts = '<span class="opts">accepts: ' +
      slot.choices.slice(0, 6).map(c => {
        const nm = esc(c.item_name + (c.mod_name ? ` (${c.mod_name})` : ""));
        return `<span class="opt">${nm} ${fmtMoney(c.buy_cost_copper)} <span style="color:var(--ink-ghost)">·</span> ${fmtMoneyMuted(c.sell_copper)}</span>`;
      }).join("") +
      (slot.choices.length > 6 ? ' …' : '') +
      '</span>';
  }
  const sub = slot.sub_stage ? renderStage(slot.sub_stage, true) : "";
  const sell = slot.raw_sell_value > 0
    ? `<span class="sell">sell raw ${fmtMoney(slot.raw_sell_value)}</span>` : "";
  const groupBadge = slot.is_group ? ' <span class="badge dim">group</span>' : "";
  const choiceIcon = slot.choices?.[0]?.item_id ? iconHtml(slot.choices[0].item_id) : "";
  return `
    <div class="slot">
      <div class="label"><span class="amt">${slot.amount}×</span>${slot.choices?.[0]?.item_id ? itemLink(slot.choices[0].item_id, slot.label, true) : esc(slot.label)}${groupBadge}${opts}</div>
      <div class="cost">${fmtMoney(slot.cheapest_cost)}${sell}</div>
    </div>${sub}`;
}
function renderStage(stage, isSub) {
  const arrow = isSub ? '↳ ' : '';
  return `
    <div class="stage">
      <div class="stage-head">${arrow}${esc(stage.recipe_name)}<span class="time">${fmtHours(stage.time_hours)} · fuel ${stage.fuel} · makes ${stage.output_qty}</span></div>
      ${stage.slots.map(renderSlot).join("")}
    </div>`;
}
function renderPunnett(p) {
  // Find the first two slots that are IngredientGroups with >1 choice each
  const groups = (p.chain?.slots || []).filter(s => s.is_group && s.choices?.length > 1);
  if (groups.length < 2) return "";
  const a = groups[0], b = groups[1];
  // Limit to 5 each so the grid stays readable
  const aChoices = a.choices.slice(0, 5);
  const bChoices = b.choices.slice(0, 5);
  // Compute fixed cost from non-group slots
  let fixedCost = 0;
  for (const s of (p.chain?.slots || [])) {
    if (s !== a && s !== b) fixedCost += s.cheapest_cost;
  }
  // Find min/max for colour scale
  let minTotal = Infinity, maxTotal = -Infinity;
  const cells = aChoices.map(ax => bChoices.map(bx => {
    const t = fixedCost + (ax.buy_cost_copper * a.amount) + (bx.buy_cost_copper * b.amount);
    if (t < minTotal) minTotal = t;
    if (t > maxTotal) maxTotal = t;
    return t;
  }));
  const stripPrefix = (n) => n.replace(/^-?\d+\s*-\s*/, "");
  const labelA = stripPrefix(a.label);
  const labelB = stripPrefix(b.label);
  const head = `<tr><th class="corner">${esc(labelA)}<br>↓ <span style="color:var(--ink-ghost)">vs</span> ${esc(labelB)} →</th>${
    bChoices.map(bx => `<th>${esc(bx.item_name)}</th>`).join("")
  }</tr>`;
  const body = aChoices.map((ax, ai) => `<tr>
    <th>${esc(ax.item_name)}</th>
    ${cells[ai].map(t => {
      const cls = t === minTotal ? "cheap" : (t === maxTotal && minTotal !== maxTotal ? "dear" : "");
      return `<td class="${cls}">${fmtMoney(t).replace(/<\/?span[^>]*>/g, m => m).replace(/class="coin"/, 'class="coin"')}</td>`;
    }).join("")}
  </tr>`).join("");
  return `
    <div class="punnett-label">⚗ Ingredient combinatorics — total batch cost</div>
    <table class="punnett">
      <thead>${head}</thead>
      <tbody>${body}</tbody>
    </table>`;
}

function renderBrewCard(p, trendingIds, daysToRotation) {
  const isTrending = trendingIds.has(p.drink_item_id);
  const cells = [0,1,2,3,4].map(r => {
    const ageH = p.aging_hours_per_rank[r];
    return `<div class="rank-cell">
      <div class="rl">Rank ${r}${r === 0 ? '' : `<span class="age">${fmtHours(ageH)}</span>`}</div>
      <div class="profit">${fmtMoney(p.profit_per_rank[r])}</div>
      <div class="pu">${fmtMoney(p.aged_sell_per_unit[r])}/u</div>
      <div class="batch">batch ${fmtMoneyMuted(p.aged_sell[r])}</div>
    </div>`;
  }).join("");
  const startBy = isTrending && daysToRotation != null
    ? `<div class="start-by">⚜ Currently trending — ${fmtHours(p.total_brewing_hours)} brew. Start now to catch the +20% trend bonus before it rotates in ${daysToRotation}d.</div>`
    : "";
  const lockBadge = p.is_unlocked ? "" : '<span class="badge wax">locked</span>';
  const trendBadge = isTrending ? '<span class="badge gold glow">trending</span>' : '';
  return `
    <div class="brew-card ${p.is_unlocked ? '' : 'locked'}">
      <div class="head">
        <div class="name">${itemLink(p.drink_item_id, p.drink_name)} ${lockBadge} ${trendBadge}</div>
        <div class="summary">
          <span class="key">total</span> ${fmtHours(p.total_brewing_hours)} ·
          <span class="key">cost</span> ${fmtMoneyMuted(p.chain.cumulative_cost_copper)} ·
          <span class="key">per unit</span> ${fmtMoney(p.per_unit_sell)} ·
          <span class="key">batch</span> ×${p.output_qty} ${fmtMoneyMuted(p.raw_sell_copper)}
        </div>
      </div>
      ${renderStage(p.chain, false)}
      <div class="ranks">${cells}</div>
      ${renderPunnett(p)}
      <p class="note">Profit is full-batch. Cooking perks scale yield-per-craft, which moves the per-unit number linearly. Aging stacks +10% / +20% / +30% on top.</p>
      ${startBy}
    </div>`;
}
function renderBrewing() {
  const plans = STATE.data.brewing || [];
  const planData = STATE.data.plan;
  const dnr = planData ? planData.today.next_trend_rotation_in_days : null;
  const trending = new Set();
  if (planData) for (const t of planData.calendar[0].drink_trends) trending.add(t.item_id);
  const u = STATE.ui.brewing;
  const visible = u.showLocked ? plans : plans.filter(p => p.is_unlocked);
  const unlockedCount = plans.filter(p => p.is_unlocked).length;
  return `
    <h2 class="section-head"><span class="ornament">⚗</span> The brewer's compendium</h2>
    <div class="filter-bar">
      <div class="pill-group">
        <button data-toggle="unlocked" class="${u.showLocked ? '' : 'on'}">Unlocked (${unlockedCount})</button>
        <button data-toggle="all"      class="${u.showLocked ? 'on' : ''}">All (${plans.length})</button>
      </div>
      <span class="count">aging maxes at rank 4 — 5 in-game days in a barrel</span>
    </div>
    ${visible.map(p => renderBrewCard(p, trending, dnr)).join("")}`;
}

/* ============================================================
   RECIPES TAB
   ============================================================ */
const RECIPE_COLS = [
  { k: "name",                  l: "Recipe",       t: "str",   align: "" },
  { k: "group",                 l: "Group",        t: "str",   align: "" },
  { k: "output_qty",            l: "Qty",          t: "num",   align: "num" },
  { k: "per_unit_sell",         l: "Per unit",     t: "money", align: "num" },
  { k: "batch_sell",            l: "Batch",        t: "money", align: "num" },
  { k: "ingredient_buy_cost",   l: "Cost",         t: "money", align: "num" },
  { k: "profit_per_craft",      l: "Profit",       t: "money", align: "num" },
  { k: "time_hours",            l: "Time",         t: "num",   align: "num" },
];
function recipeRows() {
  const u = STATE.ui.recipes;
  let rows = STATE.data.recipes || [];
  if (u.group !== null) rows = rows.filter(r => r.group === u.group);
  const f = u.filter.trim().toLowerCase();
  if (f) rows = rows.filter(r => r.name.toLowerCase().includes(f));
  if (u.sort) {
    const col = RECIPE_COLS.find(c => c.k === u.sort);
    rows = sortRows(rows, u.sort, u.dir, col?.t || "str");
  }
  return rows;
}
function renderRecipeBody() {
  const u = STATE.ui.recipes;
  const rows = recipeRows();
  $("#recipeCount").textContent = rows.length + " recipes";
  return rows.map(r => {
    const lockBadge = r.is_unlocked ? "" : ' <span class="badge wax">locked</span>';
    const ageBadge  = r.can_be_aged ? ' <span class="badge gold">agable</span>' : "";
    const cls = r.is_unlocked ? "" : "dim";
    let mainRow = `
      <tr class="expandable ${cls}" data-rid="${r.recipe_id}">
        <td><div class="item-name">${itemLink(r.output_item_id, r.name)}${lockBadge}${ageBadge}</div></td>
        <td>${esc(r.group)}</td>
        <td class="num">${r.output_qty}</td>
        <td class="num">${fmtMoneyMuted(r.per_unit_sell)}</td>
        <td class="num">${fmtMoneyMuted(r.batch_sell)}</td>
        <td class="num">${fmtMoneyMuted(r.ingredient_buy_cost)}</td>
        <td class="num">${fmtMoney(r.profit_per_craft)}</td>
        <td class="num">${fmtHours(r.time_hours)}</td>
      </tr>`;
    let detail = "";
    if (u.expanded.has(r.recipe_id) && STATE.recipeDetailCache[r.recipe_id]) {
      const d = STATE.recipeDetailCache[r.recipe_id];
      let ranks = "";
      if (d.can_age) {
        ranks = '<div class="ranks">' + [0,1,2,3,4].map(rk => `
          <div class="rank-cell">
            <div class="rl">Rank ${rk}${rk === 0 ? '' : `<span class="age">${fmtHours(d.aging_hours_per_rank[rk])}</span>`}</div>
            <div class="profit">${fmtMoney(d.profit_per_rank_batch[rk])}</div>
            <div class="pu">${fmtMoney(d.aged_sell_per_unit[rk])}/u</div>
            <div class="batch">batch ${fmtMoneyMuted(d.aged_sell_batch[rk])}</div>
          </div>`).join("") + '</div>';
      }
      detail = `
        <tr class="detail-row">
          <td colspan="8">
            <div class="detail-title">${iconHtml(d.output_item_id, 'lg')} ${esc(d.name)}</div>
            <div class="detail-meta">total ${fmtHours(d.total_time_hours)} · cook ${fmtHours(d.active_cook_hours)} · fuel ${d.fuel} · cost ${fmtMoneyMuted(d.ingredient_buy_cost)}</div>
            ${renderStage(d.chain, false)}
            ${ranks}
          </td>
        </tr>`;
    }
    return mainRow + detail;
  }).join("");
}
function renderRecipes() {
  const u = STATE.ui.recipes;
  const headers = RECIPE_COLS.map(c =>
    `<th data-col="${c.k}" data-type="${c.t}" class="${c.align} ${u.sort === c.k ? 'sorted' : ''}">${c.l}${u.sort === c.k ? `<span class="arrow">${u.dir === 1 ? '▲' : '▼'}</span>` : ''}</th>`
  ).join("");
  const groups = ["All","Material","Food","Drink","Other"];
  const groupBtns = groups.map(g => {
    const active = (g === "All" && u.group === null) || g === u.group;
    return `<button data-group="${g}" class="${active ? 'on' : ''}">${g}</button>`;
  }).join("");
  return `
    <h2 class="section-head"><span class="ornament">⚒</span> The keeper's recipe register</h2>
    <div class="filter-bar">
      <div class="field"><input id="recipeFilter" type="text" placeholder="Search recipes…" value="${esc(u.filter)}"></div>
      <div class="pill-group">${groupBtns}</div>
      <span class="count" id="recipeCount"></span>
    </div>
    <div class="ledger-frame">
      <table class="ledger">
        <thead><tr>${headers}</tr></thead>
        <tbody id="recipeBody"></tbody>
      </table>
    </div>
    <p class="note">Click any row to unfurl its full crafting chain. Search stays focused as you type.</p>`;
}
async function toggleRecipeRow(rid) {
  const u = STATE.ui.recipes;
  if (u.expanded.has(rid)) {
    u.expanded.delete(rid);
  } else {
    u.expanded.add(rid);
    if (!STATE.recipeDetailCache[rid]) {
      try { STATE.recipeDetailCache[rid] = await jget(`/api/recipe/${rid}?` + qs()); }
      catch (e) { console.error(e); }
    }
  }
  $("#recipeBody").innerHTML = renderRecipeBody();
  bindRecipeBodyEvents();
}
function bindRecipeBodyEvents() {
  $$("#recipeBody tr.expandable").forEach(tr => {
    tr.addEventListener("click", () => toggleRecipeRow(parseInt(tr.dataset.rid)));
  });
}

/* ============================================================
   VENDORS TAB
   ============================================================ */
function renderVendors() {
  const data = STATE.data.vendors || [];
  const u = STATE.ui.vendors;
  const f = u.filter.trim().toLowerCase();
  const stockFilter = u.stock;
  const matches = (v) => {
    let list = v.items;
    if (f) {
      const vendorMatch = v.vendor.toLowerCase().includes(f);
      list = list.filter(i => vendorMatch || i.name.toLowerCase().includes(f));
    }
    if (stockFilter === "instock") list = list.filter(i => i.in_stock > 0);
    else if (stockFilter === "always") list = list.filter(i => i.always);
    else if (stockFilter === "today") list = list.filter(i => i.daily_special);
    return list;
  };
  const visible = data.filter(v => matches(v).length > 0);
  const cards = visible.map(v => {
    const items = matches(v).slice().sort((a,b) => a.buy_copper - b.buy_copper);
    const rows = items.map(i => {
      let stockBadge = "";
      if (i.in_stock !== null && i.in_stock !== undefined) {
        if (i.in_stock === 0) stockBadge = '<span class="badge wax">sold out</span>';
        else stockBadge = `<span class="badge moss">${i.in_stock} in stock</span>`;
      }
      if (i.daily_special) stockBadge += ' <span class="badge gold">today only</span>';
      return `
      <tr${i.in_stock === 0 ? ' style="opacity:0.4"' : ''}>
        <td class="nm ${i.always ? 'always' : ''}">${itemLink(i.item_id, i.name)} ${stockBadge}</td>
        <td class="num">${fmtMoney(i.buy_copper)}</td>
        <td class="num" style="color:var(--copper)">${fmtMoney(i.sell_copper)}</td>
      </tr>`;
    }).join("");
    const locPill = v.locations?.length
      ? `<span class="v-loc">${esc(v.locations.map(l => l.scene).join(", "))}</span>`
      : '<span class="v-loc unknown">location unknown</span>';
    return `
      <div class="vendor">
        <div class="v-head">
          <div>
            <div class="name">${esc(v.vendor)}</div>
            ${locPill}
          </div>
          <div class="v-meta">${items.length} of ${v.item_count} wares</div>
        </div>
        <table class="v-items"><tbody>${rows}</tbody></table>
      </div>`;
  }).join("");
  return `
    <h2 class="section-head"><span class="ornament">⚔</span> Merchants &amp; their wares</h2>
    <div class="filter-bar">
      <div class="field"><input id="vendorFilter" type="text" placeholder="Filter by vendor or item…" value="${esc(u.filter)}"></div>
      <div class="pill-group">
        <button data-vstock="all" class="${u.stock==='all'?'on':''}">All</button>
        <button data-vstock="instock" class="${u.stock==='instock'?'on':''}">In Stock Now</button>
        <button data-vstock="always" class="${u.stock==='always'?'on':''}">Always</button>
        <button data-vstock="today" class="${u.stock==='today'?'on':''}">Today Only</button>
      </div>
      <span class="count">${visible.length} merchants · ★ = always · green = in stock today</span>
    </div>
    <div class="vendor-grid">${cards || '<div class="empty">no matches</div>'}</div>`;
}

/* ============================================================
   QUESTS TAB
   ============================================================ */
function renderQuests() {
  const data = STATE.data.quests || [];
  const u = STATE.ui.quests;
  const f = u.filter.trim().toLowerCase();
  let visible = data;
  if (u.state !== "all") visible = visible.filter(q => q.state === u.state);
  if (f) visible = visible.filter(q =>
    q.name.toLowerCase().includes(f) || (q.description || "").toLowerCase().includes(f));
  const counts = {
    all: data.length,
    available: data.filter(q => q.state === "available").length,
    active: data.filter(q => q.state === "active").length,
    completed: data.filter(q => q.state === "completed").length,
  };
  const stateBtns = ["all","available","active","completed"].map(s =>
    `<button data-qstate="${s}" class="${u.state === s ? 'on' : ''}">${s} (${counts[s]})</button>`
  ).join("");
  const cards = visible.map(q => {
    const flags = [];
    if (q.is_repeatable)   flags.push('repeatable');
    if (q.only_halloween)  flags.push('halloween');
    if (q.only_christmas)  flags.push('christmas');
    if (q.required_amount > 1) flags.push(`×${q.required_amount}`);
    return `
      <div class="quest ${q.state}">
        <div class="q-head">
          <div class="q-name">${esc(q.name || `Quest #${q.quest_id}`)}</div>
          <div class="q-id">#${q.quest_id}</div>
        </div>
        ${q.description ? `<div class="q-desc">${esc(q.description)}</div>` : '<div class="empty">no description</div>'}
        ${flags.length ? `<div class="q-meta">${flags.join(' · ')}</div>` : ""}
      </div>`;
  }).join("");
  return `
    <h2 class="section-head"><span class="ornament">✦</span> The questboard</h2>
    <div class="filter-bar">
      <div class="field"><input id="questFilter" type="text" placeholder="Filter quests…" value="${esc(u.filter)}"></div>
      <div class="pill-group">${stateBtns}</div>
    </div>
    <div class="quest-grid">${cards || '<div class="empty">no quests match</div>'}</div>`;
}

/* ============================================================
   PERKS TAB
   ============================================================ */
function renderPerks() {
  const data = STATE.data.perks || { player: [], employee: [] };
  const u = STATE.ui.perks;
  const list = u.mode === "player" ? data.player : data.employee;
  const trees = {};
  for (const p of list) {
    const t = p.tree || "Misc";
    (trees[t] = trees[t] || []).push(p);
  }
  const treeBlocks = Object.entries(trees).map(([tree, perks]) => `
    <div class="perk-tree">
      <h3>${esc(tree)}<span class="ct">${perks.length} perks</span></h3>
      ${perks.map(p => `
        <div class="perk">
          <div class="pid">${p.perk_id}</div>
          <div>
            <div class="pname">${esc(p.name)}</div>
            <div class="pdesc">${esc(p.description)}</div>
          </div>
        </div>`).join("")}
    </div>`).join("");
  return `
    <h2 class="section-head"><span class="ornament">★</span> Perks &amp; talents</h2>
    <div class="filter-bar">
      <div class="pill-group">
        <button data-perk-mode="player"   class="${u.mode === 'player' ? 'on' : ''}">Player (${data.player.length})</button>
        <button data-perk-mode="employee" class="${u.mode === 'employee' ? 'on' : ''}">Employees (${data.employee.length})</button>
      </div>
    </div>
    ${treeBlocks}`;
}

/* ============================================================
   FISH / FORAGING / REPUTATION
   ============================================================ */
function renderFishOrBush(items, title, ornament, filterKey, placeholder, getMeta) {
  const u = STATE.ui[filterKey];
  const f = u.filter.trim().toLowerCase();
  const visible = !f ? items : items.filter(x => x.name.toLowerCase().includes(f));
  const tiles = visible.map(x => `
    <div class="entry">
      <span class="nm">${itemLink(x.fish_id ?? x.bush_id, x.name)}</span>
      <span class="meta">${getMeta ? getMeta(x) : ""}</span>
    </div>`).join("");
  return `
    <h2 class="section-head"><span class="ornament">${ornament}</span> ${title}</h2>
    <div class="filter-bar">
      <div class="field"><input id="${filterKey}Filter" type="text" placeholder="${placeholder}" value="${esc(u.filter)}"></div>
      <span class="count">${visible.length} entries</span>
    </div>
    <div class="list-grid">${tiles || '<div class="empty">none</div>'}</div>`;
}
function renderFish() {
  return renderFishOrBush(STATE.data.fish || [], "The angler's catalogue",
                          "≈", "fish", "Filter fish…", (x) => `#${x.fish_id}`);
}
function renderForaging() {
  return renderFishOrBush(STATE.data.bushes || [], "The forager's almanac",
                          "❦", "foraging", "Filter foraging spots…",
                          (x) => `${(x.seasons || []).join("·")} · ${x.harvest_amount_min}-${x.harvest_amount_max}/pick`);
}
function renderReputation() {
  const data = STATE.data.reputation || [];
  return `
    <h2 class="section-head"><span class="ornament">♛</span> Reputation milestones</h2>
    <div class="rep-track">
      ${data.map(r => `
        <div class="rep-node">
          <span class="rep-id">${r.rep_id}</span>
          <span class="rep-name">${esc(r.name)}</span>
          <span class="rep-meta">cap ${r.customers_capacity} · floor ${r.floor} · ${r.dining_zones} dining · ${r.crafting_zones} crafting · ${r.rented_rooms} rooms</span>
        </div>`).join("")}
    </div>`;
}

/* ============================================================
   BREW PLAN TAB — what to brew per upcoming trend week
   ============================================================ */
function renderBrewPlanWeek(w) {
  const ingChips = w.trending_ingredients.slice(0, 8).map(ing =>
    `<span class="ing-chip">${itemLink(ing.item_id, ing.name)}</span>`).join("");
  const picks = w.picks.slice(0, 8).map(p => {
    const lockBadge = p.is_unlocked ? "" : '<span class="badge wax">locked</span>';
    const wineBadge = p.is_wine ? '<span class="badge ember">wine</span>' : '';
    const startBy = p.start_brewing_by_day === 0
      ? '<span class="badge gold glow">start TODAY</span>'
      : `<span class="badge gold">start by day ${p.start_brewing_by_day}</span>`;
    const combo = p.best_combo.map(c => {
      const cls = c.is_trending ? 'class="combo trend"' : 'class="combo"';
      return `<span ${cls}>${c.slot_amount}× ${itemLink(c.item_id, c.item_name)}${c.mod_name ? ` (${esc(c.mod_name)})` : ""}</span>`;
    }).join("");
    return `
      <div class="bp-pick ${p.is_unlocked ? '' : 'locked'}">
        <div class="bp-head">
          <div class="bp-name">${itemLink(p.drink_item_id, p.drink_name)} ${lockBadge} ${wineBadge}</div>
          <div class="bp-deadline">${startBy}</div>
        </div>
        <div class="bp-stats">
          <div class="bp-stat"><div class="lbl">Profit per craft (rank 4 + trend)</div><div class="big">${fmtMoney(p.profit_per_craft_aged4)}</div></div>
          <div class="bp-stat"><div class="lbl">Per-unit (trend)</div><div class="med">${fmtMoney(p.trended_per_unit_sell)}</div></div>
          <div class="bp-stat"><div class="lbl">Cost</div><div class="med">${fmtMoneyMuted(p.ingredient_cost)}</div></div>
          <div class="bp-stat"><div class="lbl">Cook + age</div><div class="med">${fmtHours(p.total_with_aging_hours)}</div></div>
        </div>
        <div class="bp-combo">${combo}</div>
        <div class="bp-why">${p.why.map(esc).join(" · ")}</div>
      </div>`;
  }).join("");
  return `
    <div class="bp-week ${w.week_offset === 0 ? 'now' : ''}">
      <div class="bp-week-head">
        <h3>Week +${w.week_offset} <span class="ord">${esc(w.season)}</span></h3>
        <span class="bp-when">${w.days_until === 0 ? 'NOW' : `in ${w.days_until}d`}</span>
      </div>
      ${ingChips ? `<div class="bp-ings"><span class="bp-ings-l">trending ingredients:</span> ${ingChips}</div>` : ''}
      ${picks || '<div class="empty">no recipes match</div>'}
    </div>`;
}
function renderBrewPlan() {
  const data = STATE.data.brewPlan;
  if (!data || !data.weeks || !data.weeks.length) return '<div class="empty">no trend data</div>';
  return `
    <h2 class="section-head"><span class="ornament">⌗</span> Brew planner</h2>
    <p class="note">For each upcoming trend week, the drinks you should brew (and the ingredient choices that maximise margin). Trending ingredients in your slots are highlighted — using them up while they're hot is also worth +20%.</p>
    ${data.weeks.map(renderBrewPlanWeek).join("")}`;
}

/* ============================================================
   MENU PLANNER TAB
   ============================================================ */
function renderMenuPlanner() {
  const u = STATE.ui.menu;
  const recipes = (STATE.data.recipes || []).filter(r => r.is_unlocked);
  // Build trending sets for the bonus highlight
  const trending = new Set();
  if (STATE.data.plan)
    for (const t of (STATE.data.plan.calendar?.[0]?.food_trends || [])) trending.add(t.item_id);
  for (const t of (STATE.data.plan?.calendar?.[0]?.drink_trends || [])) trending.add(t.item_id);

  const f = u.filter.trim().toLowerCase();
  const visible = !f ? recipes : recipes.filter(r => r.name.toLowerCase().includes(f));

  const picked = [...u.picked].map(rid => recipes.find(r => r.recipe_id === rid)).filter(Boolean);
  // Aggregate stats
  let totalCost = 0, totalSell = 0, totalFuel = 0, totalTime = 0;
  let drinkCount = 0, foodCount = 0, trendingCount = 0;
  for (const r of picked) {
    totalCost += r.ingredient_buy_cost;
    const trendBonus = trending.has(r.output_item_id) ? 1.20 : 1.0;
    totalSell += Math.round(r.batch_sell * trendBonus);
    totalFuel += r.fuel;
    totalTime += r.time_hours;
    if (r.group === "Drink") drinkCount++;
    if (r.group === "Food")  foodCount++;
    if (trending.has(r.output_item_id)) trendingCount++;
  }
  // Unique-bar-items bonus: +3c per unique drink on every drink sold (Money.cs:435)
  const uniqueBonusPerDrink = drinkCount * 3;

  const renderRow = (r) => {
    const on = u.picked.has(r.recipe_id);
    const isTrending = trending.has(r.output_item_id);
    return `
      <tr class="menu-row ${on ? 'on' : ''} ${isTrending ? 'trending' : ''}" data-rid="${r.recipe_id}">
        <td><input type="checkbox" ${on ? 'checked' : ''} data-pick="${r.recipe_id}"></td>
        <td>${itemLink(r.output_item_id, r.name)} ${isTrending ? '<span class="badge gold glow">trending</span>' : ''}</td>
        <td>${esc(r.group)}</td>
        <td class="num">${fmtMoneyMuted(r.batch_sell)}</td>
        <td class="num">${fmtMoneyMuted(r.profit_per_craft)}</td>
        <td class="num">${fmtHours(r.time_hours)}</td>
      </tr>`;
  };

  const summary = `
    <div class="stat-grid" style="grid-template-columns:repeat(7, 1fr)">
      <div class="stat-tile"><div class="label">Picked</div><div class="value">${picked.length}</div></div>
      <div class="stat-tile"><div class="label">Foods</div><div class="value">${foodCount}</div></div>
      <div class="stat-tile"><div class="label">Drinks</div><div class="value">${drinkCount}</div><div class="sub">+${uniqueBonusPerDrink}c per drink</div></div>
      <div class="stat-tile"><div class="label">Trending</div><div class="value">${trendingCount}</div></div>
      <div class="stat-tile"><div class="label">Total fuel</div><div class="value">${totalFuel}</div></div>
      <div class="stat-tile"><div class="label">Total cost</div><div class="value money">${fmtMoney(totalCost)}</div></div>
      <div class="stat-tile"><div class="label">Total sell (w/trend)</div><div class="value money">${fmtMoney(totalSell)}</div></div>
    </div>`;

  const pickedRows = picked.length === 0
    ? '<div class="empty">No dishes picked. Tick a checkbox below to add to your menu.</div>'
    : `<div class="ledger-frame">
        <table class="ledger">
          <thead><tr><th></th><th>Recipe</th><th>Group</th><th class="num">Batch</th><th class="num">Profit</th><th class="num">Time</th></tr></thead>
          <tbody>${picked.map(renderRow).join("")}</tbody>
        </table>
      </div>`;

  const allRows = visible.map(renderRow).join("");
  return `
    <h2 class="section-head"><span class="ornament">📜</span> Menu planner</h2>
    ${summary}
    <h2 class="section-head"><span class="ornament">✓</span> Your menu (${picked.length})</h2>
    ${pickedRows}
    <h2 class="section-head"><span class="ornament">⚒</span> Add dishes</h2>
    <div class="filter-bar">
      <div class="field"><input id="menuFilter" type="text" placeholder="Filter recipes…" value="${esc(u.filter)}"></div>
      <span class="count">${visible.length} recipes available</span>
    </div>
    <div class="ledger-frame">
      <table class="ledger">
        <thead><tr><th></th><th>Recipe</th><th>Group</th><th class="num">Batch</th><th class="num">Profit</th><th class="num">Time</th></tr></thead>
        <tbody id="menuPickBody">${allRows}</tbody>
      </table>
    </div>`;
}

/* ============================================================
   SHOPPING LIST TAB
   ============================================================ */
function renderShopping() {
  const u = STATE.ui.shopping;
  const list = CART;

  // Group by vendor
  const byVendor = {};
  let totalCost = 0;
  for (const item of list) {
    const v = item.vendor || "Unknown";
    (byVendor[v] = byVendor[v] || []).push(item);
    totalCost += (item.buy_copper || 0) * item.qty;
  }

  const listHtml = list.length === 0
    ? '<div class="empty">Your shopping list is empty. Search for items below and add them.</div>'
    : Object.entries(byVendor).map(([vendor, items]) => {
        const vendorTotal = items.reduce((s, i) => s + (i.buy_copper || 0) * i.qty, 0);
        const rows = items.map(i => `
          <div class="slot">
            <div class="label">
              <span class="amt">${i.qty}×</span>${itemLink(i.item_id, i.name)}
            </div>
            <div class="cost">
              ${fmtMoney(i.buy_copper * i.qty)}
              <span style="cursor:pointer;color:var(--burgundy);margin-left:8px" onclick="removeShoppingItem(${i.item_id})">✕</span>
            </div>
          </div>`).join("");
        return `
          <div class="card" style="margin-bottom:10px">
            <div class="head">
              <div class="title" style="font-size:18px">${esc(vendor)}</div>
              <div>${fmtMoney(vendorTotal)}</div>
            </div>
            ${rows}
          </div>`;
      }).join("");

  // Search results for adding items
  const f = u.filter.trim().toLowerCase();
  let searchResults = "";
  if (f && f.length >= 2) {
    // Search vendors for matching items
    const vendors = STATE.data.vendors || [];
    const matches = [];
    for (const v of vendors) {
      for (const i of v.items) {
        if (i.name.toLowerCase().includes(f) && i.buy_copper > 0) {
          matches.push({ ...i, vendor: v.vendor });
        }
      }
    }
    // Dedupe by item_id, keep cheapest
    const seen = {};
    for (const m of matches) {
      if (!seen[m.item_id] || m.buy_copper < seen[m.item_id].buy_copper) {
        seen[m.item_id] = m;
      }
    }
    const unique = Object.values(seen).sort((a, b) => a.name.localeCompare(b.name)).slice(0, 20);
    if (unique.length) {
      searchResults = unique.map(m => `
        <div class="slot" style="cursor:pointer" onclick="addShoppingItem(${m.item_id}, '${esc(m.name).replace(/'/g,"\\'")}', ${m.buy_copper}, '${esc(m.vendor).replace(/'/g,"\\'")}')">
          <div class="label">${itemLink(m.item_id, m.name)} <span style="color:var(--ink-ghost);font-size:11px">from ${esc(m.vendor)}</span></div>
          <div class="cost">${fmtMoney(m.buy_copper)} each</div>
        </div>`).join("");
    } else {
      searchResults = '<div class="empty">no vendor sells that</div>';
    }
  }

  return `
    <h2 class="section-head"><span class="ornament">🛒</span> Shopping checklist</h2>

    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom:16px">
      <div class="stat-tile"><div class="label">Items</div><div class="value">${list.length}</div></div>
      <div class="stat-tile"><div class="label">Total units</div><div class="value">${list.reduce((s,i)=>s+i.qty,0)}</div></div>
      <div class="stat-tile"><div class="label">Total cost</div><div class="value money">${fmtMoney(totalCost)}</div></div>
    </div>

    ${listHtml}

    ${list.length > 0 ? '<button class="btn" style="background:var(--burgundy);color:#fff;border:0;padding:8px 16px;cursor:pointer;font-family:inherit;margin:8px 0" onclick="clearShopping()">Clear list</button>' : ''}

    <h2 class="section-head"><span class="ornament">+</span> Add items</h2>
    <div class="filter-bar">
      <div class="field"><input id="shopSearchFilter" type="text" placeholder="Search for an item to add…" value="${esc(u.filter)}"></div>
    </div>
    ${searchResults ? '<div class="card">' + searchResults + '</div>' : ''}
    <p class="note">Search by item name. Click to add 1 to your list. Click again to add more. Items show the cheapest vendor price.</p>`;
}

async function addShoppingItem(itemId, name, buyCost, vendor) {
  await addToCart(itemId, name, buyCost, vendor, 1);
  // Cart updates via websocket, but also update locally for instant feedback
  const existing = CART.find(i => i.item_id === itemId);
  if (existing) existing.qty = (existing.qty || 0) + 1;
  else CART.push({ item_id: itemId, name: name, qty: 1, buy_copper: buyCost, vendor: vendor });
  if (STATE.tab === "shopping") renderTab();
  const f = $("#shopSearchFilter");
  if (f) { f.focus(); f.setSelectionRange(f.value.length, f.value.length); }
}

async function removeShoppingItem(itemId) {
  await removeFromCart(itemId);
  CART = CART.filter(i => i.item_id !== itemId);
  if (STATE.tab === "shopping") renderTab();
}

async function clearShopping() {
  await clearCart();
  CART = [];
  if (STATE.tab === "shopping") renderTab();
}

/* ============================================================
   MAP TAB — canvas of hotspot positions
   ============================================================ */
function renderMap() {
  const h = STATE.data.hotspots;
  if (!h) return '<div class="empty">Hotspot data not extracted. Run scripts/dump_hotspots.py.</div>';
  const u = STATE.ui.map;
  // Count points per scene to find populated ones
  const sceneCounts = {};
  for (const k of ["trees","foraging","fishing","animals","vendors"]) {
    for (const x of (h[k] || [])) {
      sceneCounts[x.scene] = (sceneCounts[x.scene] || 0) + 1;
    }
  }
  const populatedScenes = Object.entries(sceneCounts)
    .filter(([s, n]) => n >= 5)
    .sort((a, b) => b[1] - a[1])
    .map(([s]) => s);
  // Default to the most-populated scene if user hasn't picked one
  if (u.scene === "all" || !populatedScenes.includes(u.scene)) {
    if (populatedScenes.length) u.scene = populatedScenes[0];
  }
  const sceneList = ["all", ...populatedScenes];
  const layerBtns = ["all","trees","foraging","fishing","vendors","animals"].map(l =>
    `<button data-layer="${l}" class="${u.layer === l ? 'on' : ''}">${l}</button>`).join("");
  const sceneOpts = sceneList.map(s => {
    const lbl = s === "all" ? "all scenes" : `${s}  (${sceneCounts[s] || 0} pts)`;
    return `<option value="${s}" ${u.scene === s ? 'selected' : ''}>${lbl}</option>`;
  }).join("");
  const counts = {
    trees: (h.trees || []).length,
    foraging: (h.foraging || []).length,
    fishing: (h.fishing || []).length,
    animals: (h.animals || []).length,
    vendors: (h.vendors || []).length,
  };
  return `
    <h2 class="section-head"><span class="ornament">⛰</span> The cartographer's map</h2>
    <div class="map-controls">
      <div class="pill-group">${layerBtns}</div>
      <select id="mapSceneSel">${sceneOpts}</select>
      <div class="legend">
        <span class="lg-item"><span class="dot tree"></span>tree (${counts.trees})</span>
        <span class="lg-item"><span class="dot bush"></span>foraging (${counts.foraging})</span>
        <span class="lg-item"><span class="dot fish"></span>fishing (${counts.fishing})</span>
        <span class="lg-item"><span class="dot animal"></span>animal (${counts.animals})</span>
        <span class="lg-item"><span class="dot" style="background:#983d3d"></span>vendor (${counts.vendors})</span>
      </div>
    </div>
    <div class="map-canvas-wrap">
      <canvas id="mapCanvas" width="1400" height="800"></canvas>
    </div>
    <div class="map-stats" id="mapStats"></div>
    <p class="note">Each dot is a placed object in a scene file. World coordinates are auto-fitted into the canvas. Scene filter defaults to the largest populated scene.</p>`;
}
// Cached background images per scene
const MAP_IMG_CACHE = {};
function loadMapImage(scene) {
  if (MAP_IMG_CACHE[scene]) return MAP_IMG_CACHE[scene];
  const img = new Image();
  img.src = `/maps/${scene}.png`;
  MAP_IMG_CACHE[scene] = img;
  img.onload = () => { drawMap(); };
  return img;
}

function drawMap() {
  const canvas = $("#mapCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = "#f5e9c4";
  ctx.fillRect(0, 0, W, H);

  const h = STATE.data.hotspots || {};
  const maps = STATE.data.maps || {};
  const u = STATE.ui.map;
  const layers = u.layer === "all"
    ? ["trees","foraging","fishing","animals","vendors"]
    : [u.layer];

  // Map metadata for the selected scene (only when we render a single scene
  // do we use the rendered tilemap as a background)
  const meta = (u.scene !== "all") ? maps[u.scene] : null;

  // Collect points. Hotspot positions are in PIXELS; tilemap world bounds
  // are in TILE UNITS, so convert by dividing by ppu when we have a map.
  const ppu = meta ? meta.ppu : 16;
  const points = [];
  for (const layer of layers) {
    for (const p of (h[layer] || [])) {
      if (u.scene !== "all" && p.scene !== u.scene) continue;
      const px = meta ? p.x / ppu : p.x;
      const py = meta ? p.y / ppu : p.y;
      points.push({ x: px, y: py, layer, scene: p.scene, raw: p });
    }
  }

  // World rect (in tile units when meta, otherwise world units from hotspots)
  let minX, maxX, minY, maxY;
  // Pixel rect of where the world rect will be placed inside the canvas
  let bgX, bgY, bgW, bgH;
  // Helper: world (wx, wy) -> canvas (cx, cy) — used for dots
  let toCanvas;

  if (meta) {
    minX = meta.world_min_x;
    maxX = meta.world_max_x + 1;
    minY = meta.world_min_y;
    maxY = meta.world_max_y + 1;
    const rngX = maxX - minX, rngY = maxY - minY;
    const s = Math.min(W / rngX, H / rngY);
    bgW = rngX * s;
    bgH = rngY * s;
    bgX = (W - bgW) / 2;
    bgY = (H - bgH) / 2;
    toCanvas = (wx, wy) => [
      bgX + (wx - minX) * s,
      bgY + (maxY - wy) * s,   // flip Y so up is +
    ];

    const img = loadMapImage(u.scene);
    if (img.complete && img.naturalWidth > 0) {
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(img, bgX, bgY, bgW, bgH);
    } else {
      ctx.fillStyle = "#816644";
      ctx.font = "italic 14px 'EB Garamond', serif";
      ctx.textAlign = "center";
      ctx.fillText("loading map…", W/2, H/2);
    }
  } else if (points.length) {
    minX = Infinity; maxX = -Infinity; minY = Infinity; maxY = -Infinity;
    for (const p of points) {
      if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y;
    }
    const padX = Math.max(20, (maxX - minX) * 0.05);
    const padY = Math.max(20, (maxY - minY) * 0.05);
    minX -= padX; maxX += padX; minY -= padY; maxY += padY;
    const rngX = maxX - minX, rngY = maxY - minY;
    const s = Math.min((W - 30) / rngX, (H - 30) / rngY);
    bgW = rngX * s;
    bgH = rngY * s;
    bgX = (W - bgW) / 2;
    bgY = (H - bgH) / 2;
    toCanvas = (wx, wy) => [
      bgX + (wx - minX) * s,
      bgY + (maxY - wy) * s,
    ];
  } else {
    ctx.fillStyle = "#816644";
    ctx.font = "italic 16px 'EB Garamond', serif";
    ctx.textAlign = "center";
    ctx.fillText("(no points to draw)", W/2, H/2);
    $("#mapStats").textContent = "0 points";
    return;
  }

  // Light grid overlay (only when no background)
  if (!meta) {
    ctx.strokeStyle = "rgba(173, 149, 84, 0.18)";
    ctx.lineWidth = 0.5;
    const step = 100;
    for (let gx = Math.ceil(minX / step) * step; gx <= maxX; gx += step) {
      const [px, _] = toCanvas(gx, minY);
      ctx.beginPath(); ctx.moveTo(px, bgY); ctx.lineTo(px, bgY + bgH); ctx.stroke();
    }
    for (let gy = Math.ceil(minY / step) * step; gy <= maxY; gy += step) {
      const [_, py] = toCanvas(minX, gy);
      ctx.beginPath(); ctx.moveTo(bgX, py); ctx.lineTo(bgX + bgW, py); ctx.stroke();
    }
  }

  const colours = {
    trees:    "#6a9248",
    foraging: "#983d3d",
    fishing:  "#6c9bb1",
    animals:  "#d49a2a",
    vendors:  "#5c2a8a",
  };
  // Dedupe overlapping points
  const seen = new Set();
  let drawn = 0;
  const labelDraws = [];
  for (const p of points) {
    const key = `${p.layer}|${p.scene}|${p.x.toFixed(1)}|${p.y.toFixed(1)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const [px, py] = toCanvas(p.x, p.y);
    ctx.fillStyle = colours[p.layer] || "#000";
    if (p.layer === "vendors") {
      // Star marker for vendors
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff8e1";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      // p.raw still has the original record from the loop above
      if (p.raw?.name) labelDraws.push({ px, py, name: p.raw.name });
    } else {
      ctx.beginPath();
      ctx.arc(px, py, p.layer === "fishing" ? 4 : 3, 0, Math.PI * 2);
      ctx.fill();
    }
    drawn++;
  }
  // Vendor labels
  ctx.font = "11px 'EB Garamond', serif";
  ctx.fillStyle = "#3a2918";
  ctx.strokeStyle = "#fff8e1";
  ctx.lineWidth = 3;
  ctx.textAlign = "center";
  for (const ld of labelDraws) {
    ctx.strokeText(ld.name, ld.px, ld.py - 10);
    ctx.fillText(ld.name, ld.px, ld.py - 10);
  }
  $("#mapStats").textContent = `${drawn} unique points · scene ${u.scene} · bounds [${Math.round(minX)},${Math.round(minY)}] → [${Math.round(maxX)},${Math.round(maxY)}]`;
}

/* ============================================================
   ROUTING / EVENT BINDING
   ============================================================ */
const TABS = {
  plan: renderPlan,
  seeds: renderSeeds,
  brewing: renderBrewing,
  brewPlan: renderBrewPlan,
  recipes: renderRecipes,
  vendors: renderVendors,
  quests: renderQuests,
  perks: renderPerks,
  fish: renderFish,
  foraging: renderForaging,
  reputation: renderReputation,
  map: renderMap,
  menu: renderMenuPlanner,
  shopping: renderShopping,
};

function setTab(name) {
  STATE.tab = name;
  // Clear all active states
  $$("nav.tabs button[data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  // Mark parent dropdown as active if the selected tab is inside one
  $$("nav.tabs .tab-dropdown").forEach(dd => {
    const hasActive = !!dd.querySelector(`button[data-tab="${name}"]`);
    dd.classList.toggle("has-active", hasActive);
  });
  renderTab();
}
function renderTab() {
  const c = $("#content");
  const fn = TABS[STATE.tab];
  if (!fn) { c.innerHTML = '<div class="empty">unknown tab</div>'; return; }
  if (!STATE.data.plan) { c.innerHTML = '<div class="loading">Reading the ledger</div>'; return; }
  c.innerHTML = '<div class="tab-shell">' + fn() + '</div>';
  bindTab();
  // Some tabs need a follow-up render after the DOM exists
  if (STATE.tab === "seeds")    $("#seedBody").innerHTML = renderSeedsBody();
  if (STATE.tab === "recipes") { $("#recipeBody").innerHTML = renderRecipeBody(); bindRecipeBodyEvents(); }
  if (STATE.tab === "map")      drawMap();
}

function bindTab() {
  $$("table.ledger thead th").forEach(th => {
    th.addEventListener("click", () => {
      const k = th.dataset.col;
      if (!k) return;
      const u = STATE.ui[STATE.tab];
      if (!u) return;
      if (u.sort === k) u.dir = -u.dir;
      else { u.sort = k; u.dir = (th.dataset.type === "str" || th.dataset.type === "arr") ? 1 : -1; }
      renderTab();
    });
  });

  if (STATE.tab === "seeds") {
    const f = $("#seedFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.seeds.filter = f.value;
      $("#seedBody").innerHTML = renderSeedsBody();
    });
  }

  if (STATE.tab === "recipes") {
    const f = $("#recipeFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.recipes.filter = f.value;
      $("#recipeBody").innerHTML = renderRecipeBody();
      bindRecipeBodyEvents();
    });
    $$("[data-group]").forEach(b => b.addEventListener("click", () => {
      const g = b.dataset.group;
      STATE.ui.recipes.group = (g === "All") ? null : g;
      $$("[data-group]").forEach(x => x.classList.toggle("on", x.dataset.group === g));
      $("#recipeBody").innerHTML = renderRecipeBody();
      bindRecipeBodyEvents();
    }));
  }

  if (STATE.tab === "brewing") {
    $$("[data-toggle]").forEach(b => b.addEventListener("click", () => {
      STATE.ui.brewing.showLocked = b.dataset.toggle === "all";
      renderTab();
    }));
  }

  if (STATE.tab === "vendors") {
    const f = $("#vendorFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.vendors.filter = f.value;
      // Only re-render the vendor grid container
      const wrap = $(".vendor-grid");
      if (wrap) {
        // simplest: full re-render of tab content
        renderTab();
        // restore caret
        const ff = $("#vendorFilter");
        if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
      }
    });
    $$("[data-vstock]").forEach(b => b.addEventListener("click", () => {
      STATE.ui.vendors.stock = b.dataset.vstock;
      renderTab();
    }));
  }

  if (STATE.tab === "quests") {
    const f = $("#questFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.quests.filter = f.value;
      renderTab();
      const ff = $("#questFilter");
      if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
    });
    $$("[data-qstate]").forEach(b => b.addEventListener("click", () => {
      STATE.ui.quests.state = b.dataset.qstate;
      renderTab();
    }));
  }

  if (STATE.tab === "perks") {
    $$("[data-perk-mode]").forEach(b => b.addEventListener("click", () => {
      STATE.ui.perks.mode = b.dataset.perkMode;
      renderTab();
    }));
  }

  if (STATE.tab === "fish") {
    const f = $("#fishFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.fish.filter = f.value;
      renderTab();
      const ff = $("#fishFilter");
      if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
    });
  }

  if (STATE.tab === "foraging") {
    const f = $("#foragingFilter");
    if (f) f.addEventListener("input", () => {
      STATE.ui.foraging.filter = f.value;
      renderTab();
      const ff = $("#foragingFilter");
      if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
    });
  }

  if (STATE.tab === "menu") {
    const f = $("#menuFilter");
    if (f) {
      f.addEventListener("input", () => {
        STATE.ui.menu.filter = f.value;
        renderTab();
        const ff = $("#menuFilter");
        if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
      });
    }
    $$("[data-pick]").forEach(cb => cb.addEventListener("change", (e) => {
      e.stopPropagation();
      const rid = parseInt(cb.dataset.pick);
      if (cb.checked) STATE.ui.menu.picked.add(rid);
      else            STATE.ui.menu.picked.delete(rid);
      renderTab();
    }));
  }

  if (STATE.tab === "shopping") {
    const f = $("#shopSearchFilter");
    if (f) {
      f.addEventListener("input", () => {
        STATE.ui.shopping.filter = f.value;
        renderTab();
        const ff = $("#shopSearchFilter");
        if (ff) { ff.focus(); ff.setSelectionRange(ff.value.length, ff.value.length); }
      });
    }
  }

  if (STATE.tab === "map") {
    $$("[data-layer]").forEach(b => b.addEventListener("click", () => {
      STATE.ui.map.layer = b.dataset.layer;
      $$("[data-layer]").forEach(x => x.classList.toggle("on", x.dataset.layer === STATE.ui.map.layer));
      drawMap();
    }));
    const sceneSel = $("#mapSceneSel");
    if (sceneSel) sceneSel.addEventListener("change", () => {
      STATE.ui.map.scene = sceneSel.value;
      drawMap();
    });
  }
}

/* ============================================================
   GLOBAL FUZZY SEARCH
   ============================================================ */
function buildSearchIndex() {
  const idx = [];
  for (const r of (STATE.data.recipes || []))
    idx.push({ kind: "recipe", id: r.recipe_id, name: r.name, tab: "recipes" });
  for (const i of (STATE.data.seeds || []))
    if (i.is_obtainable) idx.push({ kind: "crop", id: i.crop_id, name: i.name, tab: "seeds" });
  for (const v of (STATE.data.vendors || []))
    idx.push({ kind: "vendor", id: v.shop_id, name: v.vendor, tab: "vendors" });
  for (const v of (STATE.data.vendors || []))
    for (const it of v.items)
      idx.push({ kind: "item", id: it.item_id, name: it.name, tab: "vendors" });
  for (const q of (STATE.data.quests || []))
    idx.push({ kind: "quest", id: q.quest_id, name: q.name, tab: "quests" });
  for (const f of (STATE.data.fish || []))
    idx.push({ kind: "fish", id: f.fish_id, name: f.name, tab: "fish" });
  for (const b of (STATE.data.bushes || []))
    idx.push({ kind: "bush", id: b.bush_id, name: b.name, tab: "foraging" });
  for (const p of (STATE.data.brewing || []))
    idx.push({ kind: "drink", id: p.drink_item_id, name: p.drink_name, tab: "brewing" });
  for (const p of (STATE.data.perks?.player || []))
    idx.push({ kind: "perk", id: p.perk_id, name: p.name, tab: "perks" });
  return idx;
}

let SEARCH_INDEX = null;

function fuzzyScore(query, target) {
  query = query.toLowerCase();
  target = target.toLowerCase();
  // Exact substring is a strong match
  const i = target.indexOf(query);
  if (i === 0) return 1000 - target.length;
  if (i > 0)   return 500 - i - target.length;
  // Subsequence match — every char of query appears in order
  let qi = 0, score = 100;
  for (let ti = 0; ti < target.length && qi < query.length; ti++) {
    if (target[ti] === query[qi]) { qi++; score--; }
  }
  return qi === query.length ? score : -1;
}
function runSearch(query) {
  if (!query.trim()) { $("#searchResults").classList.remove("open"); return; }
  if (!SEARCH_INDEX) SEARCH_INDEX = buildSearchIndex();
  const scored = SEARCH_INDEX
    .map(e => ({ e, s: fuzzyScore(query, e.name) }))
    .filter(x => x.s > 0)
    .sort((a, b) => b.s - a.s)
    .slice(0, 24);
  if (!scored.length) {
    $("#searchResults").innerHTML = '<div class="search-result"><span class="nm" style="color:var(--ink-ghost)">no matches</span></div>';
  } else {
    $("#searchResults").innerHTML = scored.map(({ e }) => `
      <div class="search-result" data-tab="${e.tab}" data-name="${esc(e.name)}">
        <div class="nm">${iconHtml(e.id)}${esc(e.name)}</div>
        <div class="kind">${e.kind}</div>
      </div>`).join("");
    $$("#searchResults .search-result").forEach(el => el.addEventListener("click", () => {
      setTab(el.dataset.tab);
      // Pre-fill any tab filter on jump
      const fname = el.dataset.name;
      setTimeout(() => {
        const f = $(`#${el.dataset.tab}Filter`) || $("#recipeFilter") || $("#vendorFilter") || $("#seedFilter");
        if (f) {
          f.value = fname;
          f.dispatchEvent(new Event("input"));
        }
      }, 30);
      $("#searchResults").classList.remove("open");
      $("#globalSearch").value = "";
    }));
  }
  $("#searchResults").classList.add("open");
}

/* ============================================================
   WEBSOCKET
   ============================================================ */
function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  let backoff = 800;
  const open = () => {
    let ws;
    try { ws = new WebSocket(`${proto}://${location.host}/ws`); }
    catch (_) { return setTimeout(open, backoff); }
    ws.onopen = () => {
      backoff = 800;
      const p = $("#ws-pill");
      p.classList.remove("dead"); p.classList.add("live"); p.textContent = "live";
    };
    ws.onclose = () => {
      const p = $("#ws-pill");
      p.classList.remove("live"); p.classList.add("dead"); p.textContent = "offline";
      backoff = Math.min(backoff * 1.6, 12000);
      setTimeout(open, backoff);
    };
    ws.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (m.type === "save_changed") setTimeout(loadAll, 500);
        if (m.type === "cart_updated" && m.slot === STATE.slot) {
          CART = m.cart || [];
          if (STATE.tab === "shopping") renderTab();
        }
      } catch (_) {}
    };
  };
  open();
}

/* ============================================================
   BOOT
   ============================================================ */
async function boot() {
  STATE.saves = await jget("/api/saves").catch(() => []);
  STATE.languages = await jget("/api/languages").catch(() => []);
  if (STATE.saves.length) STATE.slot = STATE.saves[0].slot_id;

  $("#slot").innerHTML = STATE.saves.map(s =>
    `<option value="${esc(s.slot_id)}">${esc(s.label)}</option>`).join("") || '<option>no save</option>';
  $("#lang").innerHTML = STATE.languages.map(l =>
    `<option value="${esc(l.name)}">${esc(l.name)}</option>`).join("") || '<option>English</option>';
  $("#lang").value = STATE.lang;

  $("#slot").onchange = () => { STATE.slot = $("#slot").value; loadAll(); loadCart(); };
  $("#lang").onchange = () => { STATE.lang = $("#lang").value; loadAll(); };

  // Top-level tab buttons (Plan)
  $$("nav.tabs > .row > button[data-tab]").forEach(b =>
    b.addEventListener("click", () => {
      $$(".tab-dropdown").forEach(dd => dd.classList.remove("open"));
      setTab(b.dataset.tab);
    }));

  // Dropdown triggers — toggle open/close
  $$(".tab-trigger").forEach(trigger => {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const dd = trigger.closest(".tab-dropdown");
      const wasOpen = dd.classList.contains("open");
      $$(".tab-dropdown").forEach(d => d.classList.remove("open"));
      if (!wasOpen) dd.classList.add("open");
    });
  });

  // Dropdown menu items — select tab and close dropdown
  $$(".tab-menu button[data-tab]").forEach(b => {
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      $$(".tab-dropdown").forEach(dd => dd.classList.remove("open"));
      setTab(b.dataset.tab);
    });
  });

  // Close dropdowns when clicking elsewhere
  document.addEventListener("click", () => {
    $$(".tab-dropdown").forEach(dd => dd.classList.remove("open"));
  });

  // Global search
  const gs = $("#globalSearch");
  let st;
  gs.addEventListener("input", () => {
    clearTimeout(st);
    SEARCH_INDEX = null;
    st = setTimeout(() => runSearch(gs.value), 80);
  });
  gs.addEventListener("focus", () => { if (gs.value) runSearch(gs.value); });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".global-search")) $("#searchResults").classList.remove("open");
  });

  await loadAll();
  await loadCart();
  connectWS();
}
boot();
</script>
</body>
</html>
"""
