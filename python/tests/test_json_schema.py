"""模型导出的 JSON Schema 就是源定义：引用展开后逐项相同，x- 约束一并带出；
泛型只替换 items 的元素与 data；FastAPI 生成的 OpenAPI 里可选字段不会变成可为 null。"""

from typing import Annotated, Any, Literal

import pytest
from fastapi import Body, FastAPI
from pydantic import BaseModel

from done_coding_schema_api import (
    BoundedList,
    CursorList,
    CursorListCursor,
    CursorListRequest,
    ErrorBody,
    ErrorDetail,
    ErrorField,
    ListFilter,
    ListFilterCondition,
    PagedList,
    PagedListPage,
    PagedListRequest,
    ServiceErrorCode,
    ServiceErrorCodes,
    SuccessEnvelope,
    load_schema,
)

DOCUMENT_KEYWORDS = {"$schema", "$id", "$defs"}

# 模型 → (定义名, 文件内 JSON Pointer)：独立于实现里按标题查找的逻辑。
SOURCES: dict[type[BaseModel], tuple[str, str]] = {
    SuccessEnvelope: ("success-envelope", ""),
    ErrorBody: ("error-body", ""),
    ErrorDetail: ("error-body", "/$defs/errorDetail"),
    ErrorField: ("error-body", "/$defs/errorField"),
    BoundedList: ("bounded-list", ""),
    PagedList: ("paged-list", ""),
    PagedListPage: ("paged-list", "/$defs/page"),
    CursorList: ("cursor-list", ""),
    CursorListCursor: ("cursor-list", "/$defs/cursor"),
    PagedListRequest: ("paged-list-request", ""),
    CursorListRequest: ("cursor-list-request", ""),
    ListFilter: ("list-filter", ""),
    ListFilterCondition: ("list-filter", "/$defs/condition"),
    ServiceErrorCodes: ("service-error-codes", ""),
    ServiceErrorCode: ("service-error-codes", "/$defs/code"),
}


def _at(document: Any, pointer: str) -> Any:
    for token in pointer.split("/")[1:] if pointer else []:
        document = document[token]
    return document


def assert_same_as_source(exported: Any, node: Any, document: dict[str, Any]) -> None:
    """exported 与源定义 node 相同；node 里的 $ref 按所在文档解析后再比。"""
    if isinstance(node, dict) and "$ref" in node:
        target, _, pointer = node["$ref"].partition("#")
        if target:
            document = load_schema(target.removesuffix(".schema.json"))
        siblings = {key: value for key, value in node.items() if key != "$ref"}
        assert_same_as_source(
            exported, {**_at(document, pointer), **siblings}, document
        )
        return
    if isinstance(node, dict):
        assert isinstance(exported, dict)
        expected_keys = set(node) - DOCUMENT_KEYWORDS
        assert set(exported) == expected_keys
        for key in expected_keys:
            assert_same_as_source(exported[key], node[key], document)
    elif isinstance(node, list):
        assert isinstance(exported, list) and len(exported) == len(node)
        for exported_item, item in zip(exported, node, strict=True):
            assert_same_as_source(exported_item, item, document)
    else:
        assert exported == node and type(exported) is type(node)


@pytest.mark.parametrize("mode", ["validation", "serialization"])
@pytest.mark.parametrize(
    "model", list(SOURCES), ids=[model.__name__ for model in SOURCES]
)
def test_exported_schema_is_the_source_definition(
    model: type[BaseModel], mode: Literal["validation", "serialization"]
) -> None:
    name, pointer = SOURCES[model]
    document = load_schema(name)
    assert_same_as_source(
        model.model_json_schema(mode=mode), _at(document, pointer), document
    )


def test_cross_field_constraints_are_exported() -> None:
    paged = PagedList.model_json_schema()
    assert paged["x-itemsWithinPage"] is True
    assert paged["properties"]["cursor"] is False
    assert paged["properties"]["page"]["x-totalPageEqualsCeil"] is True
    error = ErrorBody.model_json_schema()
    assert error["properties"]["code"]["not"] == {"const": "OK"}


class User(BaseModel):
    id: str
    name: str


def _without(schema: dict[str, Any], *path: str) -> dict[str, Any]:
    """去掉 path 处的键后的拷贝（用来比较除泛型参数以外的部分）。"""
    head, *rest = path
    copy = {key: value for key, value in schema.items() if key != "$defs"}
    if rest:
        copy[head] = _without(copy[head], *rest)
    else:
        copy.pop(head)
    return copy


@pytest.mark.parametrize("model", [BoundedList, PagedList, CursorList])
def test_list_type_parameter_replaces_item_schema_only(model: type[BaseModel]) -> None:
    exported = model[User].model_json_schema()  # type: ignore[index]
    assert exported["properties"]["items"]["items"] == {"$ref": "#/$defs/User"}
    assert set(exported["$defs"]) == {"User"}
    source = model.model_json_schema()
    assert _without(exported, "properties", "items", "items") == source


def test_envelope_type_parameter_replaces_data_only() -> None:
    exported = SuccessEnvelope[PagedList[User]].model_json_schema()
    data = exported["properties"]["data"]
    source = SuccessEnvelope.model_json_schema()
    assert data["description"] == source["properties"]["data"]["description"]
    paged = exported["$defs"][data["$ref"].removeprefix("#/$defs/")]
    assert paged["properties"]["items"]["items"] == {"$ref": "#/$defs/User"}
    assert _without(exported, "properties", "data") == _without(
        source, "properties", "data"
    )
    optional = SuccessEnvelope[User | None].model_json_schema()["properties"]["data"]
    assert {"type": "null"} in optional["anyOf"]


def test_subclass_fields_are_added() -> None:
    class UserPage(PagedList[User]):
        summary: dict[str, int]

    exported = UserPage.model_json_schema()
    assert exported["properties"]["summary"]["type"] == "object"
    assert "summary" in exported["required"]
    assert exported["x-itemsWithinPage"] is True


def _allows_null(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    kinds = schema.get("type")
    if kinds == "null" or (isinstance(kinds, list) and "null" in kinds):
        return True
    return any(
        _allows_null(option)
        for keyword in ("anyOf", "oneOf")
        for option in schema.get(keyword, [])
    )


def _optional_fields_allowing_null(node: Any, where: str) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        required = set(node.get("required", []))
        for name, field in (node.get("properties") or {}).items():
            if name not in required and _allows_null(field):
                found.append(f"{where}.{name}")
        for key, child in node.items():
            found += _optional_fields_allowing_null(child, f"{where}/{key}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            found += _optional_fields_allowing_null(child, f"{where}/{index}")
    return found


def test_fastapi_openapi_uses_source_definitions() -> None:
    app = FastAPI()

    @app.get("/users", response_model=SuccessEnvelope[PagedList[User]])
    def list_users() -> Any: ...

    @app.get("/failure", response_model=ErrorBody)
    def failure() -> Any: ...

    @app.post("/codes")
    def register(codes: Annotated[ServiceErrorCodes, Body()]) -> None: ...

    components = app.openapi()["components"]["schemas"]
    assert _optional_fields_allowing_null(components, "components") == []
    for name, model in (
        ("ErrorBody", ErrorBody),
        ("ServiceErrorCodes", ServiceErrorCodes),
    ):
        matching = [key for key in components if key.startswith(name)]
        assert matching, name
        for key in matching:
            assert components[key] == model.model_json_schema()
    paged = next(key for key in components if key.startswith("PagedList_User_"))
    assert components[paged]["properties"]["items"]["items"] == {
        "$ref": "#/components/schemas/User"
    }
