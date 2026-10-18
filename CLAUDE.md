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

**aitools testing:**

- `aitools-test` - Run all `aitools` tests and the `cicd/tests/` tests covering the scripts
  beside it, with pytest (always runs from `cicd/` directory)
- `aitools-test aitools/tests/test_git_helpers.py` - Run specific test file (paths relative to `cicd/`)

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

**Utilities:**

- `poetry-lock` - Regenerate all Poetry lockfiles (run after adding dependencies to `common`)
- `generate-openapi-schema` - Print OpenAPI schema JSON
- `generate-third-party` - Regenerate `THIRD-PARTY.md`, its `Frontend/public/` copy and
  `THIRD-PARTY.lock`. A section is a syft scan of an image's *package inventory*, so the lock keys
  it on the inputs that can change that inventory and on nothing else: the image's Dockerfile
  (where every `FROM` pins its base by digest, and the apt, apk, plugin and model versions are
  pinned too), the build arguments its Skaffold configuration declares, and whatever
  `cicd/third_party_inputs.yaml` adds for it - dependency lockfiles and installer scripts. A
  section is reused byte-for-byte while that key is unchanged, so a change to application source,
  configuration or documentation scans nothing, builds nothing and leaves the lock alone.
  **The generated file must depend on the repository alone** - it is committed by CI, and a
  generator that answers differently on two runners pushes a commit per pipeline forever, which is
  why build arguments are hashed as written rather than as resolved (`DOCKER_REGISTRY` expands to a
  dependency-proxy prefix in CI and to `docker.io` elsewhere). **Adding an image, or a `COPY` that
  installs something, means declaring it in `cicd/third_party_inputs.yaml`** - the tests in
  `cicd/tests/test_third_party_inputs.py` fail until every image has an entry and every `COPY`
  source is either keyed or listed as `not_keyed`, because the alternative fails silently: a
  licence document that no longer describes what the image ships. Pass `--refresh` to rescan every
  image regardless of the lock, which is the only way to notice inventories no file hash can track
  - `roundcube` composer-requires its plugins at build time with no lockfile, `alpine` uses `~=`
  apk pins, `worker` and `tika` use apt version wildcards, and `ollama-models` pulls mutable model
  tags
- `cicd/check_chart_hostnames.sh` - Assert that `hostnames.ingress` in `charts/values.yaml` is
  exactly the set of hosts the chart routes by name - `spec.rules[].host` on an Ingress and
  HostSNI(`<name>.<domain>`) on an IngressRouteTCP - and that each Ingress's `spec.tls[].hosts` is a
  subset of its own rules. Runs as a git hook on any change under `charts/`, to the checker itself or
  to `vars.sh`, and needs no cluster (`helm template` is client-side). **Adding a service with an
  Ingress means adding its name to `hostnames.ingress`** - that list is what the pre-install Job puts
  in the TLS certificate's `subjectAltName` and what `charts/templates/common/certificate.yaml`
  renders into `dnsNames`, one entry per host, and a wildcard cannot stand in for it (`*.loom` has
  one dot, and OpenSSL will not expand a wildcard under a single-label parent). A host served by
  entrypoint rather than by a route that names it goes in `hostnames.extra` instead. See the
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
- `aitools` unit tests: `aitools-test` (runs all tests in `cicd/aitools/tests/` and
  `cicd/tests/`, the latter covering the scripts at the root of `cicd/`) — always from
  `cicd/`, not from `cicd/aitools/`, where the `aitools.py` module shadows the `aitools` package
  and every import fails
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

**Retry classification:**

A Celery task's `autoretry_for` must name exactly the exception the code below it raises for a
*transient* failure — nothing wider, nothing narrower. Getting it wrong is silent in both
directions: too narrow and a service outage is treated as a property of the document, too wide and
a deterministic failure occupies a worker for the whole backoff budget (with `retry_backoff=True`
and `max_retries=15`, roughly an hour, multiplied by the chunk count of every affected document).

