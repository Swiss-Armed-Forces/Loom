#!/usr/bin/env python3
"""Generate THIRD-PARTY.md, its Frontend copy and THIRD-PARTY.lock.

The document lists every third-party component Loom ships: the licence files
checked in beside each component, the Python and JavaScript dependency trees,
and a syft scan of every container image.

Scanning an image is the expensive part, so each image's section is pinned to a
key over the inputs that can change what the scan reports - see
third_party_inputs.py for what those are. While the key is unchanged the
committed section is still the answer and is reused byte-for-byte; only images
whose key moved are rebuilt and rescanned.

That pinning is what keeps the output a function of this repository. Scanning
whatever image a runner happens to hold under a tag does not: two runners hold
images built at different times, answer differently, and - because CI commits
this file - each pipeline then pushes the other one's answer back.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from minikube_env import get_minikube_docker_environment
from third_party_inputs import ImageInputs, load_image_inputs

SCRIPT_DIR = Path(__file__).resolve().parent
TOPLEVEL_DIR = SCRIPT_DIR.parent

FRONTEND_DIR = TOPLEVEL_DIR / "Frontend"
SYFT_TEMPLATE = SCRIPT_DIR / "syft-template.txt"
CICD_SKAFFOLD = SCRIPT_DIR / "skaffold"

THIRD_PARTY_LICENCES = Path("THIRD-PARTY.md")
THIRD_PARTY_LOCK = Path("THIRD-PARTY.lock")
FRONTEND_STATIC_LICENCES = FRONTEND_DIR / "public" / THIRD_PARTY_LICENCES.name

PROFILE = "prod"

IMAGE_HEADING_PREFIX = "### "
SECTION_HEADING_PREFIXES = ("## ", "### ")
LOCK_SYFT_PREFIX = "# syft "

ISSUE_TRACKER_URL = (
    "https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/new"
)

PREAMBLE = f"""# Third Party Licenses
<!-- markdownlint-disable -->
This document serves to provide a comprehensive overview of all third-party software
components utilized in the development and operation of the "Loom" product.
Our intent is to maintain transparency and adhere strictly to the licensing terms
associated with each incorporated software package.

Within this file, you will find a detailed list of the open-source and proprietary
software libraries, frameworks, and tools that are integrated into Loom, along with
their respective licenses.

We are committed to respecting the intellectual property rights of others and ensuring
full compliance with all applicable license obligations.

Should you identify any instance of potential license infringement or trademark violation
related to the third-party software listed herein, we encourage you to promptly notify
the owners of "Loom" by opening a new issue via the following link:

* [Loom Issue Tracker]({ISSUE_TRACKER_URL})

Your diligence in bringing such matters to our attention is greatly appreciated and will
enable us to take appropriate and timely action to rectify any concerns."""

LOCK_PREAMBLE = f"""# What produced each section of {THIRD_PARTY_LICENCES}.
#
# Each key hashes the inputs that can change which packages an image ships -
# its Dockerfile, its build arguments, and the dependency lockfiles and
# installer scripts cicd/third_party_inputs.yaml declares for it. While the key
# is unchanged the committed section is reused byte-for-byte instead of
# rescanned, so a change that cannot alter an inventory - application source,
# configuration, documentation - leaves this file alone.
#
# The key is a function of this repository and of nothing else, which is what
# keeps the generated document stable across runners and pipelines. Rescan
# everything with: generate-third-party --refresh"""


@dataclass(frozen=True)
class ImageRef:
    """A container image as Skaffold reports it: a name and an input-hash tag."""

    name: str
    tag: str

    @property
    def reference(self) -> str:
        """The image as docker addresses it."""
        return f"{self.name}:{self.tag}"

    @staticmethod
    def parse(reference: str) -> "ImageRef":
        """Split a reference on its last colon, which a registry port cannot occupy."""
        name, separator, tag = reference.rpartition(":")
        if not separator:
            raise ValueError(f"Image reference carries no tag: '{reference}'")
        return ImageRef(name=name, tag=tag)


@dataclass(frozen=True)
class Lock:
    """What the committed document's sections were generated from."""

    syft_version: str
    keys: Mapping[str, str]

    def key_for(self, image_name: str) -> str | None:
        """The key that produced this image's committed section, if any."""
        return self.keys.get(image_name)


@dataclass(frozen=True)
class ScanDecision:
    """Whether an image has to be rescanned, and what decided it."""

    inputs: ImageInputs
    scan: bool
    reason: str


@dataclass(frozen=True)
class CommandEnvironment:
    """Environment for the external tools this script drives."""

    variables: Mapping[str, str]


