"""Unit tests for the THIRD-PARTY.md generator.

The important one is test_the_committed_document_round_trips: it decomposes the
real committed document into the parts the generator assembles, reuses every
image section exactly as a pipeline with an unchanged lock would, and asserts
the result is the committed file byte-for-byte.

That is the property the whole design rests on. If reuse and a fresh scan do
not render identically, every pipeline regenerates the file, commits it, and
starts another one - which is the loop this generator exists to end.
"""

from pathlib import Path

import pytest
from cyclonedx.model import Property
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType

from generate_third_party import (
    IMAGE_PREFIX,
    SBOM_KEY_PROPERTY,
    THIRD_PARTY_LICENCES,
    TOPLEVEL_DIR,
    Checkout,
    ImageRef,
    Lock,
    ScanContext,
    check,
    decide_scan,
    get_committed_section,
    get_image_tags,
    image_component,
    main,
    parse_lock,
    parse_sbom,
    read_sbom_key,
    remove_stale_sboms,
    render_document,
    render_lock,
    render_sbom,
    render_section,
    sbom_path,
    write_sbom,
)
from third_party_inputs import ArtifactDeclaration, ImageInputs, load_image_inputs

SYFT_VERSION = "1.51.0"
TIKA_NAME = "registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/tika"
TIKA_KEY = "lic-098abbec50f6b3bf0c4a007c32988a67103ec90b3158365e4d84466ee62cb0fd"


def _image_inputs(name: str, key: str) -> ImageInputs:
    """A synthetic image, so the decision tests need no repository on disk."""
    return ImageInputs(
        declaration=ArtifactDeclaration(
            name=name,
            config=Path("skaffold.yaml"),
            context=Path("tika-server"),
            dockerfile=Path("tika-server/Dockerfile"),
            build_args={},
            target=None,
            platforms=(),
        ),
        files=(Path("tika-server/Dockerfile"),),
        key=key,
    )


TIKA = _image_inputs(TIKA_NAME, TIKA_KEY)


def _sbom(name: str = TIKA_NAME) -> Bom:
    """An SBOM of an image, as syft's scan of one arrives: a container and no
    packages."""
    bom = Bom()
    bom.metadata.component = Component(name=name, type=ComponentType.CONTAINER)
    return bom


def _split_once(text: str, separator: str) -> tuple[str, str]:
    """Split on a separator that must occur, returning both sides."""
    before, found, after = text.partition(separator)
    assert found, f"missing separator: {separator!r}"
    return before, after


@pytest.fixture(name="document")
def fixture_document() -> str:
    """The committed THIRD-PARTY.md, which previous runs generated."""
    return (TOPLEVEL_DIR / THIRD_PARTY_LICENCES).read_text(encoding="utf-8")


def test_the_committed_document_round_trips(document: str) -> None:
    """Reusing every section must reproduce the committed file exactly."""
    _, after_components = _split_once(document, "## Components\n\n")
    components, after_python_heading = _split_once(after_components, "\n## Python\n\n")
    python, after_javascript_heading = _split_once(
        after_python_heading, "\n## JavaScript\n\n"
    )
    javascript, _ = _split_once(after_javascript_heading, "\n## Container\n\n")

    image_names = [
        line.removeprefix("### ")
        for line in document.splitlines()
        if line.startswith("### registry.")
    ]
    assert image_names, "the committed document lists no images"

    containers = ""
    for image_name in image_names:
        section = get_committed_section(document, image_name)
        assert section is not None, f"no committed section for {image_name}"
        containers += section

    assert render_document(components, python, javascript, containers) == document


def test_a_section_is_rendered_the_same_whether_scanned_or_reused() -> None:
    """A reused section and a freshly scanned one have to be interchangeable."""
    body = "| Package | Version |\n| ------- | ------- |\n| curl | 8.18.0 |\n"
    scanned = render_section("some/image", body)
    document = f"## Container\n{scanned}\n### other/image\n\nbody\n"

    assert get_committed_section(document, "some/image") == scanned


def test_a_missing_section_is_reported_as_missing() -> None:
    """The lock may name an image the document does not describe."""
    assert get_committed_section("## Container\n\n### a/b\n\nbody\n", "c/d") is None


def test_the_last_section_of_a_document_is_extracted() -> None:
    """The final image has no following heading to stop at."""
    body = "| Package |\n| ------- |\n"
    document = f"## Container\n{render_section('a/b', body)}"

    assert get_committed_section(document, "a/b") == render_section("a/b", body)


def test_an_image_reference_splits_on_its_last_colon() -> None:
    """A registry may carry a port, which is a colon the tag does not own."""
    reference = "registry.example.com:5000/loom/worker:prod-abc123"

    assert ImageRef.parse(reference) == ImageRef(
        name="registry.example.com:5000/loom/worker", tag="prod-abc123"
    )
    assert ImageRef.parse(reference).reference == reference


