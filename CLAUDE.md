# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Loom** is an open-source document search engine that automates indexing of data sources, performs OCR,
extracts content and metadata, and offers powerful search capabilities with RAG chatbot functionality.
It's designed for ephemeral, secure, task-specific deployments - not as a long-running production service.

Key architectural principles:

- No upgrade path guarantees (deploy fresh, analyze, shut down)
- No user management (all users fully trusted)
- Not suitable for public exposure (trusted environment only)
- Modular, extensible toolkit approach

## Architecture

Loom uses a microservices architecture running on Kubernetes (via minikube for single-node deployments):

### Backend Services (Python)

The backend is organized into four Poetry-managed packages in `backend/`:

1. **common** - Shared infrastructure used by all other packages:
    - Celery app configuration and task infrastructure
    - Repository patterns (Elasticsearch via `es_repository.py`)
    - Services: file storage, encryption, queuing, IMAP
    - Models and domain objects
    - Message queue integration (RabbitMQ via `pubsub_service.py`)

2. **api** - FastAPI REST API (`backend/api/api/`):
    - Entry point: `main.py` and `api.py`
    - Routes in `routers/` directory
    - OpenAPI schema generation for frontend TypeScript types
    - Prometheus metrics integration

3. **worker** - Celery worker for file processing (`backend/worker/worker/`):
    - `index_file/` - File content extraction and indexing pipeline
    - `ai/` - AI-powered summarization, RAG, and translation
    - `create_archive/` - Archive generation tasks
    - `periodic/` - Scheduled background tasks
    - Entry point: `main.py` with Celery tasks in `tasks.py`

4. **crawler** - Watches S3 buckets and schedules file processing:
    - Monitors uploaded files via polling and triggers worker tasks

### Task Queue Architecture

Loom uses **Celery** with **RabbitMQ** as the message broker. Tasks flow through a dead-letter chain:

- Regular queues for task execution
- Graveyard queue for tasks that exceeded the regular delivery limit
- Dead queue for tasks that exceeded the graveyard delivery limit
- Abyss queue for unprocessable tasks (no worker consumes; messages expire via TTL)
- Delivery limits are configurable via `settings.py`; queue wiring in `common/celery_app.py`

### Frontend (TypeScript/React)

Located in `Frontend/`:

- Built with Vite + React + TypeScript
- API types auto-generated from backend OpenAPI schema
- Uses pnpm for package management (via corepack)

### Data Storage

- **Elasticsearch** - Full-text search and document indexing
- **Redis** - Caching layer
- **SeaweedFS** - S3-compatible object storage for uploaded files

### External Services

- **Apache Tika** - Content extraction engine
- **Gotenberg** - Document rendering to PDF
- **Ollama** - AI inference server for LLM features
- **Traefik** - Reverse proxy and ingress controller

All services accessible via `*.loom` domains (configured in /etc/hosts by `up.sh`).

## Development Environment

Loom uses **devenv** (Nix-based) for reproducible development environments. When you `cd` into the repo,
direnv automatically loads the environment.

### Common Commands

All commands below are provided by devenv scripts (run `devenv-help` to see full list):

**Application lifecycle:**

- `up` - Start Loom (wraps `./up.sh`)
- `down` - Stop Loom
- `build` - Build all Docker images

**Backend testing:**

- `backend-test` - Run all backend tests with pytest and coverage (always runs from `backend/` directory)
- `backend-test api/tests/test_foo.py` - Run specific test file (paths are relative to `backend/`)
- `backend-test worker/tests/test_bar.py::test_function` - Run specific test function
- Scope tests to relevant packages/files when possible — e.g. `backend-test api/` to run only API tests

**Frontend:**

- `frontend-test` - Run frontend tests
- `frontend-build` - Build frontend bundle
- `generate-frontend-api` - Regenerate TypeScript API types from backend OpenAPI schema

**Integration tests:**

- `run-integrationtest` - Run full integration test suite

**Data management:**

- `wipe-data` - Clear all indexed data from Loom

**Kubernetes/Docker:**

- `kubernetes-pause` - Pause cluster (saves resources)
- `kubernetes-stop` - Stop cluster
- `kubernetes-delete` - Delete cluster entirely
- `kubernetes-fetch-all-pod-logs` - Dump all pod logs to `logs/` directory
- `docker-minikube` - Docker CLI wrapper to communicate with minikube's Docker daemon

**Appliance image:**

