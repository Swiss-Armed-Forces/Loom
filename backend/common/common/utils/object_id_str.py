from bson import ObjectId
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


def check_object_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")
    return value


ObjectIdStr = Annotated[str, AfterValidator(check_object_id)]
