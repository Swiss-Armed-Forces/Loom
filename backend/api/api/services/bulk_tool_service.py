"""Query-scoped bulk actions, each held for the user's approval before it dispatches."""

import logging
from typing import NoReturn
from uuid import UUID, uuid4

from common.ai_context.tool_models import (
    BulkAction,
    BulkApprovalRequest,
    BulkDispatchResult,
    BulkEnrichmentAction,
    BulkMetadataAction,
)
from common.file.file_repository import FileRepository, Tags
from common.services.query_builder import (
    AI_PIT_KEEPALIVE,
    INVALID_QUERY_ERRORS,
    QueryParameters,
    convert_keepalive_to_seconds,
    invalid_query_message,
)
from common.services.task_scheduling_service import (
    TaskSchedulingService,
    UpdateFileRequest,
)
from common.settings import settings
from pydantic import BaseModel
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.exceptions import ApprovalRequired, ToolFailed
from pydantic_ai.tools import Tool as PydanticTool
from redis import StrictRedis

from api.services.agent_deps import AgentDeps

logger = logging.getLogger(__name__)

_APPROVAL_KEY_PREFIX = "aibulkapproval"

APPROVAL_INSTRUCTIONS = (
    "Every one of these actions is put to the user for approval before anything is "
    "dispatched, together with the number of files it would cover. That happens on "
    "its own, so call the action the user asked for directly and do not ask for "
    "agreement yourself first. A call that comes back denied is the user's answer: "
    "say so and do not repeat it.\n"
)


class BulkApproval(BaseModel):
    """One bulk action put to the user, kept from the question to the answer.

    It is held here rather than carried through the approval round trip because an
    answer cannot carry it: a client resolves an AG-UI interrupt with approve or deny
    and nothing else, so what was approved has to be read back from where it was
    written. That makes this record the authority on what an answer buys — the one
    action, over the one query, on the one snapshot, that the count shown to the user
    was taken from.
    """

    approval_id: UUID
    action: BulkAction
    query_string: str
    # The point-in-time the count was taken against, which the dispatch is pinned to.
    query_id: str
    matched_files: int


class ApprovedQuery(BaseModel):
    """A query the user has agreed to act on, bound to the snapshot they were shown.

    ``query`` carries that snapshot as its ``query_id``, which is what the sweep runs
    on, so the files acted on are the files that were counted.
    """

    query: QueryParameters
    matched_files: int


