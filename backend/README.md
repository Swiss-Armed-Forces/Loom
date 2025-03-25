# Backend

This directory contains multiple python packages.

## API

The Loom REST api

[more...](./api/README.md)

## Crawler

A crawler that watches a directory and schedules files for processing

[more...](./crawler/README.md)

## Worker

Celery worker that processes files

[more...](./worker/README.md)

## Common

A library that contains shared logic and is used by the other packages of `backend/`

[more...](./common/README.md)

## Install dependencies

The dependencies on the individual packages are managed with [Poetry](https://python-poetry.org/).

To add a package, call `poetry add some_package` in the directory of the package (e.g. backend/api).

This will install the package in the virtual environment, add it to the `pyproject.toml` file and update the `poetry.lock` file.

**IMPORTANT:** _When adding dependencies to `commmon`, it is required to call `poetry lock` in all the other packages that depend on `common`._

This ensured that the `poetry.lock` file gets updated and all the correct packages will be installed.

## Testing and linting

All Python code in the backend needs to pass the unit and lint tests performed by the CI/CD pipeline. It is recommended run those checks locally first to avoid unncessary commits.

Unit tests can be run locally by using the `backend-test` devenv script.

![](https://imgs.xkcd.com/comics/code_quality.png "Obligatory XKCD reference")
