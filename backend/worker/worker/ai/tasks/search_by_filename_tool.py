from uuid import UUID

from common.ai_context.tool_models import FilenameSearchEntry, SearchByFilenameResult
from common.dependencies import get_celery_app, get_file_repository
from common.services.query_builder import QueryParameters

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask

app = get_celery_app()


@app.task(base=AiContextProcessingTask)
def search_by_filename_work_task(filename: str) -> SearchByFilenameResult:
    file_repository = get_file_repository()
    query = QueryParameters(search_string="*")
    result = file_repository.get_flat_files_by_query(query=query, filename=filename)
    files = [
        FilenameSearchEntry(full_path=str(n.full_path), file_id=n.file_id)
        for n in result.nodes
        if n.file_id is not None
    ]
    return SearchByFilenameResult(query=filename, files=files)


@app.task(bind=True, base=AiContextProcessingTask)
def search_by_filename_tool_task(
    self: AiContextProcessingTask, filename: str, _context_id: UUID
) -> SearchByFilenameResult:
    return self.replace(search_by_filename_work_task.s(filename))
