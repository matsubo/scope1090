# Frontend UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 UX features (loading skeletons, fullscreen modal, collapsible panels, refresh countdown, keyboard shortcuts) to the graphs1090 static HTML dashboard.

**Architecture:** Pure vanilla JS + CSS additions to three existing files. No build step, no dependencies. Each feature is self-contained and ships as its own commit.

**Tech Stack:** Vanilla JS (ES6+), CSS custom properties, localStorage, `keydown` event delegation

---

## File Map

| File | Changes |
|------|---------|
| `html/index.html` | Add modal DOM, shortcuts-help DOM, refresh-bar inside sticky-bar |
| `html/portal.css` | Add skeleton, modal, panel collapse, countdown, kbd styles |
| `html/graphs.js` | Add `applySkeletons`, `openModal`, `closeModal`, `handleModalClick`, `initPanels`, `startCountdown`, `initKeyboard`, `toggleShortcutsHelp`; modify `switchView` |

---

## Task 1: Loading Skeletons

**Files:**
- Modify: `html/portal.css` — add pulse animation
- Modify: `html/graphs.js` — add `applySkeletons()`, call it in `switchView()`

- [ ] **Step 1: Add skeleton CSS to `html/portal.css`**

Append after the last rule (after `.hl { ... }`):

```css
/* Loading skeleton */
@keyframes skeleton-pulse {
    0%, 100% { opacity: 0.35; }
    50%       { opacity: 0.7; }
}

.skeleton {
    background: var(--border);
    animation: skeleton-pulse 1.4s ease-in-out infinite;
    min-height: 60px;
    border-radius: 3px;
}

.skeleton.error {
    animation: none;
    opacity: 0.25;
}
```

- [ ] **Step 2: Add `applySkeletons()` to `html/graphs.js`**

Add this function after `setGraph()` (after line 73, before `function switchView`):

```js
function applySkeletons() {
    document.querySelectorAll('.img-responsive').forEach(img => {
        img.classList.add('skeleton');
        img.classList.remove('error');
        img.onload  = () => img.classList.remove('skeleton');
        img.onerror = () => img.classList.add('error');
    });
}
```

- [ ] **Step 3: Call `applySkeletons()` at the top of `switchView()`**

In `switchView()`, the current first two lines are:
```js
clearTimeout(refreshTimer);
refreshTimer = setTimeout(switchView, refreshInterval);
```

Change to:
```js
clearTimeout(refreshTimer);
refreshTimer = setTimeout(switchView, refreshInterval);
applySkeletons();
```

- [ ] **Step 4: Manual test**

Open `html/index.html` in a browser (e.g. `python3 -m http.server 8080` in the `html/` dir, then visit `http://localhost:8080`).

- Click any timeframe button (e.g. "8 hours")
- Each graph area should briefly flash a gray pulsing rectangle before the image loads (or stays gray with lower opacity if the image 404s)
- No broken-image icons visible

- [ ] **Step 5: Commit**

```bash
git add html/portal.css html/graphs.js
git commit -m "feat: add loading skeleton animation on graph refresh"
```

---

## Task 2: Fullscreen Modal

**Files:**
- Modify: `html/index.html` — add `#modal` DOM before `</body>`
- Modify: `html/portal.css` — add modal styles
- Modify: `html/graphs.js` — add `openModal`, `closeModal`, `handleModalClick`, click-delegation listener

- [ ] **Step 1: Add modal HTML to `html/index.html`**

Insert before the `<script src="graphs.js"></script>` line:

```html
	<div id="modal" style="display:none" onclick="handleModalClick(event)">
		<div class="modal-inner">
			<div class="modal-header">
				<span class="modal-title"></span>
				<button class="modal-close" onclick="closeModal()">✕</button>
			</div>
			<div class="modal-img-wrap">
				<img id="modal-img" src="" alt="">
			</div>
		</div>
	</div>

	<div id="shortcuts-help" style="display:none" onclick="handleShortcutsClick(event)">
		<div class="shortcuts-inner">
			<div class="shortcuts-header">
				<span>Keyboard Shortcuts</span>
				<button onclick="toggleShortcutsHelp()">✕</button>
			</div>
			<table class="shortcuts-table">
				<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>Previous / next timeframe</td></tr>
				<tr><td><kbd>f</kbd></td><td>Open first graph fullscreen</td></tr>
				<tr><td><kbd>c</kbd></td><td>Toggle crosshair</td></tr>
				<tr><td><kbd>?</kbd></td><td>Show / hide this help</td></tr>
				<tr><td><kbd>Esc</kbd></td><td>Close modal or help</td></tr>
			</table>
		</div>
	</div>
```

