"""Initialize the fastapi app."""

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from api.routers import (
    ai,
    archives,
    caching,
    docs,
    files,
    index,
    queues,
    summarization,
    tags,
    translation,
    websocket,
)
from api.settings import settings

STATIC_ASSETS_PATH = Path(__file__).parent.parent / "static"


def remove_null_from_any_of(schema: Dict[str, Any]) -> Dict[str, Any]:
    if "properties" in schema:
        for prop, prop_schema in schema["properties"].items():
            if "anyOf" in prop_schema:
                any_of = prop_schema["anyOf"]
                if len(any_of) == 2 and {"type": "null"} in any_of:
                    schema["properties"][prop] = [
                        x for x in any_of if x != {"type": "null"}
                    ][0]
                    if "required" in schema:
                        schema["required"] = [
                            x for x in schema["required"] if x != prop
                        ]
                else:
                    raise NotImplementedError(
                        "anyOf with more than 2 elements not supported"
                    )

    return schema


def patch_openapi_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    for component_name, component_schema in schema["components"]["schemas"].items():
        schema["components"]["schemas"][component_name] = remove_null_from_any_of(
            component_schema
        )
    return schema


def init_api() -> FastAPI:
    api = FastAPI(
        title=settings.app_title,
        docs_url=None,
        redoc_url=None,
        servers=[{"url": "/", "description": "Loom API"}],
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # static assets
    api.mount("/static", StaticFiles(directory=STATIC_ASSETS_PATH), name="static")

    # register routers
    api.include_router(docs.router)
    api.include_router(archives.router, prefix="/v1/archive", tags=["archives"])
    api.include_router(tags.router, prefix="/v1/files/tags", tags=["tags"])
    api.include_router(queues.router, prefix="/v1/queues", tags=["queues"])
    api.include_router(
        translation.router, prefix="/v1/files/translation", tags=["translation"]
    )
    api.include_router(index.router, prefix="/v1/files/index", tags=["index"])
    api.include_router(caching.router, prefix="/v1/caching", tags=["caching"])
    api.include_router(websocket.router, prefix="/v1/websocket", tags=["websocket"])
    api.include_router(
        summarization.router, prefix="/v1/files/summarization", tags=["summarization"]
    )
    api.include_router(ai.router, prefix="/v1/ai", tags=["ai"])
    api.include_router(files.router, prefix="/v1/files", tags=["files"])

    def custom_openapi():
        if api.openapi_schema:
            return api.openapi_schema

        openapi_schema = get_openapi(
            title=api.title,
            version=api.version,
            openapi_version=api.openapi_version,
            summary=api.summary,
            description=api.description,
            terms_of_service=api.terms_of_service,
            contact=api.contact,
            license_info=api.license_info,
            routes=api.routes,
            webhooks=api.webhooks.routes,
            tags=api.openapi_tags,
            servers=api.servers,
            separate_input_output_schemas=api.separate_input_output_schemas,
        )
        # Patching the openapi schema so the frontend code generator can handle it
        # If a model has a property that is optional (e.g.`sha256: str | None`) this
        # will be represented as `anyOf` in the openapi schema.
        # The frontend code generator does not handle this correctly, so we remove the
        # `null` type from the `anyOf` and remove the property from the `required` list.
        api.openapi_schema = patch_openapi_schema(openapi_schema)

        return api.openapi_schema

    # This is the recommended way to customize OpenAPI schema in FastAPI
    # https://fastapi.tiangolo.com/how-to/extending-openapi/
    api.openapi = custom_openapi  # type: ignore

    return api