- **The service layer classifies**, because it is the only layer that sees the status code. It
  raises a distinct type per outcome under one base — see `TikaTransientError` /
  `TikaPermanentError` in `worker/services/tika_service.py`, and the matching pairs in
  `rspamd_service.py` and `common/llm/exceptions.py`. A service that wraps an exception
  (`raise XError from exc`) has to be checked against what the task declares: `TikaError` wrapping
  `requests.HTTPError` while the task declared `RequestException` is what made every Tika 5xx
  degrade a PDF to the strings extractor without a single retry.
- **Classify from what the service actually reports, not from the status class.** The default for
  an unrecognised failure is transient, because a wasted retry budget is cheaper than silently
  discarding work that would have succeeded — but check each 5xx before assuming it. Gotenberg
  answers `500` on a document's own route when LibreOffice cannot open the file, so there it is a
  verdict and only `503`/`502`/`429`/`408` are worth retrying; Tika answers `5xx` when its forked
  parser was killed and keeps refusals to `4xx`, so there the whole `5xx` range is transient.
  Misreading a verdict as transient is not a wasted budget — it holds the file out of the index for
  the entire backoff before degrading to the same answer.
- **The task decides degrade-vs-fail with `BaseTask.is_last_attempt`**, never by comparing
  `self.request.retries` against the limit by hand.
- **A task that degrades logs a warning.** Degrading silently is why the Tika defect went unnoticed
  for so long: the only trace it left was `tika_handled_by` on the indexed document.

### Issue and Merge Request Templates

Both templates are tracked in this repo. **Read the file at the moment you write the issue or MR
description** — do not reproduce its structure from memory, it changes.

**Issues** → `.gitlab/issue_templates/Default.md`. One combined form for bug reports and feature
requests: tick exactly one `📝 Issue Type` box (`[ ]` → `[x]`), fill the section matching that
type, and delete the section that does not apply along with the `<!-- -->` hint comments. Keep the
headings and their emoji verbatim — they are what makes issues scannable.

**Merge requests** → `.gitlab/merge_request_templates/Default.md`. `# 📌 Summary` gets a short
paragraph followed by `Added:` / `Changed:` / `Removed:` / `Fixed:` bullet lists; `## 🔗 Issue
Reference` gets `Closes #<issue-number>`.

**The MR title and description are not commentary about the change — they become the title and
message of the squashed commit on `main`.** Write both as the commit message you want in the
history, and nothing else.

That has two consequences, and both are gotten wrong by default:

- **The title is a conventional commit subject**, `type(scope): description`, max 72 characters,
  lowercase after the colon, describing *what* changed — exactly the rule in `### Git Commit
  Format` below, because it ends up being that commit's subject. Use the same types the history
  uses: `feat`, `fix`, `refactor`, `docs`, `chore`, with the scope naming the area
  (`feat(api): serve chart metadata from the cluster on /v1/about`,
  `fix(worker): retry on the exceptions services actually raise`). A sentence-style title like
  "Add X and port Y to Python" is wrong, however descriptive it reads.
- **The description contains the template's headings and nothing else.** Do not add sections of
  your own — no "Notes for review", "Testing", "Background", "Implementation notes", no trailing
  summary of what you did. Anything extra becomes permanent commit message on `main`. Review
  commentary belongs in an MR *comment*, which is not part of the commit.

The `%{...}` placeholder under the Summary heading is a GitLab expansion variable that only fires
when an MR is created through the **web UI**. Sent through the REST API it stays in the
description verbatim, so replace it with the real summary text whenever you write a description
any other way.

