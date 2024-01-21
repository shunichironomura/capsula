from __future__ import annotations

__all__ = [
    "HashAlgorithm",
    "compute_hash",
]
import hashlib
import io
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Callable, Dict

logger = logging.getLogger(__name__)

if sys.version_info >= (3, 11):
    file_digest = hashlib.file_digest
else:
    from typing import Protocol

    class _BytesIOLike(Protocol):
        def getbuffer(self) -> io.ReadableBuffer:
            ...

    class _FileDigestFileObj(Protocol):
        def readinto(self, __buf: bytearray) -> int:
            ...

        def readable(self) -> bool:
            ...

    def file_digest(
        fileobj: _BytesIOLike | _FileDigestFileObj,
        digest: str | Callable[[], hashlib._Hash],
        /,
        *,
        _bufsize: int = 2**18,
    ):
        """Hash the contents of a file-like object. Returns a digest object.

        *fileobj* must be a file-like object opened for reading in binary mode.
        It accepts file objects from open(), io.BytesIO(), and SocketIO objects.
        The function may bypass Python's I/O and use the file descriptor *fileno*
        directly.

        *digest* must either be a hash algorithm name as a *str*, a hash
        constructor, or a callable that returns a hash object.
        """
        # On Linux we could use AF_ALG sockets and sendfile() to archive zero-copy
        # hashing with hardware acceleration.
        if isinstance(digest, str):
            digestobj = hashlib.new(digest)
        else:
            digestobj = digest()

        if hasattr(fileobj, "getbuffer"):
            # io.BytesIO object, use zero-copy buffer
            digestobj.update(fileobj.getbuffer())
            return digestobj

        # Only binary files implement readinto().
        if not (hasattr(fileobj, "readinto") and hasattr(fileobj, "readable") and fileobj.readable()):
            raise ValueError(f"'{fileobj!r}' is not a file-like object in binary reading mode.")

        # binary file, socket.SocketIO object
        # Note: socket I/O uses different syscalls than file I/O.
        buf = bytearray(_bufsize)  # Reusable buffer to reduce allocations.
        view = memoryview(buf)
        while True:
            size = fileobj.readinto(buf)
            if size == 0:
                break  # EOF
            digestobj.update(view[:size])

        return digestobj


class HashAlgorithm(Enum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA3_256 = "sha3-256"
    SHA3_384 = "sha3-384"
    SHA3_512 = "sha3-512"


_HASH_CONSTRUCTOR: Dict[HashAlgorithm, Callable[..., hashlib._Hash]] = {
    HashAlgorithm.MD5: hashlib.md5,
    HashAlgorithm.SHA1: hashlib.sha1,
    HashAlgorithm.SHA256: hashlib.sha256,
    HashAlgorithm.SHA3_256: hashlib.sha3_256,
    HashAlgorithm.SHA3_384: hashlib.sha3_384,
    HashAlgorithm.SHA3_512: hashlib.sha3_512,
}

assert set(_HASH_CONSTRUCTOR.keys()) == set(HashAlgorithm)


def compute_hash(file_path: Path, algorithm: HashAlgorithm | Callable[..., hashlib._Hash]) -> str:
    buf_size = 65536  # lets read stuff in 64kb chunks!

    algorithm_ = _HASH_CONSTRUCTOR[algorithm] if isinstance(algorithm, HashAlgorithm) else algorithm
    hash_value = algorithm_()

    with file_path.open("rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            hash_value.update(data)

    return hash_value.hexdigest()
