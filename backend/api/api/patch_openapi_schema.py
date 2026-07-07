from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def _remove_null_from_any_of(schema: Dict[str, Any]) -> Dict[str, Any]:
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


def _flatten_nullable_anyof(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Rewrite nullable ``anyOf`` properties across all component schemas.

    OpenAPI represents ``str | None`` (and similar optional types) as ``anyOf: [{...},
    {"type": "null"}]``. The frontend code generator does not handle this representation
    correctly, so this transformation removes the ``null`` branch from the ``anyOf`` and
    marks the property as optional by removing it from the schema's ``required`` list.
    """
    for component_name, component_schema in schema["components"]["schemas"].items():
        schema["components"]["schemas"][component_name] = _remove_null_from_any_of(
            component_schema
        )

    return schema


def patch_openapi_schema_for_app(app: FastAPI):
    """Patch openapi schema for app (in place)"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        summary=app.summary,
        description=app.description,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
        routes=app.routes,
        webhooks=app.webhooks.routes,
        tags=app.openapi_tags,
        servers=app.servers,
        separate_input_output_schemas=app.separate_input_output_schemas,
    )
    openapi_schema = _flatten_nullable_anyof(openapi_schema)
    app.openapi_schema = openapi_schema
