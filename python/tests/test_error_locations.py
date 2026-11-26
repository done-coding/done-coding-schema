"""手写校验的报错位置指到具体字段；「不得出现」的字段指到多出来的那个。"""

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from done_coding_schema_api import (
    BoundedList,
    CursorList,
    ErrorBody,
    ListFilter,
    PagedList,
    ServiceErrorCodes,
    SuccessEnvelope,
)

PAGE = {"totalRecord": 21, "pageSize": 10, "totalPage": 3}
ERROR = {
    "code": "INVALID_REQUEST",
    "message": "请求参数不合法",
    "data": None,
    "error": {"retryable": False, "outcome": "not_executed"},
    "requestId": "req-01",
}
CODE = {
    "code": "ORDER_LOCKED",
    "stage": "accept",
    "httpStatus": 409,
    "retryable": False,
    "outcome": "not_executed",
    "meaning": "订单已锁定",
}


def _field(**overrides: Any) -> dict[str, Any]:
    return {"in": "body", "code": "required", "message": "必填", **overrides}


CASES: list[tuple[str, type[BaseModel], Any, set[tuple[Any, ...]]]] = [
    (
        "totalPage 不对",
        PagedList,
        {"items": [], "page": {**PAGE, "totalPage": 2}},
        {("page", "totalPage")},
    ),
    (
        "items 超过 pageSize 与 totalRecord",
        PagedList,
        {"items": [1, 2, 3], "page": {"totalRecord": 2, "pageSize": 2, "totalPage": 1}},
        {("items",)},
    ),
    (
        "嵌在成功外壳里",
        SuccessEnvelope[PagedList[Any]],
        {
            "code": "OK",
            "message": "",
            "data": {"items": [], "page": {**PAGE, "totalPage": 2}},
        },
        {("data", "page", "totalPage")},
    ),
    (
        "页码式带 cursor",
        PagedList,
        {"items": [], "page": PAGE, "cursor": {"hasMore": False}},
        {("cursor",)},
    ),
    (
        "一次性列表带 page 与 cursor",
        BoundedList,
        {"items": [], "page": PAGE, "cursor": {"hasMore": False}},
        {("page",), ("cursor",)},
    ),
    (
        "游标式带 page",
        CursorList,
        {"items": [], "cursor": {"hasMore": False}, "page": PAGE},
        {("page",)},
    ),
    (
        "还有更多却没给 next",
        CursorList,
        {"items": [], "cursor": {"hasMore": True}},
        {("cursor", "next")},
    ),
    ("错误体 code 为 OK", ErrorBody, {**ERROR, "code": "OK"}, {("code",)}),
    (
        "in 为 body 缺 pointer、带 parameter",
        ErrorBody,
        {
            **ERROR,
            "error": {**ERROR["error"], "fields": [_field(parameter="x")]},
        },
        {
            ("error", "fields", 0, "pointer"),
            ("error", "fields", 0, "parameter"),
        },
    ),
    (
        "in 为 query 带 pointer",
        ErrorBody,
        {
            **ERROR,
            "error": {
                **ERROR["error"],
                "fields": [
                    _field(pointer="/a"),
                    _field(**{"in": "query", "parameter": "p", "pointer": "/a"}),
                ],
            },
        },
        {("error", "fields", 1, "pointer")},
    ),
    ("可选字段显式 null", ErrorBody, {**ERROR, "detail": None}, {("detail",)}),
    ("筛选条件为空", ListFilter, {"status": {}}, {("status",)}),
    (
        "专有码各项",
        ServiceErrorCodes,
        {
            "service": "order",
            "codes": [
                CODE,
                {key: value for key, value in CODE.items() if key != "httpStatus"},
                {**CODE, "code": "NOT_FOUND"},
                {**CODE, "stage": "execute", "additionalHttpStatuses": [423]},
                {**CODE, "code": "B", "additionalHttpStatuses": [409, 423, 423]},
            ],
        },
        {
            ("codes", 1, "httpStatus"),
            ("codes", 1, "code"),  # 与第 0 项同码
            ("codes", 2, "code"),
            ("codes", 3, "httpStatus"),
            ("codes", 3, "additionalHttpStatuses"),
            ("codes", 3, "code"),
            ("codes", 4, "additionalHttpStatuses"),
        },
    ),
]


@pytest.mark.parametrize(
    ("model", "data", "locs"),
    [case[1:] for case in CASES],
    ids=[case[0] for case in CASES],
)
def test_error_points_to_field(
    model: type[BaseModel], data: Any, locs: set[tuple[Any, ...]]
) -> None:
    with pytest.raises(ValidationError) as caught:
        model.model_validate(data)
    assert {error["loc"] for error in caught.value.errors()} == locs
