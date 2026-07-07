import pytest
import requests
from api.models.statistics_model import (
    GroupedHistogramStatisticsModel,
    HitsPerGroupEntryModel,
    TermsStatisticsModel,
)
from common.file.file_statistics import AvailableStat
from common.services.query_builder import QueryParameters

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api, fetch_query_id
from utils.upload_asset import upload_many_assets


def _get_available_stats() -> list[AvailableStat]:
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/terms",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    stats = [AvailableStat.model_validate(s) for s in response.json()]
    r = requests.get(
        f"{FILES_ENDPOINT}/stats/histogram",
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    stats += [AvailableStat.model_validate(s) for s in r.json()]
    return stats


def _get_terms_stats(
    stat_name: str,
    search_string: str = "*",
) -> TermsStatisticsModel:
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/terms/{stat_name}",
        params=QueryParameters(search_string=search_string, query_id=fetch_query_id()),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return TermsStatisticsModel.model_validate(response.json())


def _get_histogram_stats(
    stat_name: str,
    search_string: str = "*",
) -> TermsStatisticsModel:
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/histogram/{stat_name}",
        params=QueryParameters(search_string=search_string, query_id=fetch_query_id()),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return TermsStatisticsModel.model_validate(response.json())


def _get_grouped_stats(
    stat: str,
    group_by: str,
    search_string: str = "*",
) -> GroupedHistogramStatisticsModel:
    params = {
        **QueryParameters(
            search_string=search_string, query_id=fetch_query_id()
        ).model_dump(),
    }
    response = requests.get(
        f"{FILES_ENDPOINT}/stats/histogram/{stat}/grouped/{group_by}",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GroupedHistogramStatisticsModel.model_validate(response.json())


class TestStatsWithoutFiles:

    def test_get_available_stats(self):
        stats = _get_available_stats()
        ids = [s.id for s in stats]
        assert "extension" in ids
        assert "source" in ids
        assert "magic_file_type" in ids
        assert "tika_file_type" in ids
        assert "flagged" in ids
        assert "seen" in ids
        assert "uploaded_datetime" in ids
        assert "tika_meta.dcterms_created" in ids
        assert "tika_meta.dcterms_modified" in ids
        assert "size" in ids
        for s in stats:
            assert s.label != ""

    def test_get_histogram_stats_date(self):
        res = _get_histogram_stats("uploaded_datetime")
        assert res.stat == "uploaded_datetime"
        assert res.key == "uploaded_datetime"
        assert isinstance(res.data, list)

    def test_get_histogram_stats_number(self):
        res = _get_histogram_stats("size")
        assert res.stat == "size"
        assert res.key == "size"
        assert isinstance(res.data, list)

    def test_get_terms_stats_on_empty_es(self):
        res = _get_terms_stats("magic_file_type")
        assert res.stat == "magic_file_type"
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

    def test_get_terms_stats_on_filled_es(self):
        res = _get_terms_stats("extension")
        assert res.file_count == 3
        assert res.stat == "extension"
        assert HitsPerGroupEntryModel(name=".txt", hits_count=1) in res.data
        assert HitsPerGroupEntryModel(name=".png", hits_count=1) in res.data
        assert HitsPerGroupEntryModel(name=".eml", hits_count=1) in res.data

    def test_get_terms_stats_on_filled_es_no_match_query(self):
        res = _get_terms_stats("extension", "DOES_NOT_EXIST")
        assert res.file_count == 0
        assert res.stat == "extension"
        assert res.data == []

    def test_get_grouped_stats_on_filled_es(self):
        res = _get_grouped_stats("uploaded_datetime", "extension")
        assert res.stat == "uploaded_datetime"
        assert res.group_by == "extension"
        assert res.file_count == 3
        assert isinstance(res.data, list)
        assert len(res.data) > 0
        for entry in res.data:
            assert isinstance(entry.groups, dict)

    def test_get_grouped_stats_number_histogram_on_filled_es(self):
        res = _get_grouped_stats("size", "extension")
        assert res.stat == "size"
        assert res.group_by == "extension"
        assert res.file_count == 3
        assert isinstance(res.data, list)
        assert len(res.data) > 0
        for entry in res.data:
            assert isinstance(entry.groups, dict)
