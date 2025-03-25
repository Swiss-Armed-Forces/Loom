from typing import Iterator

from gridfs import GridOut


def chunked_iterator_for_stream(stream: GridOut) -> Iterator[bytes]:
    while True:
        chunk = stream.readchunk()
        if chunk == b"":
            return
        yield chunk
