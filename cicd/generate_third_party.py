#!/usr/bin/env python3
"""Generate THIRD-PARTY.md, its Frontend copy, THIRD-PARTY.lock and sbom/.

The document lists every third-party component Loom ships: the licence files
checked in beside each component, the Python and JavaScript dependency trees,
and a syft scan of every container image. The same scan also writes a CycloneDX
SBOM per image to sbom/, so that tools can read what people read in the
document.

Scanning an image is the expensive part, so each image's section is pinned to a
key over the inputs that can change what the scan reports - see
third_party_inputs.py for what those are. While the key is unchanged the
committed section is still the answer and is reused byte-for-byte; only images
whose key moved are rebuilt and rescanned.

That pinning is what keeps the output a function of this repository. Scanning
whatever image a runner happens to hold under a tag does not: two runners hold
images built at different times, answer differently, and - because CI commits
this file - each pipeline then pushes the other one's answer back.

An SBOM is read, edited and written as cyclonedx-python-lib's `Bom`, so that
what this script states about a CycloneDX document is checked by the library's
model rather than by dictionary lookups spelled out here. The serialiser decides
two things no input does - the serial number and, once the image's build-derived
bom-ref is dropped, the image component's bom-ref - and left to it they are
random, so normalise_sbom pins both. render_sbom then validates what it
serialised, because the model implements what it implements: a document it
cannot represent must fail the run rather than be committed as a file no tool
can read.
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from cyclonedx.model import Property
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from cyclonedx.output import make_outputter
from cyclonedx.schema import OutputFormat, SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator
from pydantic import BaseModel, Field

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
SBOM_DIR = Path("sbom")
SBOM_SUFFIX = ".cdx.json"
# The lock key an SBOM was written for, as a CycloneDX property in its metadata.
SBOM_KEY_PROPERTY = "loom:lock-key"
# The layer syft found a package in. Layer digests are not a function of the
# repository: a rebuild of the same inputs produces new ones.
SBOM_LAYER_PROPERTY = re.compile(r"^syft:location:\d+:layerID$")
# The specification every committed SBOM is written in. The model carries no
# version of its own, so this is the one place that decides it.
SBOM_SCHEMA_VERSION = SchemaVersion.V1_7
# Namespace for the serial number each SBOM is given; see normalise_sbom.
SBOM_SERIAL_NAMESPACE = uuid.UUID("3f2f4b3c-1b33-5a8f-9c2e-6d5a1f0c7b24")

IMAGE_PREFIX = "registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/"

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
class Checkout:
    """The working tree the generated files are read from and written to.

    Every path this script reads or writes hangs off `root`, so that what a run acts on
    is an argument rather than the process's working directory.
    """

    root: Path

    @property
    def document(self) -> Path:
        """THIRD-PARTY.md."""
        return self.root / THIRD_PARTY_LICENCES

    @property
    def frontend_document(self) -> Path:
        """The copy of the document the frontend serves."""
        return self.root / FRONTEND_STATIC_LICENCES

    @property
    def lock(self) -> Path:
        """THIRD-PARTY.lock."""
        return self.root / THIRD_PARTY_LOCK

    def sbom(self, image_name: str) -> Path:
        """Where this image's SBOM is committed."""
        return self.root / sbom_path(image_name)

    def sboms(self) -> list[Path]:
        """Every committed SBOM, in a stable order."""
        return sorted((self.root / SBOM_DIR).glob(f"*{SBOM_SUFFIX}"))

    def read_document(self) -> str:
        """The committed document, or empty when no run has written one."""
        if not self.document.is_file():
            return ""
        return self.document.read_text(encoding="utf-8")


@dataclass(frozen=True)
class ScanContext:
    """What every image's decision in one run is made against.

    One value per run, beside the one image a decision is about, so that deciding reads
    nothing a caller did not hand it.
    """

    checkout: Checkout
    lock: Lock
    document: str
    syft_version: str
    refresh: bool


@dataclass(frozen=True)
class CommandEnvironment:
    """Environment for the external tools this script drives."""

    variables: Mapping[str, str]


class SkaffoldBuild(BaseModel):
    """One image `skaffold build --quiet` reports having built."""

    tag: str


