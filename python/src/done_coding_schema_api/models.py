"""生成模型之上的薄包装（手写）。

只做两件事，不新增、不改名、不放宽任何字段：

1. 成功外壳与三种列表做成泛型：只把 ``data``、``items`` 的类型换成类型参数，
   便于写 ``SuccessEnvelope[PagedList[User]]``；
2. 补上生成工具表达不了的约束：定义里的 if / then / else、not，以及标准 JSON Schema
   写不出、用 x- 关键字声明的跨字段约束（语义见仓根 scripts/lib/validator.mjs）。

嵌套结构的约束在顶层模型上检查（如页码式的 totalPage 在 ``PagedList`` 上检查），
单独使用生成的嵌套模型时不含这些检查。同一组样例同时跑生成模型与本层，
差异逐条登记在 tests/test_examples.py 的 GENERATED_GAPS 里。
"""

import re
from typing import Any, Generic

from pydantic import BaseModel, model_validator
from typing_extensions import TypeVar

from ._generated import bounded_list as _bounded
from ._generated import cursor_list as _cursor
from ._generated import error_body as _error
from ._generated import list_filter as _filter
from ._generated import paged_list as _paged
from ._generated import service_error_codes as _service
from ._generated import success_envelope as _success
from ._generated.constants import COMMON_ERROR_CODE_TABLE, COMMON_ERROR_CODES

DataT = TypeVar(
    "DataT",
    bound=BaseModel | dict[str, Any] | None,
    default=dict[str, Any] | None,
)
ItemT = TypeVar("ItemT", default=Any)

_RESERVED_HTTP_CODE = re.compile(r"^HTTP_[0-9]+$")


def _forbid_keys(data: Any, keys: tuple[str, ...], what: str) -> Any:
    """「不得出现」的字段（定义里写作 false）。"""
    if isinstance(data, dict):
        present = [key for key in keys if key in data]
        if present:
            raise ValueError(f"{what}不得带 {'、'.join(present)}")
    return data


class SuccessEnvelope(_success.SuccessEnvelope, Generic[DataT]):
    """成功外壳。``DataT`` 是结果对象的类型（或 None）。"""

    data: DataT


class BoundedList(_bounded.BoundedList, Generic[ItemT]):
    """一次性列表。``ItemT`` 是元素类型。"""

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_paging(cls, data: Any) -> Any:
        return _forbid_keys(data, ("page", "cursor"), "一次性列表")


class PagedList(_paged.PagedList, Generic[ItemT]):
    """页码式列表。``ItemT`` 是元素类型。"""

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_cursor(cls, data: Any) -> Any:
        return _forbid_keys(data, ("cursor",), "页码式列表")

    @model_validator(mode="after")
    def _total_page(self) -> "PagedList[ItemT]":
        # x-totalPageEqualsCeil；总数为 0 时 totalPage 为 0 也由此保证。
        page = self.page
        expected = -(-page.totalRecord // page.pageSize)
        if page.totalPage != expected:
            raise ValueError(
                f"totalPage 应为 ceil(totalRecord / pageSize) = {expected}"
            )
        return self


class CursorList(_cursor.CursorList, Generic[ItemT]):
    """游标式列表。``ItemT`` 是元素类型。"""

    items: list[ItemT]

    @model_validator(mode="before")
    @classmethod
    def _no_page(cls, data: Any) -> Any:
        return _forbid_keys(data, ("page",), "游标式列表")

    @model_validator(mode="after")
    def _next_when_more(self) -> "CursorList[ItemT]":
        if self.cursor.hasMore and self.cursor.next is None:
            raise ValueError("hasMore 为 true 时必须给 next")
        return self


class ErrorBody(_error.ErrorBody):
    """错误体。"""

    @model_validator(mode="after")
    def _semantics(self) -> "ErrorBody":
        if self.code == "OK":
            raise ValueError("错误体的 code 不能是 OK")
        row = COMMON_ERROR_CODE_TABLE.get(self.code)
        if row is not None and (
            self.error.retryable != row["retryable"]
            or self.error.outcome != row["outcome"]
        ):
            raise ValueError(
                f"{self.code} 的 retryable / outcome 须为 "
                f"{row['retryable']} / {row['outcome']}"
            )
        for index, field in enumerate(self.error.fields or []):
            if field.in_ == "body":
                if field.pointer is None or field.parameter is not None:
                    raise ValueError(
                        f"error.fields[{index}]：in 为 body 时须有 pointer、"
                        "不能有 parameter"
                    )
            elif field.parameter is None or field.pointer is not None:
                raise ValueError(
                    f"error.fields[{index}]：in 不为 body 时须有 parameter、"
                    "不能有 pointer"
                )
        return self


class ListFilter(_filter.ListFilter):
    """筛选参数。"""

    @model_validator(mode="after")
    def _conditions(self) -> "ListFilter":
        for name, condition in self.root.items():
            if not condition.model_fields_set:
                raise ValueError(f"{name}：筛选条件至少要有一个操作")
        return self


class ServiceErrorCodes(_service.ServiceErrorCodes):
    """一个服务的专有业务码清单。"""

    @model_validator(mode="after")
    def _codes(self) -> "ServiceErrorCodes":
        seen: dict[str, int] = {}
        for index, item in enumerate(self.codes):
            where = f"codes[{index}]"
            # 与 OK、HTTP_<数字>、通用码按字节比较，不做大小写归一。
            if (
                item.code == "OK"
                or _RESERVED_HTTP_CODE.match(item.code)
                or item.code in COMMON_ERROR_CODES
            ):
                raise ValueError(f"{where}：{item.code} 是保留码或通用码")
            if item.stage == "execute":
                if item.httpStatus is not None or item.additionalHttpStatuses:
                    raise ValueError(
                        f"{where}：execute 不得有 httpStatus 与 additionalHttpStatuses"
                    )
            elif item.httpStatus is None:
                raise ValueError(f"{where}：{item.stage} 必须有 httpStatus")
            extra = [status.root for status in item.additionalHttpStatuses or []]
            if len(set(extra)) != len(extra):
                raise ValueError(f"{where}：additionalHttpStatuses 有重复")
            if item.httpStatus in extra:
                # x-arrayExcludesProperty
                raise ValueError(f"{where}：additionalHttpStatuses 不能含主状态")
            if item.code in seen:
                # x-uniqueItemsBy
                raise ValueError(f"{where}：code 与第 {seen[item.code]} 项重复")
            seen[item.code] = index
        return self
