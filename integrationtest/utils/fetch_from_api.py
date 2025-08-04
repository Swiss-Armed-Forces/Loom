# NOTE: This file for various reasons very ugly and need urgent refactoring.
# Some reasons why this is what it is atm:
# - No shared base class between Hit and ArchiveHit
# - ...
# This should be resolved with issue #86
# also that we have to to the following is very ugly:
# pylint: disable=too-many-arguments

import logging
import time
from collections import Counter
from typing import Any, Iterable, Literal
from uuid import UUID

import requests
from api.models.archives_model import ArchiveHit, ArchivesModel
from api.routers.files import (
    GetFilePreviewResponse,
    GetFileResponse,
    GetFilesCountResponse,
    GetFilesQuery,
    GetFilesResponse,
    GetQuery,
    GetQueryResponse,
)
from common.models.es_repository import DEFAULT_PAGE_SIZE
from common.services.query_builder import QueryParameters
from requests import Response

from utils.celery_inspect import is_celery_idle
from utils.consts import ARCHIVE_ENDPOINT, FILES_ENDPOINT, REQUEST_TIMEOUT

DEFAULT_MAX_WAIT_TIME_PER_FILE = 300
BATCH_WAIT_TIME = 10


class FetchException(Exception):
    pass


def _quote_str_for_query(query: str):
    safe_query = query.replace('"', '\\"')
    return safe_query if safe_query.isalpha() else f'"{safe_query}"'


