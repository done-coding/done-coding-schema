"""用仓根 schemas/examples/ 的同一组样例核对 Python 模型。

样例的合法 / 不合法由定义校验（仓根 pnpm check:examples）保证，这里把它当作定义的判决：

- 包装层（对外导出的模型）对每个样例的接受与拒绝必须与定义一致，JSON 与 Python 两种输入都测；
- 生成模型（未经包装）与定义不一致的样例必须恰好是 GENERATED_GAPS 登记的那些：
  多出一条（生成物悄悄变宽）或少了一条（登记过期）都失败。
"""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from done_coding_schema_api import (
    BoundedList,
    CursorList,
    CursorListRequest,
    ErrorBody,
    ListFilter,
    PagedList,
    PagedListRequest,
    ServiceErrorCodes,
    SuccessEnvelope,
)
from done_coding_schema_api._generated import (
    bounded_list,
    cursor_list,
    error_body,
    list_filter,
    paged_list,
    service_error_codes,
    success_envelope,
)

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "schemas" / "examples"


def _as_error_body(data: Any) -> Any:
    """通用失败码表的样例只含 code 与 error，补齐成完整的错误体再校验。"""
    return {**data, "message": "x", "data": None, "requestId": "r"}


def _same(data: Any) -> Any:
    return data


# 结构名 → (生成模型, 包装层模型, 样例到模型输入的转换)
CASES: dict[str, tuple[type[BaseModel], type[BaseModel], Callable[[Any], Any]]] = {
    "success-envelope": (success_envelope.SuccessEnvelope, SuccessEnvelope, _same),
    "error-body": (error_body.ErrorBody, ErrorBody, _same),
    "common-error-codes": (error_body.ErrorBody, ErrorBody, _as_error_body),
    "bounded-list": (bounded_list.BoundedList, BoundedList, _same),
    "paged-list": (paged_list.PagedList, PagedList, _same),
    "cursor-list": (cursor_list.CursorList, CursorList, _same),
    "paged-list-request": (PagedListRequest, PagedListRequest, _same),
    "cursor-list-request": (CursorListRequest, CursorListRequest, _same),
    "list-filter": (list_filter.ListFilter, ListFilter, _same),
    "service-error-codes": (
        service_error_codes.ServiceErrorCodes,
        ServiceErrorCodes,
        _same,
    ),
}

# 生成模型与定义不一致的样例：(结构名, 样例名) → 原因与包装层的补法。
# 生成工具只读得懂字段与单字段约束；下列约束在交给它之前已去掉（见 scripts/lib/shape.mjs），
# 由 models.py 的校验补上。
_FALSE = "定义里写作 false 的字段生成前去掉，列表顶层又允许附带字段 → {}拒绝"
_FIELD_AT = (
    "fields 项的 if/then/else（in 决定 pointer / parameter）→ ErrorBody._semantics"
)
_STAGE = "stage 的 if/then/else → ServiceErrorCodes._codes"
_RESERVED = "保留码与通用码（not）→ ServiceErrorCodes._codes"
_CEIL = "x-totalPageEqualsCeil 与 totalRecord 为 0 的 if/then → PagedList._total_page"

GENERATED_GAPS: dict[tuple[str, str], str] = {
    ("bounded-list", "带 page"): _FALSE.format("BoundedList._no_paging "),
    ("bounded-list", "带 cursor"): _FALSE.format("BoundedList._no_paging "),
    ("paged-list", "同时带 cursor"): _FALSE.format("PagedList._no_cursor "),
    ("cursor-list", "同时带 page"): _FALSE.format("CursorList._no_page "),
    ("paged-list", "totalPage 不等于 ceil(totalRecord / pageSize)"): _CEIL,
    ("paged-list", "总数为 0 时 totalPage 不为 0"): _CEIL,
    ("cursor-list", "还有更多却没给 next"): (
        "hasMore 为 true 时 next 必有（if/then）→ CursorList._next_when_more"
    ),
    ("error-body", "code 为 OK"): "code 不能是 OK（not）→ ErrorBody._semantics",
    ("error-body", "in 为 body 缺 pointer"): _FIELD_AT,
    ("error-body", "in 为 body 带 parameter"): _FIELD_AT,
    ("error-body", "in 为 query 缺 parameter"): _FIELD_AT,
    ("error-body", "in 为 header 带 pointer"): _FIELD_AT,
    ("list-filter", "条件对象为空"): (
        "minProperties 生成工具不支持 → ListFilter._conditions"
    ),
    ("service-error-codes", "清单内 code 重复"): (
        "x-uniqueItemsBy → ServiceErrorCodes._codes"
    ),
    ("service-error-codes", "code 为保留的 OK"): _RESERVED,
    ("service-error-codes", "code 为保留的 HTTP_<数字>"): _RESERVED,
    ("service-error-codes", "code 重新定义通用码"): _RESERVED,
    ("service-error-codes", "accept 缺 httpStatus"): _STAGE,
    ("service-error-codes", "both 缺 httpStatus"): _STAGE,
    ("service-error-codes", "execute 带 httpStatus"): _STAGE,
    ("service-error-codes", "execute 带 additionalHttpStatuses"): _STAGE,
    ("service-error-codes", "additionalHttpStatuses 重复"): (
        "uniqueItems 生成工具不支持 → ServiceErrorCodes._codes"
    ),
    ("service-error-codes", "additionalHttpStatuses 含主状态"): (
        "x-arrayExcludesProperty → ServiceErrorCodes._codes"
    ),
}


def _load() -> list[tuple[str, str, Any, bool]]:
    samples = []
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        examples = json.loads(path.read_text(encoding="utf-8"))
        for group, valid in (("valid", True), ("invalid", False)):
            for sample in examples[group]:
                samples.append((path.stem, sample["name"], sample["data"], valid))
    return samples


SAMPLES = _load()


def _accepts_json(model: type[BaseModel], data: Any) -> bool:
    try:
        model.model_validate_json(json.dumps(data))
    except ValidationError:
        return False
    return True


def _accepts_python(model: type[BaseModel], data: Any) -> bool:
    try:
        model.model_validate(copy.deepcopy(data))
    except ValidationError:
        return False
    return True


def test_every_example_file_has_a_model() -> None:
    assert {path.stem for path in EXAMPLES_DIR.glob("*.json")} == set(CASES)


@pytest.mark.parametrize(
    ("structure", "name", "data", "valid"),
    SAMPLES,
    ids=[f"{structure}:{name}" for structure, name, _, _ in SAMPLES],
)
@pytest.mark.parametrize("accepts", [_accepts_json, _accepts_python])
def test_wrapper_matches_definition(
    structure: str,
    name: str,
    data: Any,
    valid: bool,
    accepts: Callable[[type[BaseModel], Any], bool],
) -> None:
    _, wrapper, convert = CASES[structure]
    assert accepts(wrapper, convert(data)) is valid


def test_generated_gaps_are_exactly_registered() -> None:
    actual = set()
    for structure, name, data, valid in SAMPLES:
        generated, _, convert = CASES[structure]
        if _accepts_json(generated, convert(data)) is not valid:
            actual.add((structure, name))
    assert sorted(actual - GENERATED_GAPS.keys()) == [], "生成模型新增了不一致"
    assert sorted(GENERATED_GAPS.keys() - actual) == [], "登记的不一致已不存在"
