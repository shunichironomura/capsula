import tempfile
from pathlib import Path

import pytest

from capsula._backport import file_digest

# Hashes of "Hello world!" for various algorithms
_HELLO_WORLD_HASH = {
    # Checked with `echo -n "Hello world!" | md5sum`
    # "md5sum": "86fb269d190d2c85f6e0468ceca42a20",
    # Checked with `echo -n "Hello world!" | sha1sum`
    "sha1": "d3486ae9136e7856bc42212385ea797094475802",
    # Checked with `echo -n "Hello world!" | sha256sum`
    "sha256": "c0535e4be2b79ffd93291305436bf889314e4a3faec05ecffcbb7df31ad9e51a",
    # Checked with `echo -n "Hello world!" | openssl dgst -sha3-256`
    "sha3-256": "d6ea8f9a1f22e1298e5a9506bd066f23cc56001f5d36582344a628649df53ae8",
    # Checked with `echo -n "Hello world!" | openssl dgst -sha3-384`
    "sha3-384": "f9210511d0b2862bdcb672daa3f6a4284576ccb24d5b293b366b39c24c41a6918464035ec4466b12e22056bf559c7a49",
    # Checked with `echo -n "Hello world!" | openssl dgst -sha3-512`
    "sha3-512": "95decc72f0a50ae4d9d5378e1b2252587cfc71977e43292c8f1b84648248509f"
    "1bc18bc6f0b0d0b8606a643eff61d611ae84e6fbd4a2683165706bd6fd48b334",
}


@pytest.mark.parametrize(
    "algorithm",
    list(_HELLO_WORLD_HASH),
)
def test_compute_hash(algorithm: str) -> None:
    # In Windows, we cannot open a NamedTemporaryFile twice
    # Ref: https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile_path = Path(tmpdir) / "test.txt"
        with tmpfile_path.open("wb") as f:
            f.write(b"Hello world!")
        with tmpfile_path.open("rb") as f:
            digest = file_digest(f, algorithm).hexdigest()
        assert digest == _HELLO_WORLD_HASH[algorithm]
