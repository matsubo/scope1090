# Frontend Improvements Design

**Date:** 2026-04-03  
**Scope:** graphs1090 fork (matsubo/graphs1090) — frontend only  
**Status:** Approved

---

## Goals

Add 5 UX improvements to the graphs1090 web frontend while keeping the existing architecture intact (static PNGs served from `/run/graphs1090/`). No new backend dependencies. No new npm build step.

---

## Features

### 1. Loading Skeletons

**What:** Animated pulse placeholder shown on each graph image while it loads.

**How:**
- `switchView()` adds `.skeleton` class to every `<img>` before setting `src`
- `img.onload` removes `.skeleton`
- `img.onerror` keeps `.skeleton` with reduced opacity (graph not yet generated)
- CSS: `@keyframes skeleton-pulse` fades the background between two grays

**Acceptance criteria:**
- Skeleton appears immediately when timeframe changes
- Skeleton disappears once image fully loads
- No flash of broken-image icon

---

### 2. Keyboard Shortcuts

**What:** Keyboard navigation for power users.

**Shortcuts:**

| Key | Action |
|-----|--------|
| `←` | Previous timeframe (2h → wrap to 3650d) |
| `→` | Next timeframe (up to 3650d → wrap to 2h) |
| `f` | Open fullscreen modal for last-clicked graph |
| `c` | Toggle crosshair |
| `?` | Show/hide shortcut help overlay |
| `Escape` | Close modal or help overlay |

**How:**
- Single `keydown` listener on `document`
- Guard: skip if `event.target` is `INPUT`, `TEXTAREA`, `SELECT`, or `event.ctrlKey`/`event.metaKey` is set
- Timeframe list stored as ordered array; current index tracked alongside `timeFrame` variable
- `?` overlay: fixed-position semi-transparent panel listing all shortcuts

**Acceptance criteria:**
- Arrows cycle through all 14 timeframes correctly, including wrap-around
- Shortcuts do not fire when user is typing in an input
- Escape closes any open overlay

---

### 3. Fullscreen Modal (Simple)

**What:** Click any graph image → opens a lightbox modal showing the full-resolution PNG.

**Layout:**
```
#modal  (position: fixed; inset: 0; background: rgba(0,0,0,0.88); z-index: 1000)
  .modal-inner  (max-width: 95vw; max-height: 95vh; display: flex; flex-direction: column)
    .modal-header
      span.modal-title   (graph name from img alt text)
      button.modal-close (✕)
    .modal-img-wrap
      img  (max-width: 100%; max-height: calc(95vh - 48px); object-fit: contain)
```

**How:**
- Each `<a>` wrapping a graph gets `onclick="openModal(event, id)"` replacing the default href navigation
- `openModal` sets `img.src` to the full-size PNG URL, sets `modal-title`, shows `#modal`, adds `overflow: hidden` to `<body>`
- Close triggers: ✕ button, click on `#modal` backdrop (not `.modal-inner`), Escape key
- `closeModal` removes `overflow: hidden`

**Acceptance criteria:**
- Clicking any graph opens modal with correct image
- Clicking the dark backdrop or pressing Escape closes it
- Body does not scroll while modal is open
- Works on mobile (image scales to fit viewport)

---

### 4. Collapsible Panels

**What:** Each panel section (ADS-B 1090, Airspy, UAT 978, System) can be collapsed by clicking its header.

**How:**
- `initPanels()` called on page load
- Adds `cursor: pointer` and a chevron (`▾` when open, `▸` when collapsed) to each `.panel-heading`
- Click handler on `.panel-heading` toggles `.panel-body` `display` between `block` and `none`, flips chevron
- State persisted in `localStorage` as `panels` key: `{ "panel_1090": true, "panel_system": false, ... }` (true = expanded)
- On load: reads localStorage, applies saved state before first render to avoid flicker