- `build-appliance-image` - Build (and optionally flash) a NixOS appliance USB installer.
  `--platform` picks the box: `spark` (DGX Spark, aarch64), `evo-x2` (GMKtec EVO-X2, x86_64) or
  `nuc12` (Intel NUC 12 Pro, x86_64). The build host must match the platform's architecture unless
  `--allow-cross` is given. See `Documentation/appliance.md`
- `build-appliance-image --no-gpu` - Build CPU-only for a platform that offloads to a GPU (today
  only `evo-x2`, which runs Ollama on its Radeon 8060S via ROCm). There is no `--gpu`: the GPU is
  declared per platform in `nixos/platforms/<id>.nix`. Use this when a box turns out not to
  enumerate its own GPU, which otherwise stops Loom from starting at all. Note it also drops the
  AI services, since those follow the GPU
- `build-appliance-image --interface NAME` - Pin the appliance NIC by the name the box reports
  (`enp2s0`, not `eth0`). Only needed when no platform matches the hardware; without it a wired
  port is claimed automatically
- `build-appliance-image --vm-serial` - Add a getty on ttyS0 to the installer and to the box it
  installs, so a VM can be driven from a terminal that copies and pastes. For
  `appliance-vm installer --serial`; refused alongside `--flash`, because the result is one unit
  different from a real stick
- `build-appliance-image --wifi` - Additionally run a bridged WiFi access point on the appliance.
  Radios are disabled in every other image. Related flags: `--wifi-ssid`, `--wifi-psk`,
  `--wifi-country`, `--wifi-interface`. Changes the appliance threat model - see
  `Documentation/appliance.md`
- `appliance-test` - Run the NixOS appliance tests (`nixos/tests/`). Takes any of `hardware`,
  `appliance`, `install`, `wifi`, `mouse`, `usb-ingest`, `interface-fallback`; with no argument it
  runs all seven, cheapest first. Defaults to the platform matching the host architecture — the VM tests boot
  a real kernel, so they cannot be cross-built. `--gc` collects garbage afterwards and
  `--min-free GB` sets how much space nix should free mid-build; see the disk budget section in
  `nixos/README.md`
- `appliance-test hardware --platform all` - The one test that boots nothing: it asserts what
  `nixos-hardware` gives each platform and that the Loom overrides still take the desktop userspace
  back off. Needs no KVM and is not bound to the host architecture, so `--platform all` checks all
  three from one machine in seconds. Run it after every renovate bump of the `nixos-hardware` pin.
  `all` is refused for any selection that includes a VM test
- `appliance-test --no-kvm` - Build the VM tests without the `kvm` system feature, so qemu falls
  back to software emulation — correct, and five to ten times slower. With neither this nor
  `--kvm` (which fails rather than taking the slow path) the script probes `/dev/kvm` and says
  which way it went. This is what lets the tests run on a CI runner with no nested virtualisation
- `appliance-vm box` - Boot the appliance in a VM for manual testing. Fast (a minute, no tag, no
  image build) and shows everything above the disk: the console session, the branding, the units,
  the banner. Not the bootloader, the LUKS root or the installer — nixpkgs' qemu-vm module
  overrides those away. Opens a window and exposes a serial socket
- `appliance-vm installer` - The real stick image, virtually flashed onto a file and booted under
  UEFI against emulated NVMe. Runs the actual installer onto an actual pool, reboots into what it
  installed, and persists across runs. Needs a tag, since the image embeds a tagged checkout.
  `--serial` adds a getty on ttyS0 so the VM can be driven from a terminal that copies and pastes —
  one unit more than a real stick carries, so it refuses to be flashed. Related flags: `--disks`,
  `--disk-size`, `--usb DIR`, `--memory`, `--cores`, `--no-gui`, `--force`
- `appliance-vm attach` - Connect to a running VM's serial port. Lands in the same tmux session
  tty1 is showing, as the only client
- `appliance-vm reset` - Delete a platform's VM state (`.appliance-vm/<platform>/`): the disks, the
  flashed stick and the UEFI variables. Gigabytes
- `appliance-check` - The appliance checks that boot nothing, in about a minute: `appliance-pytest`
  then `appliance-eval`, both of them below. Runs both even when the first fails. Needs neither KVM
  nor a matching architecture, which is why this is the appliance job that runs on every CI pipeline
  while the VM tests are gated on what the MR touched
