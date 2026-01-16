# Backend

This directory contains multiple python packages.

* [API: The Loom REST api](./api/README.md)
* [Crawler: Watches locations and schedules files for processing](./crawler/README.md)
* [Worker: Processes files](./worker/README.md)
* [Common: shared logic and is used by the other packages of `backend/`](./common/README.md)

## Install dependencies

The dependencies on the individual packages are managed with [Poetry](https://python-poetry.org/).

To add a package, call `poetry add some_package` in the directory of the package (e.g. backend/api).

This will install the package in the virtual environment, add it to the `pyproject.toml`
file and update the `poetry.lock` file.

**IMPORTANT:** _When adding dependencies to `common`, it is required to call `poetry lock`
in all the other packages that depend on `common`. The devenv utility: `poetry-lock`
updates all lock files in all packages._

## Testing and linting

All Python code in the backend needs to pass the unit and lint tests performed by the CI/CD pipeline.
It is recommended run those checks locally first to avoid unnecessary commits.

Unit tests can be run locally by using the `backend-test` devenv script.
