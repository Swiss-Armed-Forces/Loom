from uuid import UUID

from common.models.mongo_repository import BaseMongoRepository, MongoRepositoryObject


class RootTaskInformation(MongoRepositoryObject):
    root_task_id: UUID
    object_id: UUID


class RootTaskInformationRepository(BaseMongoRepository[RootTaskInformation]):
    @property
    def _object_type(self) -> type[RootTaskInformation]:
        return RootTaskInformation

    def get_by_root_task_id(self, root_task_id: UUID) -> RootTaskInformation:
        root_task_info = self._repo.find_one_by({"root_task_id": root_task_id})
        if root_task_info is None:
            raise ValueError(f"Root task info with id {root_task_id} not found")
        return root_task_info
