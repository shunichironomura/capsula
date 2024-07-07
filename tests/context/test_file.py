from pathlib import Path

import pytest

import capsula


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    source_file = tmp_path / "source.txt"
    # Write some data to the file
    # sha256 hash of "This is a test file" is:
    # e2d0fe1585a63ec6009c8016ff8dda8b17719a637405a4e23c0ff81339148249
    source_file.write_text("This is a test file")
    return source_file


_SOURCE_FILE_HASH = {
    "sha256": "e2d0fe1585a63ec6009c8016ff8dda8b17719a637405a4e23c0ff81339148249",
    "md5": "0b26e313ed4a7ca6904b0e9369e5b957",
}


def test_file_context_init(source_file: Path) -> None:
    fc = capsula.FileContext(path=source_file)
    assert fc._path == source_file
    assert fc._hash_algorithm == "sha256"
    assert fc._compute_hash is True
    assert fc._copy_to == ()
    assert fc._move_to is None
    assert fc._ignore_missing is False


def test_file_context_hash(source_file: Path) -> None:
    fc = capsula.FileContext(path=source_file)
    data = fc.encapsulate()
    assert data["copied_to"] == ()
    assert data["moved_to"] is None
    assert data["hash"] is not None
    assert data["hash"]["algorithm"] == "sha256"
    assert data["hash"]["digest"] == _SOURCE_FILE_HASH["sha256"]


def test_file_context_hash_md5(source_file: Path) -> None:
    fc = capsula.FileContext(path=source_file, hash_algorithm="md5")
    data = fc.encapsulate()
    assert data["copied_to"] == ()
    assert data["moved_to"] is None
    assert data["hash"] is not None
    assert data["hash"]["algorithm"] == "md5"
    assert data["hash"]["digest"] == _SOURCE_FILE_HASH["md5"]


def test_ignore_missing_false(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.txt"
    fc = capsula.FileContext(path=missing_file, compute_hash=False, ignore_missing=False)
    with pytest.raises(FileNotFoundError):
        fc.encapsulate()


def test_ignore_missing_true(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.txt"
    fc = capsula.FileContext(path=missing_file, compute_hash=False, ignore_missing=True)
    data = fc.encapsulate()
    assert data["copied_to"] == ()
    assert data["moved_to"] is None
    assert data["hash"] is None
