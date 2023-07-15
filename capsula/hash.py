import hashlib
import logging
from enum import Enum
from pathlib import Path
from typing import Callable, Dict

logger = logging.getLogger(__name__)


class HashAlgorithm(Enum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA3_256 = "sha3-256"
    SHA3_384 = "sha3-384"
    SHA3_512 = "sha3-512"


_HASH_CONSTRUCTOR: Dict[HashAlgorithm, Callable[..., "hashlib._Hash"]] = {  # noqa: SLF001
    HashAlgorithm.MD5: hashlib.md5,
    HashAlgorithm.SHA1: hashlib.sha1,
    HashAlgorithm.SHA256: hashlib.sha256,
    HashAlgorithm.SHA3_256: hashlib.sha3_256,
    HashAlgorithm.SHA3_384: hashlib.sha3_384,
    HashAlgorithm.SHA3_512: hashlib.sha3_512,
}

assert set(_HASH_CONSTRUCTOR.keys()) == set(HashAlgorithm)


def compute_hash(file_path: Path, algorithm: HashAlgorithm) -> str:
    buf_size = 65536  # lets read stuff in 64kb chunks!

    hash_value = _HASH_CONSTRUCTOR[algorithm]()

    with file_path.open("rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            hash_value.update(data)

    return hash_value.hexdigest()
