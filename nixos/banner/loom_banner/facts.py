"""What the screen says, split by when it is known.

`Box` is settled when the image is built and arrives on the command line, the way `loom-
platform-info` already takes the platform's own claims. `Live` is read at print time,
every time, because a banner is rendered once per boot and several of these change
underneath it: a box booted on the recovery passphrase has no USB key and its guard
never arms, a cluster takes minutes to come up, and the portal password is replaced at
midnight.
"""

from dataclasses import dataclass
from pathlib import Path

# What `state` holds while the guard is watching a key, and while it is not.
GUARD_ARMED = "armed"
GUARD_DISARMED = "disarmed"

# Stands in for the portal password when the file is there but this process may not
# read it -- an operator running `loom-info` by hand rather than the root unit that
# renders the login screen. Saying so beats dropping the row, which would read as
# "this image has no portal password".
WITHHELD = "-- readable by root; try: sudo loom-info"


@dataclass(frozen=True)
class KeyGuard:
    """What this image's guard will do when the key leaves.

    Carried rather than assumed, because a --debug image only warns and a banner
    promising a poweroff is the one claim on this screen an operator can disprove by
    pulling the stick.
    """

    action: str = "poweroff"
    grace: int = 0
    arm_deadline: int = 0


@dataclass(frozen=True)
class Wifi:
    """The access point's credentials, empty on an image without one."""

    ssid: str = ""
    psk: str = ""


@dataclass(frozen=True)
class Portal:
    """Where the captive portal is, and whether it can issue a certificate."""

    host: str = ""
    issues_certificates: bool = False


@dataclass(frozen=True)
class Box:
    """The facts the image was built with, grouped by the feature they belong to."""

    tag: str
    platform: str
    runs_ai: bool = True
    meets_resource_minimum: bool = True
    key_guard: KeyGuard = KeyGuard()
    wifi: Wifi = Wifi()
    portal: Portal = Portal()


@dataclass(frozen=True)
class Paths:
    """Where the live facts are published, as the modules that own them declare it."""

    network_conf: Path
    ready_summary: Path
    key_guard_state: Path
    key_guard_deadline: Path
    recovery_passphrase: Path
    portal_password: Path


@dataclass(frozen=True)
class Live:
    """The facts as they are at the moment of painting."""

    wired_interface: str = ""
    subnet: str = ""
    summary: str = ""
    key_guard: str = ""
    key_guard_pending: bool = False
    recovery_passphrase: str = ""
    portal_password: str = ""

    @classmethod
    def read(cls, paths: Paths) -> "Live":
        conf = _conf(paths.network_conf)
        return cls(
            # The wired port, which is not the interface holding the address once an
            # access point bridges the two.
            wired_interface=conf.get("LOOM_WIRED_INTERFACE", ""),
            subnet=conf.get("LOOM_SUBNET", ""),
            summary=_line(paths.ready_summary),
            key_guard=_line(paths.key_guard_state),
            # The file exists on a box that booted from the stick and has not armed,
            # which is the one case where this screen has seconds left on it.
            key_guard_pending=paths.key_guard_deadline.is_file(),
            recovery_passphrase=_line(paths.recovery_passphrase),
            portal_password=_line(paths.portal_password, withheld=WITHHELD),
        )


def _line(path: Path, withheld: str = "") -> str:
    """The first line of a published file, or nothing.

    Nothing is the normal state for most of these -- no key guard on a box that booted
    without a stick, no summary while the cluster has not answered -- so a missing file
    is not a failure and the row it would have filled simply does not appear.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        return withheld
    except OSError:
        return ""
    return content.strip().splitlines()[0].strip() if content.strip() else ""


def _conf(path: Path) -> dict[str, str]:
    """A `KEY=value` file, read without a shell.

    Only the assignments are taken; anything else in there is a comment or a blank and
    is none of this screen's business.
    """
    values: dict[str, str] = {}
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return values
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("\"'")
    return values
