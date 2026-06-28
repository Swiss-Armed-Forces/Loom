from pathlib import Path
from typing import Any

from common.services.query_builder import QueryBuilderException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.metrics import init_metrics
from api.patch_openapi_schema import patch_openapi_schema_for_app
from api.routers import (
    ai,
    aitools,
    archives,
    beat,
    caching,
    celery_inspect,
    complete_estimate,
    docs,
    files,
    image_description,
    imap,
    index,
    init_elasticsearch,
    metrics,
    queues,
    summarization,
    tags,
    translation,
    websocket,
    wipe_data,
)
from api.settings import settings

STATIC_ASSETS_PATH = Path(__file__).parent.parent / "static"


def init_api(collect_metrics=True) -> FastAPI:
    api = FastAPI(
        title=settings.app_title,
        docs_url=None,
        redoc_url=None,
        servers=[{"url": "/", "description": "Loom API"}],
    )

    # metrics
    if collect_metrics:
        init_metrics(api)

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # global exception handlers
    api.add_exception_handler(
        QueryBuilderException,
        lambda _, ex: JSONResponse(status_code=400, content={"detail": str(ex)}),
    )

    # static assets
    api.mount("/static", StaticFiles(directory=STATIC_ASSETS_PATH), name="static")

    # register routers
    api.include_router(docs.router)
    api.include_router(metrics.router, prefix="/v1/metrics", tags=["metrics"])
    api.include_router(archives.router, prefix="/v1/archive", tags=["archives"])
    api.include_router(tags.router, prefix="/v1/files/tags", tags=["tags"])
    api.include_router(queues.router, prefix="/v1/queues", tags=["queues"])
    api.include_router(
        complete_estimate.router,
        prefix="/v1/complete-estimate",
        tags=["complete-estimate"],
    )
    api.include_router(
        celery_inspect.router,
        prefix="/v1/celery-inspect",
        tags=["celery-inspect"],
    )
    api.include_router(
        translation.router, prefix="/v1/files/translation", tags=["translation"]
    )
    api.include_router(index.router, prefix="/v1/files/index", tags=["index"])
    api.include_router(caching.router, prefix="/v1/caching", tags=["caching"])
    api.include_router(websocket.router, prefix="/v1/websocket", tags=["websocket"])
    api.include_router(
        summarization.router, prefix="/v1/files/summarization", tags=["summarization"]
    )
    api.include_router(
        image_description.router,
        prefix="/v1/files/image_description",
        tags=["image_description"],
    )
    api.include_router(ai.router, prefix="/v1/ai", tags=["ai"])
    api.include_router(aitools.router, prefix="/v1/aitools", tags=["aitools"])
    api.include_router(files.router, prefix="/v1/files", tags=["files"])
    api.include_router(imap.router, prefix="/v1/imap", tags=["imap"])
    api.include_router(beat.router, prefix="/v1/beat", tags=["beat"])
    api.include_router(wipe_data.router, prefix="/v1/wipe-data", tags=["wipe-data"])
    api.include_router(
        init_elasticsearch.router,
        prefix="/v1/init/elasticsearch",
        tags=["init"],
    )

    def custom_openapi() -> dict[str, Any]:
        if api.openapi_schema:
            return api.openapi_schema
        patch_openapi_schema_for_app(api)
        if api.openapi_schema is None:
            raise RuntimeError("openapi_schema is None")
        return api.openapi_schema

    # This is the recommended way to customize OpenAPI schema in FastAPI
    # https://fastapi.tiangolo.com/how-to/extending-openapi/
    api.openapi = custom_openapi  # type: ignore

    return api