**Acceptance criteria:**
- All panels start expanded by default (first visit)
- Collapse/expand animates smoothly (CSS `max-height` transition)
- State survives page reload
- Panels that are hidden server-side (airspy, 978) are unaffected

---

### 5. Refresh Countdown + Manual Refresh

**What:** Shows time until next auto-refresh. Manual refresh button for immediate update.

**Layout addition to sticky bar:**
```
[2h] [8h] ... [Crosshair]    ↺  next in 58s
```

**How:**
- `startCountdown(ms)` called at end of `switchView()` — takes `refreshInterval` as input
- Uses `setInterval` (1s tick) to decrement displayed seconds
- Clears interval at start of next `switchView()` call (already clears `refreshTimer` there)
- Manual refresh button (`↺`) calls `switchView()` immediately
- Countdown display: `<span id="refresh-countdown">` in sticky bar, right-aligned
- Shows "refreshing…" briefly while images are loading (skeleton active), then resets

**Acceptance criteria:**
- Countdown counts down correctly from `refreshInterval / 1000` to 0
- Manual refresh button triggers immediate reload of all graphs
- Countdown resets to full interval after each refresh (manual or auto)
- No countdown interval leak (cleared before each new `switchView`)

---

## File Changes

### `html/graphs.js`

New functions added (all below the existing `//*** DO NOT EDIT BELOW ***//` section):

| Function | Lines (est.) | Purpose |
|----------|-------------|---------|
| `applySkeletons()` | ~15 | Apply/remove skeleton class on all graph images |
| `initKeyboard()` | ~35 | Keyboard shortcut listener |
| `openModal(event, id)` | ~20 | Open fullscreen modal |
| `closeModal()` | ~10 | Close modal, restore scroll |
| `initPanels()` | ~30 | Collapsible panel setup + localStorage restore |
| `startCountdown(ms)` | ~20 | Countdown timer + manual refresh support |

Modified:
- `switchView()`: call `applySkeletons()` at start, `startCountdown()` at end, clear `countdownInterval` at top (separate from `refreshTimer`)
- `toggleCrosshair()`: unchanged (already vanilla)

**Estimated final size:** ~370 lines (within 400-line guideline)

### `html/portal.css`

New rules:

- `.skeleton` — pulse animation on graph image background
- `#modal`, `.modal-inner`, `.modal-header`, `.modal-title`, `.modal-close`, `.modal-img-wrap img` — lightbox
- `.panel-heading` — `cursor: pointer`, chevron via `::after` pseudo-element
- `.panel-body` — `max-height` + `overflow: hidden` transition for collapse animation
- `#refresh-countdown` — right-aligned small text in sticky bar
- `.btn-refresh` — manual refresh button style
- `#shortcuts-help` — fixed overlay for keyboard shortcut list

### `html/index.html`

New elements:

- `<div id="modal">` — lightbox, inserted before closing `</body>`
- `<span id="refresh-countdown">` and `<button class="btn-refresh">` — inside `.sticky-bar`
- `<div id="shortcuts-help">` — keyboard help overlay
- `initPanels()`, `initKeyboard()`, `startCountdown()` called via `DOMContentLoaded` or inline at bottom of `<body>`

---

## Out of Scope

- Interactive charts (Chart.js / uPlot) — separate project
- Real-time WebSocket/SSE — separate project
- Backend shell script refactor — Phase 2
- Drag-and-drop panel reordering

---

## Testing

Manual checklist (no automated test framework for frontend):

- [ ] Each skeleton appears on timeframe switch, disappears on load
- [ ] Arrow keys cycle through all 14 timeframes
- [ ] `?` shows shortcut list, Escape closes it
- [ ] Clicking graph opens modal, Escape / backdrop click closes it
- [ ] Body scroll locked while modal open
- [ ] Panel collapse/expand works, survives reload
- [ ] Countdown counts down, manual ↺ triggers immediate refresh
- [ ] No console errors on load or interaction
- [ ] Mobile: modal image fits viewport, buttons are tappable