- [ ] **Step 2: Add modal + shortcuts CSS to `html/portal.css`**

Append after the skeleton rules:

```css
/* Fullscreen modal */
#modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.88);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-inner {
    max-width: 95vw;
    max-height: 95vh;
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--panel-head-bg);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    gap: 12px;
}

.modal-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.1rem;
    cursor: pointer;
    color: var(--text-muted);
    padding: 0 4px;
    line-height: 1;
    flex-shrink: 0;
}

.modal-close:hover { color: var(--text); }

.modal-img-wrap {
    overflow: auto;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
}

.modal-img-wrap img {
    max-width: 100%;
    max-height: calc(95vh - 52px);
    object-fit: contain;
    display: block;
}

/* Keyboard shortcuts overlay */
#shortcuts-help {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 1001;
    display: flex;
    align-items: center;
    justify-content: center;
}

.shortcuts-inner {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 24px;
    min-width: 280px;
}

.shortcuts-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text);
}

.shortcuts-header button {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-muted);
    font-size: 1rem;
    padding: 0;
}

.shortcuts-header button:hover { color: var(--text); }

.shortcuts-table {
    border-collapse: collapse;
    width: 100%;
}

.shortcuts-table td {
    padding: 5px 8px;
    color: var(--text);
    font-size: 0.85rem;
    vertical-align: middle;
}

.shortcuts-table td:first-child {
    white-space: nowrap;
    color: var(--text-muted);
}

kbd {
    background: var(--btn-bg);
    border: 1px solid var(--btn-border);
    border-radius: 3px;
    padding: 1px 5px;
    font-size: 0.75rem;
    font-family: monospace;
    color: var(--text);
}
```

- [ ] **Step 3: Add modal JS functions to `html/graphs.js`**

Append after `toggleCrosshair()` (after line 209):

```js
function openModal(img) {
    const modal    = document.getElementById('modal');
    const modalImg = document.getElementById('modal-img');
    modal.querySelector('.modal-title').textContent = img.alt || '';
    modalImg.src = img.src;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
    document.body.style.overflow = '';
}

function handleModalClick(e) {
    if (e.target === document.getElementById('modal')) closeModal();
}

function toggleShortcutsHelp() {
    const el = document.getElementById('shortcuts-help');
    el.style.display = el.style.display === 'none' ? 'flex' : 'none';
}

function handleShortcutsClick(e) {
    if (e.target === document.getElementById('shortcuts-help')) toggleShortcutsHelp();
}

// Open modal on graph image click (event delegation — no HTML changes needed)
document.addEventListener('click', function(e) {
    const img = e.target.closest('.img-responsive');
    if (!img || !img.src || img.classList.contains('skeleton')) return;
    e.preventDefault();
    openModal(img);
});
```

- [ ] **Step 4: Manual test**

With local server running (`python3 -m http.server 8080` in `html/`):

- Click any graph image → modal opens with dark overlay, graph title in header, image displayed
- Click the ✕ button → modal closes
- Click the dark backdrop area (outside the white inner box) → modal closes
- Scroll the page with modal open → page does not scroll (body overflow hidden)
- Resize to mobile width → image scales to fit inside modal

- [ ] **Step 5: Commit**

```bash
git add html/index.html html/portal.css html/graphs.js
git commit -m "feat: add fullscreen modal and keyboard shortcuts help overlay"
```

---

## Task 3: Collapsible Panels

**Files:**
- Modify: `html/portal.css` — panel heading cursor + chevron pseudo-element
- Modify: `html/graphs.js` — add `initPanels()`, call at bottom of file

- [ ] **Step 1: Add collapsible panel CSS to `html/portal.css`**

Append after the existing `.panel-heading { ... }` rule (do not replace it — these declarations layer on top via cascade):

```css
/* Collapsible panels */
.panel-heading {
    cursor: pointer;
    user-select: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-heading::after {
    content: '▾';
    font-size: 0.85rem;
    color: var(--text-muted);
    flex-shrink: 0;
}

.panel-heading.collapsed::after {
    content: '▸';
}
```

- [ ] **Step 2: Add `initPanels()` to `html/graphs.js`**

Append after `handleShortcutsClick()`:

