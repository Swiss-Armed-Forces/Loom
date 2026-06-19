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
- **LibreTranslate** - Translation service
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

- `backend-test` - Run all backend tests with pytest and coverage (from `backend/` directory)
- `backend-test backend/api/tests/test_foo.py` - Run specific test file
- `backend-test backend/worker/tests/test_bar.py::test_function` - Run specific test

**Frontend:**

- `frontend-test` - Run frontend tests
- `frontend-build` - Build frontend bundle
- `generate-frontend-api` - Regenerate TypeScript API types from backend OpenAPI schema (also runs lint-fix)

**Linting:**

- `lint` - Run all linters (Python: black, isort, autoflake, pylint, mypy, flake8; Frontend: eslint, prettier; etc.)
- `lint-fix` - Auto-fix linting issues where possible

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
- ESLint requires staged files (uses `git ls-files`), so stage deletions/renames before running `lint-fix`
- Changes auto-reload when `up --development` is running

### Testing Strategy

**Unit tests:**

- Backend: `backend-test` runs all tests in `backend/*/tests/`
- Frontend: `frontend-test`

**Integration tests:**

- Located in `integrationtest/`
- Run with `run-integrationtest`
- Simulates full workflows against running Loom instance

**Test execution:**

- Tests create temp artifacts in `.pytest_tmp` (not `/tmp`) to avoid RAM usage
- Per-test timeout configured in `pytest.ini`
- Coverage reports generated automatically

### Creating Issues (Bug Reports & Feature Requests)

Always use the issue template at `.gitlab/issue_templates/Default.md` when creating GitLab issues.
It covers both bug reports and feature requests in a single form.

### Git Workflow

Per `CONTRIBUTING.md`:

- Always create an issue first
- Use GitLab's "Create Merge Request" button from the issue (auto-links and names branch)
- Open MR early as **Draft**
- MR title becomes release note entry - make it descriptive
- Squash merging used - individual commit messages don't matter
- Use `Closes #issue-number` in MR description
- Remove Draft status only when ready for review

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

- Adding imports inside functions (rather than at the top of the file)
- Adding linter-disabling rules (e.g. `# noqa`, `# type: ignore`, `# pylint: disable`, `# flake8: noqa`)

- Python: Follow PEP 8, enforced by black + flake8 + pylint
- Use type hints everywhere (mypy enforced)
- **Never use `dict`, `tuple`, or other generic collection types as function return types.** Always
  define and use a proper named type (Pydantic model, dataclass, `TypedDict`, or `NamedTuple`).
  Define a new type if one does not already exist. This applies to all functions, including helpers.
- Pydantic models for validation and serialization
- Repository pattern for data access (see `common/models/`)
- Dependency injection via FastAPI dependencies and Celery task context
- Async/await where appropriate (FastAPI routes)

## Testing Requirements

- All new backend features require unit tests
- Integration tests for user-facing workflows
- Maintain test coverage (coverage reports generated automatically)
- Tests must pass locally before pushing
- CI/CD pipeline runs full test suite + linting

## Additional Documentation

- `Documentation/devenv-setup.md` - Development environment setup
- `CONTRIBUTING.md` - Full Git workflow and collaboration guidelines
- `README.md` - Project overview and features