def test_an_untagged_image_reference_is_rejected() -> None:
    """Skaffold always reports a tag; anything else is a parsing mistake."""
    with pytest.raises(ValueError):
        ImageRef.parse("registry.example.com/loom/worker")


def test_the_images_skaffold_reports_building_are_read_from_its_json() -> None:
    """Only the tags are read, and a report naming no build is not an error."""
    output = (
        '{"builds":[{"imageName":"registry.example.com/loom/worker",'
        '"tag":"registry.example.com/loom/worker:prod-abc123"},'
        '{"imageName":"registry.example.com/loom/api",'
        '"tag":"registry.example.com/loom/api:prod-def456"}]}'
    )

    assert get_image_tags(output) == [
        ImageRef(name="registry.example.com/loom/worker", tag="prod-abc123"),
        ImageRef(name="registry.example.com/loom/api", tag="prod-def456"),
    ]
    assert get_image_tags("{}") == []


def test_the_lock_round_trips() -> None:
    """What the generator writes is what it reads back."""
    rendered = render_lock(SYFT_VERSION, [TIKA])

    assert parse_lock(rendered) == Lock(
        syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key}
    )


def test_the_lock_is_sorted(tmp_path: Path) -> None:
    """A stable order keeps the diff of a key change to that key."""
    images = [
        _image_inputs("c/image", "lic-3"),
        _image_inputs("a/image", "lic-1"),
        _image_inputs("b/image", "lic-2"),
    ]
    lock_file = tmp_path / "THIRD-PARTY.lock"
    lock_file.write_text(render_lock(SYFT_VERSION, images), encoding="utf-8")

    entries = [
        line
        for line in lock_file.read_text(encoding="utf-8").splitlines()
        if not line.startswith("#")
    ]
    assert entries == ["a/image lic-1", "b/image lic-2", "c/image lic-3"]


def _write_unkeyed_sbom(path: Path) -> None:
    """Commit an SBOM that records no lock key, which write_sbom cannot produce.

    Rendered rather than written, because writing normalises, and normalising is what
    records the key.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_sbom(_sbom()), encoding="utf-8")


def _checkout_with_tika(root: Path) -> Checkout:
    """A checkout whose sbom/ holds a committed SBOM for TIKA."""
    checkout = Checkout(root=root)
    write_sbom(checkout.sbom(TIKA.name), _sbom(), TIKA.key)
    return checkout


def _document_with_tika() -> str:
    return f"## Container\n{render_section(TIKA.name, 'body\n')}"


def _context(
    checkout: Checkout,
    lock: Lock,
    document: str | None = None,
    refresh: bool = False,
) -> ScanContext:
    """What one run decides against, with TIKA's own document by default."""
    return ScanContext(
        checkout=checkout,
        lock=lock,
        document=_document_with_tika() if document is None else document,
        syft_version=SYFT_VERSION,
        refresh=refresh,
    )


def test_an_unchanged_key_is_reused(tmp_path: Path) -> None:
    """The whole point: a key the lock vouches for is not scanned again."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})

    decision = decide_scan(TIKA, _context(_checkout_with_tika(tmp_path), lock))

    assert not decision.scan


@pytest.mark.parametrize(
    "lock,refresh,expected_reason",
    [
        (Lock(syft_version="", keys={}), False, "syft unknown -> 1.51.0"),
        (
            Lock(syft_version="0.9.0", keys={TIKA.name: TIKA.key}),
            False,
            "syft 0.9.0 -> 1.51.0",
        ),
        (
            Lock(syft_version=SYFT_VERSION, keys={TIKA.name: "lic-older"}),
            False,
            f"inputs lic-older -> {TIKA.key}",
        ),
        (
            Lock(syft_version=SYFT_VERSION, keys={}),
            False,
            f"inputs unlocked -> {TIKA.key}",
        ),
        (
            Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key}),
            True,
            "--refresh was given",
        ),
    ],
)
def test_an_image_is_rescanned_when_the_lock_cannot_vouch_for_it(
    tmp_path: Path, lock: Lock, refresh: bool, expected_reason: str
) -> None:
    """Every branch that forces a scan, and the reason it reports."""
    decision = decide_scan(
        TIKA, _context(_checkout_with_tika(tmp_path), lock, refresh=refresh)
    )

    assert decision.scan
    assert decision.reason == expected_reason


def test_an_image_the_document_lost_is_rescanned(tmp_path: Path) -> None:
    """A lock entry without a section cannot be trusted."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})

    decision = decide_scan(
        TIKA, _context(_checkout_with_tika(tmp_path), lock, document="## Container\n")
    )

    assert decision.scan
    assert decision.reason == "the document has no such section"


