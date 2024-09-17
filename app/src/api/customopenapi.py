from fastapi.openapi.utils import get_openapi

from ..settings import API_ROUTE

title = "Twitter-clone API"
description = "API for twitter-clone"
version = "1.0.0"
schema_for_remove = ["HTTPValidationError", "ValidationError"]
schema_for_rename = {"Body_post_image_medias_post": "MediaPost"}


def remove_422s(openapi_schema) -> None:
    # https://fastapi.tiangolo.com/how-to/extending-openapi/#serve-the-static-files
    paths = openapi_schema["paths"]
    for _path, operations in paths.items():
        for _method, metadata in operations.items():
            metadata["responses"].pop("422", None)


def remove_schemas(openapi_schema, schema_list) -> None:
    schemas = openapi_schema["components"]["schemas"]
    for schema_name in schema_list:
        schemas.pop(schema_name, None)


def recursive_rename(target: dict, value, new_value) -> None:
    for k, v in target.items():
        if v == value:
            target[k] = new_value
        if isinstance(v, dict):
            recursive_rename(v, value, new_value)


def rename_schema(openapi_schema, schema_name, new_name) -> None:

    # Переименование в схемах
    schemas = openapi_schema["components"]["schemas"]
    description = schemas.pop(schema_name, None)
    schemas[new_name] = description

    # Переименование в ссылках
    paths = openapi_schema["paths"]
    ref = f"#/components/schemas/{schema_name}"
    new_ref = f"#/components/schemas/{new_name}"
    recursive_rename(paths, ref, new_ref)


def add_api_prefix(openapi_schema, prefix):
    paths: dict = openapi_schema["paths"]
    new_paths = {}
    for path in paths.keys():
        new_paths[prefix + path] = paths[path]
    openapi_schema["paths"] = new_paths


def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
    )
    # Удаление 422
    remove_422s(openapi_schema)

    # Удаление не нужных схем
    remove_schemas(openapi_schema, schema_for_remove)

    # Переименование схемы
    for name, new_name in schema_for_rename.items():
        rename_schema(openapi_schema, name, new_name)
    # Сортировка схем
    schemas = openapi_schema["components"]["schemas"]
    openapi_schema["components"]["schemas"] = dict(sorted(schemas.items()))
    if API_ROUTE:
        add_api_prefix(openapi_schema, API_ROUTE)
    # openapi_schema["info"]["x-logo"] = {
    #     "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    # }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
