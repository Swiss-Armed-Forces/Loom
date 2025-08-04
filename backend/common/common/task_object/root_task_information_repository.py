from uuid import UUID

from pydantic import Field

from common.models.mongo_repository import BaseMongoRepository, MongoRepositoryObject


class RootTaskInformation(MongoRepositoryObject):
    root_task_id: UUID
    object_id: UUID
    started_async_branches: list[UUID] = Field(default_factory=list)
    completed_async_branches: list[UUID] = Field(default_factory=list)


class RootTaskInformationRepository(BaseMongoRepository[RootTaskInformation]):
    @property
    def _object_type(self) -> type[RootTaskInformation]:
        return RootTaskInformation

    def get_by_root_task_id(self, root_task_id: UUID) -> RootTaskInformation:
        root_task_info = self._repo.find_one_by({"root_task_id": root_task_id})
        if root_task_info is None:
            raise ValueError(f"Root task info with id {root_task_id} not found")
        return root_task_info

    def add_started_async_branch(self, root_task_id: UUID, async_branch_id: UUID):
        """Atomic update of started_async_branches."""
        collction = self._repo.get_collection()
        result = collction.update_one(
            {"root_task_id": root_task_id},
            {"$push": {"started_async_branches": async_branch_id}},
        )
        if result.modified_count != 1:
            raise ValueError(f"Failed registering started async branch: {result}")

    def add_completed_async_branch(self, root_task_id: UUID, async_branch_id: UUID):
        """Atomic update of completed_async_branches."""
        collction = self._repo.get_collection()
        result = collction.update_one(
            {"root_task_id": root_task_id},
            {"$push": {"completed_async_branches": async_branch_id}},
        )
        if result.modified_count != 1:
            raise ValueError(f"Failed registering completed async branch: {result}")
