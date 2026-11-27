"""内置的查询参数模型：线上名、整数解码、继承收紧、FastAPI 下的参数说明与实际请求。"""

import asyncio
import json
from typing import Annotated, Any

import pytest
from fastapi import FastAPI, Query
from pydantic import Field, ValidationError

from done_coding_schema_api import (
    CursorListQuery,
    JsonInt,
    PagedListQuery,
    load_schema,
)
from done_coding_schema_api.reference import (
    CURSOR_LIST_REQUEST_PARAMS,
    PAGED_LIST_REQUEST_PARAMS,
)


class OrderQuery(PagedListQuery):
    """使用方自己的每页条数：默认 20、上限 50；不必写别名与解码。"""

    pageSize: JsonInt = Field(default=20, le=50)


class EventQuery(CursorListQuery):
    limit: JsonInt = Field(default=20, le=50)


def test_decoding_rule_comes_from_the_definition() -> None:
    for name in ("paged-list-request", "cursor-list-request"):
        assert (
            load_schema(name)["x-queryIntegerPattern"]
            == r"^(?:0|[1-9][0-9]*)$(?![\s\S])"
        )


def test_wire_names_are_prefixed_field_names() -> None:
    assert [f.alias for f in PagedListQuery.model_fields.values()] == list(
        PAGED_LIST_REQUEST_PARAMS.values()
    )
    assert [f.alias for f in CursorListQuery.model_fields.values()] == list(
        CURSOR_LIST_REQUEST_PARAMS.values()
    )


def test_decodes_query_strings() -> None:
    query = PagedListQuery.model_validate(
        {
            "page.page": "2",
            "page.pageSize": "20",
            "page.query": "甲",
            "page.orderBy": "name desc",
        }
    )
    assert (query.page, query.pageSize, query.query, query.orderBy) == (
        2,
        20,
        "甲",
        "name desc",
    )
    assert type(query.page) is int
    assert query.model_dump(exclude_none=True) == {
        "page.page": 2,
        "page.pageSize": 20,
        "page.query": "甲",
        "page.orderBy": "name desc",
    }
    cursor = CursorListQuery.model_validate({"cursor.after": "x", "cursor.limit": "5"})
    assert (cursor.after, cursor.limit) == ("x", 5)


@pytest.mark.parametrize(
    "text", ["02", "+2", " 2", "2 ", "2.0", "1e1", "", "-1", "٣", "2\n", "0x2"]
)
def test_rejects_integers_not_written_as_plain_decimal(text: str) -> None:
    with pytest.raises(ValidationError) as caught:
        PagedListQuery.model_validate({"page.page": text})
    assert [error["loc"] for error in caught.value.errors()] == [("page.page",)]


@pytest.mark.parametrize(
    ("text", "ok"), [("0", False), ("1", True), ("10", True), ("100", True)]
)
def test_decoded_integers_are_checked_against_bounds(text: str, ok: bool) -> None:
    try:
        PagedListQuery.model_validate({"page.pageSize": text})
    except ValidationError:
        assert not ok
    else:
        assert ok


def test_prefix_rules() -> None:
    # 前缀外的参数不归它管，忽略；裸名不收；前缀下未声明的参数不合法。
    assert PagedListQuery.model_validate({"q": "x", "pageSize": "20"}).pageSize is None
    with pytest.raises(ValidationError) as caught:
        PagedListQuery.model_validate({"page.limit": "1"})
    assert caught.value.errors()[0]["loc"] == ("page.limit",)
    with pytest.raises(ValidationError):
        CursorListQuery.model_validate({"cursor.before": "x"})


def test_subclass_only_tightens() -> None:
    assert OrderQuery().pageSize == 20
    assert OrderQuery.model_validate({"page.pageSize": "50"}).pageSize == 50
    for text in ("0", "51", "02"):
        with pytest.raises(ValidationError):
            OrderQuery.model_validate({"page.pageSize": text})
    exported = OrderQuery.model_json_schema()["properties"]["page.pageSize"]
    assert (exported["minimum"], exported["maximum"], exported["default"]) == (
        1,
        50,
        20,
    )
    assert EventQuery.model_validate({"cursor.limit": "30"}).limit == 30