- `appliance-pytest` - The appliance's own pytest suites: `nixos/installer/tests`,
  `nixos/ready/tests`, `nixos/usb-ingest/tests` and `nixos/console-mouse/tests`. Each also runs in its package's
  `checkPhase`, so a mistake fails an image build too; running them here needs nothing built.
  Extra arguments go to pytest
- `appliance-eval` - Instantiates the stick image for all three platforms and the tests for this
  one, building nothing. Catches a module that no longer evaluates, a renamed option, a failed
  assertion and a typo in a test file. `--platform` (repeatable), `--verbose`
- `loom-platform-info` - Report this box's hardware — wired ports and their drivers, radios and
  whether they do AP mode, GPU with the firmware VRAM carve-out beside the GTT pool, firmware
  version — and, on an appliance, how that compares with what `nixos/platforms/<id>.nix` declared.
  Plain bash with no Nix dependency (`nixos/scripts/platform_info.sh`), so it also runs on a box
  that is not running Loom yet. This is how the guessed values in a platform file get checked
  against real hardware. `--json`, `--output`

**Utilities:**

- `poetry-lock` - Regenerate all Poetry lockfiles (run after adding dependencies to `common`)
- `generate-openapi-schema` - Print OpenAPI schema JSON
- `cicd/check_chart_hostnames.sh` - Assert that `hostnames.ingress` in `charts/values.yaml` is
  exactly the set of hosts the chart's Ingress rules render. Runs as a git hook on any change under
  `charts/`, needs no cluster (`helm template` is client-side). **Adding a service with an Ingress
  means adding its name to `hostnames.ingress`** - that list is what the pre-install Job puts in the
  TLS certificate's `subjectAltName`, one entry per host, and a wildcard cannot stand in for it
  (`*.loom` has one dot, and OpenSSL will not expand a wildcard under a single-label parent). A host
  served by entrypoint rather than by an Ingress rule goes in `hostnames.extra` instead. See the
  `## Hostnames and the self-signed certificate` section in `Documentation/installation.md`

**AI developer tools (`aitools` subcommands):**

- `aitools mr-review [<MR URL or IID>] [--fix]` - Run a multi-agent AI review of an MR and
  post findings as inline GitLab comments; omit the MR argument to auto-detect the MR for
  the current branch; pass `--fix` to auto-apply findings instead of posting them as comments
- `aitools mr-watch [<MR URL or IID>]` - Watch an MR's pipeline and auto-fix CI failures
- `aitools mr-fix [<MR URL or IID>]` - Address unresolved MR review comments using Claude
  in agentic mode; omit the argument to fix the MR for the current branch
- `aitools mr-create` / `mr-describe` / `mr-update` - MR lifecycle helpers
- `aitools job-diagnose <job-id>` - Diagnose a specific CI job failure
- All `aitools` subcommands operate on the branch of the *current* working tree, checking it out
  in place - run them from your worktree, never from the user's primary checkout

## Development Workflow

### Making Code Changes

**Backend (Python):**

- Code is organized by domain in each package's subdirectory
- All Python uses **Poetry** for dependency management
- When adding dependencies to `common`, run `poetry add <package>` in `backend/common/`, then `poetry-lock` to update all dependent packages
- Tests use pytest with fixtures; configuration in `pytest.ini`
- Type hints enforced via mypy
- Code style: black (formatter), isort (import sorting), autoflake (unused imports)
- Pre-commit hooks auto-format on commit

**Frontend (TypeScript):**

- Use `cd Frontend && pnpm <command>` or run via corepack
- API types regenerated with `generate-frontend-api` - don't manually edit `src/app/api/generated/`
- ESLint requires staged files (uses `git ls-files`), so stage deletions/renames before committing
- Changes auto-reload when `up --development` is running

### Testing

**When to write tests:**

- Before adding a test, ask yourself: will this test actually test critical functionality, and will
  it add real value? Since we have types, tests that merely verify type constraints or trivially
  re-test what types already enforce are not valuable. Focus on behaviour, edge cases, and logic
  that types cannot capture.
- All new backend features require unit tests
- Integration tests for user-facing workflows

**Running tests:**

- Backend unit tests: `backend-test` (runs all tests in `backend/*/tests/`)
- Frontend unit tests: `frontend-test`
- Integration tests: `run-integrationtest` — simulates full workflows against a running Loom instance
- Tests create temp artifacts in `.pytest_tmp` (not `/tmp`) to avoid RAM usage
- CI/CD pipeline runs the full test suite and linting via git-hooks

**Integration test design — class vs. no class:**

