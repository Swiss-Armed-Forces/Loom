from common.dependencies import (  # Adjust import based on your structure
    get_imap_service,
)
from common.file.file_repository import ImapPurePath
from common.services.imap_service import IMAPService, IMAPServiceError
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

default_imap_service = Depends(get_imap_service)


@router.get("/folder/messages/count")
def count_messages(
    folder: ImapPurePath | None = None,
    recurse: bool = False,
    imap_service: IMAPService = default_imap_service,
) -> int:
    try:
        count = imap_service.count_messages(folder=folder, recurse=recurse)
    except IMAPServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return count


@router.put("/folder/subscribe")
def subscribe_folder(
    folder: ImapPurePath | None = None,
    recurse: bool = False,
    imap_service: IMAPService = default_imap_service,
):
    try:
        imap_service.subscribe_folder(folder=folder, recurse=recurse)
    except IMAPServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/folder/unsubscribe")
def unsubscribe_folder(
    folder: ImapPurePath | None = None,
    recurse: bool = False,
    imap_service: IMAPService = default_imap_service,
):
    try:
        imap_service.unsubscribe_folder(folder=folder, recurse=recurse)
    except IMAPServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