class SkaffoldBuildReport(BaseModel):
    """What `skaffold build --quiet` writes to stdout.

    Only the tags are read; a build that reports none is a build that produced none.
    """

    builds: list[SkaffoldBuild] = Field(default_factory=list)


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
    report = SkaffoldBuildReport.model_validate_json(skaffold_output)
    return [ImageRef.parse(build.tag) for build in report.builds]


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


def sbom_path(image_name: str) -> Path:
    """Where an image's SBOM is committed: sbom/<name below the registry path>.

    A name outside the project's registry path would need a naming rule of its own, so
    it is refused rather than given an unreadable file name.
    """
    if not image_name.startswith(IMAGE_PREFIX):
        raise ValueError(f"Image is outside {IMAGE_PREFIX}: '{image_name}'")
    short_name = image_name.removeprefix(IMAGE_PREFIX).replace("/", "-")
    return SBOM_DIR / f"{short_name}{SBOM_SUFFIX}"


def scan_image(
    image: ImageRef, sbom: Path, key: str, environment: CommandEnvironment
) -> str:
    """Scan an image with syft: write its SBOM, and return this document's section.

    The SBOM records `key`, the lock key of the inputs the image was built from.

    Both outputs come from one scan, so the SBOM costs no second export of the
    image. Per-file entries are left out of the scan (`file.metadata.selection`
    none): neither output uses them, and for the larger images they would make
    the SBOM many times the size of the package list it exists to carry.

    syft exports the image to a tar under TMPDIR before reading it, and these
    images run to several gigabytes each. The directory is therefore private to
    this scan and removed as soon as it is done: a run that scans every image -
    a first run, or one after `--refresh` - otherwise needs disk for all of
    them at once, and a runner that fills up fails the whole job.

    syft does not always report failure through its exit status - on SIGINT it
    exits 0 with no output - so empty output is treated as the failure it is,
    and so is an SBOM that was not written.
    """
    logging.info("Scanning image: %s", image.reference)
    variables = dict(environment.variables)
    # Not /tmp, which is RAM here, and not the system default for the same reason.
    syft_tmpdir = Path(tempfile.mkdtemp(dir=Path.cwd(), prefix=".syft-tmp."))
    variables["TMPDIR"] = str(syft_tmpdir)
    variables["SYFT_FILE_METADATA_SELECTION"] = "none"
    raw_sbom = syft_tmpdir / "sbom.cdx.json"
    try:
        output = run_command(
            [
                "syft",
                "scan",
                "--output",
                "template",
                "--template",
                str(SYFT_TEMPLATE),
                "--output",
                f"cyclonedx-json={raw_sbom}",
                f"docker:{image.reference}",
            ],
            CommandEnvironment(variables=variables),
        )
        if not output.strip():
            raise RuntimeError(f"No output from syft scan of '{image.reference}'")
        if not raw_sbom.is_file():
            raise RuntimeError(f"syft wrote no SBOM for '{image.reference}'")
        scanned = parse_sbom(raw_sbom)
    finally:
        shutil.rmtree(syft_tmpdir, ignore_errors=True)

    write_sbom(sbom, scanned, key)
    return output


