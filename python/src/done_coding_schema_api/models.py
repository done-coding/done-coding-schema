"""生成模型之上的薄包装（手写）。

只做两件事，不新增、不改名、不放宽任何字段：

1. 成功外壳与三种列表做成泛型：只把 ``data``、``items`` 的类型换成类型参数，
   便于写 ``SuccessEnvelope[PagedList[User]]``；
2. 补上生成工具表达不了的约束：定义里的 if / then / else、not，以及标准 JSON Schema
   写不出、用 x- 关键字声明的跨字段约束（语义见仓根 scripts/lib/validator.mjs）。
   出错位置指到具体字段，如 ("page", "totalPage")；「不得出现」的字段指到多出来的那个。

嵌套结构的约束在顶层模型上检查（如页码式的 totalPage 在 ``PagedList`` 上检查），
单独使用生成的嵌套模型时不含这些检查。同一组样例同时跑生成模型与本层，
差异逐条登记在 tests/test_examples.py 的 GENERATED_GAPS 里。
"""

import re
from typing import Any, Generic

from pydantic import BaseModel, GetJsonSchemaHandler, model_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from typing_extensions import TypeVar

from ._base import ConstraintErrors, source_json_schema
from ._generated import bounded_list as _bounded
from ._generated import cursor_list as _cursor
from ._generated import error_body as _error
from ._generated import list_filter as _filter
from ._generated import paged_list as _paged
from ._generated import service_error_codes as _service
from ._generated import success_envelope as _success

DataT = TypeVar(
    "DataT",
    bound=BaseModel | dict[str, Any] | None,
    default=dict[str, Any] | None,
)
ItemT = TypeVar("ItemT", default=Any)

_RESERVED_HTTP_CODE = re.compile(r"^HTTP_[0-9]+$")


def _forbid_keys(model: type, data: Any, keys: tuple[str, ...], what: str) -> Any:
    """「不得出现」的字段（定义里写作 false），出错位置指到该字段。"""
    if isinstance(data, dict):
        errors = ConstraintErrors(model.__name__)
        for key in keys:
            if key in data:
                errors.add((key,), "field_forbidden", f"{what}不得带 {key}", data[key])
        errors.raise_if_any()
    return data


class SuccessEnvelope(_success.SuccessEnvelope, Generic[DataT]):
    """成功外壳。``DataT`` 是结果对象的类型（或 None）。"""

    __schema_type_params__ = ("data",)

    data: DataT


class BoundedList(_bounded.BoundedList, Generic[ItemT]):
    """一次性列表。``ItemT`` 是元素类型。"""

    __schema_type_params__ = ("items",)

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_paging(cls, data: Any) -> Any:
        return _forbid_keys(cls, data, ("page", "cursor"), "一次性列表")


