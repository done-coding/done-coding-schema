"""使用方子类：重新声明的字段只能收紧，导出的结构与运行时校验同结论。

- 运行时：重新声明的字段除了按新声明校验，还要满足源定义对该字段的约束；
- 导出：该字段是源定义与新声明的交集；
- 同结论：用通用 JSON Schema 校验器拿导出的结构逐值判，结论须与模型一致。
"""

import asyncio
import json
import re
from typing import Annotated, Any, Literal

import pytest
from fastapi import FastAPI, Query
from jsonschema import Draft202012Validator
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)
from pydantic.alias_generators import to_snake

from done_coding_schema_api import (
    CursorListCursor,
    CursorListRequest,
    ErrorBody,
    ErrorField,
    JsonInt,
    PagedList,
    PagedListPage,
    PagedListRequest,
    ServiceErrorCode,
)
from done_coding_schema_api.reference import (
    CURSOR_LIST_REQUEST_PARAMS,
    PAGED_LIST_REQUEST_PARAMS,
)


class User(BaseModel):
    id: str


class OrderPageRequest(PagedListRequest):
    """每页条数：默认 20、上限 50；下限沿用定义（至少 1），不必重写。"""

    pageSize: JsonInt = Field(default=20, le=50)


class LooserPageRequest(PagedListRequest):
    """想放宽下限也放不宽：定义的 minimum 1 照常生效。"""

    pageSize: JsonInt = Field(default=20, ge=0)


class PlainIntPageRequest(PagedListRequest):
    """用普通 int 声明：严格模式下拒绝 12.0，导出也据此写成交集。"""

    pageSize: int = Field(default=20, le=50)


class OrderFailure(ErrorBody):
    """把错误体的 code 收窄到自己的一组（误把 OK 放进来也会被定义拦下）。"""

    code: Literal["ORDER_LOCKED", "ORDER_GONE", "OK"]


class TracedFailure(ErrorBody):
    """给 requestId 加自己的格式：两份 pattern 都要满足。"""

    requestId: str = Field(pattern="^req-")


class LenientFailure(ErrorBody):
    """必填字段给了默认值：不再必填，格式仍按定义。"""

    requestId: str = "unknown"


class TightCode(ServiceErrorCode):
    """专有码的含义收短到 20 字符（定义是 1000）。"""

    meaning: str = Field(max_length=20)


INTEGER_PARAMS = {
    PAGED_LIST_REQUEST_PARAMS["page"],
    PAGED_LIST_REQUEST_PARAMS["pageSize"],
}


class OrderPageQuery(OrderPageRequest):
    """线上查询参数：参数名取 PAGED_LIST_REQUEST_PARAMS（page.page、page.pageSize…），
    整数参数先从查询字符串解码，再按定义校验。"""

    model_config = ConfigDict(
        alias_generator=lambda name: PAGED_LIST_REQUEST_PARAMS[name],
        validate_by_name=False,
    )

    @model_validator(mode="before")
    @classmethod
    def _decode_integers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: int(value)
                if key in INTEGER_PARAMS
                and isinstance(value, str)
                and re.fullmatch("[0-9]+", value)
                else value
                for key, value in data.items()
            }
        return data


class OrderCursorQuery(CursorListRequest):
    """游标式的线上查询参数：cursor.after、cursor.limit；limit 上限 50。"""

    model_config = ConfigDict(
        alias_generator=lambda name: CURSOR_LIST_REQUEST_PARAMS[name],
        validate_by_name=False,
    )

    limit: JsonInt = Field(default=20, le=50)

    @model_validator(mode="before")
    @classmethod
    def _decode_limit(cls, data: Any) -> Any:
        key = CURSOR_LIST_REQUEST_PARAMS["limit"]
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, str) and re.fullmatch("[0-9]+", value):
            return {**data, key: int(value)}
        return data


ERROR = {
    "code": "ORDER_LOCKED",
    "message": "订单已锁定",
    "data": None,
    "error": {"retryable": False, "outcome": "not_executed"},
    "requestId": "req-1",
}
CODE = {
    "code": "ORDER_LOCKED",
    "stage": "accept",
    "httpStatus": 409,
    "retryable": False,
    "outcome": "not_executed",
    "meaning": "订单已锁定",
}

