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

from generate_third_party import (
    THIRD_PARTY_LICENCES,
    TOPLEVEL_DIR,
    ImageRef,
    Lock,
    decide_scan,
    get_committed_section,
    parse_lock,
    render_document,
    render_lock,
    render_section,
)
from third_party_inputs import ArtifactDeclaration, ImageInputs

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


def _document_with_tika() -> str:
    return f"## Container\n{render_section(TIKA.name, 'body\n')}"


def test_an_unchanged_key_is_reused() -> None:
    """The whole point: a key the lock vouches for is not scanned again."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})

    decision = decide_scan(
        TIKA, lock, _document_with_tika(), SYFT_VERSION, refresh=False
    )

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
    lock: Lock, refresh: bool, expected_reason: str
) -> None:
    """Every branch that forces a scan, and the reason it reports."""
    decision = decide_scan(
        TIKA, lock, _document_with_tika(), SYFT_VERSION, refresh=refresh
    )

    assert decision.scan
    assert decision.reason == expected_reason


def test_an_image_the_document_lost_is_rescanned() -> None:
    """A lock entry without a section cannot be trusted."""
    lock = Lock(syft_version=SYFT_VERSION, keys={TIKA.name: TIKA.key})

    decision = decide_scan(TIKA, lock, "## Container\n", SYFT_VERSION, refresh=False)

    assert decision.scan
    assert decision.reason == "the document has no such section"
