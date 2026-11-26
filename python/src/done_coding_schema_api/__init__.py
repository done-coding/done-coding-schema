"""跨前后端通用接口结构的 Pydantic 模型、成功码与结构定义文件。

模型与常量由仓根 ``schemas/`` 的 JSON Schema 定义生成；成功外壳、三种列表、错误体、
筛选参数与专有码清单以 ``models`` 里的包装版本导出（带泛型与生成工具表达不了的约束）。

包顶层只有结构。通用失败码与码表、列表的路径与参数名、参考数值都在
``done_coding_schema_api.reference``：只引入结构时不受任何内置的码或数值约束。
"""

from ._definitions import load_schema, schema_names, schema_path
from ._generated.constants import SUCCESS_CODES, SuccessCode
from ._generated.cursor_list import CursorListCursor
from ._generated.cursor_list_request import CursorListRequest
from ._generated.error_body import ErrorDetail, ErrorField
from ._generated.list_filter import ListFilterCondition
from ._generated.paged_list import PagedListPage
from ._generated.paged_list_request import PagedListRequest
from ._generated.service_error_codes import ServiceErrorCode
from .models import (
    BoundedList,
    CursorList,
    ErrorBody,
    ListFilter,
    PagedList,
    ServiceErrorCodes,
    SuccessEnvelope,
)

__all__ = [
    "SUCCESS_CODES",
    "BoundedList",
    "CursorList",
    "CursorListCursor",
    "CursorListRequest",
    "ErrorBody",
    "ErrorDetail",
    "ErrorField",
    "ListFilter",
    "ListFilterCondition",
    "PagedList",
    "PagedListPage",
    "PagedListRequest",
    "ServiceErrorCode",
    "ServiceErrorCodes",
    "SuccessCode",
    "SuccessEnvelope",
    "load_schema",
    "schema_names",
    "schema_path",
]
