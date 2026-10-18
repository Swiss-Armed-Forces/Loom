from uuid import UUID

from common.ai_context.tool_models import FolderEntry, ListFolderContentsResult
from common.dependencies import get_celery_app, get_file_repository
from common.models.cursor_pagination import SearchAfterCursor
from common.services.query_builder import QueryParameters

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.settings import settings

app = get_celery_app()


@app.task(base=AiContextProcessingTask)
def list_folder_contents_work_task(
    folder_path: str, after_cursor: SearchAfterCursor | None = None
) -> ListFolderContentsResult:
    file_repository = get_file_repository()
    query = QueryParameters(search_string="*")
    # The repository paginates on a raw path key. Wrapping it binds the cursor to
    # this tool and this folder, so a cursor from somewhere else fails loudly: a
    # foreign one would otherwise range-filter to nothing and report an empty
    # folder.
    digest = SearchAfterCursor.digest(folder_path)
    if after_cursor is not None:
        after_cursor.validate_for(
            expected_src="list_folder_contents",
            expected_digest=digest,
        )
    result = file_repository.get_full_paths_by_query(
        query=query,
        tree_node_directory_path=folder_path,
        after=str(after_cursor.last_sort[0]) if after_cursor is not None else None,
        # Explicit, so the number of entries a page spends on the model's context
        # does not follow whatever the folder view is tuned to.
        page_size=settings.tool.browse.page_size,
    )
    entries = [
        FolderEntry(
            full_path=str(node.full_path),
            is_file=node.file_id is not None,
            file_count=node.file_count,
            file_id=node.file_id,
        )
        for node in result.nodes
    ]
    next_cursor = (
        SearchAfterCursor(
            src="list_folder_contents",
            last_sort=[result.next_page_cursor],
            query_digest=digest,
        )
        if result.next_page_cursor is not None
        else None
    )
    return ListFolderContentsResult(
        folder_path=folder_path,
        entries=entries,
        has_more=next_cursor is not None,
        next_cursor=next_cursor,
    )


@app.task(bind=True, base=AiContextProcessingTask)
def list_folder_contents_tool_task(
    self: AiContextProcessingTask,
    folder_path: str,
    _context_id: UUID,
    after_cursor: SearchAfterCursor | None = None,
) -> ListFolderContentsResult:
    return self.replace(list_folder_contents_work_task.s(folder_path, after_cursor))
