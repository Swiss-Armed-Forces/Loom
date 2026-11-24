"""Merges of the generated files, replayed in real git repositories.

The generated files are merged by the keep-ours driver (.gitattributes,
cicd/set_generated_file_merge_driver.sh), and the next pipeline is trusted to correct
whatever the merge left behind. That only holds if the generator notices every
combination git can produce, and git consults no merge driver for a file that only one
side added, changed or deleted. So these tests run real merges with the repository's own
attributes and driver, then a pipeline modelled on generate() that uses the generator's
own decision and writing functions, and check the property that matters: every image's
SBOM describes the image the branch builds.

An image here is a file under images/ standing in for its Dockerfile; its key is a hash
of that file, as the real key hashes the image's inputs.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from git import GitCommandError, Repo

from generate_third_party import (
    IMAGE_PREFIX,
    THIRD_PARTY_LICENCES,
    THIRD_PARTY_LOCK,
    TOPLEVEL_DIR,
    Checkout,
    ScanContext,
    check,
    decide_scan,
    get_committed_section,
    parse_lock,
    parse_sbom,
    read_sbom_key,
    remove_stale_sboms,
    render_lock,
    render_section,
    sbom_path,
    write_sbom,
)
from third_party_inputs import ArtifactDeclaration, ImageInputs

SYFT_VERSION = "1.51.0"
IMAGES_DIR = "images"
BUILT_FROM_COMPONENT = "built-from"
MERGE_DRIVER_SCRIPT = TOPLEVEL_DIR / "cicd" / "set_generated_file_merge_driver.sh"


def _keep_ours_attributes() -> str:
    """The .gitattributes lines of this repository that route files to keep-ours."""
    lines = (TOPLEVEL_DIR / ".gitattributes").read_text(encoding="utf-8").splitlines()
    routed = [line for line in lines if "merge=keep-ours" in line]
    assert any(line.startswith("sbom/") for line in routed)
    return "\n".join(routed) + "\n"


def _name(short: str) -> str:
    return f"{IMAGE_PREFIX}{short}"


def _declared(repo: Repo) -> list[ImageInputs]:
    """The images the checkout declares, keyed by their stand-in Dockerfile."""
    inputs = []
    for dockerfile in sorted(Path(repo.working_dir, IMAGES_DIR).iterdir()):
        content = dockerfile.read_bytes()
        inputs.append(
            ImageInputs(
                declaration=ArtifactDeclaration(
                    name=_name(dockerfile.name),
                    config=Path("skaffold.yaml"),
                    context=Path(IMAGES_DIR),
                    dockerfile=Path(IMAGES_DIR, dockerfile.name),
                    build_args={},
                    target=None,
                    platforms=(),
                ),
                files=(Path(IMAGES_DIR, dockerfile.name),),
                key=f"lic-{hashlib.sha256(content).hexdigest()[:16]}",
            )
        )
    return inputs


def _built_from(repo: Repo, image: ImageInputs) -> str:
    """What a scan of the image would find: the Dockerfile it was built from."""
    return Path(repo.working_dir, image.declaration.dockerfile).read_text(
        encoding="utf-8"
    )


def _scan_result(repo: Repo, image: ImageInputs) -> Bom:
    """A stand-in for a syft scan: one package naming what the image was built from."""
    bom = Bom()
    bom.metadata.component = Component(name=image.name, type=ComponentType.CONTAINER)
    bom.components.add(
        Component(
            name=BUILT_FROM_COMPONENT,
            bom_ref=BUILT_FROM_COMPONENT,
            version=_built_from(repo, image),
            type=ComponentType.LIBRARY,
        )
    )
    return bom


def _read_built_from(sbom: Path) -> str:
    """Read back what _scan_result recorded."""
    packages = [
        component
        for component in parse_sbom(sbom).components
        if component.name == BUILT_FROM_COMPONENT
    ]
    assert len(packages) == 1, f"{sbom} records no scan result"
    return str(packages[0].version)


def _checkout(repo: Repo) -> Checkout:
    """The repository under test, as the generator addresses a working tree."""
    return Checkout(root=Path(repo.working_dir))


def _commit_all(repo: Repo, message: str) -> None:
    repo.git.add("-A")
    repo.git.commit("-m", message, "--allow-empty")


def _set_image(repo: Repo, short: str, content: str | None) -> None:
    """Change an image's inputs; None drops the image."""
    path = Path(repo.working_dir, IMAGES_DIR, short)
    if content is None:
        path.unlink()
    else:
        path.write_text(content, encoding="utf-8")
    _commit_all(repo, f"change {short}")


