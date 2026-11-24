// 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
// 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
/**
 * 成功码。成功外壳的 code 只能是这一组里的值。
 */
export const SUCCESS_CODES = {
  OK: "OK",
} as const;
export type SuccessCode = (typeof SUCCESS_CODES)[keyof typeof SUCCESS_CODES];
/**
 * 通用失败码。错误体的 code 是开放字符串，这里只列通用的一组；
 * 各服务可以有自己的专有码，遇到不认识的码按 HTTP 状态归类处理。
 */
export const COMMON_ERROR_CODES = {
  INVALID_REQUEST: "INVALID_REQUEST",
  UNAUTHENTICATED: "UNAUTHENTICATED",
  FORBIDDEN: "FORBIDDEN",
  NOT_FOUND: "NOT_FOUND",
  ROUTE_NOT_FOUND: "ROUTE_NOT_FOUND",
  METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
  CONFLICT: "CONFLICT",
  RATE_LIMITED: "RATE_LIMITED",
  INTERNAL_ERROR: "INTERNAL_ERROR",
  LIST_LIMIT_EXCEEDED: "LIST_LIMIT_EXCEEDED",
  SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
} as const;
export type CommonErrorCode =
  (typeof COMMON_ERROR_CODES)[keyof typeof COMMON_ERROR_CODES];
/**
 * 通用失败码 → HTTP 状态、能否重试、是否已执行（outcome）与含义。
 */
export const COMMON_ERROR_CODE_TABLE = {
  INVALID_REQUEST: {
    httpStatus: 400,
    retryable: false,
    outcome: "not_executed",
    meaning: "请求不符合接口契约",
  },
  UNAUTHENTICATED: {
    httpStatus: 401,
    retryable: false,
    outcome: "not_executed",
    meaning: "未登录，或令牌无效、过期",
  },
  FORBIDDEN: {
    httpStatus: 403,
    retryable: false,
    outcome: "not_executed",
    meaning: "已认证但无权执行",
  },
  NOT_FOUND: {
    httpStatus: 404,
    retryable: false,
    outcome: "not_executed",
    meaning: "资源不存在，或调用方无权得知其存在",
  },
  ROUTE_NOT_FOUND: {
    httpStatus: 404,
    retryable: false,
    outcome: "not_executed",
    meaning: "接口路径不存在",
  },
  METHOD_NOT_ALLOWED: {
    httpStatus: 405,
    retryable: false,
    outcome: "not_executed",
    meaning: "接口不支持该 HTTP 方法",
  },
  CONFLICT: {
    httpStatus: 409,
    retryable: false,
    outcome: "not_executed",
    meaning: "资源状态冲突",
  },
  RATE_LIMITED: {
    httpStatus: 429,
    retryable: true,
    outcome: "not_executed",
    meaning: "请求过于频繁，可稍后重试",
  },
  INTERNAL_ERROR: {
    httpStatus: 500,
    retryable: false,
    outcome: "unknown",
    meaning: "服务内部错误，可能已产生副作用",
  },
  LIST_LIMIT_EXCEEDED: {
    httpStatus: 500,
    retryable: false,
    outcome: "unknown",
    meaning: "一次性列表的结果超出接口声明的上限",
  },
  SERVICE_UNAVAILABLE: {
    httpStatus: 503,
    retryable: true,
    outcome: "unknown",
    meaning: "服务或其依赖暂不可用",
  },
} as const;
/**
 * BoundedList 响应里各字段的路径（由定义 bounded-list.schema.json 生成）。
 */
export const BOUNDED_LIST_RESPONSE_PATHS = {
  items: "items",
} as const;
/**
 * CursorListRequest 的线上参数名（由定义 cursor-list-request.schema.json 生成）。
 */
export const CURSOR_LIST_REQUEST_PARAMS = {
  after: "cursor.after",
  limit: "cursor.limit",
} as const;
/**
 * CursorList 响应里各字段的路径（由定义 cursor-list.schema.json 生成）。
 */
export const CURSOR_LIST_RESPONSE_PATHS = {
  items: "items",
  next: "cursor.next",
  hasMore: "cursor.hasMore",
} as const;
/**
 * ListFilter 的线上参数名（由定义 list-filter.schema.json 生成）。
 */
export const LIST_FILTER_PARAMS = {
  prefix: "filter.",
  operators: {
    eq: "eq",
  },
} as const;
/**
 * PagedListRequest 的线上参数名（由定义 paged-list-request.schema.json 生成）。
 */
export const PAGED_LIST_REQUEST_PARAMS = {
  page: "page.page",
  pageSize: "page.pageSize",
  query: "page.query",
  orderBy: "page.orderBy",
} as const;
/**
 * PagedList 响应里各字段的路径（由定义 paged-list.schema.json 生成）。
 */
export const PAGED_LIST_RESPONSE_PATHS = {
  items: "items",
  totalRecord: "page.totalRecord",
  pageSize: "page.pageSize",
  totalPage: "page.totalPage",
} as const;
