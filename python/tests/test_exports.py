"""两层出口：包顶层只有结构，参考资源只在 reference 子模块。"""

import done_coding_schema_api as package
from done_coding_schema_api import ServiceErrorCodes, reference
from done_coding_schema_api.reference import (
    COMMON_ERROR_CODES,
    CURSOR_LIST_REFERENCE_VALUES,
    PAGED_LIST_REFERENCE_VALUES,
    ReservedCodeHit,
    find_reserved_codes,
)

REFERENCE_NAMES = {
    "COMMON_ERROR_CODES",
    "CommonErrorCode",
    "COMMON_ERROR_CODE_TABLE",
    "BOUNDED_LIST_RESPONSE_PATHS",
    "PAGED_LIST_REQUEST_PARAMS",
    "PAGED_LIST_RESPONSE_PATHS",
    "CURSOR_LIST_REQUEST_PARAMS",
    "CURSOR_LIST_RESPONSE_PATHS",
    "LIST_FILTER_PARAMS",
    "PAGED_LIST_REFERENCE_VALUES",
    "CURSOR_LIST_REFERENCE_VALUES",
    "reference_error_detail",
    "find_reserved_codes",
    "load_reference_schema",
    "reference_schema_names",
    "reference_schema_path",
}


def test_top_level_exports_no_reference_resource() -> None:
    assert REFERENCE_NAMES.isdisjoint(package.__all__)
    for name in REFERENCE_NAMES:
        assert not hasattr(package, name), name
    # 旧名不留转发别名。
    assert not hasattr(package, "default_error_detail")
    assert not hasattr(reference, "default_error_detail")


def test_reference_module_exports_them() -> None:
    assert REFERENCE_NAMES <= set(reference.__all__)
    for name in reference.__all__:
        assert hasattr(reference, name), name
    assert set(reference.__all__).isdisjoint(package.__all__)


def test_reference_values() -> None:
    assert dict(PAGED_LIST_REFERENCE_VALUES) == {
        "page": 1,
        "pageSize": 10,
        "maxPageSize": 100,
    }
    assert dict(CURSOR_LIST_REFERENCE_VALUES) == {"maxLimit": 100}


CODE = {
    "stage": "accept",
    "httpStatus": 409,
    "retryable": False,
    "outcome": "not_executed",
    "meaning": "订单已锁定",
}
CODES = ServiceErrorCodes.model_validate(
    {
        "service": "order",
        "codes": [
            {**CODE, "code": "ORDER_LOCKED"},
            {**CODE, "code": "NOT_FOUND"},
            {**CODE, "code": "not_found"},
            {**CODE, "code": "QUOTA_USED_UP"},
        ],
    }
)


def test_structure_accepts_common_code_as_service_code() -> None:
    assert CODES.codes[1].code == "NOT_FOUND"


def test_find_reserved_codes_compares_only_what_is_passed() -> None:
    assert find_reserved_codes(CODES, []) == []
    assert find_reserved_codes(CODES, COMMON_ERROR_CODES) == [
        ReservedCodeHit(1, "NOT_FOUND")
    ]
    own = {**COMMON_ERROR_CODES, "QUOTA_USED_UP": "QUOTA_USED_UP"}
    assert find_reserved_codes(CODES, own) == [
        ReservedCodeHit(1, "NOT_FOUND"),
        ReservedCodeHit(3, "QUOTA_USED_UP"),
    ]
