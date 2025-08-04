import pytest
import requests
from api.models.statistics_model import (
    GenericStatisticsModel,
    HitsPerGroupEntryModel,
    SummaryStatisticsModel,
)
from common.file.file_repository import Stat
from common.services.query_builder import QueryParameters

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api, fetch_query_id
from utils.upload_asset import upload_many_assets


def _get_summary_stats(
    search_string: str = "*",
) -> SummaryStatisticsModel:
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/summary",
        params=QueryParameters(search_string=search_string, query_id=fetch_query_id()),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return SummaryStatisticsModel.model_validate(response.json())


def _get_generic_stats(
    stat_name: Stat,
    search_string: str = "*",
) -> GenericStatisticsModel:
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/generic/{stat_name.value}",
        params=QueryParameters(search_string=search_string, query_id=fetch_query_id()),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GenericStatisticsModel.model_validate(response.json())


class TestStatsWithoutFiles:

    def test_get_stat_summary_on_empty_es(self):
        res = _get_summary_stats()
        assert res.count == 0
        assert res.avg == 0
        assert res.max == 0
        assert res.min == 0

    def test_get_generic_stats_on_empty_es(self):
        res = _get_generic_stats(Stat.FILE_TYPE_MAGIC)
        assert res.stat == Stat.FILE_TYPE_MAGIC.value
        assert res.data == []
        assert res.file_count == 0
        assert isinstance(res.key, str)


class TestStatsWithFiles:

    asset_list = ["1.png", "basic_email.eml", "text_de.txt"]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_get_summary_stats_on_filled_es(self):
        res = _get_summary_stats()
        assert res.count == 3
        assert int(res.avg) == 4101
        assert res.max == 10552
        assert res.min == 233

    def test_get_generic_stats_on_filled_es(self):
        res = _get_generic_stats(Stat.EXTENSIONS)
        assert res.file_count == 3
        assert res.stat == Stat.EXTENSIONS.value
        assert HitsPerGroupEntryModel(name=".txt", hits_count=1) in res.data
        assert HitsPerGroupEntryModel(name=".png", hits_count=1) in res.data
        assert HitsPerGroupEntryModel(name=".eml", hits_count=1) in res.data

    def test_get_summary_stats_on_filled_es_no_match_query(self):
        res = _get_summary_stats("DOES_NOT_EXIST")
        assert res.count == 0
        assert res.avg == 0
        assert res.max == 0
        assert res.min == 0

    def test_get_generic_stats_on_filled_es_no_match_query(self):
        res = _get_generic_stats(Stat.EXTENSIONS, "DOES_NOT_EXIST")
        assert res.file_count == 0
        assert res.stat == Stat.EXTENSIONS.value
        assert res.data == []
