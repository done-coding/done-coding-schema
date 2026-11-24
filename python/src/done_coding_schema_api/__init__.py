"""跨前后端通用接口结构的 Pydantic 模型与常量。

模型与常量由仓根 ``schemas/`` 的 JSON Schema 定义生成；成功外壳、三种列表、错误体、
筛选参数与专有码清单以 ``models`` 里的包装版本导出（带泛型与生成工具表达不了的约束）。
"""

from ._generated.constants import (
    BOUNDED_LIST_RESPONSE_PATHS,
    COMMON_ERROR_CODE_TABLE,
    COMMON_ERROR_CODES,
    CURSOR_LIST_REQUEST_PARAMS,
    CURSOR_LIST_RESPONSE_PATHS,
    LIST_FILTER_PARAMS,
    PAGED_LIST_REQUEST_PARAMS,
    PAGED_LIST_RESPONSE_PATHS,
    SUCCESS_CODES,
    CommonErrorCode,
    SuccessCode,
)
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
    "BOUNDED_LIST_RESPONSE_PATHS",
    "COMMON_ERROR_CODES",
    "COMMON_ERROR_CODE_TABLE",
    "CURSOR_LIST_REQUEST_PARAMS",
    "CURSOR_LIST_RESPONSE_PATHS",
    "LIST_FILTER_PARAMS",
    "PAGED_LIST_REQUEST_PARAMS",
    "PAGED_LIST_RESPONSE_PATHS",
    "SUCCESS_CODES",
    "BoundedList",
    "CommonErrorCode",
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
]