def test_an_image_without_a_committed_sbom_is_rescanned(tmp_path: Path) -> None:
    """A section the lock vouches for still needs its SBOM beside it."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})

    decision = decide_scan(TIKA, _context(Checkout(root=tmp_path), lock))

    assert decision.scan
    assert decision.reason == "no SBOM is committed"


@pytest.mark.parametrize(
    "sbom_key,expected_reason",
    [
        ("lic-other", f"SBOM lic-other -> {TIKA_KEY}"),
        (None, f"SBOM unkeyed -> {TIKA_KEY}"),
    ],
)
def test_an_sbom_written_for_other_inputs_is_rescanned(
    tmp_path: Path,
    sbom_key: str | None,
    expected_reason: str,
) -> None:
    """An SBOM a merge took from the other side describes the other side's image.

    git takes a file only one side added without asking the merge driver, so the lock
    can vouch for the inputs while the SBOM beside it came from elsewhere.
    """
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})
    checkout = Checkout(root=tmp_path)
    if sbom_key is None:
        _write_unkeyed_sbom(checkout.sbom(TIKA.name))
    else:
        write_sbom(checkout.sbom(TIKA.name), _sbom(), sbom_key)

    decision = decide_scan(TIKA, _context(checkout, lock))

    assert decision.scan
    assert decision.reason == expected_reason


def test_an_sbom_that_is_not_a_cyclonedx_object_fails_the_run(tmp_path: Path) -> None:
    """Something else wrote it; scanning over it would hide that."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})
    checkout = Checkout(root=tmp_path)
    checkout.sbom(TIKA.name).parent.mkdir(parents=True)
    checkout.sbom(TIKA.name).write_text("<<<<<<< HEAD\n", encoding="utf-8")

    with pytest.raises(ValueError, match="tika.cdx.json is not valid JSON"):
        decide_scan(TIKA, _context(checkout, lock))


def test_every_declared_image_has_its_own_sbom_file() -> None:
    """Two images sharing an SBOM file would overwrite each other's."""
    names = [sbom_path(image.name) for image in load_image_inputs()]

    assert len(names) == len(set(names))
    assert sbom_path(f"{IMAGE_PREFIX}kedacore/keda") == Path(
        "sbom/kedacore-keda.cdx.json"
    )


def test_an_image_outside_the_registry_path_is_refused() -> None:
    """Such a name needs its own naming rule; guessing one hides the mistake."""
    with pytest.raises(ValueError):
        sbom_path("docker.io/library/alpine")


SYFT_SCANS = Path(__file__).parent / "data"


def test_two_builds_of_the_same_inputs_write_the_same_sbom(tmp_path: Path) -> None:
    """A rebuild must not rewrite the committed SBOM.

    The data are two syft 1.51.0 scans, with SYFT_FILE_METADATA_SELECTION=none as
    scan_image runs it, of one Dockerfile built twice without cache, cut down to a few
    packages. They differ in each package's layer digest and in the image's bom-ref and
    tag, none of which follow from the inputs the lock key covers. The serialiser's own
    choices - the serial number, and the image's bom-ref once the built one is gone -
    are in the same class and are pinned rather than minted.
    """
    scans = [SYFT_SCANS / f"syft-scan-build-{build}.json" for build in (1, 2)]
    scanned = [parse_sbom(scan) for scan in scans]
    # Without these the test passes on two copies of one scan, proving nothing.
    assert scanned[0].components != scanned[1].components
    assert scanned[0].metadata.timestamp != scanned[1].metadata.timestamp
    assert image_component(scanned[0]).version != image_component(scanned[1]).version
    assert (
        image_component(scanned[0]).bom_ref.value
        != image_component(scanned[1]).bom_ref.value
    )

    written = []
    for build, scan in enumerate(scans):
        path = tmp_path / f"{build}.cdx.json"
        write_sbom(path, parse_sbom(scan), "k")
        written.append(path.read_text(encoding="utf-8"))

    assert written[0] == written[1]
    # Absence is asserted against the text: reading a file back gives a
    # BomMetaData, whose timestamp defaults to now when the file carries none.
    assert "layerID" not in written[0]
    assert '"timestamp"' not in written[0]
    image = image_component(parse_sbom(tmp_path / "0.cdx.json"))
    assert image.name == f"{IMAGE_PREFIX}example"
    assert image.bom_ref.value == f"{IMAGE_PREFIX}example"
    assert image.version is None
    assert {
        component.bom_ref.value
        for component in parse_sbom(tmp_path / "0.cdx.json").components
    } == {component.bom_ref.value for component in scanned[0].components}


