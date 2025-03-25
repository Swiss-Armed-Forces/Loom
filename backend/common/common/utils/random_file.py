from contextlib import contextmanager
from os import urandom
from pathlib import Path
from random import choices
from string import printable
from tempfile import NamedTemporaryFile
from typing import IO, Generator


@contextmanager
def random_file(tmp_path: Path, total_size: int) -> Generator[IO, None, None]:
    block_size = 1 * (1024**2)  # 1 MiB
    with NamedTemporaryFile(dir=tmp_path) as fd:
        for _ in range(total_size // block_size):
            fd.write(urandom(block_size))
        fd.write(urandom(total_size % block_size))
        fd.flush()
        fd.seek(0)
        yield fd


@contextmanager
def random_file_printable(tmp_path: Path, total_size: int) -> Generator[IO, None, None]:
    block_size = 1 * (1024**2)  # 1 MiB
    with NamedTemporaryFile(mode="w+", dir=tmp_path) as fd:
        for _ in range(total_size // block_size):
            fd.write("".join(choices(printable, k=block_size)))
        fd.write("".join(choices(printable, k=total_size % block_size)))
        fd.flush()
        fd.seek(0)
        yield fd
