from pathlib import PurePath

from common.dependencies import (  # Adjust import based on your structure
    get_imap_service,
)
from common.services.imap_service import IMAPService
from fastapi import APIRouter, Depends

router = APIRouter()

default_imap_service = Depends(get_imap_service)


@router.get("/messages/count")
async def count_imap_messages(
    folder: str | None = None,
    recurse: bool = False,
    imap_service: IMAPService = default_imap_service,
) -> int:
    folder_path = PurePath(folder) if folder else None
    count = imap_service.count_messages(folder=folder_path, recurse=recurse)
    return count