```js
function initPanels() {
    const saved = JSON.parse(localStorage.getItem('panels') || '{}');
    document.querySelectorAll('.panel').forEach(panel => {
        const id = panel.id;
        if (!id) return;
        const heading = panel.querySelector('.panel-heading');
        const body    = panel.querySelector('.panel-body');
        if (!heading || !body) return;

        // Restore saved state (default: expanded)
        if (saved[id] === false) {
            body.style.display = 'none';
            heading.classList.add('collapsed');
        }

        heading.addEventListener('click', () => {
            const isNowCollapsed = body.style.display !== 'none';
            body.style.display = isNowCollapsed ? 'none' : '';
            heading.classList.toggle('collapsed', isNowCollapsed);
            const state = JSON.parse(localStorage.getItem('panels') || '{}');
            state[id] = !isNowCollapsed;
            localStorage.setItem('panels', JSON.stringify(state));
        });
    });
}

initPanels();
```

- [ ] **Step 3: Manual test**

- Click the "ADS-B 1090 Graphs" panel heading → body collapses, chevron changes to ▸
- Click again → body expands, chevron changes to ▾
- Reload the page → collapsed state is preserved
- Open DevTools → Application → Local Storage: verify `panels` key contains `{"panel_1090": false}` when collapsed
- Panels that are `display:none` server-side (airspy, 978) are unaffected (their heading click does nothing harmful)

- [ ] **Step 4: Commit**

```bash
git add html/portal.css html/graphs.js
git commit -m "feat: add collapsible panels with localStorage persistence"
```

---

## Task 4: Refresh Countdown + Manual Refresh

**Files:**
- Modify: `html/index.html` — add refresh-bar inside sticky-bar
- Modify: `html/portal.css` — add refresh-bar styles
- Modify: `html/graphs.js` — add `countdownInterval`, `startCountdown()`, update `switchView()`

- [ ] **Step 1: Add refresh bar HTML to `html/index.html`**

Inside `.sticky-bar`, after the closing `</div>` of `.btn-group`:

```html
            <div class="refresh-bar">
                <button class="btn btn-refresh" onclick="switchView()" title="Refresh now">↺</button>
                <span id="refresh-countdown"></span>
            </div>
```

The `.sticky-bar` section should look like:

```html
        <div class="sticky-bar">
            <div class="btn-group" role="group">
                <button ...>2 hours</button>
                ...
                <button ...>Crosshair</button>
            </div>
            <div class="refresh-bar">
                <button class="btn btn-refresh" onclick="switchView()" title="Refresh now">↺</button>
                <span id="refresh-countdown"></span>
            </div>
        </div>
```

Note: also remove the duplicate `sticky-bar` class from the inner `.btn-group` div (it currently reads `class="btn-group sticky-bar"`; change to just `class="btn-group"`).

- [ ] **Step 2: Add refresh-bar CSS to `html/portal.css`**

The outer `.sticky-bar` currently uses `text-align: center`. Change it to flex to allow the refresh bar to sit below the buttons. Replace the existing `.sticky-bar` rule:

```css
.sticky-bar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--bg);
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
}
```

Append the new refresh-bar rules:

```css
/* Refresh countdown bar */
.refresh-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: var(--text-muted);
    padding-bottom: 2px;
}

.btn-refresh {
    font-size: 0.9rem;
    padding: 1px 6px;
    line-height: 1.4;
}

#refresh-countdown {
    min-width: 90px;
}
```

- [ ] **Step 3: Add `countdownInterval` and `startCountdown()` to `html/graphs.js`**

Add the module-level variable near `refreshTimer` (around line 149):

```js
let countdownInterval = null;
```

Append `startCountdown()` after `initPanels()`:

```js
function startCountdown(ms) {
    clearInterval(countdownInterval);
    const el = document.getElementById('refresh-countdown');
    if (!el) return;
    let remaining = Math.round(ms / 1000);
    el.textContent = `next in ${remaining}s`;
    countdownInterval = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
            el.textContent = 'refreshing\u2026';
            clearInterval(countdownInterval);
        } else {
            el.textContent = `next in ${remaining}s`;
        }
    }, 1000);
}
```

- [ ] **Step 4: Update `switchView()` to clear countdown and start it after refresh**

At the top of `switchView()`, add `clearInterval(countdownInterval)` right after `clearTimeout(refreshTimer)`:

```js
function switchView(newTimeFrame) {
    clearTimeout(refreshTimer);
    clearInterval(countdownInterval);
    applySkeletons();
    refreshTimer = setTimeout(switchView, refreshInterval);
    ...
```