def fetch_query_id(get_query: GetQuery | None = None) -> str:
    if get_query is None:
        get_query = GetQuery()
    response: Response = requests.post(
        f"{FILES_ENDPOINT}/query",
        params=get_query.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    get_query_response = GetQueryResponse.model_validate(response.json())
    return get_query_response.query_id


def build_search_string(
    search_string: str, field: str, field_value: str | Iterable[str]
) -> str:
    if isinstance(field_value, str):
        field_value = [field_value]

    field_search_string = (
        f'{field}:({" OR ".join(_quote_str_for_query(v) for v in field_value)})'
    )

    return (
        f"({search_string}) AND {field_search_string}"
        if search_string != "*"
        else field_search_string
    )


def fetch_files_count_from_api(files_query: GetFilesQuery) -> GetFilesCountResponse:
    response = requests.get(
        f"{FILES_ENDPOINT}/count",
        params=files_query.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GetFilesCountResponse.model_validate(response.json())


def fetch_files_by_query_from_api(files_query: GetFilesQuery) -> GetFilesResponse:
    response = requests.get(
        f"{FILES_ENDPOINT}/",
        params=files_query.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GetFilesResponse.model_validate(response.json())


# pylint: disable=too-many-arguments, too-many-locals, too-many-branches
def fetch_archives_from_api(
    expected_no_of_archives: int = 1,
    expected_state: str | None = "created",
    max_wait_time_per_archive: int | None = None,
    bad_states: tuple[str, ...] = ("failed",),
    wait_for_celery_idle: bool = False,
) -> list[ArchiveHit]:
    if max_wait_time_per_archive is None:
        max_wait_time_per_archive = DEFAULT_MAX_WAIT_TIME_PER_FILE

    max_wait_time = expected_no_of_archives * max_wait_time_per_archive
    wait_cycles = (max_wait_time // BATCH_WAIT_TIME) + 1
    error_msgs = []

    # remove expected state from bad states
    bad_states = tuple(
        bad_state for bad_state in bad_states if bad_state != expected_state
    )

    # Retry the get request maximally 3 times
    for retry_attempts in range(wait_cycles):
        time.sleep(BATCH_WAIT_TIME)  # wait before trying to fetch
        response = requests.get(
            f"{ARCHIVE_ENDPOINT}/",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        hits_model = ArchivesModel.model_validate(response.json())
        hits = hits_model.hits
        number_in_expected_state = sum(
            1
            for file in hits
            if expected_state is None or file.content.state == expected_state
        )
        number_in_bad_state = sum(
            1 for file in hits if file.content.state in bad_states
        )

        logging.debug(
            "Query attempt %d/%d, n_hits=%d/%d, n_%s=%d/%d, n_%s=%d/%d",
            retry_attempts + 1,
            wait_cycles,
            len(hits),
            expected_no_of_archives,
            expected_state,
            number_in_expected_state,
            expected_no_of_archives,
            bad_states,
            number_in_bad_state,
            len(hits),
        )

        if number_in_bad_state > 0:
            error_msgs.append(
                f"{number_in_bad_state} / {len(hits)} results in bad state detected!"
            )
            break

        if number_in_expected_state > expected_no_of_archives:
            error_msgs.append(
                "Too many hits in expected state."
                f" state: '{expected_state}'"
                f" got: {number_in_expected_state}"
                f" expected: {expected_no_of_archives}"
            )
            break

        if wait_for_celery_idle:
            if not is_celery_idle():
                logging.debug("Celery not idle yet")
                continue

        if number_in_expected_state == expected_no_of_archives:
            # Successful response with expected number of results
            # and all results processed.
            #    => log response and return immediately.
            logging.debug("Successful response after %d tries", retry_attempts)
            return hits
    # The requests have not returned the correct response, so log
    #    what we can and raise an exception to fail the test.
    if len(hits) != expected_no_of_archives:
        error_msgs.append(
            f"Expected {expected_no_of_archives} but got {len(hits)} hits."
        )

    if any(result.content.state != expected_state for result in hits):
        divergent_states = Counter(
            hit.content.state for hit in hits if hit.content.state != expected_state
        )
        error_msgs.append(f"Results are in the wrong states: {divergent_states}")
    error_msg = (
        f"Failed to fetch {expected_no_of_archives} archives "
        + f"hits with expected state '{expected_state}' "
        + f"Retried fetch {retry_attempts} times "
        + f"in a period of {max_wait_time} seconds\n"
        + "\n".join(error_msgs)
    )
    logging.error(error_msg)
    raise FetchException(error_msg)


def fetch_files_from_api(
    search_string: str = "*",
    languages: list[str] | None = None,
    sort_by_field: str = "_score",
    sort_direction: Literal["asc", "desc"] = "asc",
    expected_no_of_files: int = 1,
    expected_state: str = "processed",
    sort_id: list[Any] | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_wait_time_per_file: int | None = None,
    bad_states: tuple[str, ...] = ("failed",),
    wait_for_celery_idle: bool = False,
) -> GetFilesResponse:
    if max_wait_time_per_file is None:
        max_wait_time_per_file = DEFAULT_MAX_WAIT_TIME_PER_FILE
    if languages is None:
        languages = []
    if sort_id is None:
        sort_id = []

    max_wait_time = expected_no_of_files * max_wait_time_per_file
    wait_cycles = (max_wait_time // BATCH_WAIT_TIME) + 1
    error_msgs = []

    # remove expected state from bad states
    bad_states = tuple(
        bad_state for bad_state in bad_states if bad_state != expected_state
    )

    for retry_attempts in range(0, wait_cycles):
        if retry_attempts != 0:
            time.sleep(BATCH_WAIT_TIME)  # wait before trying to fetch

        # search for expected state
        files_query = GetFilesQuery(
            query_id=fetch_query_id(),
            search_string=build_search_string(
                search_string=search_string,
                field="state",
                field_value=expected_state,
            ),
            languages=languages,
            sort_id=sort_id,
            page_size=page_size,
            sort_by_field=sort_by_field,
            sort_direction=sort_direction,
        )
        response_file_count = fetch_files_count_from_api(files_query).total_files

        # search for bad states
        if len(bad_states) > 0:
            bad_states_files_query = files_query.model_copy()
            bad_states_files_query.search_string = build_search_string(
                search_string=search_string,
                field="state",
                field_value=bad_states,
            )

            file_response_bad_state = fetch_files_count_from_api(
                bad_states_files_query
            ).total_files
        else:
            file_response_bad_state = 0

        logging.debug(
            "Query attempt %d/%d, n_%s=%d/%d, n_%s=%d",
            retry_attempts + 1,
            wait_cycles,
            expected_state,
            response_file_count,
            expected_no_of_files,
            bad_states,
            file_response_bad_state,
        )

        if response_file_count > expected_no_of_files:
            error_msgs.append(
                "More files than expected."
                f" got: {response_file_count}"
                f" expected: {expected_no_of_files}"
            )
            break

        if file_response_bad_state is not None and file_response_bad_state > 0:
            error_msgs.append(
                "Results are in the wrong states:" f" {file_response_bad_state}"
            )
            break

        if wait_for_celery_idle:
            if not is_celery_idle():
                logging.debug("Celery not idle yet")
                continue

        if response_file_count == expected_no_of_files:
            # Successful response with expected number of results
            # and all results processed.
            #    => log response and return immediately.
            logging.debug("Successful response after %d tries", retry_attempts)

            file_response_expected_state = fetch_files_by_query_from_api(files_query)
            return file_response_expected_state

    # The requests have not returned the correct response, so log
    #    what we can and raise an exception to fail the test.
    if response_file_count != expected_no_of_files:
        error_msgs.append(
            f"Expected {expected_no_of_files} but got" f" {response_file_count} files."
        )

    error_msg = (
        f"Failed to fetch {expected_no_of_files} "
        + f"using query: '{search_string}'\n"
        + f"Retried fetch {retry_attempts} times "
        + f"in a period of {max_wait_time} seconds\n"
        + "\n".join(error_msgs)
    )
    logging.error(error_msg)
    raise FetchException(error_msg)


def get_file_preview_by_name(
    file_name: str,
    search_string: str = "*",
    languages: list[str] | None = None,
    expected_state: str = "processed",
    max_wait_time_per_file: int | None = None,
    bad_states: tuple[str, ...] = ("failed",),
    wait_for_celery_idle: bool = False,
) -> GetFilePreviewResponse:
    if max_wait_time_per_file is None:
        max_wait_time_per_file = DEFAULT_MAX_WAIT_TIME_PER_FILE

    search_string = build_search_string(
        search_string=search_string, field="short_name", field_value=file_name
    )
    response = fetch_files_from_api(
        search_string=search_string,
        languages=languages,
        expected_no_of_files=1,
        expected_state=expected_state,
        max_wait_time_per_file=max_wait_time_per_file,
        bad_states=bad_states,
        wait_for_celery_idle=wait_for_celery_idle,
    )

    return get_file_preview_by_file_id_without_waiting(
        file_id=response.files[0].file_id,
        search_string=search_string,
        languages=languages,
    )


def get_file_preview_by_file_id_without_waiting(
    file_id: UUID,
    search_string: str = "*",
    languages: list[str] | None = None,
) -> GetFilePreviewResponse:
    if languages is None:
        languages = []

    response = requests.get(
        f"{FILES_ENDPOINT}/{file_id}/preview",
        params=QueryParameters(
            query_id=fetch_query_id(),
            search_string=search_string,
            languages=languages,
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GetFilePreviewResponse.model_validate(response.json())


def get_file_by_name(
    file_name: str,
    search_string: str = "*",
    languages: list[str] | None = None,
    expected_state: str = "processed",
    max_wait_time_per_file: int | None = None,
    bad_states: tuple[str, ...] = ("failed",),
    wait_for_celery_idle: bool = False,
) -> GetFileResponse:
    if max_wait_time_per_file is None:
        max_wait_time_per_file = DEFAULT_MAX_WAIT_TIME_PER_FILE

    if languages is None:
        languages = []

    search_string = build_search_string(
        search_string=search_string, field="short_name", field_value=file_name
    )
    files = fetch_files_from_api(
        search_string=search_string,
        languages=languages,
        expected_no_of_files=1,
        expected_state=expected_state,
        max_wait_time_per_file=max_wait_time_per_file,
        bad_states=bad_states,
        wait_for_celery_idle=wait_for_celery_idle,
    )

    response = requests.get(
        f"{FILES_ENDPOINT}/{files.files[0].file_id}",
        params=QueryParameters(
            query_id=fetch_query_id(),
            search_string=search_string,
            languages=languages,
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GetFileResponse.model_validate(response.json())
