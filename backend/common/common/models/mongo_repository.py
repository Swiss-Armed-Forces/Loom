import logging
from typing import Generic, TypeVar

from bson import ObjectId
from pydantic import Field
from pydantic_mongo import (  # type: ignore[import-untyped]
    AbstractRepository,
    ObjectIdField,
)
from pymongo.database import Database

from common.models.base_repository import BaseRepository, RepositoryObject

logger = logging.getLogger(__name__)


class MongoRepositoryObject(RepositoryObject):
    id: ObjectIdField = Field(default_factory=ObjectIdField)
    # Sadly, defining id as property does not work with
    # pydantic_mongo. The reason is that properties do not
    # apper in the Type.model_fields list hence the folloginw check
    # fails:
    # https://github.com/jefersondaniel/pydantic-mongo/blob/2dc51499cda997af026efa6c5bd32892a457cbd1/pydantic_mongo/abstract_repository.py#L58
    #
    # We should really open an issue for this...
    #
    # @computed_field
    # @property
    # @abstractmethod
    # def id(self) -> ObjectIdField:
    #    raise NotImplementedError("id field not implemented")

    @property
    def id_(self) -> ObjectIdField:
        return self.id


MongoRepositoryObjectT = TypeVar("MongoRepositoryObjectT", bound=MongoRepositoryObject)


class BaseMongoRepository(
    BaseRepository[MongoRepositoryObjectT],
    Generic[MongoRepositoryObjectT],
):
    """Repository for CRUD operations backed by Mongo DB."""

    def __init__(self, database: Database, *args, **kwargs):
        self._repo = self._get_mongo_repository(database)
        super().__init__(*args, **kwargs)

    def _get_mongo_repository(
        self, database: Database
    ) -> AbstractRepository[MongoRepositoryObjectT]:
        class _MongoRepository(AbstractRepository[MongoRepositoryObjectT]):
            class Meta:  # pylint: disable=too-few-public-methods
                collection_name = self._object_type.__name__
                document_class: type[MongoRepositoryObjectT] = self._object_type

        return _MongoRepository(database=database)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        MONGO_REPOSITORY_TYPES.append(cls)

    def save(self, obj: MongoRepositoryObjectT):
        self._repo.save(obj)

    def get_by_id(self, id_: ObjectId) -> MongoRepositoryObjectT | None:
        return self._repo.find_one_by_id(id_)

    def get_all(self) -> list[MongoRepositoryObjectT]:
        return list(self._repo.find_by({"_id": "$all"}))


# A list of all known repositories
MONGO_REPOSITORY_TYPES: list[type[BaseMongoRepository]] = []
