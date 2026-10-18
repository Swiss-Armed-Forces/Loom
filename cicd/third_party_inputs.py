"""The licence-relevant inputs of each container image, and the key they hash to.

A syft scan reports an image's *package inventory*: the OS packages, Python
site-packages and JavaScript modules it ships. Only a small part of what goes
into building an image can change that inventory, and the rest - application
source, configuration, static assets - cannot. Keying the generated document on
the whole build context therefore invalidates it on changes that provably
cannot alter a single byte of the answer.

This module declares the narrow set instead. An image's key covers:

* the arguments its Skaffold configuration passes to the build, as written
  rather than as resolved. `DOCKER_REGISTRY` expands to a dependency-proxy
  prefix in CI and to `docker.io` elsewhere, so hashing the resolved value
  would make the key depend on where it was computed - the very thing the lock
  exists to prevent,
* its Dockerfile, which is where every `FROM` in this repository pins its base
  image by digest, and where the apt, apk and plugin versions are pinned too,
* whatever `third_party_inputs.yaml` adds for that image: the dependency
  lockfiles and installer scripts that live outside the Dockerfile.

Separated from generate_third_party.py in the same way check_resources_model.py
is separated from check_resources.py, so neither file has to be read whole to
follow the other.
"""

import hashlib
import json
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
TOPLEVEL_DIR = SCRIPT_DIR.parent

INPUTS_MANIFEST = SCRIPT_DIR / "third_party_inputs.yaml"

# traefik and keda first, then the root configuration. This is the order the
# images are documented in, and the document is rewritten whole if it changes.
SKAFFOLD_CONFIGS = (
    TOPLEVEL_DIR / "traefik" / "skaffold.yaml",
    TOPLEVEL_DIR / "keda" / "skaffold.yaml",
    TOPLEVEL_DIR / "skaffold.yaml",
)

KEY_PREFIX = "lic-"

GLOB_CHARACTERS = ("*", "?", "[")

COPY_INSTRUCTIONS = ("COPY", "ADD")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArtifactDeclaration:
    """One image as a Skaffold configuration declares it.

    `config` is the configuration it was declared in, which is what decides how the
    image is built when it does have to be scanned.
    """

    name: str
    config: Path
    context: Path
    dockerfile: Path
    build_args: Mapping[str, str]
    target: str | None
    platforms: tuple[str, ...]


@dataclass(frozen=True)
class ManifestEntry:
    """What an image declares beyond its Dockerfile.

    `files` are repo-relative paths or globs whose content can change the package
    inventory. `not_keyed` names the `COPY` and `ADD` sources deliberately left out
    of the key - application source, configuration, static assets, or a directory
    whose inventory-determining contents are listed in `files` instead. It buys
    nothing at runtime and exists so that find_unclassified_copy_sources can tell
    "this was considered and does not matter" from "nobody has looked at this yet".
    """

    files: tuple[str, ...]
    not_keyed: tuple[str, ...]


@dataclass(frozen=True)
class InputManifest:
    """Every image's declaration, keyed by the image name Skaffold uses."""

    entries: Mapping[str, ManifestEntry]

    def entry_for(self, image_name: str) -> ManifestEntry:
        """The entry for an image, which every image is required to have."""
        entry = self.entries.get(image_name)
        if entry is None:
            raise KeyError(
                f"'{image_name}' has no entry in {INPUTS_MANIFEST.name}. Add one - "
                "an image without a declaration cannot be keyed, and would be "
                "documented from whatever happened to be committed."
            )
        return entry


@dataclass(frozen=True)
class ImageInputs:
    """An image's licence-relevant inputs and the key they hash to."""

    declaration: ArtifactDeclaration
    files: tuple[Path, ...]
    key: str

    @property
    def name(self) -> str:
        """The image name, which is what the lock and the document are keyed by."""
        return self.declaration.name


def load_artifacts() -> list[ArtifactDeclaration]:
    """Read every image out of the Skaffold configurations, in document order.

    The configurations are read as data rather than through `skaffold build
    --dry-run`, which is what keeps this off the critical path: a pipeline with
    nothing to scan then needs no skaffold, no docker daemon and no build context
    hashing at all.

    Only the `prod` profile is ever generated, and in all three configurations that
    profile carries no patches - production is the default - so the artifacts are
    taken as they are declared.
    """
    artifacts: list[ArtifactDeclaration] = []
    for config in SKAFFOLD_CONFIGS:
        document = yaml.safe_load(config.read_text(encoding="utf-8"))
        base = config.parent
        for artifact in document["build"]["artifacts"]:
            context = (base / artifact.get("context", ".")).resolve()
            docker = artifact.get("docker", {})
            dockerfile = (context / docker.get("dockerfile", "Dockerfile")).resolve()
            artifacts.append(
                ArtifactDeclaration(
                    name=artifact["image"],
                    config=config,
                    context=context.relative_to(TOPLEVEL_DIR),
                    dockerfile=dockerfile.relative_to(TOPLEVEL_DIR),
                    build_args=dict(docker.get("buildArgs") or {}),
                    target=docker.get("target"),
                    platforms=tuple(artifact.get("platforms") or ()),
                )
            )
    return artifacts


