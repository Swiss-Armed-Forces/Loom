"""Test doubles that ship with `common`, so every package that depends on it can use
them.

Deliberately inside the distribution rather than beside the tests: `common`'s own tests
are not packaged (backend/common/pyproject.toml ships `{ include = "common" }` only), so
anything living there is unreachable from crawler, worker and api -- leaving a hand-made
copy per suite as the only alternative.

Nothing here is imported by production code, and nothing here may import anything that
is not already a dependency of `common`.
"""
