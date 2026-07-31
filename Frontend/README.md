# Loom Frontend

As long as the development docker setup is up and running,
changes to any TSX or CSS files are watched and will cause an auto-regeneration of the bundle.

## Important commands

### Adjusting packages

All pnpm commands should be run through corepack to guarantee the right pnpm version used **and**
either have to be run in the Frontend directory.

```shell
cd $(git rev-parse --show-toplevel)/Frontend  # cd Frontend root
pnpm help
```

### Regenerate typing

Can be found at: `src/app/api/generated`, generated from backend python code:
This also runs Lint & autofix at the end

```shell
generate_frontend_api
```

### Lint & autofix

Important: this uses `git ls-files` to find typescript files, this means if you do not stage a
deletion of a file for example, you will run into an error where eslint cannot find a file that you already deleted.
To solve this, stage any renaming / deletions or creations of typescript files -> `git add path/to/file`.

```shell
lint_fix_frontend
```

## Product tours

The tour provider starts the global tour on a visitor's first visit and stores completion or
dismissal together with the acknowledged copy hashes for every step under `loom.tours.v1`. On later
visits, it automatically shows only added steps or steps whose English title, description, or
step-specific button copy has a hash that visitor has not acknowledged. Presentation-only changes
such as selectors, placement, viewport rules, and wait times do not change the hash. Completion and
dismissal both acknowledge the selected hashes that are eligible for the current viewport so the
same update is not offered repeatedly. Viewport-filtered updates remain available on a compatible
device. Partial tours begin with a welcome-back step introducing the changes. The header menu's
**Take a Tour** action always launches the complete tour. Tour steps are configured in
`src/app/tours/catalog.ts`.
The welcome step offers **Skip Tour**. The tour introduces query syntax, runs the `*` search-all
query, and then walks through processing-health indicators, result-card anatomy, document details,
folders, tags, saved queries, bulk and automatic actions, statistics, and chat. Tour scenes
temporarily open the relevant panels or a document preview through context overrides; they do not
change the visitor's persisted sidebar layout, open document tabs, or URL.

To add or change a tour step:

- Add stable `data-tour` attributes to rendered elements; do not target generated MUI class names.
- Add the step to `GLOBAL_TOUR_STEPS` with a unique, stable `id`. Duplicate IDs prevent automatic
  tour versioning. Changing an existing step's English copy automatically offers that step again
  without changing its ID.
- Add its title and description to `public/locales/en/translation.json`.
- Set `preparation: "search-results"` when the target needs loaded result data. Incremental tours
  silently reuse existing results or run the search-all query before showing those steps. Pending
  automatic preparation is cancelled if the visitor leaves search or manually starts a full tour.
- Test desktop and mobile layouts. Missing optional targets are skipped and acknowledged
  automatically. Set `skipIfMissing: false` when a missing target should abort the tour and remain
  unacknowledged for retry after the configuration is repaired.

Components inside `TourProvider` can offer a replay action through the same completion and dismissal
lifecycle:

```tsx
import { useTour } from "@app/tours/useTour";

const { startTour } = useTour();

<Button onClick={startTour}>Replay introduction</Button>;
```