def parse_sbom(path: Path) -> Bom:
    """Read a CycloneDX document into the typed model.

    A file the model cannot read raises: something other than this generator wrote it,
    and rescanning over it would hide that.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error
    try:
        # cyclonedx-python-lib injects from_json through a class decorator, so
        # mypy sees no such attribute on Bom.
        parsed = Bom.from_json(document)  # type: ignore[attr-defined]
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path} is not a CycloneDX document: {error}") from error
    if parsed is None:
        raise ValueError(f"{path} is not a CycloneDX document")
    return parsed


def image_component(bom: Bom) -> Component:
    """The component the SBOM describes, which for a syft image scan is the image."""
    image = bom.metadata.component
    if image is None:
        raise ValueError("The SBOM describes no component")
    return image


def normalise_sbom(bom: Bom, key: str) -> None:
    """Pin everything a rebuild of the same inputs would otherwise move.

    The SBOM is committed and only rewritten when its lock key changes, so it may state
    only what follows from the inputs the key covers, and it must come out of the
    serialiser the same way every time.

    The scan's timestamp and the image's version - its Skaffold tag, a hash of the whole
    build context - move with changes the key ignores, and the layer a package was found
    in is a digest the build produces. None of them survive.

    Identity is the half the serialiser decides rather than syft: left alone it mints a
    random serial number, and a random bom-ref for the image once the build-derived one
    is gone. Both are derived here instead, from the image and the key - the inputs the
    file already describes - so two runs over one image agree. The model holds a
    dependency's ref as the component's own BomRef, so renaming the image's bom-ref
    renames it everywhere it is referenced.

    `key` is recorded as SBOM_KEY_PROPERTY, so that sbom_mismatch can tell which inputs
    the file describes; see there for why the lock cannot.
    """
    image = image_component(bom)
    image.version = None
    image.bom_ref.value = image.name
    # cyclonedx-python-lib types the property as datetime, but the serialiser
    # leaves an unset one out, which is what a committed SBOM needs.
    bom.metadata.timestamp = None  # type: ignore[assignment]
    bom.serial_number = uuid.uuid5(SBOM_SERIAL_NAMESPACE, f"{image.name}:{key}")

    for component in bom.components:
        # The serialiser mints a random bom-ref for a component that carries none,
        # which would rewrite this file on every run.
        if not component.bom_ref.value:
            raise ValueError(f"A component carries no bom-ref: '{component.name}'")
        for prop in list(component.properties):
            if SBOM_LAYER_PROPERTY.match(prop.name):
                component.properties.remove(prop)

    for prop in list(bom.metadata.properties):
        if prop.name == SBOM_KEY_PROPERTY:
            bom.metadata.properties.remove(prop)
    bom.metadata.properties.add(Property(name=SBOM_KEY_PROPERTY, value=key))


def render_sbom(bom: Bom) -> str:
    """Serialise an SBOM, and refuse to hand back one the specification rejects.

    The model implements what it implements, and this file is committed for tools to
    read rather than for people, so a document it serialises into something invalid has
    to fail the run instead of reaching sbom/.
    """
    rendered = make_outputter(
        bom, OutputFormat.JSON, SBOM_SCHEMA_VERSION
    ).output_as_string(indent=2)
    error = JsonStrictValidator(SBOM_SCHEMA_VERSION).validate_str(rendered)
    if error is not None:
        raise ValueError(
            f"The SBOM is not valid CycloneDX {SBOM_SCHEMA_VERSION.to_version()}:"
            f" {error}"
        )
    return rendered if rendered.endswith("\n") else rendered + "\n"


def write_sbom(path: Path, bom: Bom, key: str) -> None:
    """Normalise an SBOM for the inputs `key` covers and commit it."""
    normalise_sbom(bom, key)
    rendered = render_sbom(bom)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def read_sbom_key(path: Path) -> str | None:
    """The lock key a committed SBOM was written for; None if it records none."""
    for prop in parse_sbom(path).metadata.properties:
        if prop.name == SBOM_KEY_PROPERTY:
            return prop.value
    return None


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


def sbom_mismatch(inputs: ImageInputs, checkout: Checkout) -> str | None:
    """Why the committed SBOM cannot be reused for `inputs`; None if it can.

    It has to record the key the lock vouches for: a merge can leave an
    image's SBOM and the lock from different sides, because git runs the
    keep-ours driver only for a file both sides changed, and a checkout
    without the driver merges the lock line by line. Such an SBOM
    describes an image this branch never built.
    """
    path = checkout.sbom(inputs.name)
    if not path.is_file():
        return "no SBOM is committed"
    sbom_key = read_sbom_key(path)
    if sbom_key != inputs.key:
        return f"SBOM {sbom_key or 'unkeyed'} -> {inputs.key}"
    return None


def decide_scan(inputs: ImageInputs, context: ScanContext) -> ScanDecision:
    """Decide whether an image must be rescanned, and record why."""
    if context.refresh:
        return ScanDecision(inputs=inputs, scan=True, reason="--refresh was given")
    locked_syft = context.lock.syft_version
    if locked_syft != context.syft_version:
        return ScanDecision(
            inputs=inputs,
            scan=True,
            reason=f"syft {locked_syft or 'unknown'} -> {context.syft_version}",
        )
    locked_key = context.lock.key_for(inputs.name)
    if locked_key != inputs.key:
        return ScanDecision(
            inputs=inputs,
            scan=True,
            reason=f"inputs {locked_key or 'unlocked'} -> {inputs.key}",
        )
    if get_committed_section(context.document, inputs.name) is None:
        return ScanDecision(
            inputs=inputs, scan=True, reason="the document has no such section"
        )
    reason = sbom_mismatch(inputs, context.checkout)
    if reason is not None:
        return ScanDecision(inputs=inputs, scan=True, reason=reason)
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
    checkout: Checkout,
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
            body = scan_image(
                reference, checkout.sbom(name), decision.inputs.key, environment
            ).strip("\n")
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


def remove_stale_sboms(inputs: Sequence[ImageInputs], checkout: Checkout) -> None:
    """Delete the SBOM of every image that is no longer declared.

    The document and the lock are rewritten whole, so a dropped image leaves them on its
    own; an SBOM is a file of its own and has to be removed.
    """
    for path in undeclared_sboms(inputs, checkout):
        logging.info("Removing SBOM of an image no longer declared: %s", path)
        path.unlink()


def undeclared_sboms(inputs: Sequence[ImageInputs], checkout: Checkout) -> list[Path]:
    """The committed SBOMs that belong to no declared image."""
    expected = {sbom_path(image.name).name for image in inputs}
    return [path for path in checkout.sboms() if path.name not in expected]


def check(
    checkout: Checkout, inputs: Sequence[ImageInputs], syft_version: str
) -> list[str]:
    """What a run would rescan or remove, found without building or writing anything.

    Empty when the lock, the document and the SBOMs all describe the
    images this checkout declares. The pipeline runs this where it does
    not regenerate: on main and on tags, where a merge made on the
    server, which uses no merge driver, can leave them from different
    sides with no later run to correct it.
    """
    context = ScanContext(
        checkout=checkout,
        lock=read_lock(checkout.lock),
        document=checkout.read_document(),
        syft_version=syft_version,
        refresh=False,
    )
    problems = []
    for image in inputs:
        decision = decide_scan(image, context)
        if decision.scan:
            problems.append(f"{image.name}: {decision.reason}")
    problems.extend(
        f"{path}: the SBOM of an image no longer declared"
        for path in undeclared_sboms(inputs, checkout)
    )
    return problems


def generate(
    checkout: Checkout,
    inputs: Sequence[ImageInputs],
    syft_version: str,
    refresh: bool,
    environment: CommandEnvironment,
) -> None:
    """Regenerate the document, its frontend copy, the lock and the SBOMs."""
    logging.info("Running: generate_third_party_licenses")
    document = checkout.read_document()
    context = ScanContext(
        checkout=checkout,
        lock=read_lock(checkout.lock),
        document=document,
        syft_version=syft_version,
        refresh=refresh,
    )
    decisions = [decide_scan(image, context) for image in inputs]

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
        get_container_licenses(decisions, references, environment, document, checkout),
    )

    checkout.document.write_text(rendered, encoding="utf-8")
    checkout.lock.write_text(render_lock(syft_version, inputs), encoding="utf-8")
    remove_stale_sboms(inputs, checkout)
    # The frontend serves its own copy of the file. Writing it here keeps the
    # two in step within a single run; left to generate_frontend_static, which
    # runs beside this script rather than after it, the copy trails a pipeline
    # behind.
    shutil.copyfile(checkout.document, checkout.frontend_document)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate THIRD-PARTY.md, its Frontend copy, THIRD-PARTY.lock and sbom/."
        )
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
        "-c",
        "--check",
        action="store_true",
        help=(
            "write nothing: exit 1 and say why if a run would rescan an image "
            "or remove an SBOM"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="log every command that is run",
    )
    args = parser.parse_args(argv)
    if args.check and args.refresh:
        parser.error("--check and --refresh cannot be combined")
    return args


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

    # What a run acts on is assembled here and passed down, so that everything
    # below decides from its arguments alone.
    checkout = Checkout(root=Path.cwd())
    syft_version = get_syft_version(environment)
    logging.info("Reading the declared images and their licence inputs")
    inputs = load_image_inputs()

    if args.check:
        problems = check(checkout, inputs, syft_version)
        for problem in problems:
            logging.error("Out of date: %s", problem)
        if problems:
            logging.error("Run generate-third-party on a branch and merge the result")
            return 1
        logging.info("The lock, the document and the SBOMs match the declared images")
        return 0

    generate(checkout, inputs, syft_version, args.refresh, environment)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