@dataclass(frozen=True)
class SkaffoldInvocation:
    """How one Skaffold configuration is driven: the command, and where from."""

    argv: tuple[str, ...]
    cwd: Path | None


def run_command(
    argv: Sequence[str],
    environment: CommandEnvironment,
    cwd: Path | None = None,
    capture: bool = True,
) -> str:
    """Run a command, fail on a non-zero exit, and return its stdout when captured."""
    logging.debug("running: %s", " ".join(argv))
    completed = subprocess.run(  # nosec B603 - argv is built here, never a shell string
        list(argv),
        check=True,
        cwd=cwd,
        env=dict(environment.variables),
        stdout=subprocess.PIPE if capture else None,
        text=True,
    )
    return completed.stdout if capture else ""


def get_minikube_environment(environment: CommandEnvironment) -> CommandEnvironment:
    """Return the environment extended so that docker addresses minikube's daemon.

    Applying the variables to one mapping keeps the change inside this process rather
    than in a shell.
    """
    variables = dict(environment.variables)
    variables.update(get_minikube_docker_environment().variables)
    return CommandEnvironment(variables=variables)


def get_image_tags(skaffold_output: str) -> list[ImageRef]:
    """Parse the image references out of `skaffold build --quiet` JSON."""
    builds = json.loads(skaffold_output).get("builds", [])
    return [ImageRef.parse(build["tag"]) for build in builds]


def get_build_invocation(config: Path) -> SkaffoldInvocation:
    """How to drive Skaffold for the configuration an image was declared in.

    traefik and keda go through cicd/skaffold, which untars their bundled chart and
    exports the versions their configurations read; the root configuration is run
    directly.
    """
    traefik = TOPLEVEL_DIR / "traefik" / "skaffold.yaml"
    keda = TOPLEVEL_DIR / "keda" / "skaffold.yaml"
    root = TOPLEVEL_DIR / "skaffold.yaml"
    invocations = {
        traefik: SkaffoldInvocation(argv=(str(CICD_SKAFFOLD), "traefik"), cwd=None),
        keda: SkaffoldInvocation(argv=(str(CICD_SKAFFOLD), "keda"), cwd=None),
        root: SkaffoldInvocation(argv=("skaffold",), cwd=TOPLEVEL_DIR),
    }
    invocation = invocations.get(config)
    if invocation is None:
        raise RuntimeError(f"No build invocation is defined for '{config}'")
    return invocation


def group_by_config(inputs: Sequence[ImageInputs]) -> dict[Path, list[ImageInputs]]:
    """Group images by the Skaffold configuration that declares them."""
    grouped: dict[Path, list[ImageInputs]] = {}
    for image in inputs:
        grouped.setdefault(image.declaration.config, []).append(image)
    return grouped


def build_images(
    inputs: Sequence[ImageInputs], environment: CommandEnvironment
) -> None:
    """Build exactly the images that have to be scanned, so syft has something to read.

    `--build-image` restricts the build to the named artifacts. Building the rest
    would be work with no output: their sections are reused from the document.
    """
    for config, images in group_by_config(inputs).items():
        invocation = get_build_invocation(config)
        selected = [argument for image in images for argument in ("-b", image.name)]
        run_command(
            [
                *invocation.argv,
                "build",
                "--profile",
                PROFILE,
                "--push=false",
                *selected,
            ],
            environment,
            cwd=invocation.cwd,
            capture=False,
        )


def resolve_references(
    inputs: Sequence[ImageInputs], environment: CommandEnvironment
) -> dict[str, ImageRef]:
    """Ask Skaffold what it tagged the images it just built.

    Only reached when something has to be scanned. `--dry-run` recomputes the tags
    without building, and they are deterministic, so it reports the tags the build above
    produced.
    """
    references: dict[str, ImageRef] = {}
    for config in group_by_config(inputs):
        invocation = get_build_invocation(config)
        output = run_command(
            [*invocation.argv, "build", "--dry-run", "--quiet", "--profile", PROFILE],
            environment,
            cwd=invocation.cwd,
        )
        for image in get_image_tags(output):
            references[image.name] = image
    return references


def get_syft_version(environment: CommandEnvironment) -> str:
    """The running syft's version, which decides whether old sections still apply."""
    output = run_command(["syft", "--version"], environment)
    return output.replace("syft", "").strip()


