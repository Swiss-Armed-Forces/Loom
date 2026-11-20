"""Unit tests for cicd/verify_venv.py.

Two things decide whether this check is worth having: it has to notice a file that a
distribution claims and the virtualenv no longer has, and it must not cry wolf over
byte-compilation artifacts, which are absent from healthy virtualenvs in their hundreds.
"""

from pathlib import Path

from verify_venv import verify

SITE_PACKAGES = "lib/python3.14/site-packages"


def make_dist(venv: Path, name: str, files: dict[str, str]) -> Path:
    """Install a fake distribution, with a RECORD listing what it wrote."""
    site_packages = venv / SITE_PACKAGES
    dist_info = site_packages / f"{name}.dist-info"
    dist_info.mkdir(parents=True)

    for path, body in files.items():
        target = site_packages / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)

    record = "\n".join(f"{path},sha256=x,{len(body)}" for path, body in files.items())
    (dist_info / "RECORD").write_text(record)
    return site_packages


def test_intact_virtualenv_passes(tmp_path: Path) -> None:
    """Nothing is reported while every claimed file is on disk."""
    make_dist(tmp_path, "pycryptodome-3.23.0", {"Crypto/Cipher/AES.py": "aes"})

    result = verify(tmp_path)

    assert result.complete
    assert result.checked == 1
    assert result.distributions == 1


def test_missing_file_is_reported(tmp_path: Path) -> None:
    """A short cache restore is a file the RECORD claims and the disk lacks."""
    site_packages = make_dist(
        tmp_path,
        "pycryptodome-3.23.0",
        {"Crypto/Cipher/AES.py": "aes", "Crypto/Hash/MD5.py": "md5"},
    )
    (site_packages / "Crypto/Cipher/AES.py").unlink()

    result = verify(tmp_path)

    assert not result.complete
    assert [entry.path for entry in result.missing] == ["Crypto/Cipher/AES.py"]
    assert result.missing[0].distribution == "pycryptodome-3.23.0.dist-info"


def test_absent_byte_compilation_artifacts_pass(tmp_path: Path) -> None:
    """Pip's own RECORD lists hundreds of these that no install ever writes."""
    site_packages = make_dist(
        tmp_path,
        "pip-26.1.2",
        {
            "pip/__init__.py": "pip",
            "pip/_vendor/rich/color.cpython-314.pyc": "compiled",
            "pip/_internal/__pycache__/main.cpython-314.pyc": "compiled",
        },
    )
    (site_packages / "pip/_vendor/rich/color.cpython-314.pyc").unlink()
    (site_packages / "pip/_internal/__pycache__/main.cpython-314.pyc").unlink()

    result = verify(tmp_path)

    assert result.complete
    assert result.checked == 1
