from __future__ import annotations

__all__ = [
    "AbstractContextManager",
    "Annotated",
    "Concatenate",
    "ParamSpec",
    "Self",
    "TypeAlias",
    "file_digest",
    "tomllib",
]

import hashlib
import sys
from typing import TYPE_CHECKING, Callable

if sys.version_info >= (3, 11):
    from typing import Self

    import tomllib
else:
    import tomli as tomllib
    from typing_extensions import Self

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec, TypeAlias
else:
    from typing_extensions import Concatenate, ParamSpec, TypeAlias

if sys.version_info >= (3, 9):
    from contextlib import AbstractContextManager
    from typing import Annotated
else:
    from typing import ContextManager as AbstractContextManager

    from typing_extensions import Annotated


if sys.version_info >= (3, 11):
    file_digest = hashlib.file_digest
else:
    if TYPE_CHECKING:
        from typing_extensions import Buffer
    from typing import Protocol

    class _BytesIOLike(Protocol):
        def getbuffer(self) -> Buffer: ...

    class _FileDigestFileObj(Protocol):
        def readinto(self, __buf: bytearray) -> int: ...

        def readable(self) -> bool: ...

    def file_digest(
        fileobj: _BytesIOLike | _FileDigestFileObj,
        digest: str | Callable[[], hashlib._Hash],
        /,
        *,
        _bufsize: int = 2**18,
    ) -> hashlib._Hash:
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
