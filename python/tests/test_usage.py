"""对外用法：泛型嵌套、输出字段名、附带字段与常量。"""

import pytest
from pydantic import BaseModel, ValidationError

from done_coding_schema_api import (
    COMMON_ERROR_CODE_TABLE,
    PAGED_LIST_REQUEST_PARAMS,
    PAGED_LIST_RESPONSE_PATHS,
    ErrorBody,
    PagedList,
    PagedListRequest,
    ServiceErrorCodes,
    SuccessEnvelope,
)


class User(BaseModel):
    id: str
    name: str


PAYLOAD = {
    "code": "OK",
    "message": "",
    "data": {
        "items": [{"id": "u1", "name": "甲"}],
        "page": {"totalRecord": 1, "pageSize": 10, "totalPage": 1},
        "summary": {"active": 1},
    },
}


def test_generic_envelope_of_paged_list() -> None:
    result = SuccessEnvelope[PagedList[User]].model_validate(PAYLOAD)
    assert isinstance(result.data.items[0], User)
    assert result.data.items[0].name == "甲"
    assert result.data.page.totalRecord == 1
    # 列表顶层的附带字段保留，原样输出。
    assert result.model_dump() == PAYLOAD


def test_item_type_is_checked() -> None:
    bad = {**PAYLOAD, "data": {**PAYLOAD["data"], "items": [{"id": "u1"}]}}
    with pytest.raises(ValidationError):
        SuccessEnvelope[PagedList[User]].model_validate(bad)


def test_nested_list_rules_apply_inside_envelope() -> None:
    bad_page = {"totalRecord": 21, "pageSize": 10, "totalPage": 2}
    bad = {**PAYLOAD, "data": {**PAYLOAD["data"], "page": bad_page}}
    with pytest.raises(ValidationError, match="ceil"):
        SuccessEnvelope[PagedList[User]].model_validate(bad)


def test_error_field_uses_wire_name() -> None:
    body = ErrorBody.model_validate(
        {
            "code": "INVALID_REQUEST",
            "message": "请求参数不合法",
            "data": None,
            "error": {
                "retryable": False,
                "outcome": "not_executed",
                "fields": [
                    {
                        "in": "query",
                        "code": "out_of_range",
                        "message": "超出范围",
                        "parameter": "page.pageSize",
                    }
                ],
            },
            "requestId": "req-01",
        }
    )
    assert body.error.fields[0].in_ == "query"
    dumped = body.model_dump(exclude_none=True)
    assert dumped["error"]["fields"][0]["in"] == "query"


def test_constants() -> None:
    assert PAGED_LIST_REQUEST_PARAMS["pageSize"] == "page.pageSize"
    assert "page" not in PAGED_LIST_RESPONSE_PATHS
    assert COMMON_ERROR_CODE_TABLE["RATE_LIMITED"]["retryable"] is True
    with pytest.raises(TypeError):
        PAGED_LIST_REQUEST_PARAMS["pageSize"] = "x"  # type: ignore[index]


def test_integral_float_becomes_int() -> None:
    # JSON Schema 的 integer 接受 12.0；校验后归一成 int，输出也是整数。
    page = PagedList.model_validate_json(
        '{"items": [], "page": {"totalRecord": 0.0, "pageSize": 10.0, "totalPage": 0}}'
    ).page
    assert (page.totalRecord, page.pageSize) == (0, 10)
    assert type(page.pageSize) is int
    codes = ServiceErrorCodes.model_validate(
        {
            "service": "order",
            "codes": [
                {
                    "code": "ORDER_LOCKED",
                    "stage": "both",
                    "httpStatus": 409.0,
                    "additionalHttpStatuses": [423.0],
                    "retryable": False,
                    "outcome": "not_executed",
                    "meaning": "订单已锁定",
                }
            ],
        }
    )
    assert codes.model_dump()["codes"][0]["additionalHttpStatuses"] == [423]
    assert type(codes.codes[0].httpStatus) is int


@pytest.mark.parametrize("value", [12.5, "12", True, float("inf"), float("nan")])
def test_non_integers_are_still_rejected(value: object) -> None:
    with pytest.raises(ValidationError):
        PagedListRequest.model_validate({"pageSize": value})