class PagedList(_paged.PagedList, Generic[ItemT]):
    """页码式列表。``ItemT`` 是元素类型。"""

    __schema_type_params__ = ("items",)

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_cursor(cls, data: Any) -> Any:
        return _forbid_keys(cls, data, ("cursor",), "页码式列表")

    @model_validator(mode="after")
    def _page_consistency(self) -> "PagedList[ItemT]":
        page = self.page
        errors = ConstraintErrors(type(self).__name__)
        # x-totalPageEqualsCeil；总数为 0 时 totalPage 为 0 也由此保证。
        expected = -(-page.totalRecord // page.pageSize)
        if page.totalPage != expected:
            errors.add(
                ("page", "totalPage"),
                "total_page_mismatch",
                f"totalPage 应为 ceil(totalRecord / pageSize) = {expected}",
                page.totalPage,
            )
        # x-itemsWithinPage
        for by, limit in (
            ("pageSize", page.pageSize),
            ("totalRecord", page.totalRecord),
        ):
            if len(self.items) > limit:
                errors.add(
                    ("items",),
                    "items_exceed_page",
                    f"items 有 {len(self.items)} 条，超过 {by}（{limit}）",
                    len(self.items),
                )
        errors.raise_if_any()
        return self


class CursorList(_cursor.CursorList, Generic[ItemT]):
    """游标式列表。``ItemT`` 是元素类型。"""

    __schema_type_params__ = ("items",)

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_page(cls, data: Any) -> Any:
        return _forbid_keys(cls, data, ("page",), "游标式列表")

    @model_validator(mode="after")
    def _next_when_more(self) -> "CursorList[ItemT]":
        errors = ConstraintErrors(type(self).__name__)
        if self.cursor.hasMore and self.cursor.next is None:
            errors.add(
                ("cursor", "next"),
                "field_required",
                "hasMore 为 true 时必须给 next",
                None,
            )
        errors.raise_if_any()
        return self


class ErrorBody(_error.ErrorBody):
    """错误体。"""

    @model_validator(mode="after")
    def _semantics(self) -> "ErrorBody":
        errors = ConstraintErrors(type(self).__name__)
        if self.code == "OK":
            errors.add(("code",), "code_reserved", "错误体的 code 不能是 OK", self.code)
        for index, field in enumerate(self.error.fields or []):
            at = ("error", "fields", index)
            if field.in_ == "body":
                if field.pointer is None:
                    errors.add(
                        (*at, "pointer"),
                        "field_required",
                        "in 为 body 时须有 pointer",
                        None,
                    )
                if field.parameter is not None:
                    errors.add(
                        (*at, "parameter"),
                        "field_forbidden",
                        "in 为 body 时不能有 parameter",
                        field.parameter,
                    )
            else:
                if field.parameter is None:
                    errors.add(
                        (*at, "parameter"),
                        "field_required",
                        "in 不为 body 时须有 parameter",
                        None,
                    )
                if field.pointer is not None:
                    errors.add(
                        (*at, "pointer"),
                        "field_forbidden",
                        "in 不为 body 时不能有 pointer",
                        field.pointer,
                    )
        errors.raise_if_any()
        return self


class ListFilter(_filter.ListFilter):
    """筛选参数。"""

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # RootModel 不继承 SchemaModel，单独接上「导出即源定义」。
        return source_json_schema(cls, core_schema, handler)

    @model_validator(mode="after")
    def _conditions(self) -> "ListFilter":
        errors = ConstraintErrors(type(self).__name__)
        for name, condition in self.root.items():
            if not condition.model_fields_set:
                errors.add(
                    (name,),
                    "condition_empty",
                    "筛选条件至少要有一个操作",
                    condition.model_dump(),
                )
        errors.raise_if_any()
        return self


def _check_service_code(
    errors: ConstraintErrors, index: int, item: _service.ServiceErrorCode
) -> None:
    at = ("codes", index)
    # 结构保留字只有 OK 与 HTTP_<数字>，按字节比较，不做大小写归一。
    # 要避开某组通用码由使用方显式检查，见 reference.find_reserved_codes。
    if item.code == "OK" or _RESERVED_HTTP_CODE.match(item.code):
        errors.add((*at, "code"), "code_reserved", "是结构保留码", item.code)
    if item.stage == "execute":
        if item.httpStatus is not None:
            errors.add(
                (*at, "httpStatus"),
                "field_forbidden",
                "execute 不得有 httpStatus",
                item.httpStatus,
            )
        if item.additionalHttpStatuses is not None:
            errors.add(
                (*at, "additionalHttpStatuses"),
                "field_forbidden",
                "execute 不得有 additionalHttpStatuses",
                [status.root for status in item.additionalHttpStatuses],
            )
    elif item.httpStatus is None:
        errors.add(
            (*at, "httpStatus"),
            "field_required",
            f"{item.stage} 必须有 httpStatus",
            None,
        )
    extra = [status.root for status in item.additionalHttpStatuses or []]
    if len(set(extra)) != len(extra):
        errors.add(
            (*at, "additionalHttpStatuses"),
            "duplicate_value",
            "additionalHttpStatuses 有重复",
            extra,
        )
    if item.httpStatus in extra:
        # x-arrayExcludesProperty
        errors.add(
            (*at, "additionalHttpStatuses"),
            "array_contains_property",
            "additionalHttpStatuses 不能含主状态 httpStatus",
            extra,
        )


class ServiceErrorCodes(_service.ServiceErrorCodes):
    """一个服务的专有业务码清单。"""

    @model_validator(mode="after")
    def _codes(self) -> "ServiceErrorCodes":
        errors = ConstraintErrors(type(self).__name__)
        seen: dict[str, int] = {}
        for index, item in enumerate(self.codes):
            _check_service_code(errors, index, item)
            if item.code in seen:
                # x-uniqueItemsBy
                errors.add(
                    ("codes", index, "code"),
                    "duplicate_value",
                    f"code 与第 {seen[item.code]} 项重复",
                    item.code,
                )
            else:
                seen[item.code] = index
        errors.raise_if_any()
        return self
