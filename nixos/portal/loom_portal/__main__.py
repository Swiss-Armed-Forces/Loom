"""Assemble the portal from what the appliance told it, and serve.

The defaults come from the environment, which is how `nixos/portal.nix` passes the facts
only Nix knows -- whether this image requires a client certificate, which scheme the
frontend answers on, where the Loom mark is in the store. Every one of them can also be
given on the command line, so an operator on the box can run a second copy on another
port and look at it without rebuilding anything.

This is the only module that reads `os.environ`. Everything below it takes a
`PortalSettings`.
"""

import argparse
import logging
import os
import sys

from loom_portal.anchor import AnchorFile
from loom_portal.clock import Clock
from loom_portal.password import AttemptBucket, PasswordFile, PasswordGate
from loom_portal.portal import Portal
from loom_portal.server import serve
from loom_portal.settings import (
    DEFAULT_ACCENT,
    DEFAULT_STATE_DIR,
    PortalBind,
    PortalBrand,
    PortalLimits,
    PortalSettings,
    PortalUrls,
    validated_accent,
)
from loom_portal.spool import Spool
from loom_portal.validated import ValidatedClients

ENV_PREFIX = "LOOM_PORTAL_"


def build_settings(argv: list[str] | None = None) -> PortalSettings:
    defaults = PortalUrls()
    parser = argparse.ArgumentParser(
        prog="loom-portal",
        description="Serve the appliance's captive portal page.",
    )
    parser.add_argument("--listen", default=_env("LISTEN", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(_env("PORT", "18082")))
    parser.add_argument(
        "--frontend-url", default=_env("FRONTEND_URL", defaults.frontend)
    )
    parser.add_argument("--portal-url", default=_env("URL", defaults.portal))
    parser.add_argument(
        "--portal-redirect-url",
        default=_env("REDIRECT_URL", defaults.portal_redirect),
        help="where an unvalidated connectivity probe is sent; `loom.portal.target`",
    )
    parser.add_argument("--secure-url", default=_env("SECURE_URL", defaults.secure))
    parser.add_argument("--tag", default=_env("TAG", "dev"))
    parser.add_argument("--logo", default=_env("LOGO", ""))
    parser.add_argument("--accent", default=_env("ACCENT", DEFAULT_ACCENT))
    parser.add_argument("--state-dir", default=_env("STATE_DIR", DEFAULT_STATE_DIR))
    parser.add_argument(
        "--tls-placeholder",
        default=_env("TLS_PLACEHOLDER", ""),
        help="marker file that exists while the TLS listener is the stand-in pair",
    )
    parser.add_argument(
        "--mtls",
        action="store_true",
        default=_env("MTLS", "0") == "1",
        help="This box requires a client certificate, so offer one.",
    )
    parser.add_argument("--verbose", action="store_true")
    arguments = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if arguments.verbose else logging.INFO,
        # systemd takes the timestamp and the unit name, so neither belongs here.
        format="%(message)s",
        stream=sys.stdout,
    )

    return PortalSettings(
        bind=PortalBind(address=arguments.listen, port=arguments.port),
        urls=PortalUrls(
            frontend=arguments.frontend_url,
            portal=arguments.portal_url,
            portal_redirect=arguments.portal_redirect_url,
            secure=arguments.secure_url,
        ),
        brand=PortalBrand(
            tag=arguments.tag,
            accent=validated_accent(arguments.accent),
            logo_path=arguments.logo,
        ),
        limits=PortalLimits(),
        state_dir=arguments.state_dir,
        mtls=arguments.mtls,
        tls_placeholder_path=arguments.tls_placeholder,
    )


def build_portal(
    settings: PortalSettings,
    clock: Clock | None = None,
    spool: Spool | None = None,
) -> Portal:
    """Wire the four seams together.

    One function, so that the suite builds a portal the same way the service does rather
    than reproducing the wiring and drifting from it. `clock` and `spool` are the two the
    suite substitutes: the first so no test ever sleeps, the second so the issuance flow
    can be driven without a root unit on the other side of a directory.
    """
    clock = clock or Clock()
    limits = settings.limits
    return Portal(
        settings=settings,
        anchor=AnchorFile(settings.anchor_path, settings.fingerprint_path),
        gate=PasswordGate(
            passwords=PasswordFile(
                settings.password_path, settings.previous_password_path
            ),
            bucket=AttemptBucket(clock, limits.attempts, limits.attempt_window_s),
            clock=clock,
            wrong_delay_s=limits.wrong_password_delay_s,
        ),
        spool=spool
        or Spool(
            requests_dir=settings.requests_dir,
            bundles_dir=settings.bundles_dir,
            clock=clock,
            max_in_flight=limits.max_in_flight,
            timeout_s=limits.issue_timeout_s,
        ),
        validated=ValidatedClients(
            directory=settings.validated_dir,
            clock=clock,
            ttl_s=limits.validated_ttl_s,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    settings = build_settings(argv)
    serve(build_portal(settings), settings)
    return 0


def _env(name: str, default: str) -> str:
    return os.environ.get(ENV_PREFIX + name, default)


if __name__ == "__main__":
    raise SystemExit(main())
