from datetime import datetime
from pathlib import PurePath
from uuid import uuid4

from bson import ObjectId

from common.services.query_builder import KeepAlive, QueryParameters


class TestValueDefaults:  # pylint: disable=too-few-public-methods
    test_uuid = uuid4()
    test_int = 123
    test_long = 1125899906842624
    test_float = 0.321
    test_str = "just a test"
    test_keep_alive: KeepAlive = "10s"
    test_empty_list: list = []
    test_str_list: list[str] = ["a", "list", "of", "a", "string"]
    test_str_list_no_duplicates = [
        "just",
        "a",
        "test",
        "for",
        "testing",
        "the",
        "thing",
    ]
    test_object_id = ObjectId()
    test_object_id_str = str(ObjectId())
    test_datetime = datetime.now()
    test_pure_path = PurePath("/a/path/to/nowhere.txt")
    test_uuid_list = [uuid4(), uuid4()]
    test_bool = False
    test_empty_dict: dict = {}
    test_str_str_dict = {"A": "B", "C": "D", "E": "F", "G": "H"}
    test_query = QueryParameters(
        query_id=str(uuid4()),
        search_string="Query something",
        languages=["us", "cz", "de"],
        keep_alive=test_keep_alive,
    )
    test_vector = [0.1, 0.3, 3.1415, 123]
