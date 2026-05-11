# pylint: disable=redefined-outer-name
import io
from collections.abc import Generator
from datetime import timedelta

import pytest
from common.utils.flush_s3_bucket import flush_s3_bucket
from crawler.dependencies import get_s3_client, init
from minio.error import S3Error

from utils.consts import ASSETS_DIR

_TEST_FILENAME = "empty_file.txt"
_TEST_BUCKET_NAME = "test"


@pytest.fixture(autouse=True)
def setup_crawler_dependencies():
    init()


@pytest.fixture
def test_bucket() -> Generator[str, None, None]:
    client = get_s3_client()
    flush_s3_bucket(client, _TEST_BUCKET_NAME)
    try:
        client.remove_bucket(_TEST_BUCKET_NAME)
    except S3Error:
        pass
    client.make_bucket(_TEST_BUCKET_NAME)
    yield _TEST_BUCKET_NAME
    flush_s3_bucket(client, _TEST_BUCKET_NAME)
    client.remove_bucket(_TEST_BUCKET_NAME)


class TestS3Client:

    def test_check_bucket_exists(self, test_bucket: str):
        assert get_s3_client().bucket_exists(test_bucket)

    def test_upload_file(self, test_bucket: str):
        client = get_s3_client()
        file_src = ASSETS_DIR / _TEST_FILENAME
        with open(file_src, "rb") as file:
            f = file.read()
            client.put_object(
                test_bucket,
                _TEST_FILENAME,
                io.BytesIO(f),
                len(f),
            )
        assert client.stat_object(test_bucket, _TEST_FILENAME)

    def test_multipart_upload_file(self, test_bucket: str):
        client = get_s3_client()
        file_src = ASSETS_DIR / _TEST_FILENAME
        with open(file_src, "rb") as file:
            f = file.read()
            client.put_object(
                test_bucket,
                _TEST_FILENAME,
                io.BytesIO(f),
                -1,
                part_size=10 * 1024 * 1024,
            )
        assert client.stat_object(test_bucket, _TEST_FILENAME)


class TestFlushS3Bucket:

    def test_flush_empty_bucket(self, test_bucket: str):
        client = get_s3_client()
        # Flushing an empty bucket should not raise
        flush_s3_bucket(client, test_bucket)
        assert client.bucket_exists(test_bucket)

    def test_flush_nonexistent_bucket(self):
        # Flushing a non-existent bucket should not raise
        flush_s3_bucket(get_s3_client(), "nonexistent-bucket-12345")

    def test_flush_removes_all_objects(self, test_bucket: str):
        client = get_s3_client()
        # Add some objects to the bucket
        for i in range(5):
            data = f"test content {i}".encode()
            client.put_object(
                test_bucket,
                f"test-object-{i}.txt",
                io.BytesIO(data),
                len(data),
            )

        # Verify objects exist
        objects_before = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_before) == 5

        # Flush the bucket
        flush_s3_bucket(client, test_bucket)

        # Verify bucket still exists but is empty
        assert client.bucket_exists(test_bucket)
        objects_after = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_after) == 0

    def test_flush_removes_nested_objects(self, test_bucket: str):
        client = get_s3_client()
        # Add objects with nested paths
        paths = [
            "root.txt",
            "dir1/file1.txt",
            "dir1/file2.txt",
            "dir1/subdir/file3.txt",
            "dir2/file4.txt",
        ]
        for path in paths:
            data = b"test content"
            client.put_object(
                test_bucket,
                path,
                io.BytesIO(data),
                len(data),
            )

        # Verify objects exist
        objects_before = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_before) == len(paths)

        # Flush the bucket
        flush_s3_bucket(client, test_bucket)

        # Verify bucket is empty
        objects_after = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_after) == 0

    def test_flush_with_min_age_preserves_new_objects(self, test_bucket: str):
        client = get_s3_client()
        # Add some objects to the bucket
        for i in range(3):
            data = f"test content {i}".encode()
            client.put_object(
                test_bucket,
                f"new-object-{i}.txt",
                io.BytesIO(data),
                len(data),
            )

        # Verify objects exist
        objects_before = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_before) == 3

        # Flush with min_age=1 minute - objects just created should be preserved
        flush_s3_bucket(client, test_bucket, min_age=timedelta(minutes=1))

        # Verify objects are still there (they are less than 1 minute old)
        objects_after = list(client.list_objects(test_bucket, recursive=True))
        assert len(objects_after) == 3
