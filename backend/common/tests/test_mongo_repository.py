import logging
from unittest.mock import MagicMock

import pytest
from pydantic import ConfigDict
from pydantic_mongo import AbstractRepository
from pymongo.database import Database

from common.models.base_repository import RepositoryObject
from common.models.es_repository import BaseEsRepository
from common.models.mongo_repository import BaseMongoRepository, MongoRepositoryObject
from mocks.test_value_defaults import TestValueDefaults

logger = logging.getLogger(__name__)


class _TestMongoRepositoryObject(MongoRepositoryObject):
    test_int: int
    test_str: str
    test_str_list: list[str]


class _TestMongoRepository(BaseMongoRepository[_TestMongoRepositoryObject]):
    def __init__(
        self,
        mock_types=False,
    ):
        # Note: we use on purpose not spec=type[...] here, mostly because
        # that does not work work mocking @classmethods.
        # I am not quite sure why.. Ahhh ducktyping..
        self.object_type: _TestMongoRepositoryObject | MagicMock = (
            _TestMongoRepositoryObject
            if not mock_types
            else MagicMock(spec=_TestMongoRepositoryObject)
        )
        # Always mock the repo
        self.repo = MagicMock(spec=AbstractRepository)
        super().__init__(None)

    def _get_mongo_repository(
        self, database: Database
    ) -> AbstractRepository[_TestMongoRepositoryObject]:
        return self.repo

    @property
    def _object_type(self) -> type[_TestMongoRepositoryObject]:
        return self.object_type


class _TestInstances(MongoRepositoryObject):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    object: RepositoryObject


REPOSITORY_TEST_INSTANCES: dict[type[BaseEsRepository], list[_TestInstances]] = {
    _TestMongoRepository: [
        _TestInstances(
            object=_TestMongoRepositoryObject(
                # MongoRepositoryObject
                id=TestValueDefaults.test_object_id,
                # _TestEsRepositoryObject
                test_int=TestValueDefaults.test_int,
                test_str=TestValueDefaults.test_str,
                test_str_list=TestValueDefaults.test_str_list,
            ),
        )
    ],
}


def get_test_repository_object_instances() -> list[_TestMongoRepositoryObject]:
    def testcases():
        for test_instance in REPOSITORY_TEST_INSTANCES[_TestMongoRepository]:
            yield test_instance.object

    return list(testcases())


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_get_by_id(obj: _TestMongoRepositoryObject):
    repository = _TestMongoRepository(mock_types=True)

    repository.get_by_id(obj.id_)

    repository.repo.find_one_by_id.assert_called_once_with(
        obj.id_,
    )


def test_es_repository_get_all():
    repository = _TestMongoRepository(mock_types=True)
    repository.get_all()

    repository.repo.find_by.assert_called_once_with({"_id": "$all"})


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_save(obj: _TestMongoRepositoryObject):
    repository = _TestMongoRepository(mock_types=True)

    repository.save(obj)

    repository.repo.save.assert_called_once_with(obj)
