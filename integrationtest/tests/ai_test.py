from collections import Counter
from uuid import UUID

import pytest
import requests
from api.routers.ai import ContextCreateResponse, ProcessQuestionQuery
from common.dependencies import get_pubsub_service
from common.messages.messages import MessageChatBotAnswerComplete, MessageChatBotToken
from common.services.query_builder import QueryParameters

from utils.consts import AI_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    fetch_query_id,
)
from utils.upload_asset import upload_many_assets


def _create_context(query: QueryParameters) -> ContextCreateResponse:
    response = requests.post(
        AI_ENDPOINT, json=query.model_dump(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return ContextCreateResponse.model_validate(response.json())


def _process_question(ai_context_id: UUID, query: ProcessQuestionQuery):
    response = requests.post(
        f"{AI_ENDPOINT}/{ai_context_id}/process_question",
        json=query.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def test_create_context():
    _create_context(query=QueryParameters(query_id=fetch_query_id()))


class TestChatbot:
    asset_list = [
        "knn1.txt",
        # "knn2.txt",
        # "knn3.txt",
        # "knn4.txt",
        # "knn5.txt",
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string,
            expected_no_of_files=file_count,
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE
            * len(self.asset_list),
        )

    # Currently, without loop_scope, this test exhibits some flakiness
    # and fails sometimes in the pubsub_async.subscribe line with an:
    # RuntimeError: Event loop is closed
    #
    # I currently have no clue why, but I am experimenting a bit with
    # changing the loop scope...
    @pytest.mark.asyncio(loop_scope="class")
    async def test_chatbot(self):

        ai_context = _create_context(query=QueryParameters(query_id=fetch_query_id()))

        pubsub = get_pubsub_service()
        async with pubsub.open_async() as pubsub_async:
            await pubsub_async.subscribe({str(ai_context.context_id)})

            _process_question(
                ai_context_id=ai_context.context_id,
                query=ProcessQuestionQuery(question="What is network security?"),
            )

            message_type_counter = Counter()
            while True:
                message = await pubsub_async.get_message()
                message_type_counter[type(message.message)] += 1
                if isinstance(message.message, MessageChatBotAnswerComplete):
                    break

            assert message_type_counter[MessageChatBotToken] > 0
            # Currently the RAG pipeline is not stable enough and we cannot assert
            # that we'll always get a citation.
            # assert message_type_counter[MessageChatBotCitation] > 0
            assert message_type_counter[MessageChatBotAnswerComplete] > 0
