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
dismissal under `loom.tours.v1`. Tour steps are configured in `src/app/tours/catalog.ts`.

To add or change a tour step:

1. Add stable `data-tour` attributes to rendered elements; do not target generated MUI class names.
2. Add the step to `GLOBAL_TOUR_STEPS`.
3. Add its title and description to `public/locales/en/translation.json`.
4. Test desktop and mobile layouts. Missing targets are skipped automatically.

Components inside `TourProvider` can offer a replay action through the same completion and dismissal
lifecycle:

```tsx
import { useTour } from "@app/tours/useTour";

const { startTour } = useTour();

<Button onClick={startTour}>Replay introduction</Button>;
```
