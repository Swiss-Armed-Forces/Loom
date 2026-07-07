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

**Utilities:**

- `poetry-lock` - Regenerate all Poetry lockfiles (run after adding dependencies to `common`)
- `generate-openapi-schema` - Print OpenAPI schema JSON

**AI developer tools (`aitools` subcommands):**

- `aitools mr-review [<MR URL or IID>] [--fix]` - Run a multi-agent AI review of an MR and
  post findings as inline GitLab comments; omit the MR argument to auto-detect the MR for
  the current branch; pass `--fix` to auto-apply findings instead of posting them as comments
- `aitools mr-watch [<MR URL or IID>]` - Watch an MR's pipeline and auto-fix CI failures
- `aitools mr-fix [<MR URL or IID>]` - Address unresolved MR review comments using Claude
  in agentic mode; omit the argument to fix the MR for the current branch
- `aitools mr-create` / `mr-describe` / `mr-update` - MR lifecycle helpers
- `aitools job-diagnose <job-id>` - Diagnose a specific CI job failure

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

### Git Workflow

Per `CONTRIBUTING.md`:

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
- Flower UI shows Celery task execution and failures
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
- **Never use `dict`, `tuple`, or other generic collection types as function return types.** Always
  define and use a proper named type (Pydantic model, dataclass, `TypedDict`, or `NamedTuple`).
  Define a new type if one does not already exist. This applies to all functions, including helpers.
- Pydantic models for validation and serialization
- Repository pattern for data access (see `common/models/`)
- Dependency injection via FastAPI dependencies and Celery task context
- Async/await where appropriate (FastAPI routes)

## Additional Documentation

- `Documentation/devenv-setup.md` - Development environment setup
- `CONTRIBUTING.md` - Full Git workflow and collaboration guidelines
- `README.md` - Project overview and features