def _pipeline(repo: Repo, with_sboms: bool = True) -> list[str]:
    """Run what generate() does and commit it; return the images it scanned.

    `with_sboms=False` is the generator before per-image SBOMs existed: the lock and the
    document only.
    """
    checkout = _checkout(repo)
    document = checkout.read_document()
    lock = parse_lock(
        checkout.lock.read_text(encoding="utf-8") if checkout.lock.is_file() else ""
    )
    inputs = _declared(repo)

    context = ScanContext(
        checkout=checkout,
        lock=lock,
        document=document,
        syft_version=SYFT_VERSION,
        refresh=False,
    )
    scanned, sections = [], []
    for image in inputs:
        scan = decide_scan(image, context).scan
        if not with_sboms:
            scan = lock.key_for(image.name) != image.key or (
                get_committed_section(document, image.name) is None
            )
        if scan:
            scanned.append(image.declaration.dockerfile.name)
            body = f"built from {_built_from(repo, image)}\n"
            sections.append(render_section(image.name, body))
            if with_sboms:
                write_sbom(
                    checkout.sbom(image.name), _scan_result(repo, image), image.key
                )
        else:
            section = get_committed_section(document, image.name)
            assert section is not None
            sections.append(section)

    checkout.document.write_text("## Container\n" + "".join(sections), encoding="utf-8")
    checkout.lock.write_text(render_lock(SYFT_VERSION, inputs), encoding="utf-8")
    if with_sboms:
        remove_stale_sboms(inputs, checkout)
    _commit_all(repo, "chore: update generated files")
    return scanned


def _assert_consistent(repo: Repo) -> None:
    """Every SBOM describes the image this checkout builds, under the lock's key."""
    checkout = _checkout(repo)
    lock = parse_lock(checkout.lock.read_text(encoding="utf-8"))
    document = checkout.read_document()
    inputs = _declared(repo)
    for image in inputs:
        sbom = checkout.sbom(image.name)
        assert lock.key_for(image.name) == image.key
        assert read_sbom_key(sbom) == image.key
        built_from = _read_built_from(sbom)
        assert built_from == _built_from(repo, image), image.name
        assert f"built from {built_from}" in (
            get_committed_section(document, image.name) or ""
        )
    expected = {sbom_path(image.name).name for image in inputs}
    assert {path.name for path in checkout.sboms()} == expected


def _merge(repo: Repo, branch: str, into: str) -> None:
    repo.git.checkout(into)
    repo.git.merge(branch, "--no-edit")


@pytest.fixture(name="repo")
def fixture_repo(tmp_path: Path) -> Repo:
    """Main with images a and b, configured the way devenv configures a checkout."""
    hooks_path = tmp_path / "no-hooks"
    hooks_path.mkdir()
    root = tmp_path / "repo"
    (root / IMAGES_DIR).mkdir(parents=True)
    repo = Repo.init(root, initial_branch="main")
    for key, value in [
        ("user.email", "test@example.com"),
        ("user.name", "Test"),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks_path)),
    ]:
        repo.git.config(key, value)
    subprocess.run(["bash", str(MERGE_DRIVER_SCRIPT)], cwd=root, check=True)
    (root / ".gitattributes").write_text(_keep_ours_attributes(), encoding="utf-8")
    (root / IMAGES_DIR / "a").write_text("FROM a:1\n", encoding="utf-8")
    (root / IMAGES_DIR / "b").write_text("FROM b:1\n", encoding="utf-8")
    _commit_all(repo, "initial")
    return repo


def test_a_branch_from_before_sboms_does_not_inherit_mains_sbom(repo: Repo) -> None:
    """The reported case: the branch keeps its lock and takes main's SBOM for a."""
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("main")
    _pipeline(repo)  # the first pipeline with SBOMs: every image gets one

    _merge(repo, "main", into="feature")
    sbom_a = Path(repo.working_dir, sbom_path(_name("a")))
    assert "FROM a:1" in sbom_a.read_text(encoding="utf-8")  # main's, adopted

    assert _pipeline(repo) == ["a"]
    _assert_consistent(repo)


def test_both_sides_rescanned_the_same_image(repo: Repo) -> None:
    """Both changed a: the driver keeps the branch's files, the merged inputs win."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo)
    repo.git.checkout("feature")
    _set_image(repo, "a", "FROM a:1\nRUN feature\n")
    _pipeline(repo)

    with pytest.raises(GitCommandError):
        _merge(repo, "main", into="feature")  # images/a itself conflicts
    Path(repo.working_dir, IMAGES_DIR, "a").write_text(
        "FROM a:2\nRUN feature\n", encoding="utf-8"
    )
    _commit_all(repo, "merge main")

    assert _pipeline(repo) == ["a"]
    _assert_consistent(repo)


def test_each_side_rescanned_a_different_image(repo: Repo) -> None:
    """Main changed a, the branch b: git takes main's SBOM for a without the driver."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo)

    _merge(repo, "main", into="feature")

    assert _pipeline(repo) == ["a"]
    _assert_consistent(repo)