# (模型, 一组数据)：每条数据都由模型与导出结构各判一次。
CASES: list[tuple[type[BaseModel], list[Any]]] = [
    (
        OrderPageRequest,
        [{}, *({"pageSize": v} for v in (0, 1, 12.0, 20, 50, 51, 12.5, "20", True))],
    ),
    (LooserPageRequest, [{"pageSize": v} for v in (-1, 0, 1, 500)]),
    (PlainIntPageRequest, [{"pageSize": v} for v in (0, 1, 12.0, 50, 51)]),
    (
        OrderFailure,
        [{**ERROR, "code": c} for c in ("ORDER_LOCKED", "ORDER_GONE", "OK", "OTHER")],
    ),
    (
        TracedFailure,
        [{**ERROR, "requestId": r} for r in ("req-1", "abc", "req 1", "req-")],
    ),
    (LenientFailure, [{k: v for k, v in ERROR.items() if k != "requestId"}, ERROR]),
    (TightCode, [CODE, {**CODE, "meaning": "长" * 21}, {**CODE, "meaning": ""}]),
    (
        OrderPageQuery,
        [{"page.pageSize": v} for v in (0, 1, 20, 50, 51)]
        + [{"pageSize": 20}, {"page.page": 2, "page.query": "甲"}, {"page.limit": 1}],
    ),
    (
        OrderCursorQuery,
        [{"cursor.limit": v} for v in (0, 1, 50, 51)]
        + [
            {"cursor.after": "x"},
            {"cursor.after": ""},
            {"limit": 20},
            {"cursor.before": "x"},
        ],
    ),
]


def _model_accepts(model: type[BaseModel], data: Any) -> bool:
    try:
        model.model_validate_json(json.dumps(data, ensure_ascii=False))
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize(
    ("model", "data"),
    [(model, item) for model, items in CASES for item in items],
    ids=[
        f"{model.__name__}:{json.dumps(item, ensure_ascii=False)[:60]}"
        for model, items in CASES
        for item in items
    ],
)
def test_export_and_runtime_agree(model: type[BaseModel], data: Any) -> None:
    exported = Draft202012Validator(model.model_json_schema()).is_valid(data)
    assert _model_accepts(model, data) is exported


def test_redeclared_field_keeps_source_constraint_at_runtime() -> None:
    for model in (OrderPageRequest, LooserPageRequest, PlainIntPageRequest):
        with pytest.raises(ValidationError) as caught:
            model.model_validate({"pageSize": 0})
        assert [error["loc"] for error in caught.value.errors()] == [("pageSize",)]
    assert OrderPageRequest().pageSize == 20
    assert OrderPageRequest.model_validate_json('{"pageSize": 12.0}').pageSize == 12


def test_redeclared_field_is_exported_as_intersection() -> None:
    source = PagedListRequest.model_json_schema()["properties"]["pageSize"]
    assert source == {
        "description": source["description"],
        "type": "integer",
        "minimum": 1,
    }
    exported = OrderPageRequest.model_json_schema()
    assert exported["properties"]["pageSize"] == {
        **source,
        "default": 20,
        "maximum": 50,
    }
    # 放宽下限的声明不改变导出的下限。
    looser = LooserPageRequest.model_json_schema()["properties"]["pageSize"]
    assert looser["minimum"] == 1
    # 未改的字段仍是源定义。
    assert (
        exported["properties"]["query"]
        == PagedListRequest.model_json_schema()["properties"]["query"]
    )
    assert "required" not in exported


def test_narrowed_and_extra_patterns_are_exported() -> None:
    code = OrderFailure.model_json_schema()["properties"]["code"]
    assert code["enum"] == ["ORDER_LOCKED", "ORDER_GONE", "OK"]
    assert code["pattern"] == "^[A-Za-z][A-Za-z0-9_]{0,127}$"
    assert code["not"] == {"const": "OK"}
    request_id = TracedFailure.model_json_schema()["properties"]["requestId"]
    assert request_id["pattern"] == "^\\S{1,128}$"
    assert request_id["allOf"] == [{"pattern": "^req-"}]
    meaning = TightCode.model_json_schema()["properties"]["meaning"]
    assert (meaning["minLength"], meaning["maxLength"]) == (1, 20)