class BulkToolService:
    """Provides the bulk tool functions for the pydantic-ai agent.

    Separate from ToolService because the two act differently: every tool there ends
    in a blocking task call, while each of these dispatches a fire-and-forget sweep
    across a whole query and returns as soon as the work is queued.
    """

    def __init__(
        self,
        task_scheduling_service: TaskSchedulingService,
        file_repository: FileRepository,
        redis_cache_client: StrictRedis,
    ) -> None:
        self._task_scheduling_service = task_scheduling_service
        self._file_repository = file_repository
        self._redis_client = redis_cache_client

        t = settings.llm.agent.tool_timeout

        # Handed to ToolService rather than wrapped in a Capability here: the bulk
        # actions and the per-file ones share the `enrichment` bundle, and a Capability
        # can only be assembled where both halves are in reach.
        self.tools: list[PydanticTool[AgentDeps]] = [
            PydanticTool(self.bulk_summarize, timeout=t),
            PydanticTool(self.bulk_translate, timeout=t),
            PydanticTool(self.bulk_describe_images, timeout=t),
            PydanticTool(self.bulk_add_tags, timeout=t),
            PydanticTool(self.bulk_update_files, timeout=t),
        ]

    def _approval_key(self, ctx: RunContext[AgentDeps]) -> str:
        """Where the approval for the call in ``ctx`` is kept.

        Keyed on the tool call the approval was raised from, which is what makes every
        bulk call a decision of its own: pydantic-ai re-enters the tool under the same
        ``tool_call_id`` once the user has answered, so two bulk calls in one model
        response are two ids, two stored approvals and two answers. The conversation is
        in the key as well, so an id a model reuses across conversations cannot reach
        an approval given in another one.
        """
        if ctx.tool_call_id is None:
            raise ToolFailed(
                "Nothing was dispatched: this action arrived without a call id, and "
                "an approval can only be held against one."
            )
        return f"{_APPROVAL_KEY_PREFIX}:{ctx.deps.context.id_}:{ctx.tool_call_id}"

    def _approved_query(
        self,
        ctx: RunContext[AgentDeps],
        action: BulkAction,
        query_string: str,
    ) -> ApprovedQuery:
        """Hold the call for the user's approval, and hand back what they agreed to.

        The first call raises ApprovalRequired, which ends the agent run with the count
        attached and puts the decision to the user; the approved call re-enters here
        with ``ctx.tool_call_approved`` set and goes on to dispatch. The confirmation is
        therefore enforced by this code on the way to every dispatch, rather than being
        a sequence of calls the agent has to be relied on to make.
        """
        key = self._approval_key(ctx)
        if ctx.tool_call_approved:
            return self._spend_approval(
                key, action, query_string, ctx.deps.approved_bulk_ids
            )
        self._request_approval(key, action, query_string)

    def _request_approval(
        self, key: str, action: BulkAction, query_string: str
    ) -> NoReturn:
        """Count what the query covers and put that number to the user.

        The count is taken against a point-in-time of its own, and that snapshot is
        what the dispatch is later pinned to: the number somebody agrees to is only an
        answer if the files acted on are the files that were counted.
        """
        try:
            query = QueryParameters(
                keep_alive=AI_PIT_KEEPALIVE, search_string=query_string
            )
            query_id = self._file_repository.open_point_in_time(
                keep_alive=AI_PIT_KEEPALIVE
            )
            query.query_id = query_id
            matched_files = self._file_repository.count_by_query(query)
        # A query the model composed is the model's to fix, so every rejection has to
        # come back as something it can act on rather than as a tool error.
        except INVALID_QUERY_ERRORS as exc:
            logger.warning("bulk action: invalid query '%s': %s", query_string, exc)
            raise ModelRetry(invalid_query_message(query_string, exc)) from exc

        if matched_files == 0:
            raise ModelRetry(
                f"No file matches '{query_string}', so there is nothing to act on. "
                "Check the query with execute_query before trying again."
            )

        approval = BulkApproval(
            approval_id=uuid4(),
            action=action,
            query_string=query_string,
            query_id=query_id,
            matched_files=matched_files,
        )
        # The record outlives the snapshot it names by nothing: an answer that arrives
        # after the snapshot is gone is an answer about a count nobody can act on.
        self._redis_client.set(
            key,
            approval.model_dump_json(),
            ex=convert_keepalive_to_seconds(AI_PIT_KEEPALIVE),
        )
        logger.info(
            "Bulk action %s over '%s' awaits approval %s for %d files",
            action,
            query_string,
            approval.approval_id,
            matched_files,
        )
        raise ApprovalRequired(
            metadata=BulkApprovalRequest(
                approval_id=approval.approval_id,
                action=action,
                query_string=query_string,
                matched_files=matched_files,
            ).model_dump(mode="json")
        )

    def _spend_approval(
        self,
        key: str,
        action: BulkAction,
        query_string: str,
        approved_bulk_ids: frozenset[UUID],
    ) -> ApprovedQuery:
        """Take the approval given for this call, once.

        Three things have to agree before anything is dispatched, and each closes a way
        the dispatch could differ from what was shown:

        - the record is read with GETDEL, so an answer is gone before anything is
          queued and cannot be spent twice;
        - the client named this record's ``approval_id`` in the request it answered
          with, so the answer is to the question that was asked rather than to a call
          id;
        - the action and query string are the ones the record describes, because an
          approval may come back with edited arguments.
        """
        raw_approval = self._redis_client.getdel(key)
        if raw_approval is None:
            raise ModelRetry(
                "Nothing was dispatched: the approval for this action is no longer "
                "held, so there is no record of what was agreed to. Call the action "
                "again to ask afresh."
            )

        approval = BulkApproval.model_validate_json(raw_approval)
        if approval.approval_id not in approved_bulk_ids:
            logger.warning(
                "Approval %s was not named by the answer that would spend it",
                approval.approval_id,
            )
            raise ToolFailed(
                "Nothing was dispatched: the answer does not name the approval it is "
                "answering, so there is nothing to show it was given for this action."
            )

        if approval.action != action or approval.query_string != query_string:
            logger.warning(
                "Approval %s was given for %s over '%s', not for %s over '%s'",
                approval.approval_id,
                approval.action,
                approval.query_string,
                action,
                query_string,
            )
            raise ToolFailed(
                "Nothing was dispatched: this call is not the one that was approved."
            )

        logger.info(
            "Dispatching bulk action %s over '%s' on approval %s for %d files",
            action,
            query_string,
            approval.approval_id,
            approval.matched_files,
        )
        return ApprovedQuery(
            query=QueryParameters(
                query_id=approval.query_id,
                keep_alive=AI_PIT_KEEPALIVE,
                search_string=approval.query_string,
            ),
            matched_files=approval.matched_files,
        )

    def bulk_summarize(
        self, ctx: RunContext[AgentDeps], query_string: str
    ) -> BulkDispatchResult:
        """Queue AI summarization for every file a query matches.

        Returns once the work is queued. Summarizing a corpus takes hours, so report
        it as started rather than finished.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as returned by
                suggest_queries, selecting the files to summarize.
        """
        approved = self._approved_query(
            ctx, BulkEnrichmentAction.SUMMARIZE, query_string
        )
        self._task_scheduling_service.dispatch_summarize_files(query=approved.query)
        return BulkDispatchResult(
            action=BulkEnrichmentAction.SUMMARIZE,
            query_string=query_string,
            matched_files=approved.matched_files,
        )

    def bulk_translate(
        self, ctx: RunContext[AgentDeps], query_string: str, source_language: str
    ) -> BulkDispatchResult:
        """Queue AI translation for every file a query matches.

        Returns once the work is queued. Translating a corpus takes hours, so report
        it as started rather than finished. The target language is configured
        server-side.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as returned by
                suggest_queries, selecting the files to translate.
            source_language: BCP 47 / ISO 639-1 language code the matched documents
                are written in, e.g. "de", "fr", "en".
        """
        approved = self._approved_query(
            ctx, BulkEnrichmentAction.TRANSLATE, query_string
        )
        self._task_scheduling_service.dispatch_translate_files(
            query=approved.query, lang=source_language
        )
        return BulkDispatchResult(
            action=BulkEnrichmentAction.TRANSLATE,
            query_string=query_string,
            matched_files=approved.matched_files,
        )

    def bulk_describe_images(
        self, ctx: RunContext[AgentDeps], query_string: str
    ) -> BulkDispatchResult:
        """Queue AI image description for every file a query matches.

        Returns once the work is queued. Only image files are described; a query that
        matches other files describes nothing for them.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as returned by
                suggest_queries, selecting the files to describe.
        """
        approved = self._approved_query(
            ctx, BulkEnrichmentAction.DESCRIBE_IMAGES, query_string
        )
        self._task_scheduling_service.dispatch_describe_images(query=approved.query)
        return BulkDispatchResult(
            action=BulkEnrichmentAction.DESCRIBE_IMAGES,
            query_string=query_string,
            matched_files=approved.matched_files,
        )

    def bulk_add_tags(
        self, ctx: RunContext[AgentDeps], query_string: str, tags: Tags
    ) -> BulkDispatchResult:
        """Add tags to every file a query matches.

        Returns once the work is queued; the tags appear on the matched files shortly
        afterwards. There is no undo.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as returned by
                suggest_queries, selecting the files to tag.
            tags: Tag names to add to every matched file. At least one.
        """
        approved = self._approved_query(ctx, BulkMetadataAction.ADD_TAGS, query_string)
        self._task_scheduling_service.dispatch_add_tags_to_files(
            query=approved.query, tags=tags
        )
        return BulkDispatchResult(
            action=BulkMetadataAction.ADD_TAGS,
            query_string=query_string,
            matched_files=approved.matched_files,
        )

    def bulk_update_files(
        self,
        ctx: RunContext[AgentDeps],
        query_string: str,
        request: UpdateFileRequest,
    ) -> BulkDispatchResult:
        """Set the seen, flagged or hidden state of every file a query matches.

        At least one flag has to be given; a flag left out of request keeps its
        current value on every matched file. Returns once the work is queued. There is
        no undo.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as returned by
                suggest_queries, selecting the files to write to.
            request: The flags to set on every matched file: seen marks them as seen
                (True) or unseen (False), flagged flags (True) or unflags (False)
                them, and hidden hides (True) or unhides (False) them.
        """
        if request.sets_nothing:
            raise ModelRetry("Give at least one of seen, flagged or hidden to update.")
        approved = self._approved_query(
            ctx, BulkMetadataAction.UPDATE_FILES, query_string
        )
        self._task_scheduling_service.dispatch_update(
            query=approved.query, request=request
        )
        return BulkDispatchResult(
            action=BulkMetadataAction.UPDATE_FILES,
            query_string=query_string,
            matched_files=approved.matched_files,
        )