def scan_image(image: ImageRef, environment: CommandEnvironment) -> str:
    """Scan an image with syft and render it as this document's section body.

    syft exports the image to a tar under TMPDIR before reading it, and these
    images run to several gigabytes each. The directory is therefore private to
    this scan and removed as soon as it is done: a run that scans every image -
    a first run, or one after `--refresh` - otherwise needs disk for all of
    them at once, and a runner that fills up fails the whole job.

    syft does not always report failure through its exit status - on SIGINT it
    exits 0 with no output - so empty output is treated as the failure it is.
    """
    logging.info("Scanning image: %s", image.reference)
    variables = dict(environment.variables)
    # Not /tmp, which is RAM here, and not the system default for the same reason.
    syft_tmpdir = Path(tempfile.mkdtemp(dir=Path.cwd(), prefix=".syft-tmp."))
    variables["TMPDIR"] = str(syft_tmpdir)
    try:
        output = run_command(
            [
                "syft",
                "scan",
                "--output",
                "template",
                "--template",
                str(SYFT_TEMPLATE),
                f"docker:{image.reference}",
            ],
            CommandEnvironment(variables=variables),
        )
    finally:
        shutil.rmtree(syft_tmpdir, ignore_errors=True)
    if not output.strip():
        raise RuntimeError(f"No output from syft scan of '{image.reference}'")
    return output


def render_section(heading: str, body: str) -> str:
    """Render one section: a blank line, its heading, a blank line, then the body.

    Every section carries its own leading blank line, which is why a heading is followed
    by two of them in the document; the parts are concatenated as they are, so this
    shape is the whole layout.
    """
    return f"\n{IMAGE_HEADING_PREFIX}{heading}\n\n{body}"


def get_committed_section(document: str, image_name: str) -> str | None:
    """Return an image's section of an already generated document.

    Returns it in exactly the shape a fresh scan renders, so that reusing a section and
    rescanning an image are interchangeable.
    """
    heading = f"{IMAGE_HEADING_PREFIX}{image_name}"
    lines = document.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None

    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith(SECTION_HEADING_PREFIXES):
            break
        body.append(line)
    return render_section(image_name, "\n".join(body).strip("\n") + "\n")


def parse_lock(content: str) -> Lock:
    """Read a lock file: a syft version in a comment, then one image per line."""
    syft_version = ""
    keys: dict[str, str] = {}
    for line in content.splitlines():
        if line.startswith(LOCK_SYFT_PREFIX):
            syft_version = line[len(LOCK_SYFT_PREFIX) :].strip()
            continue
        if not line or line.startswith("#"):
            continue
        name, _, key = line.partition(" ")
        keys[name] = key.strip()
    return Lock(syft_version=syft_version, keys=keys)


def read_lock(path: Path) -> Lock:
    """Read the lock, treating a missing one as "nothing is pinned"."""
    if not path.is_file():
        logging.info("No %s: scanning every image", path)
        return Lock(syft_version="", keys={})
    return parse_lock(path.read_text(encoding="utf-8"))


def render_lock(syft_version: str, inputs: Sequence[ImageInputs]) -> str:
    """Render the lock for the images this run documented."""
    lines = [
        LOCK_PREAMBLE,
        f"{LOCK_SYFT_PREFIX}{syft_version}",
        *sorted(f"{image.name} {image.key}" for image in inputs),
    ]
    return "\n".join(lines) + "\n"


def decide_scan(
    inputs: ImageInputs,
    lock: Lock,
    document: str,
    syft_version: str,
    refresh: bool,
) -> ScanDecision:
    """Decide whether an image must be rescanned, and record why."""
    if refresh:
        return ScanDecision(inputs=inputs, scan=True, reason="--refresh was given")
    if lock.syft_version != syft_version:
        return ScanDecision(
            inputs=inputs,
            scan=True,
            reason=f"syft {lock.syft_version or 'unknown'} -> {syft_version}",
        )
    locked_key = lock.key_for(inputs.name)
    if locked_key != inputs.key:
        return ScanDecision(
            inputs=inputs,
            scan=True,
            reason=f"inputs {locked_key or 'unlocked'} -> {inputs.key}",
        )
    if get_committed_section(document, inputs.name) is None:
        return ScanDecision(
            inputs=inputs, scan=True, reason="the document has no such section"
        )
    return ScanDecision(inputs=inputs, scan=False, reason="inputs unchanged")


def get_component_licenses() -> str:
    """The licence file each component checks in beside itself.

    The file is emitted verbatim and followed by a blank line.
    """
    logging.info("Getting: component_licenses")
    sections: list[str] = []
    for licence in sorted(TOPLEVEL_DIR.glob(f"*/{THIRD_PARTY_LICENCES.name}")):
        content = licence.read_text(encoding="utf-8")
        sections.append(render_section(licence.parent.name, f"{content}\n"))
    return "".join(sections)


def get_python_licenses(environment: CommandEnvironment) -> str:
    """The Python dependency tree, as pip-licenses renders it."""
    logging.info("Getting: python_licenses")
    return run_command(
        ["pip-licenses", "--order=license", "--format=markdown"], environment
    )


