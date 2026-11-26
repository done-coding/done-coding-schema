"""参考资源出口：通用失败码与码表、列表的路径与参数名、参考数值、参考资源定义文件，
以及让专有码避开某组码的检查函数。

这些只是参考，不随结构生效：包顶层的模型不读它们，包也不替使用方填写；要用须从本模块
显式引入、显式写进自己的代码。常量由仓根 ``schemas/`` 的定义生成。
"""

from collections.abc import Iterable
from typing import NamedTuple

from ._definitions import (
    load_reference_schema,
    reference_schema_names,
    reference_schema_path,
)
from ._generated.error_body import ErrorDetail
from ._generated.reference_constants import (
    BOUNDED_LIST_RESPONSE_PATHS,
    COMMON_ERROR_CODE_TABLE,
    COMMON_ERROR_CODES,
    CURSOR_LIST_REFERENCE_VALUES,
    CURSOR_LIST_REQUEST_PARAMS,
    CURSOR_LIST_RESPONSE_PATHS,
    LIST_FILTER_PARAMS,
    PAGED_LIST_REFERENCE_VALUES,
    PAGED_LIST_REQUEST_PARAMS,
    PAGED_LIST_RESPONSE_PATHS,
    CommonErrorCode,
)
from ._generated.service_error_codes import ServiceErrorCodes


def reference_error_detail(code: str) -> ErrorDetail | None:
    """通用失败码的参考处置信息（retryable 与 outcome 取码表里的参考值）；不是通用码时返回 None。

    包不替使用方填写：只有显式调用本函数才用到表中值。能确定更具体的重试性或执行结局时
    照常改写，如 ``reference_error_detail("SERVICE_UNAVAILABLE").model_copy(update={"outcome": "not_executed"})``。
    """
    row = COMMON_ERROR_CODE_TABLE.get(code)
    if row is None:
        return None
    return ErrorDetail(retryable=row["retryable"], outcome=row["outcome"])


class ReservedCodeHit(NamedTuple):
    """专有码清单里撞上保留码集合的一项：index 是它在 codes 里的位置。"""

    index: int
    code: str


def find_reserved_codes(
    codes: ServiceErrorCodes, reserved: Iterable[str]
) -> list[ReservedCodeHit]:
    """找出专有码清单里与 reserved 重名的项。

    结构本身只把 OK 与 HTTP_<数字> 当保留字；要让专有码避开某组通用码（如本模块的
    ``COMMON_ERROR_CODES``，或自己的一组），把那组码传进来。按字节比较，不做大小写归一；
    reserved 为空就什么也不比。返回空列表即没有撞码。
    """
    reserved_set = set(reserved)
    return [
        ReservedCodeHit(index, item.code)
        for index, item in enumerate(codes.codes)
        if item.code in reserved_set
    ]


__all__ = [
    "BOUNDED_LIST_RESPONSE_PATHS",
    "COMMON_ERROR_CODES",
    "COMMON_ERROR_CODE_TABLE",
    "CURSOR_LIST_REFERENCE_VALUES",
    "CURSOR_LIST_REQUEST_PARAMS",
    "CURSOR_LIST_RESPONSE_PATHS",
    "LIST_FILTER_PARAMS",
    "PAGED_LIST_REFERENCE_VALUES",
    "PAGED_LIST_REQUEST_PARAMS",
    "PAGED_LIST_RESPONSE_PATHS",
    "CommonErrorCode",
    "ReservedCodeHit",
    "find_reserved_codes",
    "load_reference_schema",
    "reference_error_detail",
    "reference_schema_names",
    "reference_schema_path",
]
