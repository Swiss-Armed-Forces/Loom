import logging
from collections.abc import Callable
from enum import StrEnum
from typing import Annotated

from common.dependencies import get_wipe_service
from common.services.wipe_service import WipeService
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

CONFIRMATION_STRING = "wipe"
default_wipe_service = Depends(get_wipe_service)


class WipeComponent(StrEnum):
    CELERY = "celery"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"
    S3 = "s3"
    FILE_STORAGE = "file_storage"
    LAZYBYTES = "lazybytes"
    IMAP = "imap"


_WIPE_DISPATCH: dict[WipeComponent, Callable[[WipeService], None]] = {
    WipeComponent.CELERY: lambda s: s.wipe_celery(),
    WipeComponent.ELASTICSEARCH: lambda s: s.wipe_elasticsearch(),
    WipeComponent.REDIS: lambda s: s.wipe_redis(),
    WipeComponent.S3: lambda s: s.wipe_s3(),
    WipeComponent.FILE_STORAGE: lambda s: s.wipe_file_storage(),
    WipeComponent.LAZYBYTES: lambda s: s.wipe_lazybytes(),
    WipeComponent.IMAP: lambda s: s.wipe_imap(),
}


@router.post("/")
def wipe_data_endpoint(
    confirmation: Annotated[
        str,
        Query(description=f'Must equal "{CONFIRMATION_STRING}" to confirm the wipe.'),
    ],
    components: Annotated[
        list[WipeComponent] | None,
        Query(description="Components to wipe. If omitted, all components are wiped."),
    ] = None,
    wipe_service: WipeService = default_wipe_service,
) -> None:
    if confirmation != CONFIRMATION_STRING:
        raise HTTPException(status_code=400, detail="Invalid confirmation string")
    resolved = components or list(WipeComponent)
    for component in resolved:
        logger.info("Wiping component via API: %s", component)
        _WIPE_DISPATCH[component](wipe_service)