This applies no matter how the issue or MR is created — GitLab UI, REST API, `glab`, or
`aitools mr-create` / `mr-describe` / `mr-update`.

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
- `direnv allow` only marks the directory trusted — it builds nothing. **Enter the environment
  once with `direnv exec <worktree> true`**, which creates the worktree's own `.venv`, `.devenv`
  and `.pre-commit-config.yaml`, then run every command there as
  `direnv exec <worktree> <command>`. Until that happens the worktree has no environment of its
  own and inherits the primary checkout's `PATH`, so `python`, `pytest` and the linters resolve
  editable path dependencies — `aitools` among them — to the *primary checkout's* sources and
  report on code that is not the code under test
- Each checkout installs its git hooks into its own git directory — `.git/hooks` in the main
  worktree, `.git/worktrees/<name>/hooks` in a linked one — pointed there by
  `cicd/set_worktree_hooks_path.sh` before devenv installs them. The hook *set*, its excludes and
  its pinned tools therefore come from the `devenv.nix` of the tree you commit in, and deleting a
  worktree cannot break committing in the others. A worktree has no hooks of its own until devenv
  is entered in it once
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
`run-integrationtest` and all `kubernetes-*` commands. There is one cluster per machine and every
checkout talks to it — `MINIKUBE_HOME` resolves to the main worktree, matching the `~/.kube/config`
that minikube writes — so these commands do not fail in a worktree, they succeed *against the
primary checkout's running system*: `up` redeploys it from the worktree's sources, and `wipe-data`
and `kubernetes-delete` destroy it. Safe in a worktree: `backend-test`, `frontend-test`,
`frontend-build`, `generate-frontend-api`, `poetry-lock`, and all `git` and `aitools` commands.

**Finishing up:** commit and push from the worktree — git config and refs are shared. Then
**take the MR out of Draft and start a pipeline for it** (see `### Finishing an MR` below), and
report the worktree path, the branch, the MR and the pipeline so the user can review the diff
there. Leave the worktree in place. **Never merge, rebase the primary checkout, or remove the
worktree on your own.** Remove one only when asked, with `git worktree remove <path>` and never
`--force`.

### Git Workflow

Per `CONTRIBUTING.md`:

- Implement in a dedicated worktree, not the primary checkout (see the section above)
- Always create an issue first, filling `.gitlab/issue_templates/Default.md` (see
  `### Issue and Merge Request Templates` above)
- Use GitLab's "Create Merge Request" button from the issue (auto-links and names branch)
- Open MR early as **Draft**, with the description following
  `.gitlab/merge_request_templates/Default.md`
- MR title is a conventional commit subject (`type(scope): description`, max 72 chars) and
  becomes the release note entry — see `### Issue and Merge Request Templates` above
- Squash merging used - individual commit messages don't matter, but the **MR title and
  description do**: they become the squashed commit on `main`. Keep the description to the
  template's headings and add no sections of your own
- Use `Closes #issue-number` under the MR description's `## 🔗 Issue Reference` heading
- Remove Draft status when the work is done, and start a pipeline yourself (see below)

### Finishing an MR

**When you are done working — the change is committed, pushed and its tests pass — undraft the
MR and start a pipeline for it.** Do both, in that order, without waiting to be asked. A Draft MR
is invisible to CI, so leaving one behind means nobody finds out whether the change builds.

Why both steps are needed, per the `workflow:rules:` in `.gitlab-ci.yml`:

- Merge request pipelines only run when the title does **not** start with `Draft`, and branch
  pipelines are skipped outright while an MR is open (`$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS`
  → `when: never`). So **a Draft MR runs no pipeline at all**, however often you push.
- Undrafting is a title change, and a title change does not create a pipeline. Removing the
  `Draft:` prefix therefore leaves the MR with the *stale* pipeline status it already had — the
  pipeline has to be created explicitly.

Undraft by stripping the `Draft:` prefix from the title (`mr.title`, then `mr.save()`), then
create the pipeline with `mr.pipelines.create()` — the MR-pipelines endpoint, not
`project.pipelines.create()`, whose branch pipeline the rules above discard. Afterwards
`aitools mr-watch` follows that pipeline and fixes what fails.

