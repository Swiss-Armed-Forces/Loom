from uuid import UUID

from common.ai_context.tool_models import FolderEntry, ListFolderContentsResult
from common.dependencies import get_celery_app, get_file_repository
from common.services.query_builder import QueryParameters

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask

app = get_celery_app()


@app.task(base=AiContextProcessingTask)
def list_folder_contents_work_task(folder_path: str) -> ListFolderContentsResult:
    file_repository = get_file_repository()
    query = QueryParameters(search_string="*")
    result = file_repository.get_full_paths_by_query(
        query=query, tree_node_directory_path=folder_path
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
    return ListFolderContentsResult(folder_path=folder_path, entries=entries)


@app.task(bind=True, base=AiContextProcessingTask)
def list_folder_contents_tool_task(
    self: AiContextProcessingTask, folder_path: str, _context_id: UUID
) -> ListFolderContentsResult:
    return self.replace(list_folder_contents_work_task.s(folder_path))