def get_javascript_licenses(environment: CommandEnvironment) -> str:
    """The JavaScript dependency tree, as license-report renders it."""
    logging.info("Getting: javascript_licenses")
    return run_command(
        [
            "license-report",
            "--package",
            str(FRONTEND_DIR / "package.json"),
            "--output",
            "markdown",
            "--fields",
            "name",
            "--fields",
            "licenseType",
            "--fields",
            "installedVersion",
        ],
        environment,
    )


def get_container_licenses(
    decisions: Sequence[ScanDecision],
    references: Mapping[str, ImageRef],
    environment: CommandEnvironment,
    document: str,
) -> str:
    """Assemble every image's section, scanning only what the lock cannot vouch for."""
    logging.info("Getting: container_licenses")
    sections: list[str] = []
    for decision in decisions:
        name = decision.inputs.name
        if decision.scan:
            reference = references.get(name)
            if reference is None:
                raise RuntimeError(f"Skaffold reported no tag for '{name}'")
            body = scan_image(reference, environment).strip("\n")
            sections.append(render_section(name, body + "\n"))
            continue

        logging.info("Reusing committed section: %s", name)
        section = get_committed_section(document, name)
        if section is None:
            raise RuntimeError(f"No committed section to reuse for '{name}'")
        sections.append(section)
    return "".join(sections)


def render_document(
    component_licenses: str,
    python_licenses: str,
    javascript_licenses: str,
    container_licenses: str,
) -> str:
    """Assemble the whole document from its four generated parts.

    The parts are emitted exactly as the tools produce them, each heading preceded and
    followed by one blank line. Sections bring a leading blank line of their own, so a
    heading that introduces them is followed by two.
    """
    return (
        f"{PREAMBLE}\n"
        "\n## Components\n"
        f"\n{component_licenses}"
        "\n## Python\n"
        f"\n{python_licenses}"
        "\n## JavaScript\n"
        f"\n{javascript_licenses}"
        "\n## Container\n"
        f"\n{container_licenses}"
    )


def generate(refresh: bool, environment: CommandEnvironment) -> None:
    """Regenerate the document, its frontend copy and the lock."""
    logging.info("Running: generate_third_party_licenses")
    document = (
        THIRD_PARTY_LICENCES.read_text(encoding="utf-8")
        if THIRD_PARTY_LICENCES.is_file()
        else ""
    )
    lock = read_lock(THIRD_PARTY_LOCK)
    syft_version = get_syft_version(environment)

    logging.info("Reading the declared images and their licence inputs")
    inputs = load_image_inputs()
    decisions = [
        decide_scan(image, lock, document, syft_version, refresh) for image in inputs
    ]

    to_scan = [decision.inputs for decision in decisions if decision.scan]
    for decision in decisions:
        if decision.scan:
            logging.info("Will scan %s: %s", decision.inputs.name, decision.reason)

    # Images are only built when something has to be scanned, and then only the
    # ones that are: a change that cannot alter any package inventory needs no
    # build, no scan and no skaffold at all.
    references: dict[str, ImageRef] = {}
    if to_scan:
        logging.info("Building %d image(s) to scan", len(to_scan))
        build_images(to_scan, environment)
        references = resolve_references(to_scan, environment)
    else:
        logging.info("No licence input changed: reusing every committed section")

    rendered = render_document(
        get_component_licenses(),
        get_python_licenses(environment),
        get_javascript_licenses(environment),
        get_container_licenses(decisions, references, environment, document),
    )

    THIRD_PARTY_LICENCES.write_text(rendered, encoding="utf-8")
    THIRD_PARTY_LOCK.write_text(render_lock(syft_version, inputs), encoding="utf-8")
    # The frontend serves its own copy of the file. Writing it here keeps the
    # two in step within a single run; left to generate_frontend_static, which
    # runs beside this script rather than after it, the copy trails a pipeline
    # behind.
    shutil.copyfile(THIRD_PARTY_LICENCES, FRONTEND_STATIC_LICENCES)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(
        description="Generate THIRD-PARTY.md, its Frontend copy and THIRD-PARTY.lock."
    )
    parser.add_argument(
        "-m",
        "--minikube",
        action="store_true",
        help="talk to minikube's docker daemon",
    )
    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        help=(
            "rescan every image instead of reusing the sections "
            f"{THIRD_PARTY_LOCK} still vouches for"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="log every command that is run",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[*] %(message)s",
        stream=sys.stderr,
    )

    environment = CommandEnvironment(variables=dict(os.environ))
    if args.minikube:
        environment = get_minikube_environment(environment)

    generate(refresh=args.refresh, environment=environment)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