def parse_manifest(content: str) -> InputManifest:
    """Read the manifest, defaulting both lists so an empty entry can stay empty."""
    document = yaml.safe_load(content) or {}
    entries: dict[str, ManifestEntry] = {}
    for name, entry in (document.get("images") or {}).items():
        entry = entry or {}
        entries[name] = ManifestEntry(
            files=tuple(entry.get("files") or ()),
            not_keyed=tuple(entry.get("not_keyed") or ()),
        )
    return InputManifest(entries=entries)


def load_manifest(path: Path = INPUTS_MANIFEST) -> InputManifest:
    """Read the manifest from disk."""
    return parse_manifest(path.read_text(encoding="utf-8"))


def resolve_files(pattern: str) -> list[Path]:
    """Resolve one manifest pattern to the repo-relative files it names.

    A literal path that does not exist is an error: it is almost always a file that
    was renamed, and silently dropping it from the key is how an image stops being
    rescanned when its dependencies change. A glob is allowed to match nothing,
    because a directory legitimately empties out.
    """
    if any(character in pattern for character in GLOB_CHARACTERS):
        return sorted(
            match.relative_to(TOPLEVEL_DIR) for match in TOPLEVEL_DIR.glob(pattern)
        )
    path = TOPLEVEL_DIR / pattern
    if not path.is_file():
        raise FileNotFoundError(
            f"{INPUTS_MANIFEST.name} names '{pattern}', which does not exist"
        )
    return [Path(pattern)]


def compute_inputs(
    declaration: ArtifactDeclaration, entry: ManifestEntry
) -> ImageInputs:
    """Hash an image's declaration and inputs into the key the lock records."""
    files = [declaration.dockerfile]
    for pattern in entry.files:
        files.extend(resolve_files(pattern))
    files = sorted(set(files))

    payload = {
        "build_args": dict(declaration.build_args),
        "target": declaration.target,
        "platforms": list(declaration.platforms),
        "files": [
            {
                "path": path.as_posix(),
                "sha256": (
                    hashlib.sha256((TOPLEVEL_DIR / path).read_bytes()).hexdigest()
                ),
            }
            for path in files
        ],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ImageInputs(
        declaration=declaration, files=tuple(files), key=f"{KEY_PREFIX}{digest}"
    )


def load_image_inputs() -> list[ImageInputs]:
    """Every image the deployment builds, with the key its inputs hash to."""
    manifest = load_manifest()
    return [
        compute_inputs(declaration, manifest.entry_for(declaration.name))
        for declaration in load_artifacts()
    ]


def get_copy_sources(dockerfile: Path) -> list[str]:
    """The context-relative sources every `COPY` and `ADD` in a Dockerfile reads.

    `COPY --from=<stage>` is excluded: it reads from an earlier build stage rather than
    from the build context, so no file in this repository backs it.
    """
    text = (TOPLEVEL_DIR / dockerfile).read_text(encoding="utf-8")
    sources: list[str] = []
    for instruction in _join_continuations(text):
        tokens = shlex.split(instruction, comments=True)
        if not tokens or tokens[0].upper() not in COPY_INSTRUCTIONS:
            continue
        arguments = tokens[1:]
        if any(argument.startswith("--from=") for argument in arguments):
            continue
        arguments = [
            argument for argument in arguments if not argument.startswith("--")
        ]
        # The last argument is the destination inside the image.
        sources.extend(arguments[:-1])
    return sources


def _join_continuations(text: str) -> list[str]:
    """Fold backslash-continued Dockerfile lines into one instruction each."""
    instructions: list[str] = []
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            current += line[:-1] + " "
            continue
        instructions.append(current + line)
        current = ""
    if current:
        instructions.append(current)
    return instructions


def find_unclassified_copy_sources(
    declarations: Sequence[ArtifactDeclaration], manifest: InputManifest
) -> list[str]:
    """Report every `COPY` source that the manifest neither keys nor dismisses.

    This is the one hole the scheme has: an installer script added to a Dockerfile
    but not to `files` would leave the image keyed on inputs that no longer describe
    it, and the document would go stale with nothing to show for it. Requiring every
    source to be classified turns that into a failing test.

    A directory does not inherit coverage from a keyed file inside it. `common/`
    contains `poetry.lock`, but it also contains everything else, and treating the
    one as vouching for the other is exactly the inference that would hide the next
    installer script.
    """
    unclassified: list[str] = []
    for declaration in declarations:
        entry = manifest.entry_for(declaration.name)
        keyed = {
            path.as_posix()
            for pattern in entry.files
            for path in resolve_files(pattern)
        }
        for source in get_copy_sources(declaration.dockerfile):
            if source in entry.not_keyed:
                continue
            resolved = (declaration.context / source).as_posix().rstrip("/")
            if resolved in keyed:
                continue
            unclassified.append(f"{declaration.name}: {source}")
    return unclassified
