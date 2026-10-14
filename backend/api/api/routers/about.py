from fastapi import APIRouter
from pydantic import BaseModel

from api.settings import settings

router = APIRouter()


class AboutInfo(BaseModel):
    """Chart metadata of the Loom release serving this request."""

    name: str
    version: str
    app_version: str
    description: str


@router.get("")
def get_about() -> AboutInfo:
    return AboutInfo(
        name=settings.chart_name,
        version=settings.chart_version,
        app_version=settings.chart_app_version,
        description=settings.chart_description,
    )
