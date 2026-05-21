from uuid import UUID, uuid4

from pydantic import Field
from pydantic.main import IncEx

from common.models.base_repository import BaseRepository, RepositoryObject


class _TestRepositoryObject(RepositoryObject):
    id_field: UUID = Field(default_factory=uuid4)
    name: str = ""

    @property
    def id_(self) -> UUID:
        return self.id_field


class _TestRepository(BaseRepository[_TestRepositoryObject]):
    def __init__(self):
        super().__init__()
        self._repo: dict[UUID, _TestRepositoryObject] = {}

    @property
    def _object_type(self) -> type[_TestRepositoryObject]:
        return _TestRepositoryObject

    def save(self, obj: _TestRepositoryObject):
        self._repo[obj.id_] = obj

    def get_by_id(self, id_: UUID) -> _TestRepositoryObject:
        return self._repo[id_]

    def get_all(self) -> list[_TestRepositoryObject]:
        return list(self._repo.values())

    def update(
        self,
        obj: _TestRepositoryObject,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
    ):
        del include, exclude  # unused in test implementation
        self._repo[obj.id_] = obj

    def count(self) -> int:
        return len(self._repo)

    def flush(self) -> None:
        self._repo.clear()


def test_base_repo_save_and_get():
    repo = _TestRepository()
    obj = _TestRepositoryObject()
    repo.save(obj)
    assert obj == repo.get_by_id(obj.id_)


def test_base_repo_get_all():
    repo = _TestRepository()
    obj1 = _TestRepositoryObject(name="first")
    obj2 = _TestRepositoryObject(name="second")
    repo.save(obj1)
    repo.save(obj2)

    all_objects = repo.get_all()

    assert isinstance(all_objects, list)
    assert len(all_objects) == 2
    assert obj1 in all_objects
    assert obj2 in all_objects


def test_base_repo_update():
    repo = _TestRepository()
    obj = _TestRepositoryObject(name="original")
    repo.save(obj)

    obj.name = "updated"
    repo.update(obj)

    retrieved = repo.get_by_id(obj.id_)
    assert retrieved.name == "updated"


def test_base_repo_count():
    repo = _TestRepository()
    assert repo.count() == 0
    repo.save(_TestRepositoryObject())
    repo.save(_TestRepositoryObject())
    assert repo.count() == 2


def test_base_repo_flush():
    repo = _TestRepository()
    repo.save(_TestRepositoryObject())
    repo.save(_TestRepositoryObject())
    repo.flush()
    assert repo.count() == 0