def test_the_image_keeps_a_bom_ref_its_dependencies_still_name(tmp_path: Path) -> None:
    """The image's bom-ref is replaced, not dropped, so nothing is left dangling."""
    path = tmp_path / "x.cdx.json"
    bom = _sbom()
    package = Component(name="p", bom_ref="pkg", type=ComponentType.LIBRARY)
    bom.components.add(package)
    bom.register_dependency(image_component(bom), [package])

    write_sbom(path, bom, TIKA.key)

    written = parse_sbom(path)
    assert image_component(written).bom_ref.value == TIKA_NAME
    assert {
        dependency.ref.value: [on.ref.value for on in dependency.dependencies]
        for dependency in written.dependencies
    } == {TIKA_NAME: ["pkg"], "pkg": []}


def test_a_component_without_a_bom_ref_is_refused(tmp_path: Path) -> None:
    """The serialiser would mint a random one and rewrite this file on every run."""
    bom = _sbom()
    bom.components.add(Component(name="p", type=ComponentType.LIBRARY))

    with pytest.raises(ValueError, match="carries no bom-ref"):
        write_sbom(tmp_path / "x.cdx.json", bom, TIKA.key)


def test_an_sbom_that_describes_no_image_is_refused(tmp_path: Path) -> None:
    """Every scan here is of an image; anything else is a mistake, not a default."""
    with pytest.raises(ValueError, match="describes no component"):
        write_sbom(tmp_path / "x.cdx.json", Bom(), TIKA.key)


def test_an_sbom_records_the_key_it_was_written_for(tmp_path: Path) -> None:
    """A rewrite replaces the key and leaves syft's own properties alone."""
    path = tmp_path / "sbom" / "x.cdx.json"
    bom = _sbom()
    bom.metadata.properties.add(Property(name="syft:image:labels:x", value="y"))

    write_sbom(path, bom, "lic-1")
    write_sbom(path, parse_sbom(path), "lic-2")

    assert read_sbom_key(path) == "lic-2"
    assert list(parse_sbom(path).metadata.properties) == [
        Property(name=SBOM_KEY_PROPERTY, value="lic-2"),
        Property(name="syft:image:labels:x", value="y"),
    ]


def test_an_sbom_the_specification_rejects_is_not_written(tmp_path: Path) -> None:
    """The model represents more than the schema admits, and tools read this file."""
    path = tmp_path / "x.cdx.json"
    bom = _sbom()
    bom.components.add(
        Component(
            name="p", bom_ref="pkg", version="v" * 2000, type=ComponentType.LIBRARY
        )
    )

    with pytest.raises(ValueError, match="not valid CycloneDX 1.7"):
        write_sbom(path, bom, TIKA.key)

    assert not path.exists()


def test_the_sbom_of_an_image_no_longer_declared_is_removed(tmp_path: Path) -> None:
    """The lock and the document drop such an image on their own; a file does not."""
    checkout = _checkout_with_tika(tmp_path)
    stale = tmp_path / "sbom" / "gone.cdx.json"
    write_sbom(stale, _sbom(), "lic-gone")

    remove_stale_sboms([TIKA], checkout)

    assert checkout.sbom(TIKA.name).is_file()
    assert not stale.exists()


@pytest.fixture(name="checkout")
def fixture_checkout(tmp_path: Path) -> Checkout:
    """A checkout whose lock, document and SBOM all describe TIKA."""
    checkout = _checkout_with_tika(tmp_path)
    checkout.document.write_text(_document_with_tika(), "utf-8")
    checkout.lock.write_text(render_lock(SYFT_VERSION, [TIKA]), "utf-8")
    return checkout


def test_the_check_passes_when_everything_matches(checkout: Checkout) -> None:
    """Nothing to rescan, nothing to remove, and nothing written."""
    before = sorted(path.name for path in checkout.root.rglob("*"))

    assert not check(checkout, [TIKA], SYFT_VERSION)
    assert sorted(path.name for path in checkout.root.rglob("*")) == before


def test_the_check_names_the_sbom_of_an_undeclared_image(checkout: Checkout) -> None:
    """It is left in place: the check writes nothing."""
    stale = checkout.root / "sbom" / "gone.cdx.json"
    write_sbom(stale, _sbom(), "lic-gone")

    assert check(checkout, [TIKA], SYFT_VERSION) == [
        f"{stale}: the SBOM of an image no longer declared"
    ]
    assert stale.is_file()


def test_the_check_cannot_be_combined_with_a_refresh() -> None:
    """One writes nothing and the other rewrites everything."""
    with pytest.raises(SystemExit):
        main(["--check", "--refresh"])
