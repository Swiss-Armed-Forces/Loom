# Frontend debugging

Driving the running frontend with a real browser answers questions unit tests cannot. jsdom has no
layout engine, so a card's real height — which depends on a thumbnail arriving on its own schedule
— is invisible to it, and so is anything about paint, scroll or how the app behaves against a
corpus of real documents.

Playwright is a devDependency of `Frontend/` for exactly this. It is not wired into CI and there
are no checked-in scripts; it is a tool for looking at a running Loom.

## Where the scripts go

**Write them outside the repository** — a scratch directory is the right place. They are not
tests, nothing runs them, and nobody maintains them: left in the tree they rot against the
selectors they hardcode while reading like a suite that passes.

When a script establishes something that should keep holding, port it to a vitest test and throw
the script away. See [Closing the loop](#closing-the-loop) below.

## Launching

Needs Loom running (`up --development`) and the `chromium` that devenv already provides.

A script outside the repository cannot `import ... from "playwright"`: node resolves imports from
the script's own directory, not from the working directory, so it never finds
`Frontend/node_modules`. Reach it explicitly instead.

```javascript
import { createRequire } from "node:module";

// Resolve from Frontend/, not from wherever this script happens to live.
const { chromium } = createRequire(`${process.env.LOOM_FRONTEND}/`)("playwright");

const browser = await chromium.launch({
    // Use the browser devenv installed rather than letting Playwright
    // download a few hundred MB of its own.
    executablePath: process.env.CHROMIUM_PATH ?? "chromium",
});
const page = await browser.newPage({
    // *.loom is served under the self-signed certificate the chart generates.
    ignoreHTTPSErrors: true,
    viewport: { width: 1400, height: 900 },
});
page.on("pageerror", (e) => console.log("PAGE ERROR:", e.message));
```

```bash
cd Frontend
LOOM_FRONTEND=$PWD CHROMIUM_PATH=$(which chromium) node /path/to/scratch/check.mjs
```

Honour `LOOM_URL` in the script rather than hardcoding `https://frontend.loom/`. The demo build
(`pnpm preview:demo`) serves the app with no cluster at all, which is enough for anything about
chrome, layout or navigation — but it answers from sixteen fixtures through a service worker, so
it is no use for the result list, where the whole question is what happens over thousands of rows.

## Getting past the guided tour

**This bites first and looks like everything else being broken.** The tour's overlay swallows
every click, and Playwright refuses to click an element something else is covering. Mark the tour
as seen before the app boots:

```javascript
await page.addInitScript(() => {
    window.localStorage.setItem(
        "loom.tours.v1",
        JSON.stringify({
            schemaVersion: 1,
            introductionOutcome: "dismissed",
            acknowledgedStepHashes: {},
        }),
    );
});
```

An incremental tour whose step hashes do not match may start anyway, so dismiss defensively too —
clicking `.driver-popover-close-btn` through the DOM, not through Playwright, until
`.driver-overlay` is gone.

## Selectors

The app carries data attributes for this; prefer them to class names, which are emotion-generated
and change between builds.

| Selector | What it is |
| -------- | ---------- |
| `[data-search-input]` | The search box. Fill it and press Enter |
| `[data-search-panel]` | The result list's scroll container |
| `[data-index]` | One virtualized row. Its position is `translateY(...)` in `style.transform`, which is what to read rather than trusting document order |
| `.resultCardParent` | The card inside a row |
| `[data-highlighted="true"]` | The highlighted card |
| `[data-testid="virtual-list"]` | The sized spacer whose height is the whole list's reserved room |
| `[data-file-panel]` | The right sidebar's file detail panel |

Wait for `.resultCardParent` to be attached after a search; the rows arrive well after the
response does.

### The customization panel

Opened with `[aria-label="Customizations"]` or `[data-tour="sidebar-customization"]`. It holds
three `.MuiToggleButtonGroup-root` groups with nothing distinguishing them in the DOM, in this
order:

| Index | Group |
| ----- | ----- |
| 0 | Preset |
| 1 | Spacing |
| 2 | Card Fields |

A bare `querySelector(".MuiToggleButtonGroup-root")` silently takes Preset, so always index the
group. Individual element switches are better found by their label text — the list is long and
reorders more readily than it is renamed.

## Profiling

Two techniques worth knowing, because the devtools UI cannot be driven from a script:

- **Where the time goes.** Attach CDP with `page.context().newCDPSession(page)` and use
  `Profiler.setSamplingInterval` / `Profiler.start` / `Profiler.stop`. The default 1000µs interval
  is far too coarse for a 100ms interaction; 100µs gives a usable number of samples. Sum self time
  per function.
- **What re-rendered.** Install a stub `__REACT_DEVTOOLS_GLOBAL_HOOK__` via `addInitScript` before
  any React module loads — React calls `onCommitFiberRoot` after every commit if it finds one.
  Walking the fiber tree per commit gives both how many commits one interaction causes and which
  components ran. More than one commit means a cascade rather than a single update.

**Read shares, not milliseconds.** `frontend.loom` serves a vite dev build: React is in
development mode with StrictMode on, so every component renders twice and absolute timings are
well above what a production build gives. Frame names are unminified, which is the point.

## Closing the loop

A browser script is for finding things out. Once you know what should always be true, the
assertion belongs in `frontend-test`, where CI runs it on every merge request.

Most of it does not need a browser. `DetailedView.layout.test.tsx` is the pattern for anything
layout-shaped: it stubs `getBoundingClientRect` and `offsetHeight` from a row-height model, fires
a `ResizeObserver` by hand, and records every `scrollTo` the virtualizer writes. That is enough
for row placement, overlap, highlight placement and scroll takeover. `getComputedStyle` also
resolves emotion's injected styles under jsdom, so questions about what a variant actually renders
— `FileCardHeader.test.tsx` — are testable too.

What genuinely cannot move is the correspondence between a modelled row height and the height a
real card renders at. That one stays a browser question.
