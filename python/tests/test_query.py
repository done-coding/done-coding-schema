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
    QueryInt,
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
    # 前缀外的参数不归它管，忽略；前缀下未声明的参数不合法。
    assert PagedListQuery.model_validate({"q": "x", "limit": "20"}).pageSize is None
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
    # 与字段同名的裸名报错（不静默取默认）；严格整数写法以外的都拒。
    status, body = asyncio.run(_get(app, "/users", "pageSize=50"))
    assert status == 422
    assert body["detail"][0]["msg"] == "pageSize 应写作 page.pageSize"
    for bad in (
        "page=2",
        "cursor.limit=1&pageSize=1",
        "page.page=02",
        "page.page=%2B2",
        "page.page=2.0",
        "page.page=",
        "page.pageSize=0",
        "page.limit=1",
    ):
        assert asyncio.run(_get(app, "/users", bad))[0] == 422, bad
    assert asyncio.run(_get(app, "/orders", "page.pageSize=51"))[0] == 422


# ---- 裸名：与字段同名的不静默丢弃 ----


@pytest.mark.parametrize(
    ("model", "bare", "wire"),
    [
        (PagedListQuery, "page", "page.page"),
        (PagedListQuery, "pageSize", "page.pageSize"),
        (PagedListQuery, "query", "page.query"),
        (PagedListQuery, "orderBy", "page.orderBy"),
        (CursorListQuery, "after", "cursor.after"),
        (CursorListQuery, "limit", "cursor.limit"),
    ],
)
def test_bare_names_are_rejected_with_the_wire_name(
    model: type[PagedListQuery] | type[CursorListQuery], bare: str, wire: str
) -> None:
    for build in (
        lambda: model.model_validate({bare: "5"}),
        lambda: model(**{bare: 5}),
    ):
        with pytest.raises(ValidationError) as caught:
            build()
        [error] = caught.value.errors()
        assert error["loc"] == (bare,)
        assert error["type"] == "bare_parameter_name"
        assert error["msg"] == f"{bare} 应写作 {wire}"


def test_wire_names_still_work_for_direct_construction() -> None:
    assert PagedListQuery(**{"page.pageSize": 5}).pageSize == 5


# ---- 子类新增字段：前缀内不行，前缀外可以 ----


class OrderSearchQuery(PagedListQuery):
    """接口自己的其他查询参数声明在同一个子类里，线上名在前缀之外。"""

    pageSize: JsonInt = Field(default=20, le=50)
    status: str | None = None
    # 查询串的值都是字符串；前缀外的整数用 QueryInt，与前缀内的整数同一套写法。
    minAmount: Annotated[QueryInt | None, Field(ge=0)] = None


def test_query_subclass_cannot_add_fields_under_the_prefix() -> None:
    # 不写别名时，新加字段的线上名就是字段名，在前缀之外，可以加。
    class Ok(PagedListQuery):
        foo: str | None = None

    assert Ok.model_fields["foo"].alias == "foo"
    with pytest.raises(TypeError, match="不能新增这个前缀下的字段：foo（'page.foo'）"):
        type(
            "Bad",
            (PagedListQuery,),
            {
                "__annotations__": {"foo": str | None},
                "foo": Field(default=None, alias="page.foo"),
            },
        )
    with pytest.raises(TypeError, match="cursor.foo"):
        type(
            "Bad",
            (CursorListQuery,),
            {
                "__annotations__": {"foo": str | None},
                "foo": Field(default=None, alias="cursor.foo"),
            },
        )


def test_query_subclass_cannot_add_fields_named_like_bare_names() -> None:
    with pytest.raises(TypeError, match="'pageSize' 应写作 'page.pageSize'"):
        type(
            "Bad",
            (PagedListQuery,),
            {
                "__annotations__": {"size": str | None},
                "size": Field(default=None, alias="pageSize"),
            },
        )
    with pytest.raises(TypeError, match="'limit' 应写作 'cursor.limit'"):
        type(
            "Bad",
            (CursorListQuery,),
            {
                "__annotations__": {"limit2": str | None},
                "limit2": Field(default=None, alias="limit"),
            },
        )


def test_query_subclass_extra_fields_follow_their_own_declaration() -> None:
    query = OrderSearchQuery.model_validate(
        {"page.page": "2", "status": "paid", "minAmount": "100", "other": "x"}
    )
    assert (query.page, query.pageSize, query.status, query.minAmount) == (
        2,
        20,
        "paid",
        100,
    )
    with pytest.raises(ValidationError) as caught:
        OrderSearchQuery.model_validate({"minAmount": "-1"})
    assert caught.value.errors()[0]["loc"] == ("minAmount",)
    exported = OrderSearchQuery.model_json_schema()["properties"]
    assert list(exported) == [
        *PAGED_LIST_REQUEST_PARAMS.values(),
        "status",
        "minAmount",
    ]


def test_fastapi_query_subclass_with_own_parameters() -> None:
    app = FastAPI()

    @app.get("/orders")
    def search(params: Annotated[OrderSearchQuery, Query()]) -> dict[str, Any]:
        return params.model_dump(exclude_none=True)

    parameters = app.openapi()["paths"]["/orders"]["get"]["parameters"]
    assert [p["name"] for p in parameters] == [
        *PAGED_LIST_REQUEST_PARAMS.values(),
        "status",
        "minAmount",
    ]
    by_name = {p["name"]: p["schema"] for p in parameters}
    assert (
        by_name["page.pageSize"]["minimum"],
        by_name["page.pageSize"]["maximum"],
    ) == (1, 50)
    assert not _contains_key(
        [by_name[w] for w in PAGED_LIST_REQUEST_PARAMS.values()], "anyOf"
    )
    assert asyncio.run(
        _get(app, "/orders", "page.page=2&status=paid&minAmount=100")
    ) == (
        200,
        {"page.page": 2, "page.pageSize": 20, "status": "paid", "minAmount": 100},
    )
    for bad in (
        "minAmount=abc",
        "minAmount=02",
        "minAmount=%2B2",
        "minAmount=2.0",
        "minAmount=-1",
        "page.pageSize=51",
        "pageSize=10",
        "page.foo=1",
    ):
        assert asyncio.run(_get(app, "/orders", bad))[0] == 422, bad


# ---- QueryInt：前缀外的整数参数与前缀内同一套写法 ----


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0", 0), ("20", 20), ("100", 100)],
)
def test_query_int_accepts_plain_decimal(text: str, expected: int) -> None:
    assert OrderSearchQuery.model_validate({"minAmount": text}).minAmount == expected


@pytest.mark.parametrize(
    "text", ["02", "+2", " 2", "2.0", "1e1", "", "-1", "٣", "2\n", "true"]
)
def test_query_int_rejects_what_prefixed_integers_reject(text: str) -> None:
    for build in (
        lambda: OrderSearchQuery.model_validate({"minAmount": text}),
        lambda: PagedListQuery.model_validate({"page.page": text}),
    ):
        with pytest.raises(ValidationError):
            build()


def test_query_int_uses_the_definition_pattern() -> None:
    from done_coding_schema_api import _query

    assert (
        _query._rules("PagedListRequest").integer_text.pattern
        == load_schema("paged-list-request")["x-queryIntegerPattern"]
    )
    assert (
        load_schema("cursor-list-request")["x-queryIntegerPattern"]
        == load_schema("paged-list-request")["x-queryIntegerPattern"]
    )
