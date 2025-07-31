from common.dependencies import get_celery_app
from common.file.file_repository import Tag

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, IndexingPersister)
def persist_add_tags(persister: IndexingPersister, tags: list[Tag]):
    """Persists the tags."""
    for tag in tags:
        persister.add_tag(tag)


@persisting_task(app, IndexingPersister)
def persist_remove_tag(persister: IndexingPersister, tag: Tag):
    """Persists the tag."""
    persister.remove_tag(tag)
