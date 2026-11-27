"""用仓根 schemas/examples/ 的同一组样例核对 Python 侧，三个裁判须与定义（Ajv）同结论：

样例的合法 / 不合法由定义校验（仓根 pnpm check:examples，Ajv 加 x- 关键字）保证，这里把它当作定义的判决：

- 包装层（对外导出的模型）对每个样例的接受与拒绝必须与定义一致，JSON 与 Python 两种输入都测；
- Python 的通用校验器 jsonschema 直接拿包里的定义文件判，结论须与定义一致；通用校验器
  不认 x- 检查关键字，所以只因 x- 关键字被拒的样例，它判合法才算一致；
- 生成模型（未经包装）与定义不一致的样例必须恰好是 GENERATED_GAPS 登记的那些：
  多出一条（生成物悄悄变宽）或少了一条（登记过期）都失败。
"""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ValidationError
from referencing import Registry, Resource

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
    load_schema,
    schema_names,
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
from done_coding_schema_api.reference import (
    load_reference_schema,
    reference_schema_names,
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
_RESERVED = "结构保留码 OK 与 HTTP_<数字>（not）→ ServiceErrorCodes._codes"
_CEIL = (
    "x-totalPageEqualsCeil 与 totalRecord 为 0 的 if/then → PagedList._page_consistency"
)
_ITEMS = "x-itemsWithinPage → PagedList._page_consistency"

GENERATED_GAPS: dict[tuple[str, str], str] = {
    ("bounded-list", "带 page"): _FALSE.format("BoundedList._no_paging "),
    ("bounded-list", "带 cursor"): _FALSE.format("BoundedList._no_paging "),
    ("paged-list", "同时带 cursor"): _FALSE.format("PagedList._no_cursor "),
    ("cursor-list", "同时带 page"): _FALSE.format("CursorList._no_page "),
    ("paged-list", "totalPage 不等于 ceil(totalRecord / pageSize)"): _CEIL,
    ("paged-list", "总数为 0 时 totalPage 不为 0"): _CEIL,
    ("paged-list", "items 条数超过 pageSize"): _ITEMS,
    ("paged-list", "items 条数超过 totalRecord"): _ITEMS,
    ("paged-list", "总数为 0 时 items 不为空"): _ITEMS,
    ("paged-list", "items 条数同时超过 pageSize 与 totalRecord"): _ITEMS,
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


# ---- 第三个裁判：Python jsonschema 直接拿包里的定义文件判 ----


def _documents() -> dict[str, dict[str, Any]]:
    return {
        **{name: load_schema(name) for name in schema_names()},
        **{name: load_reference_schema(name) for name in reference_schema_names()},
    }


DOCUMENTS = _documents()
REGISTRY = Registry().with_resources(
    (document["$id"], Resource.from_contents(document))
    for document in DOCUMENTS.values()
)

VALIDATORS = {
    name: Draft202012Validator(document, registry=REGISTRY)
    for name, document in DOCUMENTS.items()
}


def _generic_samples() -> list[tuple[str, str, Any, bool]]:
    """(结构名, 样例名, 数据, 通用校验器应判合法)：只因 x- 关键字被拒的样例应判合法。"""
    samples = []
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        examples = json.loads(path.read_text(encoding="utf-8"))
        for sample in examples.get("valid", []):
            samples.append((path.stem, sample["name"], sample["data"], True))
        for sample in examples.get("invalid", []):
            only_extensions = all(
                error["keyword"].startswith("x-") for error in sample["errors"]
            )
            samples.append((path.stem, sample["name"], sample["data"], only_extensions))
    return samples


GENERIC_SAMPLES = _generic_samples()


@pytest.mark.parametrize(
    ("structure", "name", "data", "valid"),
    GENERIC_SAMPLES,
    ids=[f"{structure}:{name}" for structure, name, _, _ in GENERIC_SAMPLES],
)
def test_jsonschema_on_definition_files_matches_definition(
    structure: str, name: str, data: Any, valid: bool
) -> None:
    assert VALIDATORS[structure].is_valid(data) is valid


def test_only_extension_keywords_are_loosened() -> None:
    """通用校验器只在 x- 检查关键字上比定义宽，且只落在用了它们的结构上。"""
    loosened = {
        (structure, name)
        for (structure, name, _, generic), (_, _, _, strict) in zip(
            GENERIC_SAMPLES, SAMPLES, strict=True
        )
        if generic and not strict
    }
    assert {structure for structure, _ in loosened} == {
        "paged-list",
        "service-error-codes",
    }


# ---- 错误类型：x- 检查关键字的 errorType 与 Python 包报的类型相同 ----


def _typed_samples() -> list[tuple[str, Any, list[str]]]:
    """(样例名, 数据, 定义校验器报的 errorType 列表)：只取带 errorType 的不合法样例。"""
    examples = json.loads(
        (EXAMPLES_DIR / "paged-list.json").read_text(encoding="utf-8")
    )
    return [
        (
            sample["name"],
            sample["data"],
            sorted(
                error["params"]["errorType"]
                for error in sample["errors"]
                if "errorType" in error.get("params", {})
            ),
        )
        for sample in examples["invalid"]
        if any("errorType" in error.get("params", {}) for error in sample["errors"])
    ]


TYPED_SAMPLES = _typed_samples()


@pytest.mark.parametrize(
    ("name", "data", "expected"),
    TYPED_SAMPLES,
    ids=[name for name, _, _ in TYPED_SAMPLES],
)
def test_error_types_match_definition_validator(
    name: str, data: Any, expected: list[str]
) -> None:
    with pytest.raises(ValidationError) as caught:
        PagedList.model_validate(data)
    types = sorted(
        error["type"]
        for error in caught.value.errors()
        if error["type"].startswith("items_exceed_")
    )
    assert types == expected


def test_both_item_count_error_types_are_covered() -> None:
    assert {t for _, _, expected in TYPED_SAMPLES for t in expected} == {
        "items_exceed_page_size",
        "items_exceed_total_record",
    }
