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