**When the MR stops tracking its branch, close and reopen it.** GitLab sometimes leaves an MR
stuck on an old head commit, and everything downstream then misbehaves:
`mr.pipelines.create()` answers **405** while `mr.detailed_merge_status` is `preparing`, `mr.sha`
keeps reporting a commit the branch has long moved past, and `generate_frontend_static` fails on
purpose rather than run CI on what it sees as a stale commit. Pushing again does not clear it.
Closing and reopening the MR (`state_event`) does, within seconds: the status becomes `unchecked`,
`mr.sha` catches up with the branch, and the pipeline can be created. Compare `mr.sha` against
`project.branches.get(<branch>).commit` to tell this apart from a real failure.

Keep the MR in Draft only while it is deliberately unfinished — an MR opened early for discussion
before the work exists, or one the user asked you to leave alone.

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

**Attaching a debugger.** `up --development` runs `skaffold dev` and forwards exactly the ports
listed under `portForward` in the `dev` profile of `skaffold.yaml` — nothing is discovered
automatically. Each one matches an attach configuration in `.vscode/launch.json`, so the two lists
have to be changed together:

| Component | Port | Listener declared in |
| --------- | ---- | -------------------- |
| api | 4401 | `backend/api/Dockerfile` (dev stage `CMD`) |
| worker | 5500 | `charts/values-development.yaml` (`worker.command`) |
| reaper | 5501 | `charts/values-development.yaml` (`reaper.command`) |
| persister | 5502 | `charts/values-development.yaml` (`persister.command`) |
| beat | 5503 | `charts/values-development.yaml` (`beat.command`) |
| crawler | 6601 | `backend/crawler/Dockerfile` (dev stage `CMD`) |

Two things to know when a debugger will not attach:

- **`localPort` is a request, not a reservation.** If anything already holds 4401 — a leftover
  `kubectl port-forward` from a previous run is the usual culprit — skaffold forwards on the next
  free port instead and says so. Read its `Port forwarding ... -> 127.0.0.1:<port>` lines rather
  than assuming the configured port.
- **Only one pod per workload is forwarded.** Scale a component past one replica (`replicaCount`,
  HPA or KEDA) and the other replicas have no forward at all.

A pod paused on a breakpoint would normally be restarted by its probes;
`charts/values-debug-probes.yaml` prevents that and is applied automatically by `--development`.

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
- **`cicd/` is a linted Python root like any backend package.** Its scripts go through black,
  isort, autoflake, docformatter, flake8, pylint and mypy, with mypy configured by
  `cicd/mypy.ini` because mypy reads its settings from the directory a tool runs in. Tests for
  them live in `cicd/tests/`. `cicd/aitools` is a root nested inside it; `nestedSubdirExcludes`
  in `devenv.nix` keeps each file linted by the innermost root that contains it, so adding a
  python root under another one needs no further wiring. A long shell script in `cicd/` is
  better rewritten in Python than grown - the tools above only cover the Python
- Repository pattern for data access (see `common/models/`)
- Dependency injection via FastAPI dependencies and Celery task context
- Async/await where appropriate (FastAPI routes)
- **Helm: a container's shell script belongs in `charts/files/<component>/*.sh`, not inline in the
  template.** Anything past a couple of lines is a file mounted through a ConfigMap - see
  `charts/templates/pre-install/` for the pattern (a short `until nc -vz ...; do sleep 2; done` wait
  loop can stay inline). A script inlined into a template is a YAML string that shellcheck never
  sees, and the repo runs shellcheck with `-o all`. Values reach the script through the container's
  `args:` as long options, and the script parses them in a `while`/`case` loop and asserts each one
  is set

## Additional Documentation

- `Documentation/devenv-setup.md` - Development environment setup
- `CONTRIBUTING.md` - Full Git workflow and collaboration guidelines
- `README.md` - Project overview and features
