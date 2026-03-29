import io

import pytest
from common.utils.flush_s3_bucket import flush_s3_bucket
from crawler.dependencies import get_s3_client
from minio import Minio

# pylint: disable=redefined-outer-name

TEST_BUCKET_NAME = "flush-test-bucket"


class TestFlushS3Bucket:

    @pytest.fixture(scope="class")
    def client(self) -> Minio:
        return get_s3_client()

    @pytest.fixture(autouse=True)
    def setup_bucket(self, client: Minio):
        if not client.bucket_exists(TEST_BUCKET_NAME):
            client.make_bucket(TEST_BUCKET_NAME)
        yield
        # Cleanup: flush the bucket after each test
        flush_s3_bucket(client, TEST_BUCKET_NAME)

    def test_flush_empty_bucket(self, client: Minio):
        # Flushing an empty bucket should not raise
        flush_s3_bucket(client, TEST_BUCKET_NAME)
        assert client.bucket_exists(TEST_BUCKET_NAME)

    def test_flush_nonexistent_bucket(self, client: Minio):
        # Flushing a non-existent bucket should not raise
        flush_s3_bucket(client, "nonexistent-bucket-12345")

    def test_flush_removes_all_objects(self, client: Minio):
        # Add some objects to the bucket
        for i in range(5):
            data = f"test content {i}".encode()
            client.put_object(
                TEST_BUCKET_NAME,
                f"test-object-{i}.txt",
                io.BytesIO(data),
                len(data),
            )

        # Verify objects exist
        objects_before = list(client.list_objects(TEST_BUCKET_NAME, recursive=True))
        assert len(objects_before) == 5

        # Flush the bucket
        flush_s3_bucket(client, TEST_BUCKET_NAME)

        # Verify bucket still exists but is empty
        assert client.bucket_exists(TEST_BUCKET_NAME)
        objects_after = list(client.list_objects(TEST_BUCKET_NAME, recursive=True))
        assert len(objects_after) == 0

    def test_flush_removes_nested_objects(self, client: Minio):
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
                TEST_BUCKET_NAME,
                path,
                io.BytesIO(data),
                len(data),
            )

        # Verify objects exist
        objects_before = list(client.list_objects(TEST_BUCKET_NAME, recursive=True))
        assert len(objects_before) == len(paths)

        # Flush the bucket
        flush_s3_bucket(client, TEST_BUCKET_NAME)

        # Verify bucket is empty
        objects_after = list(client.list_objects(TEST_BUCKET_NAME, recursive=True))
        assert len(objects_after) == 0
