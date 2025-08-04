import io

import pytest
from crawler.dependencies import get_minio_client, init
from crawler.settings import settings
from minio import Minio

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import get_file_preview_by_name

TEST_BUCKET_NAME = "test"


class TestCrawler:

    @pytest.fixture(scope="class", autouse=True)
    def client(self) -> Minio:
        init()

        client = get_minio_client()
        return client

    def test_check_bucket_exists(self, client: Minio):
        client.make_bucket(TEST_BUCKET_NAME)
        exists = client.bucket_exists(TEST_BUCKET_NAME)
        assert exists

    def test_upload_file(self, client: Minio):
        filename = "1.png"
        file_src = ASSETS_DIR / filename
        with open(file_src, "rb") as file:
            f = file.read()
            client.put_object(
                settings.minio_default_bucket_name,
                filename,
                io.BytesIO(f),
                -1,
                part_size=10 * 1024 * 1024,
            )
        fileprev = get_file_preview_by_name(filename)
        res_path = f"//{settings.minio_default_bucket_name}/{filename}"
        assert fileprev
        assert fileprev.name == filename
        assert fileprev.path == res_path

    def test_upload_hidden_file(self, client: Minio):
        filename = ".hidden"
        file_src = f"{ASSETS_DIR}/1.png"
        with open(file_src, "rb") as file:
            f = file.read()
            client.put_object(
                settings.minio_default_bucket_name,
                filename,
                io.BytesIO(f),
                -1,
                part_size=10 * 1024 * 1024,
            )
        fileprev = get_file_preview_by_name(filename)
        res_path = f"//{settings.minio_default_bucket_name}/{filename}"
        assert fileprev
        assert fileprev.name == filename
        assert fileprev.path == res_path

    def test_upload_file_with_quotation_mark_in_name(self, client: Minio):
        filename = '".zip'
        file_src = ASSETS_DIR / filename
        with open(file_src, "rb") as file:
            f = file.read()
            client.put_object(
                settings.minio_default_bucket_name,
                filename,
                io.BytesIO(f),
                -1,
                part_size=10 * 1024 * 1024,
            )
        fileprev = get_file_preview_by_name(filename)
        res_path = f"//{settings.minio_default_bucket_name}/{filename}"
        assert fileprev
        assert fileprev.name == filename
        assert fileprev.path == res_path