def test_required_field_with_default_becomes_optional() -> None:
    exported = LenientFailure.model_json_schema()
    assert "requestId" not in exported["required"]
    assert exported["properties"]["requestId"]["default"] == "unknown"
    assert exported["properties"]["requestId"]["pattern"] == "^\\S{1,128}$"


def test_renamed_fields_are_exported_under_wire_names() -> None:
    exported = OrderPageQuery.model_json_schema()
    assert list(exported["properties"]) == list(PAGED_LIST_REQUEST_PARAMS.values())
    assert exported["properties"]["page.pageSize"]["maximum"] == 50
    assert exported["properties"]["page.pageSize"]["minimum"] == 1
    assert exported["additionalProperties"] is False


async def _get(app: FastAPI, path: str, query: str) -> tuple[int, Any]:
    """不经 HTTP 客户端直接调用 ASGI 应用。"""
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


def test_fastapi_query_model_uses_wire_parameter_names() -> None:
    class UserPage(PagedList[User]):
        pass

    app = FastAPI()

    @app.get("/orders")
    def list_orders(params: Annotated[OrderPageQuery, Query()]) -> dict[str, Any]:
        return params.model_dump(exclude_none=True)

    @app.get("/users", response_model=UserPage)
    def list_users() -> Any: ...

    @app.get("/failure", response_model=OrderFailure)
    def failure() -> Any: ...

    document = app.openapi()
    parameters = document["paths"]["/orders"]["get"]["parameters"]
    assert [p["name"] for p in parameters] == [
        "page.page",
        "page.pageSize",
        "page.query",
        "page.orderBy",
    ]
    assert all(p["in"] == "query" for p in parameters)
    components = document["components"]["schemas"]
    assert components["UserPage"]["properties"]["items"]["items"] == {
        "$ref": "#/components/schemas/User"
    }
    assert components["OrderFailure"]["properties"]["code"]["enum"] == [
        "ORDER_LOCKED",
        "ORDER_GONE",
        "OK",
    ]

    ok = asyncio.run(
        _get(app, "/orders", "page.page=2&page.pageSize=30&page.query=%E7%94%B2")
    )
    assert ok == (200, {"page.page": 2, "page.pageSize": 30, "page.query": "甲"})
    assert asyncio.run(_get(app, "/orders", ""))[1] == {"page.pageSize": 20}
    for bad in (
        "page.pageSize=0",
        "page.pageSize=51",
        "page.pageSize=abc",
        "page.limit=1",
        "pageSize=20",
    ):
        assert asyncio.run(_get(app, "/orders", bad))[0] == 422, bad


def test_cursor_query_model_uses_wire_parameter_names() -> None:
    exported = OrderCursorQuery.model_json_schema()
    assert list(exported["properties"]) == ["cursor.after", "cursor.limit"]
    assert exported["properties"]["cursor.limit"]["minimum"] == 1
    assert exported["properties"]["cursor.limit"]["maximum"] == 50

    app = FastAPI()

    @app.get("/events")
    def list_events(params: Annotated[OrderCursorQuery, Query()]) -> dict[str, Any]:
        return params.model_dump(exclude_none=True)

    parameters = app.openapi()["paths"]["/events"]["get"]["parameters"]
    assert [p["name"] for p in parameters] == ["cursor.after", "cursor.limit"]
    ok = asyncio.run(_get(app, "/events", "cursor.after=abc&cursor.limit=30"))
    assert ok == (200, {"cursor.after": "abc", "cursor.limit": 30})
    for bad in ("cursor.limit=0", "cursor.limit=51", "cursor.after=", "limit=20"):
        assert asyncio.run(_get(app, "/events", bad))[0] == 422, bad


# ---- 包体结构不能改线上字段名 ----

