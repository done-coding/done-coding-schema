# 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
# 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
from types import MappingProxyType
from typing import Final, Literal


SUCCESS_CODES: Final = MappingProxyType({"OK": "OK"})
"""成功码。成功外壳的 code 只能是这一组里的值。"""
SuccessCode = Literal["OK"]

COMMON_ERROR_CODES: Final = MappingProxyType(
    {
        "INVALID_REQUEST": "INVALID_REQUEST",
        "UNAUTHENTICATED": "UNAUTHENTICATED",
        "FORBIDDEN": "FORBIDDEN",
        "NOT_FOUND": "NOT_FOUND",
        "ROUTE_NOT_FOUND": "ROUTE_NOT_FOUND",
        "METHOD_NOT_ALLOWED": "METHOD_NOT_ALLOWED",
        "CONFLICT": "CONFLICT",
        "RATE_LIMITED": "RATE_LIMITED",
        "INTERNAL_ERROR": "INTERNAL_ERROR",
        "LIST_LIMIT_EXCEEDED": "LIST_LIMIT_EXCEEDED",
        "SERVICE_UNAVAILABLE": "SERVICE_UNAVAILABLE",
    }
)
"""通用失败码。错误体的 code 是开放字符串，这里只列通用的一组；
各服务可以有自己的专有码，遇到不认识的码按 HTTP 状态归类处理。"""
CommonErrorCode = Literal[
    "INVALID_REQUEST",
    "UNAUTHENTICATED",
    "FORBIDDEN",
    "NOT_FOUND",
    "ROUTE_NOT_FOUND",
    "METHOD_NOT_ALLOWED",
    "CONFLICT",
    "RATE_LIMITED",
    "INTERNAL_ERROR",
    "LIST_LIMIT_EXCEEDED",
    "SERVICE_UNAVAILABLE",
]

COMMON_ERROR_CODE_TABLE: Final = MappingProxyType(
    {
        "INVALID_REQUEST": MappingProxyType(
            {
                "httpStatus": 400,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "请求不符合接口契约",
            }
        ),
        "UNAUTHENTICATED": MappingProxyType(
            {
                "httpStatus": 401,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "未登录，或令牌无效、过期",
            }
        ),
        "FORBIDDEN": MappingProxyType(
            {
                "httpStatus": 403,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "已认证但无权执行",
            }
        ),
        "NOT_FOUND": MappingProxyType(
            {
                "httpStatus": 404,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "资源不存在，或调用方无权得知其存在",
            }
        ),
        "ROUTE_NOT_FOUND": MappingProxyType(
            {
                "httpStatus": 404,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "接口路径不存在",
            }
        ),
        "METHOD_NOT_ALLOWED": MappingProxyType(
            {
                "httpStatus": 405,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "接口不支持该 HTTP 方法",
            }
        ),
        "CONFLICT": MappingProxyType(
            {
                "httpStatus": 409,
                "retryable": False,
                "outcome": "not_executed",
                "meaning": "资源状态冲突",
            }
        ),
        "RATE_LIMITED": MappingProxyType(
            {
                "httpStatus": 429,
                "retryable": True,
                "outcome": "not_executed",
                "meaning": "请求过于频繁，可稍后重试",
            }
        ),
        "INTERNAL_ERROR": MappingProxyType(
            {
                "httpStatus": 500,
                "retryable": False,
                "outcome": "unknown",
                "meaning": "服务内部错误，可能已产生副作用",
            }
        ),
        "LIST_LIMIT_EXCEEDED": MappingProxyType(
            {
                "httpStatus": 500,
                "retryable": False,
                "outcome": "unknown",
                "meaning": "一次性列表的结果超出接口声明的上限",
            }
        ),
        "SERVICE_UNAVAILABLE": MappingProxyType(
            {
                "httpStatus": 503,
                "retryable": True,
                "outcome": "unknown",
                "meaning": "服务或其依赖暂不可用",
            }
        ),
    }
)
"""通用失败码 → HTTP 状态、能否重试与是否已执行（outcome）的缺省值、含义。
retryable 与 outcome 是缺省值：服务未另行指定时取表中值，能确定更具体的情形时可以覆盖。"""

BOUNDED_LIST_RESPONSE_PATHS: Final = MappingProxyType({"items": "items"})
"""BoundedList 响应里各字段的路径（由定义 bounded-list.schema.json 生成）。"""

CURSOR_LIST_REQUEST_PARAMS: Final = MappingProxyType(
    {"after": "cursor.after", "limit": "cursor.limit"}
)
"""CursorListRequest 的线上参数名（由定义 cursor-list-request.schema.json 生成）。"""

CURSOR_LIST_RESPONSE_PATHS: Final = MappingProxyType(
    {"items": "items", "next": "cursor.next", "hasMore": "cursor.hasMore"}
)
"""CursorList 响应里各字段的路径（由定义 cursor-list.schema.json 生成）。"""

LIST_FILTER_PARAMS: Final = MappingProxyType(
    {"prefix": "filter.", "operators": MappingProxyType({"eq": "eq"})}
)
"""ListFilter 的线上参数名（由定义 list-filter.schema.json 生成）。"""

PAGED_LIST_REQUEST_PARAMS: Final = MappingProxyType(
    {
        "page": "page.page",
        "pageSize": "page.pageSize",
        "query": "page.query",
        "orderBy": "page.orderBy",
    }
)
"""PagedListRequest 的线上参数名（由定义 paged-list-request.schema.json 生成）。"""

PAGED_LIST_RESPONSE_PATHS: Final = MappingProxyType(
    {
        "items": "items",
        "totalRecord": "page.totalRecord",
        "pageSize": "page.pageSize",
        "totalPage": "page.totalPage",
    }
)
"""PagedList 响应里各字段的路径（由定义 paged-list.schema.json 生成）。"""
