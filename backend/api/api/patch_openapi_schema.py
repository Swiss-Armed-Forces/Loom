from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


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
    """Patching the openapi schema so the frontend code generator can handle it.

    If a model has a property that is optional (e.g.`sha256: str | None`) this
    will be represented as `anyOf` in the openapi schema.
    The frontend code generator does not handle this correctly, so we remove the
    `null` type from the `anyOf` and remove the property from the `required` list.
    """
    for component_name, component_schema in schema["components"]["schemas"].items():
        schema["components"]["schemas"][component_name] = remove_null_from_any_of(
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
    app.openapi_schema = patch_openapi_schema(openapi_schema)
