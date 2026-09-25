"""The environment nixos/installer.nix starts these programs in.

Setting it is using the real interface rather than reaching past one: the wrapper in
installer.nix configures `loom-menu`, `loom-install` and `loom-wipe` entirely through
these variables, and `settings()` is the only thing that reads them. What makes a
fixture necessary rather than a module-level `os.environ` update is the `lru_cache` on
`settings()` -- it is deliberately read once per process, so a test that changes the
environment has to clear it on both sides.

Written once here rather than in each module that needs it. It was two copies, and a
third would have been the obvious way to add the next test.
"""

from collections.abc import Iterator

import pytest
from fakes import INSTALLER_ENVIRONMENT

from loom_installer.settings import settings


@pytest.fixture(name="installer_environment", autouse=True)
def _installer_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """An ordinary stick, configured the way installer.nix configures one.

    Autouse, because every module in this suite reads `settings()` somewhere below the
    surface and none of them should see the environment of whatever ran before.
    """
    for name, value in INSTALLER_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    settings.cache_clear()
    yield
    settings.cache_clear()