The `wipe_data` fixture in `conftest.py` is `scope="class"` and `autouse=True`. It purges all
queues, terminates running Celery tasks, and waits for the worker to be idle before the test runs.
The scope controls how often that cleanup happens:

- **No class (module-level functions):** `wipe_data` runs before *every* test function. Use this
  when each test needs a clean slate — e.g. it uploads files, dispatches tasks, or calls anything
  that leaves queues non-empty or state dirty for subsequent tests.
- **Class:** `wipe_data` runs once before the first test in the class, then the class shares that
  state. Use a class only when tests genuinely share a common dataset and none of them contaminate
  state for the others (e.g. a read-only search test suite that loads a fixed corpus once).

**Key rule:** if a test uploads a file, triggers a Celery pipeline, or leaves RabbitMQ queues
non-empty, it must not share a class with tests that depend on an idle worker — particularly any
test that calls a task which internally calls `wait_for_idle`. When in doubt, use module-level
functions (no class).

**When to use `disable_periodic_tasks`:**

Apply `pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")` (or the fixture directly)
when periodic beat tasks would interfere with what the test is asserting. Specifically:

- The test calls a task that uses `wait_for_idle` — beat tasks continuously add messages to queues,
  which prevents `wait_for_idle` from ever returning `True`.
- The test inspects queue depths, task counts, or file storage contents and needs a stable
  background with no surprise writes or deletions from periodic jobs.
- The test is sensitive to the `flush_file_storage_service_task` or similar maintenance tasks
  removing objects the test just created.

You do **not** need it for tests that simply upload a file and wait for it to be indexed — those
are not affected by periodic tasks running in the background.

**Monkey patching:**

Avoid monkey patching (`monkeypatch`, `unittest.mock.patch`, etc.) by default. Patching replaces
things at runtime behind the code's back, which couples tests to implementation details.
Using `MagicMock` or other test doubles is fine — the issue is *how* they reach the code under
test: pass them in via dependency injection rather than patching them into place.

Before reaching for a patch, ask yourself:

- **Is this test actually valuable?** If the only way to test something is to patch out most of its
  internals, the test may be asserting implementation details rather than behaviour.
- **Can the code be restructured for better testability?** Prefer dependency injection, small
  focused functions, and clear boundaries so that test doubles can be passed in directly.

Only patch when there is no reasonable alternative (e.g. a global external side effect that cannot
be injected). If you find yourself patching, treat it as a signal to reconsider the design first.

### Creating Issues (Bug Reports & Feature Requests)

Always use the issue template at `.gitlab/issue_templates/Default.md` when creating GitLab issues.
It covers both bug reports and feature requests in a single form.

### Documentation Check Before Committing

Before committing any implementation, review whether the changes affect user-facing behaviour,
configuration, or deployment — and if so, update the relevant documentation:

- **New Helm values files** (`charts/values-*.yaml`) → add an entry to the `## Helm Values Reference`
  section in `Documentation/installation.md`
- **New settings or configuration knobs** → check `Documentation/` for any guide that covers
  configuration and update it
- **New CLI flags, scripts, or devenv commands** → update `CLAUDE.md` (Common Commands) and any
  relevant `Documentation/` page
- **Changed defaults or behaviour** → update any doc that describes the old behaviour

If none of the documentation files need updating, proceed directly to the commit.

### Implementing Plans in a Git Worktree

Implementation work that ends in a commit belongs in a dedicated git worktree.
**Never implement directly in the primary checkout.** That checkout is where the user runs the
cluster and keeps their own branch checked out, and every `aitools` subcommand checks out branches
in the *current* working tree — running one there moves the user's branch under their feet.

- Create the issue and let GitLab's "Create Merge Request" button name the branch (see
  `### Git Workflow` below), then `git worktree add ../loom-worktrees/<branch> <branch>`
- Place worktrees **outside** the repo — there is no `.dockerignore`, so a nested worktree leaks
  into Docker build contexts, pytest collection and Skaffold watches
- Run `direnv allow` once in the new worktree; devenv files are tracked, but direnv trust is
  per directory
- A branch cannot be checked out twice → on "already checked out", ask the user to move the
  primary checkout off that branch rather than working in place

**State that does not follow into a worktree:**

- `devenv.local.nix` → gitignored, holds `GITLAB_TOKEN`; copy it across or every `aitools` GitLab
  command fails (see `Documentation/devenv-setup.md`)
