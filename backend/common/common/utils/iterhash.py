import hashlib
from typing import Generator, Iterator, Literal, Protocol

HashAlgorithm = Literal["sha256", "sha512"]


class CountingHash:
    def __init__(self, alg: HashAlgorithm):
        self._hash = hashlib.new(alg)
        self._bytes_count = 0

    def update(self, obj: bytes, /):
        self._hash.update(obj)
        self._bytes_count += len(obj)

    @property
    def bytes_count(self) -> int:
        return self._bytes_count

    def hexdigest(self):
        return self._hash.hexdigest()


class HashLike(Protocol):
    def update(self, obj: bytes, /) -> None:
        pass


def iterhash(h: HashLike, iterator: Iterator[bytes]) -> Generator[bytes, None, None]:
    for chunk in iterator:
        h.update(chunk)
        yield chunk
