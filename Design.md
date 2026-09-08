# Design.md — UI/UX Design Specification
## KavachAI — Sovereign Industrial Agentic AI Workbench
**Version:** 1.0

> **⚠️ HARD CONSTRAINT — READ FIRST**
> **Do not use any color from the blue family anywhere in this product** — no blue, no navy, no indigo, no cyan-leaning-blue, no royal/sky/steel blue, in any background, text, icon, chart series, status tag, gradient, shadow tint, focus ring, link color, or illustration. This applies to every screen, every component, every state (including hover/focus/disabled), and every exported artifact (PDF report, charts). If a design decision would naturally reach for blue (links, "info" status, primary buttons, focus rings — all conventionally blue), substitute the palette defined in §2 instead. Before shipping any screen, run the checklist in §9.

---

## 1. Design Philosophy

KavachAI must **not look like a chatbot demo**. The reference material (`frontend-design-gita__1___1_.html`) — a dark-mode, editorial, high-craft design system — is the foundation for the visual language: a serious, dark, editorial-industrial aesthetic that reads as **control room / engineering instrument**, not consumer chat app. Judges should feel they are looking at a tool an engineer would trust with a safety decision, not a toy.

Three words that should describe every screen: **precise, evidentiary, calm.** No cutesy chat bubbles, no cartoon avatars, no marketing gloss. Typography and spacing carry the authority; color is used sparingly and functionally.

### 1.1 Principles
1. **Evidence is a first-class visual citizen.** A claim without a visible source is a bug, not a style choice — every finding on screen sits next to (or one click from) its citation.
2. **Show the reasoning, not just the answer.** The agent investigation timeline is always visible during processing — it is a feature, not a loading spinner.
3. **Calm authority over hype.** Dark, low-saturation surfaces; one warm accent color used sparingly; status colors are semantic, never decorative.
4. **Confidence is quantified, not implied.** Every conclusion carries a visible confidence score and verification badge.
5. **No blue.** See constraint above — enforced as a design system rule, not a preference (§2, §9).

---

## 2. Design Tokens

Adapted from the reference design system, with the entire blue family removed and redistributed to warm/neutral hues so the palette still supports full semantic range (positive / warning / negative / info / highlight) without ever using blue.

### 2.1 Color — Core Surfaces (unchanged spirit, dark editorial base)
```css
:root {
  --bg:          #06060a;   /* page background, near-black */
  --bg-warm:     #0c0a08;   /* warm-black alt surface (hero/report header) */
  --surface:     #111115;   /* card / panel */
  --surface-2:   #19191f;   /* nested panel / table header */
  --surface-3:   #222229;   /* hover / active surface */
  --border:      #28282f;
  --border-hi:   #3a3a44;
  --text:        #eae8e4;
  --text-2:      #a09da6;
  --text-3:      #6b6872;
}
```

### 2.2 Color — Accent & Semantic (BLUE REMOVED — do not reintroduce it)
```css
:root {
  --accent:       #f0c45a;  /* primary accent — warm gold. Replaces "blue = primary" */
  --accent-dim:   #c9a23e;
  --accent-2:     #f0a050;  /* secondary accent — amber/orange, for links & interactive text
                                (replaces conventional blue links) */

  --green:        #7ee8a2;  /* positive / supported / normal */
  --teal:         #70e8d0;  /* informational / neutral-technical
                                (replaces conventional blue "info" — teal, not blue) */
  --purple:       #b88cf0;  /* agent / AI-reasoning accent (Planner, Verification) */
  --orange:       #f0a050;  /* monitor / attention */
  --red:          #f07070;  /* negative / abnormal / rejected */
  --pink:         #f08cb8;  /* highlight / rare emphasis only */
}
```
**Rule:** `--teal` is the system's "informational" color and `--purple` is the "AI/agent" color. Together they cover every job blue conventionally does (links, info badges, focus states, AI branding) without being blue. Never substitute a blue hex value for either.