- `charts/values-overwrites.yaml` and `charts/values-up-flags.yaml` → tracked but flagged
  `--skip-worktree` in the primary index, so a worktree silently gets the near-empty committed
  versions; copy them if local Helm overrides matter
- `.claude/settings.local.json` → untracked, so expect extra permission prompts; never edit
  settings files to silence them

**Keep cluster work in the primary checkout:** `up`, `down`, `build`, `wipe-data`,
`run-integrationtest` and all `kubernetes-*` commands. Their minikube, Skaffold and Docker caches
are gitignored per-directory, so a worktree would build a second cluster and contend for the same
`*.loom` hosts entries. Safe in a worktree: `backend-test`, `frontend-test`, `frontend-build`,
`generate-frontend-api`, `poetry-lock`, and all `git` and `aitools` commands.

**Finishing up:** commit and push from the worktree — git config, hooks and refs are shared. Leave
the MR in **Draft** and the worktree in place; report its path, the branch and the MR so the user
can review the diff there. **Never merge, rebase the primary checkout, or remove the worktree on
your own.** Remove one only when asked, with `git worktree remove <path>` and never `--force`.

### Git Workflow

Per `CONTRIBUTING.md`:

- Implement in a dedicated worktree, not the primary checkout (see the section above)
- Always create an issue first
- Use GitLab's "Create Merge Request" button from the issue (auto-links and names branch)
- Open MR early as **Draft**
- MR title becomes release note entry - make it descriptive
- Squash merging used - individual commit messages don't matter
- Use `Closes #issue-number` in MR description
- Remove Draft status only when ready for review

### Git Commit Format

- First line: conventional commit format — `type(scope): description`, max 72 characters
- Blank line after the title
- Body in markdown (headers with `#`, bullet points with `-`)
- Describe **what** changed, not why
- Do **not** add `Co-Authored-By` or any self-referencing author trailer

### Debugging

- Check pod logs: `kubectl logs <pod-name> -n loom`
- Or dump all logs: `kubernetes-fetch-all-pod-logs`
- RabbitMQ UI shows queue depths and message routing

## Important Technical Details

### Python Package Dependencies

The overarching `pyproject.toml` at repo root is dev-only and references all backend packages as path
dependencies. This enables IDE tooling (Pylance) to see across packages.

Each backend package has its own `pyproject.toml` and `poetry.lock`. After changing `common` dependencies,
you **must** run `poetry-lock` to update all lockfiles.

### File Processing Pipeline

1. Files uploaded to SeaweedFS bucket (via S3 API)
2. Crawler detects and schedules processing
3. Worker tasks (Celery):
    - Extract content via Tika
    - Perform OCR on images/PDFs
    - Extract metadata
    - Index in Elasticsearch
4. Frontend queries Elasticsearch via API

### Deployment Customization

Override Helm values in `charts/values-overwrites.yaml` (empty by default, automatically included by Skaffold).

## Code Style and Conventions

**Always ask the user before:**

- Adding linter-disabling rules (e.g. `# noqa`, `# type: ignore`, `# pylint: disable`, `# flake8: noqa`)

**NEVER put imports inside functions.** All imports must be at the top of the file. This is a hard rule
with almost no exceptions. Putting an import inside a function hides dependencies, makes code harder to
read and refactor, and is never necessary for normal code. If you think you need an import inside a
function, **stop and ask the user first** — there is almost certainly a better way.

- Python: Follow PEP 8, enforced by black + flake8 + pylint
- Use type hints everywhere (mypy enforced)
- **EXTREMELY IMPORTANT: Never use `dict`, `tuple`, or other generic collection types as function
  return types — not even for private helpers.** Always define and use a proper named type (Pydantic
  model, dataclass, `TypedDict`, or `NamedTuple`). Define a new type if one does not already exist.
  Raw `tuple[str, str]`, `tuple[X, Y]`, etc. are forbidden as return types. Callers should not need
  to remember what position 0 or 1 means — use a named type with descriptive field names instead.
- Pydantic models for validation and serialization
- Repository pattern for data access (see `common/models/`)
- Dependency injection via FastAPI dependencies and Celery task context
- Async/await where appropriate (FastAPI routes)

## Additional Documentation

- `Documentation/devenv-setup.md` - Development environment setup
- `Documentation/appliance.md` - NixOS appliance image and air-gapped deployment
- `nixos/README.md` - The appliance Nix code and how to build/test it
- `CONTRIBUTING.md` - Full Git workflow and collaboration guidelines
- `README.md` - Project overview and features
