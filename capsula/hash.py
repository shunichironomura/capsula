import hashlib
import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


def compute_hash(file_path: Path, algorithm: Literal["md5", "sha1", "sha256", "sha3"]) -> str:
    buf_size = 65536  # lets read stuff in 64kb chunks!

    if algorithm == "md5":
        hash_algo = hashlib.md5()  # noqa: S324
    elif algorithm == "sha1":
        hash_algo = hashlib.sha1()  # noqa: S324
    elif algorithm == "sha256":
        hash_algo = hashlib.sha256()
    elif algorithm == "sha3":
        hash_algo = hashlib.sha3_256()
    else:
        msg = "Unknown algorithm"
        raise ValueError(msg)

    with file_path.open("rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            hash_algo.update(data)

    return hash_algo.hexdigest()
