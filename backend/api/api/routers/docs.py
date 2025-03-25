import logging

from fastapi import APIRouter
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import RedirectResponse

from api.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=settings.openapi_url,
        title=f"{settings.app_title} - Swagger UI",
        oauth2_redirect_url=settings.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@router.get(settings.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@router.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=settings.openapi_url,
        title=f"{settings.app_title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