At the very end of `switchView()`, before the closing `}`, add:

```js
    startCountdown(refreshInterval);
}
```

- [ ] **Step 5: Manual test**

- Load the page → countdown appears: "next in 60s", counting down
- Click ↺ button → graphs reload immediately, countdown resets to 60s
- Click a timeframe button → countdown resets
- Hide the browser tab → countdown stops (existing visibility handler pauses timers)
- Restore tab → countdown resumes from full interval

- [ ] **Step 6: Commit**

```bash
git add html/index.html html/portal.css html/graphs.js
git commit -m "feat: add refresh countdown and manual refresh button"
```

---

## Task 5: Keyboard Shortcuts

**Files:**
- Modify: `html/graphs.js` — add `TIME_FRAMES` constant, `initKeyboard()`

(All HTML and CSS for the shortcuts overlay was already added in Task 2.)

- [ ] **Step 1: Add `TIME_FRAMES` constant and `initKeyboard()` to `html/graphs.js`**

Add the constant near the top of the file, after the `//*** DO NOT EDIT BELOW ***//` comment (around line 67):

```js
const TIME_FRAMES = ['2h','8h','24h','48h','7d','14d','30d','90d','180d','365d','730d','1095d','1825d','3650d'];
```

Append `initKeyboard()` after `startCountdown()`:

```js
function initKeyboard() {
    document.addEventListener('keydown', function(e) {
        // Don't fire shortcuts when typing in form fields
        if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
        if (e.ctrlKey || e.metaKey) return;

        switch (e.key) {
            case 'ArrowLeft': {
                const idx  = TIME_FRAMES.indexOf(timeFrame);
                const prev = (idx - 1 + TIME_FRAMES.length) % TIME_FRAMES.length;
                switchView(TIME_FRAMES[prev]);
                break;
            }
            case 'ArrowRight': {
                const idx  = TIME_FRAMES.indexOf(timeFrame);
                const next = (idx + 1) % TIME_FRAMES.length;
                switchView(TIME_FRAMES[next]);
                break;
            }
            case 'f':
            case 'F': {
                const modal = document.getElementById('modal');
                if (modal.style.display !== 'none') { closeModal(); break; }
                const firstImg = document.querySelector('.img-responsive:not(.skeleton)');
                if (firstImg) openModal(firstImg);
                break;
            }
            case 'c':
            case 'C':
                toggleCrosshair();
                break;
            case '?':
                toggleShortcutsHelp();
                break;
            case 'Escape':
                if (document.getElementById('modal').style.display !== 'none') {
                    closeModal();
                } else if (document.getElementById('shortcuts-help').style.display !== 'none') {
                    toggleShortcutsHelp();
                }
                break;
        }
    });
}

initKeyboard();
```

- [ ] **Step 2: Manual test**

- Press `→` → active timeframe advances (e.g. 2h → 8h → 24h…)
- Press `←` → active timeframe goes back; pressing `←` at 2h wraps to 10 years
- Press `?` → shortcuts overlay appears; press `?` again or `Esc` → closes
- Press `c` → crosshair toggles
- Press `f` → first loaded graph opens in modal; press `Esc` or `f` → closes
- Click inside an `<input>` field → shortcuts do not fire

- [ ] **Step 3: Commit**

```bash
git add html/graphs.js
git commit -m "feat: add keyboard shortcuts (arrows, f, c, ?, Esc)"
```

---

## Final Verification Checklist

Open `html/index.html` via `python3 -m http.server 8080` in the `html/` directory and verify:

- [ ] Skeleton pulse appears on every timeframe switch
- [ ] Broken-image state shows faded skeleton (no red ✗ icon)
- [ ] Clicking a loaded graph opens the modal with correct title
- [ ] ✕ button, backdrop click, and `Esc` all close the modal
- [ ] Body scroll is locked while modal is open
- [ ] `?` shows shortcuts table; `Esc` and backdrop click close it
- [ ] Arrow keys cycle through all 14 timeframes including wrap-around
- [ ] `f` opens first non-skeleton graph in modal
- [ ] `c` toggles the crosshair overlay
- [ ] Panel headings are clickable; body collapses/expands with chevron change
- [ ] Panel state survives page reload (check localStorage `panels` key)
- [ ] Countdown counts down from 60; ↺ resets it and triggers immediate refresh
- [ ] No `console.error` on load or any interaction
- [ ] Mobile (DevTools ≤ 600px): modal image fits viewport; all buttons are tappable
