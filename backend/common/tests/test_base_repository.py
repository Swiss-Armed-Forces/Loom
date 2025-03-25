from uuid import UUID, uuid4

from pydantic import Field

from common.models.base_repository import BaseRepository, RepositoryObject


class _TestRepositoryObject(RepositoryObject):
    id_field: UUID = Field(default_factory=uuid4)

    @property
    def id_(self) -> UUID:
        return self.id_field


class _TestRepository(BaseRepository[_TestRepositoryObject]):
    _repo: dict[UUID, _TestRepositoryObject] = {}

    @property
    def _object_type(self) -> type[_TestRepositoryObject]:
        return _TestRepositoryObject

    def save(self, obj: _TestRepositoryObject):
        self._repo[obj.id_] = obj

    def get_by_id(self, id_: UUID) -> _TestRepositoryObject:
        return self._repo[id_]

    def get_all(self) -> list[_TestRepositoryObject]:
        return self._repo.values()


def test_base_repo_save_and_get():
    repo = _TestRepository()
    obj = _TestRepositoryObject()
    repo.save(obj)
    assert obj == repo.get_by_id(obj.id_)
    assert obj in repo.get_all()
