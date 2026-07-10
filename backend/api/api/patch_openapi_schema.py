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


def _flatten_nullable_anyof_in_param_schema(
    param_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """Collapse ``anyOf: [{...}, {type: null}]`` in an individual parameter schema."""
    if "anyOf" not in param_schema:
        return param_schema
    any_of = param_schema["anyOf"]
    if len(any_of) == 2 and {"type": "null"} in any_of:
        non_null = [x for x in any_of if x != {"type": "null"}][0]
        # Preserve extra metadata (description, title, …) from the outer schema.
        merged = {k: v for k, v in param_schema.items() if k not in ("anyOf",)}
        merged.update(non_null)
        return merged
    return param_schema


def _flatten_nullable_anyof(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Rewrite nullable ``anyOf`` properties across all component schemas and inline
    path parameter schemas.

    OpenAPI represents ``str | None`` (and similar optional types) as ``anyOf: [{...},
    {"type": "null"}]``. The frontend code generator does not handle this representation
    correctly, so this transformation removes the ``null`` branch from the ``anyOf`` and
    marks the property as optional by removing it from the schema's ``required`` list.
    """
    for component_name, component_schema in schema["components"]["schemas"].items():
        schema["components"]["schemas"][component_name] = _remove_null_from_any_of(
            component_schema
        )

    # Also flatten inline nullable schemas in path/query parameters so that
    # the TypeScript generator does not create spurious model classes (e.g. After).
    for _path, path_item in schema.get("paths", {}).items():
        for _method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            for param in operation.get("parameters", []):
                if isinstance(param.get("schema"), dict):
                    param["schema"] = _flatten_nullable_anyof_in_param_schema(
                        param["schema"]
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
