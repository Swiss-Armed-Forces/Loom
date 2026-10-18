"""Unit tests for the licence keys THIRD-PARTY.lock records.

Two of these hold the manifest to the Skaffold configurations rather than to a fixture,
because the failure they guard against is silent: an image or an installer script that
nobody declares does not break a build, it just leaves the generated licence document
describing something the repository no longer ships.
"""

from pathlib import Path

import pytest

from third_party_inputs import (
    ArtifactDeclaration,
    InputManifest,
    ManifestEntry,
    compute_inputs,
    find_unclassified_copy_sources,
    get_copy_sources,
    load_artifacts,
    load_image_inputs,
    load_manifest,
    parse_manifest,
    resolve_files,
)

BACKEND_IMAGES = (
    "registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/api",
    "registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/worker",
    "registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/crawler",
)


@pytest.fixture(name="artifacts")
def fixture_artifacts() -> list[ArtifactDeclaration]:
    """Every image the Skaffold configurations declare."""
    return load_artifacts()


@pytest.fixture(name="manifest")
def fixture_manifest() -> InputManifest:
    """The committed input manifest."""
    return load_manifest()


def test_every_declared_image_has_a_manifest_entry(
    artifacts: list[ArtifactDeclaration], manifest: InputManifest
) -> None:
    """An image nobody declared cannot be keyed, and would be documented blind."""
    declared = {artifact.name for artifact in artifacts}

    assert declared == set(manifest.entries)


def test_every_copy_source_is_classified(
    artifacts: list[ArtifactDeclaration], manifest: InputManifest
) -> None:
    """The one hole in the scheme: an installer the manifest does not know about.

    Adding `COPY install-something.sh` without keying it leaves the image pinned to
    inputs that no longer describe what it ships.
    """
    unclassified = find_unclassified_copy_sources(artifacts, manifest)

    assert not unclassified, (
        "cicd/third_party_inputs.yaml does not classify these COPY sources. Add each "
        "to `files` if it can change the image's packages, or to `not_keyed` if it "
        f"carries source, configuration or assets: {unclassified}"
    )


def test_the_images_are_declared_in_document_order(
    artifacts: list[ArtifactDeclaration],
) -> None:
    """Section order is this order; changing it rewrites the whole document."""
    names = [artifact.name.rsplit("/loom/", 1)[-1] for artifact in artifacts]

    assert names[:4] == [
        "traefik",
        "kedacore/keda",
        "kedacore/keda-metrics-apiserver",
        "api",
    ]


def test_a_key_is_stable_across_runs() -> None:
    """A key that moved on its own would regenerate the document every pipeline."""
    assert [image.key for image in load_image_inputs()] == [
        image.key for image in load_image_inputs()
    ]


def test_every_key_is_distinct() -> None:
    """Two images sharing a key is how a ROCm runtime got documented as CUDA.

    Skaffold's input digest covers the build context but not the build arguments,
    so ollama-runtime-nvidia and ollama-runtime-rocm - one context, one Dockerfile,
    different GPU_VARIANT - used to hash identically.
    """
    keys = [image.key for image in load_image_inputs()]

    assert len(set(keys)) == len(keys)


def test_no_application_source_is_keyed() -> None:
    """The property this whole scheme exists for.

    A key covers Dockerfiles, dependency manifests and installer scripts. The
    moment it covers a `.py` or a `.tsx`, an ordinary code change starts rewriting
    the lock again - which is the conflict and the wasted rebuild this replaced.
    """
    source_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".php", ".vue"}

    keyed = {path.as_posix() for image in load_image_inputs() for path in image.files}

    assert not {path for path in keyed if Path(path).suffix in source_suffixes}


def test_declaring_one_more_input_moves_the_key() -> None:
    """A key covers what the manifest declares, so adding to it has to show."""
    declaration = next(
        artifact for artifact in load_artifacts() if artifact.name.endswith("/api")
    )

    with_lockfile = compute_inputs(
        declaration, ManifestEntry(files=("backend/common/poetry.lock",), not_keyed=())
    )
    without_lockfile = compute_inputs(
        declaration, ManifestEntry(files=(), not_keyed=())
    )

    assert with_lockfile.key != without_lockfile.key


def test_build_arguments_are_part_of_the_key() -> None:
    """GPU_VARIANT selects the base image, so it has to reach the key."""
    nvidia, rocm = (
        image
        for image in load_image_inputs()
        if image.name.endswith(("ollama-runtime-nvidia", "ollama-runtime-rocm"))
    )

    assert nvidia.declaration.dockerfile == rocm.declaration.dockerfile
    assert nvidia.key != rocm.key


def test_the_backend_images_are_keyed_on_their_lockfiles() -> None:
    """Common is a path dependency, so its lockfile ships in all three images."""
    by_name = {image.name: image for image in load_image_inputs()}

    for name in BACKEND_IMAGES:
        files = {path.as_posix() for path in by_name[name].files}
        assert "backend/common/poetry.lock" in files


def test_a_missing_literal_path_is_an_error() -> None:
    """A renamed file silently leaving the key is how an image stops rescanning."""
    with pytest.raises(FileNotFoundError):
        resolve_files("backend/common/poetry.lock.gone")


def test_a_glob_may_match_nothing() -> None:
    """A directory legitimately empties out; that is not a manifest mistake."""
    assert resolve_files("backend/common/*.gone") == []


def test_copy_sources_skip_earlier_build_stages() -> None:
    """`COPY --from=build` reads a stage, so no file in this repository backs it."""
    sources = get_copy_sources(Path("Frontend/Dockerfile"))

    assert "nginx.conf" in sources
    assert not [source for source in sources if source.startswith("/code/dist")]


def test_copy_sources_survive_line_continuations() -> None:
    """The frontend copies its manifests across several continued lines."""
    sources = get_copy_sources(Path("Frontend/Dockerfile"))

    assert {"package.json", "pnpm-lock.yaml", ".npmrc"} <= set(sources)


def test_an_image_without_a_manifest_entry_is_rejected() -> None:
    """Failing closed is the point: an unknown image must not be keyed silently."""
    manifest = parse_manifest("images: {}")

    with pytest.raises(KeyError):
        manifest.entry_for("example/image")


def test_an_empty_entry_keys_the_dockerfile_alone() -> None:
    """Most images pin everything in their Dockerfile and declare nothing else."""
    declaration = next(
        artifact for artifact in load_artifacts() if artifact.name.endswith("/alpine")
    )

    inputs = compute_inputs(declaration, ManifestEntry(files=(), not_keyed=()))

    assert inputs.files == (Path("alpine/Dockerfile"),)