def test_main_added_an_image(repo: Repo) -> None:
    """The branch's lock has never heard of c; main's SBOM for it is not trusted."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "c", "FROM c:1\n")
    _pipeline(repo)

    _merge(repo, "main", into="feature")

    assert _pipeline(repo) == ["c"]
    _assert_consistent(repo)


def test_main_dropped_an_image_the_branch_did_not_touch(repo: Repo) -> None:
    """Git deletes the SBOM; the branch's lock still names b, the next run drops it."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "b", None)
    _pipeline(repo)

    _merge(repo, "main", into="feature")

    assert not _pipeline(repo)
    _assert_consistent(repo)


def test_main_dropped_an_image_the_branch_rescanned(repo: Repo) -> None:
    """Modify/delete stops the merge: it is resolved by hand, not silently."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "b", None)
    _pipeline(repo)

    with pytest.raises(GitCommandError):
        _merge(repo, "main", into="feature")
    repo.git.rm("--quiet", Path(IMAGES_DIR, "b").as_posix())
    repo.git.rm("--quiet", sbom_path(_name("b")).as_posix())
    _commit_all(repo, "merge main: b is gone")

    assert not _pipeline(repo)
    _assert_consistent(repo)


def test_a_branch_merged_back_into_main(repo: Repo) -> None:
    """The other direction: main takes the branch's lock and must not keep its SBOM."""
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("main")
    _pipeline(repo)

    _merge(repo, "feature", into="main")

    assert _pipeline(repo) == ["a"]
    _assert_consistent(repo)


def test_a_branch_rebased_onto_main(repo: Repo) -> None:
    """A rebase replays the branch onto main, so keep-ours keeps main's lock."""
    _pipeline(repo)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo)
    repo.git.checkout("main")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo)

    repo.git.checkout("feature")
    repo.git.rebase("main")

    assert _pipeline(repo) == ["b"]
    _assert_consistent(repo)


@pytest.mark.parametrize("branch_has_sboms", [True, False])
def test_a_merge_without_the_driver(repo: Repo, branch_has_sboms: bool) -> None:
    """A checkout outside devenv merges the generated files line by line.

    Each side changed a different image, so the lock conflicts on neighbouring lines and
    the merge stops; the document and the SBOMs may merge on their own. Resolved the way
    it was before the driver, by keeping the branch's copy, the next pipeline has to
    correct whatever came from the other side.
    """
    repo.git.config("--remove-section", "merge.keep-ours")
    _pipeline(repo, with_sboms=branch_has_sboms)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "b", "FROM b:2\n")
    _pipeline(repo, with_sboms=branch_has_sboms)
    repo.git.checkout("main")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo)

    with pytest.raises(GitCommandError):
        _merge(repo, "main", into="feature")
    conflicted = set(repo.git.diff("--name-only", "--diff-filter=U").split())
    assert THIRD_PARTY_LOCK.name in conflicted
    assert conflicted <= {THIRD_PARTY_LICENCES.name, THIRD_PARTY_LOCK.name}
    repo.git.checkout("--ours", "--", *sorted(conflicted))
    _commit_all(repo, "merge main")

    scanned = _pipeline(repo)
    assert "a" in scanned
    assert ("b" in scanned) is not branch_has_sboms
    _assert_consistent(repo)


def test_a_merge_made_on_the_server_is_caught_by_the_check(repo: Repo) -> None:
    """Main is never regenerated, and the server merges without the driver.

    Only the branch changed the lock, so the merge is clean: main gets the branch's lock
    and keeps its own SBOM for a. No pipeline corrects main, so the check has to say so,
    and to pass again once a branch's pipeline has corrected it.
    """
    checkout = _checkout(repo)
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("-b", "feature")
    _set_image(repo, "a", "FROM a:2\n")
    _pipeline(repo, with_sboms=False)
    repo.git.checkout("main")
    _pipeline(repo)
    assert not check(checkout, _declared(repo), SYFT_VERSION)

    repo.git.config("--remove-section", "merge.keep-ours")
    _merge(repo, "feature", into="main")

    problems = check(checkout, _declared(repo), SYFT_VERSION)
    assert len(problems) == 1
    assert problems[0].startswith(f"{_name('a')}: SBOM ")
    assert _pipeline(repo) == ["a"]
    assert not check(checkout, _declared(repo), SYFT_VERSION)
    _assert_consistent(repo)