### 2.3 Typography
```css
--serif: 'Fraunces', Georgia, serif;   /* headings, report titles — editorial authority */
--sans:  'Outfit', system-ui, sans-serif;  /* UI text, body */
--mono:  'JetBrains Mono', monospace;      /* data values, IDs, timestamps, code-like evidence (e.g. "3.7 mm/s", "P-102", audit log) */
```
- Headings (`h1`–`h3`): Fraunces, weight 300–400 for large display, 700 reserved for a single emphasized word (e.g., report title's equipment ID).
- Body/UI: Outfit, 400/500/600.
- **All numeric/technical values (measurements, IDs, confidence scores, timestamps) render in `--mono`** — this is a key trust signal: data looks like data, not like prose.

### 2.4 Spacing & Radius
- 4/8px spacing scale; section padding 80–100px desktop, 40–56px mobile.
- Card radius: 12–14px. Small controls: 8px. Pills/badges: full radius.

### 2.5 Elevation & Texture
- Layered surfaces only (`bg` → `surface` → `surface-2` → `surface-3`), never a hard drop shadow on dark backgrounds — use `inset 0 1px 0 rgba(255,255,255,0.05)` hairline highlights plus a soft ambient shadow.
- Optional 3–4% opacity SVG grain overlay on the app background for material texture (matches reference system, chapter "Make It Premium").

---

## 3. Status & Semantic Color Mapping (the anti-blue table)

This table is the canonical mapping for every place a status/semantic color is needed. **No entry in this system may resolve to blue.**

| Meaning | Color token | Used for |
|---|---|---|
| Supported / Normal / Success | `--green` | Verification badge "Supported", normal equipment status, success toast |
| Informational / Neutral-technical | `--teal` | "Info" badges, links, focus rings, secondary buttons, neutral chips |
| AI / Agent activity | `--purple` | Agent avatars in the timeline, "AI reasoning" label, Planner/Verification Agent accents |
| Attention / Monitor | `--orange` | "Monitor" equipment status, partially-supported verification, warnings |
| Abnormal / Rejected / Error | `--red` | "Abnormal" equipment status, unsupported claims, error toasts, destructive actions |
| Primary brand / call to action | `--accent` (gold) | Primary buttons, active nav, key numbers (confidence score ring), logo mark |
| Rare emphasis | `--pink` | Sparingly — e.g. a single "new" badge; never for status |

Focus rings, hyperlinks, and "selected" states — all conventionally blue in most design systems — use `--teal` (info) or `--accent` (gold, for primary interactive elements) instead.

---

## 4. Information Architecture

```
Session Entry
   │
   ▼
Investigation Workspace (home) ──────► Audit Log (secondary, own route)
   │  ask a question
   ▼
Live Investigation View (agent timeline streaming)
   │  investigation completes
   ▼
Investigation Report (evidence-cited answer)
   │  drill into a citation
   ▼
Source Viewer (document page / data table / P&ID excerpt) — modal/panel, not full navigation
```

---

## 5. Screens

### 5.1 Screen 1 — Session Entry
Minimal, per `PRD.md`/`SRS.md` FR-ACC-1. Dark full-bleed background with grain texture, centered card.

```
┌──────────────────────────────────────────┐
│                                            │
│              V I G I L                    │
│   Sovereign Industrial AI Workbench       │
│                                            │
│   Name        [ ______________ ]          │
│   Department  [ Operations      ▾]        │
│                                            │
│              [ Enter Workbench ]           │
│                                            │
│   ⚬ Local inference only — no data leaves │
│     this network                          │
└──────────────────────────────────────────┘
```
- Card: `--surface` on `--bg`, 1px `--border`, 14px radius.
- Title in Fraunces 700, `--accent` for "KavachAI" wordmark only.
- The sovereignty line is small, `--text-3`, `--mono` — sets trust tone immediately.
- Primary button: `--accent` fill, `--bg` text, hover lifts `translateY(-2px)` + brightens.

### 5.2 Screen 2 — Investigation Workspace (Home)
```
┌────────────────────────────────────────────────────────────┐
│ KavachAI       Priya · HSE                    [Audit Log]   │
├────────────────────────────────────────────────────────────┤
│                                                              │
│        What do you want to investigate?                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Investigate Pump P-102 and determine whether its      │  │
│  │ condition has deteriorated.                    [ ⌁ Investigate ]│
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Suggested investigations                                   │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐     │
│  │ Fire emergency │ │ PPE required  │ │ P-102 health  │     │
│  │ procedure      │ │ Zone A        │ │ trend         │     │
│  └───────────────┘ └───────────────┘ └───────────────┘      │
│                                                              │
│  Knowledge base:  7 documents · 1 dataset · 1 P&ID  loaded  │
└────────────────────────────────────────────────────────────┘
```
- Query input: large, `--surface` field, `--mono` placeholder for the technical feel, `--accent` submit button (icon: a stylized compass/target, not a paper-plane — avoid generic-chatbot iconography).
- Suggested-question chips: `--surface-2`, `--teal` border on hover (never blue).
- Footer status line in `--text-3` confirms corpus size — subtle proof of local grounding.

### 5.3 Screen 3 — Live Investigation View
This is the product's signature screen — the visible "showing the work" moment.

```
┌────────────────────────────────────────────────────────────┐
│ Investigating: "P-102 deterioration?"                       │
├────────────────────────────────────────────────────────────┤
│  ● Planner            Decomposed into 4 sub-tasks     0.4s  │
│  ● Document Agent     Found 4 inspection reports       1.1s │
│  ● Data Agent         Computed vibration trend (+76%)  0.6s │
│  ○ Vision Agent       Reading P&ID for P-102…           ⋯   │
│  ○ Knowledge Agent    Retrieving spec threshold          ⋯  │
│  ○ Verification       Waiting on evidence bundle         ⋯  │
├────────────────────────────────────────────────────────────┤
│  live evidence preview (fills in as agents complete)        │
└────────────────────────────────────────────────────────────┘
```
- Each row: a colored dot (`--purple` = agent working, `--green` = complete, `--text-3` hollow = pending) + agent name in `--mono` + a one-line status + elapsed time in `--mono`, `--text-3`.
- This view streams over Server-Sent Events (see `API_Reference.md`); rows animate in with the reference system's stagger pattern (fade + `translateY(8px)`, 100ms stagger, `cubic-bezier(0.16,1,0.3,1)`).
- No generic spinner — the timeline **is** the loading state (satisfies NFR-USE / demo-trust goals).

### 5.4 Screen 4 — Investigation Report
The "money shot" screen for the presentation.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   P-102 INVESTIGATION                    ⚠ ATTENTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Condition: Potential deterioration detected

  KEY FINDINGS
  ┌────────────────────────────────────────────────────┐
  │ 1. Increasing vibration                              │
  │    Jan 2.1 → Apr 2.8 → Jul 3.7 mm/s   (+76%)         │
  │    ✓ Supported · Inspection Reports, pp. 4, 12, 17   │
  ├────────────────────────────────────────────────────┤
  │ 2. Increasing temperature                            │
  │    68°C → 71°C → 77°C                                 │
  │    ✓ Supported · Operating Data                      │
  ├────────────────────────────────────────────────────┤
  │ 3. Exceeds attention threshold                        │
  │    Current 3.7 mm/s > spec 3.0 mm/s                   │
  │    ✓ Supported · Pump Operating Manual, §4.2          │
  └────────────────────────────────────────────────────┘

  P&ID RELATIONSHIP        T-101 → P-102 → V-204 → R-101

  AI CONCLUSION
  The available evidence indicates that P-102's condition
  has deteriorated over the observed period. Engineering
  inspection is recommended. The evidence does NOT
  establish imminent failure.

  Confidence  ◕ 91          Verification  ✓ Verified

  [ View Evidence ]  [ View P&ID ]  [ Export Report ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- Header status pill: uses the semantic table (§3) — `--orange` background tint for "ATTENTION REQUIRED", `--red` for "ABNORMAL/CRITICAL", `--green` for "NORMAL".
- Each finding card: left edge 3px accent bar colored by its verification status (`--green` supported / `--orange` partial / `--red` unsupported-and-flagged). Values in `--mono`.
- Confidence score: a radial/ring indicator using `--accent` (gold) fill on `--surface-2` track — deliberately **not** a blue progress ring (the most common blue-default UI pattern; explicitly overridden here).
- Verification badge uses `--green` check for "Verified", `--orange` for "Partially Verified", `--red` for "Unverified — do not act without review".
- Citations (e.g., "Inspection Reports, pp. 4, 12, 17") are clickable text in `--teal` (the info/link color — never blue), opening the Source Viewer.

### 5.5 Screen 4b — "Insufficient Evidence" State (must be visually distinct, not an error page)
```
┌────────────────────────────────────────────────────────────┐
│  ⚠  INSUFFICIENT EVIDENCE                                    │
│                                                                │
│  I couldn't find reliable information about this in the      │
│  KavachAI knowledge base for this plant.                      │
│                                                                │
│  This system is designed to avoid answering beyond its        │
│  verified organizational knowledge.                           │
└────────────────────────────────────────────────────────────┘
```
- Card border and icon in `--orange` (attention, not `--red`/error — this is correct, trustworthy behavior, not a failure) — reinforces the "we'd rather say nothing than guess" narrative for judges.

### 5.6 Screen 5 — Source Viewer (drill-down panel)
- Slide-in right panel (not full navigation) showing: original document page render (if PDF), or the exact data rows (if dataset), or the annotated P&ID excerpt (if vision evidence).
- Header shows source metadata in `--mono`: `Fire_Emergency_SOP.pdf · p.4 · rev 2025-03`.
- Highlights the exact passage/row/region referenced by the finding.

### 5.7 Screen 6 — Audit Log (secondary)
Simple reverse-chronological table: timestamp, user, query, agents invoked, verification outcome, confidence. `--mono` timestamps, `--surface-2` header row, no interactive color beyond `--teal` row hover.

---

## 6. Components

| Component | Notes |
|---|---|
| Agent timeline row | See §5.3. Reusable in report view as a collapsed "How this was investigated" accordion. |
| Finding card | Left accent bar = status color; body text `--text`; values `--mono`; citation link `--teal`. |
| Status pill | Rounded-full, tinted background at 12% opacity of the semantic color, full-opacity text — matches reference system's `.tag` pattern (`background: rgba(color,0.12)`), extended to the anti-blue palette in §3. |
| Confidence ring | SVG circular progress, `--accent` stroke on `--surface-2` track, centered mono numeral. |
| Suggested-question chip | `--surface-2` fill, `--border` outline, `--teal` outline on hover/focus (replaces default blue focus ring). |
| Primary button | `--accent` fill / `--bg` text / hover: brighten + `translateY(-2px)` + soft ambient shadow. |
| Secondary button | Transparent fill, `--border-hi` outline, `--text` label, hover: `--surface-2` fill. |
| Destructive action | `--red` outline/text only — reserved, rare. |

---

## 7. Motion

Following the reference system's "premium" motion vocabulary:
- Page/panel entrance: fade + `translateY(20px)` → `0`, 0.6–0.8s, `cubic-bezier(0.16,1,0.3,1)`.
- Agent timeline rows: same easing, 100ms stagger.
- Hover states on all interactive elements: 150–200ms, transform + color only (GPU-cheap: `transform`, `opacity`, never animate `width/height/top/left`).
- No motion is purely decorative — every animation communicates state (agent working → complete, finding appearing, confidence ring filling).

---

## 8. Accessibility
- Minimum contrast: body text `--text` on `--bg`/`--surface` meets WCAG AA; status colors on tinted-pill backgrounds checked individually (gold/orange on dark are naturally high-contrast; verify `--green`/`--teal`/`--purple` similarly).
- All interactive elements have a visible focus state using `--teal` (never `--accent` alone, so focus is distinguishable from "primary action" gold, and never blue).
- Touch targets ≥44px on any responsive/tablet view.
- No information is conveyed by color alone — every status pill and finding-status also carries a text label and/or icon (✓ / ⚠ / ✗), so the design remains legible for color-vision-deficient users even under the restricted, non-blue palette.

---

## 9. Pre-Ship Checklist (run on every screen before demo)
- [ ] No hex value in the `#0000ff`–`#4d79ff` family (or any perceptually blue hue, incl. navy/indigo/sky/cyan-blue) appears anywhere — background, text, border, icon fill, chart series, gradient stop, shadow tint.
- [ ] All "info," "link," and "focus" states use `--teal`, not blue.
- [ ] All "AI/agent" branding uses `--purple`, not blue.
- [ ] Primary actions use `--accent` (gold), not blue.
- [ ] Charts/graphs (if added — e.g., vibration trend line) use `--accent`, `--teal`, `--orange`, or `--purple` for series — never blue.
- [ ] Exported PDF report inherits the same palette (no default blue hyperlink styling from the PDF renderer — override link color to `--teal`/`c9a23e` equivalent print-safe tone).