# 定义里按名字引用字段的四个结构，各一种改名写法；另加关掉 serialize_by_alias 一例。
RENAMES: list[tuple[str, type[BaseModel], dict[str, Any], str]] = [
    (
        "ErrorField 的 in 设 alias（if/then/else 按名引用 in、pointer、parameter）",
        ErrorField,
        {"__annotations__": {"in_": str}, "in_": Field(alias="location")},
        "in_",
    ),
    (
        "ErrorField 关掉 serialize_by_alias（输出会变成 in_）",
        ErrorField,
        {"model_config": ConfigDict(serialize_by_alias=False)},
        "in_",
    ),
    (
        "ServiceErrorCode 的 httpStatus 设 serialization_alias（x-arrayExcludesProperty 按名引用）",
        ServiceErrorCode,
        {
            "__annotations__": {"httpStatus": JsonInt | None},
            "httpStatus": Field(default=None, serialization_alias="status"),
        },
        "httpStatus",
    ),
    (
        "PagedListPage 用 alias_generator（x-totalPageEqualsCeil 按名引用）",
        PagedListPage,
        {"model_config": ConfigDict(alias_generator=to_snake)},
        "totalRecord",
    ),
    (
        "CursorListCursor 的 hasMore 设 validation_alias（if/then 按名引用 hasMore、next）",
        CursorListCursor,
        {
            "__annotations__": {"hasMore": bool},
            "hasMore": Field(validation_alias=AliasChoices("hasMore", "has_more")),
        },
        "hasMore",
    ),
]


# 查询参数模型只能按前缀改名，其他改名同样在类定义时被拒。
QUERY_RENAMES: list[tuple[str, type[BaseModel], dict[str, Any], str]] = [
    (
        "PagedListRequest 的 pageSize 改成 size",
        PagedListRequest,
        {
            "__annotations__": {"pageSize": JsonInt | None},
            "pageSize": Field(default=None, alias="size"),
        },
        "pageSize",
    ),
    (
        "CursorListRequest 用 alias_generator=str.upper",
        CursorListRequest,
        {"model_config": ConfigDict(alias_generator=str.upper)},
        "after",
    ),
    (
        "PagedListRequest 用了别的前缀 p.",
        PagedListRequest,
        {"model_config": ConfigDict(alias_generator=lambda name: f"p.{name}")},
        "page",
    ),
]


@pytest.mark.parametrize(
    ("base", "namespace", "field"),
    [case[1:] for case in QUERY_RENAMES],
    ids=[case[0] for case in QUERY_RENAMES],
)
def test_query_model_can_only_add_its_prefix(
    base: type[BaseModel], namespace: dict[str, Any], field: str
) -> None:
    with pytest.raises(TypeError, match=f"只能按前缀 .*改线上字段名：.*{field}"):
        type("Renamed", (base,), dict(namespace))


def test_query_model_prefix_renames_are_allowed() -> None:
    # 按前缀改名（README 的写法）与只给个别字段加前缀都通过。
    assert OrderPageQuery.model_fields["pageSize"].alias == "page.pageSize"
    assert OrderCursorQuery.model_fields["limit"].alias == "cursor.limit"

    class OnlyPageSize(PagedListRequest):
        pageSize: JsonInt | None = Field(default=None, alias="page.pageSize")

    assert OnlyPageSize.model_validate({"page.pageSize": 5}).pageSize == 5


@pytest.mark.parametrize(
    ("base", "namespace", "field"),
    [case[1:] for case in RENAMES],
    ids=[case[0] for case in RENAMES],
)
def test_body_structure_subclass_cannot_rename_fields(
    base: type[BaseModel], namespace: dict[str, Any], field: str
) -> None:
    with pytest.raises(TypeError, match=f"不能改线上字段名：.*{field}"):
        type("Renamed", (base,), dict(namespace))


def test_unrenamed_subclasses_are_still_allowed() -> None:
    # 收紧、加默认、继承参数化泛型都不改线上名。
    class Narrow(ServiceErrorCode):
        meaning: str = Field(max_length=20)

    class Page(PagedList[User]):
        pass

    assert Narrow.model_fields["meaning"].alias is None
    assert Page.model_json_schema()["properties"]["page"]["x-totalPageEqualsCeil"]