def test_exported_properties_are_the_definition() -> None:
    source = load_schema("paged-list-request")["properties"]
    exported = PagedListQuery.model_json_schema()["properties"]
    assert exported == {f"page.{name}": prop for name, prop in source.items()}


async def _get(app: FastAPI, path: str, query: str) -> tuple[int, Any]:
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": query.encode(),
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1),
    }
    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(
        m.get("body", b"") for m in messages if m["type"] == "http.response.body"
    )
    return status, json.loads(body)


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/users")
    def list_users(params: Annotated[PagedListQuery, Query()]) -> dict[str, Any]:
        return {
            "page": params.page,
            "pageSize": params.pageSize,
            "types": [type(params.page).__name__, type(params.pageSize).__name__],
        }

    @app.get("/orders")
    def list_orders(params: Annotated[OrderQuery, Query()]) -> dict[str, Any]:
        # FastAPI 0.140 等旧版本里，查询参数模型须是接口唯一的查询参数才会展开成各个参数。
        return {"pageSize": params.pageSize}

    @app.get("/events")
    def list_events(params: Annotated[CursorListQuery, Query()]) -> dict[str, Any]:
        return params.model_dump(exclude_none=True)

    return app


def _contains_key(node: Any, key: str) -> bool:
    if isinstance(node, dict):
        return key in node or any(_contains_key(v, key) for v in node.values())
    if isinstance(node, list):
        return any(_contains_key(v, key) for v in node)
    return False


def test_fastapi_openapi_parameters() -> None:
    document = _app().openapi()
    users = document["paths"]["/users"]["get"]["parameters"]
    assert [p["name"] for p in users] == list(PAGED_LIST_REQUEST_PARAMS.values())
    events = document["paths"]["/events"]["get"]["parameters"]
    assert [p["name"] for p in events] == list(CURSOR_LIST_REQUEST_PARAMS.values())
    source = load_schema("paged-list-request")["properties"]
    for parameter in users:
        schema = {k: v for k, v in parameter["schema"].items() if k != "title"}
        assert schema == source[parameter["name"].removeprefix("page.")]
        assert parameter["required"] is False
    orders = {
        p["name"]: p["schema"]
        for p in document["paths"]["/orders"]["get"]["parameters"]
    }
    assert orders["page.pageSize"]["minimum"] == 1
    assert orders["page.pageSize"]["maximum"] == 50
    assert orders["page.pageSize"]["default"] == 20
    # 约束写成 minimum / maximum，没有 ge / le；查询参数模型的参数不写成可为 null。
    for name in ("/users", "/orders", "/events"):
        parameters = document["paths"][name]["get"]["parameters"]
        for key in ("ge", "le", "anyOf"):
            assert not _contains_key(parameters, key), (name, key)


def test_fastapi_requests() -> None:
    app = _app()
    assert asyncio.run(_get(app, "/users", "page.page=2&page.pageSize=20")) == (
        200,
        {"page": 2, "pageSize": 20, "types": ["int", "int"]},
    )
    # 前缀外的参数不归它管：忽略，不报错。
    assert asyncio.run(_get(app, "/orders", "keyword=x")) == (200, {"pageSize": 20})
    assert asyncio.run(_get(app, "/events", "cursor.after=abc&cursor.limit=5")) == (
        200,
        {"cursor.after": "abc", "cursor.limit": 5},
    )
    # 裸名不收（被忽略，取默认）；严格整数写法以外的都拒。
    assert asyncio.run(_get(app, "/users", "page=2"))[1]["page"] is None
    for bad in (
        "page.page=02",
        "page.page=%2B2",
        "page.page=2.0",
        "page.page=",
        "page.pageSize=0",
        "page.limit=1",
    ):
        assert asyncio.run(_get(app, "/users", bad))[0] == 422, bad
    assert asyncio.run(_get(app, "/orders", "page.pageSize=51"))[0] == 422
