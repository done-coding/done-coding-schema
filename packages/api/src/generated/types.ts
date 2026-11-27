// 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
// 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
/**
 * 一次性列表，作成功外壳的 data。只用于条数有一个由定义决定、不随业务数据增长的上限的结果（如下拉选项）；上限由各接口在自己的契约里声明，超过上限报 LIST_LIMIT_EXCEEDED，不截断。顶层允许接口自己声明的附带字段，但不得带翻页信息。
 */
export interface BoundedList {
  /**
   * 列表数据。
   */
  items: unknown[];
  page?: never;
  cursor?: never;
}

/**
 * 游标式列表的请求参数。线上以 cursor. 前缀的查询参数传递（如 cursor.limit=20），本定义约束解码后的对象；前缀下未声明的参数不合法。线上名为「前缀.字段名」。查询串里的整数参数（type 为 integer 的字段）只收整串匹配 x-queryIntegerPattern 的十进制数字串，解码成整数后再按本定义校验；"02"、"+2"、" 2"、"2.0"、"1e1"、空串都不合法。
 */
export interface CursorListRequest {
  /**
   * 上一批返回的 next，1–1024 个字符；首批不带。
   */
  after?: string;
  /**
   * 本批最多取多少条，至少 1；不带时取多少条、上限多少由接口自己声明。
   */
  limit?: number;
}

/**
 * 游标式列表，作成功外壳的 data：消息流这类接着往下取的列表，不带总数。取数方向由各接口声明。顶层允许接口自己声明的附带字段，但不得重复表达翻页信息；不带 page。
 */
export interface CursorList {
  /**
   * 本批数据。
   */
  items: unknown[];
  cursor: CursorListCursor;
  page?: never;
}
/**
 * 接着取的位置。hasMore 为 true 时必须给 next。
 */
export interface CursorListCursor {
  /**
   * 下一批的游标，对调用方不透明，1–1024 个字符；没有更多时可省略。
   */
  next?: string;
  /**
   * 是否还有更多。
   */
  hasMore: boolean;
}

/**
 * 错误体。HTTP 状态表达大类，包体带业务码、说明、能否重试、是否已执行与出错字段定位。retryable 与 outcome 由服务按实际情形填写，包不替使用方填写；通用失败码表给了一组参考值，使用方可显式引用。
 */
export interface ErrorBody {
  /**
   * 业务码，开放字符串：字母开头，只含字母、数字、下划线，1–128 个字符；不能是 OK。使用方遇到不认识的码按 HTTP 状态归类处理。
   */
  code: string;
  /**
   * 说明，不能是纯空白。
   */
  message: string;
  /**
   * 错误体恒为 null。
   */
  data: null;
  error: ErrorDetail;
  /**
   * 请求标识，1–128 个字符，不含空白字符。
   */
  requestId: string;
  /**
   * 补充说明，可选，不限长。
   */
  detail?: string;
}
/**
 * 错误的处置信息。
 */
export interface ErrorDetail {
  /**
   * 原样重试是否可能成功。
   */
  retryable: boolean;
  /**
   * not_executed：确定没有执行；unknown：可能已产生副作用。
   */
  outcome: "not_executed" | "unknown";
  /**
   * 逐项指出出错的输入；可以是空数组。
   */
  fields?: ErrorField[];
}
/**
 * 一项出错的输入。in 为 body 时用 pointer 定位、不能有 parameter；其他位置用 parameter 定位、不能有 pointer。
 */
export interface ErrorField {
  /**
   * 出错输入所在的位置。
   */
  in: "body" | "query" | "path" | "header" | "cookie";
  /**
   * 字段级错误码：字母开头，只含字母、数字、下划线、点、短横线，1–128 个字符。
   */
  code: string;
  /**
   * 说明，不能是纯空白。
   */
  message: string;
  /**
   * 请求体内的位置，RFC 6901 JSON Pointer。
   */
  pointer?: string;
  /**
   * 参数名，1–256 个字符。
   */
  parameter?: string;
}

/**
 * 列表的筛选参数。线上写作 filter.<字段>.<操作>（如 filter.status.eq=active），本定义约束解码后的对象 {<字段>: {<操作>: 值}}；字段为小驼峰，可筛选哪些字段由接口自己声明。首版操作只有 eq。前缀下未声明的参数不合法。
 */
export interface ListFilter {
  [k: string]: ListFilterCondition;
}
/**
 * 一个字段上的筛选条件，至少一个操作。
 *
 * This interface was referenced by `ListFilter`'s JSON-Schema definition
 * via the `patternProperty` "^[a-z][a-zA-Z0-9]*$(?![\s\S])".
 */
export interface ListFilterCondition {
  /**
   * 等于；值为标量。
   */
  eq?: string | number | boolean;
}

/**
 * 页码式列表的请求参数。线上以 page. 前缀的查询参数传递（如 page.pageSize=20），本定义约束解码后的对象；前缀下未声明的参数不合法。线上名为「前缀.字段名」。查询串里的整数参数（type 为 integer 的字段）只收整串匹配 x-queryIntegerPattern 的十进制数字串，解码成整数后再按本定义校验；"02"、"+2"、" 2"、"2.0"、"1e1"、空串都不合法。
 */
export interface PagedListRequest {
  /**
   * 页码，从 1 开始；不带时的含义由接口自己声明。
   */
  page?: number;
  /**
   * 每页条数，至少 1；不带时的含义与上限由接口自己声明。
   */
  pageSize?: number;
  /**
   * 模糊搜索词，最多 200 个字符。
   */
  query?: string;
  /**
   * 排序：逗号分隔，每段是小驼峰字段名，后面可跟一个空格加 asc 或 desc（缺省 asc）；逗号后可有一个空格；最多 200 个字符。
   */
  orderBy?: string;
}

/**
 * 页码式列表，作成功外壳的 data：给人翻页的表格，能跳页、有总数。顶层允许接口自己声明的附带字段，但不得重复表达翻页信息；不带 cursor。items 的条数不超过 page.pageSize，也不超过 page.totalRecord（x-itemsWithinPage）。
 */
export interface PagedList {
  /**
   * 当前页的数据。
   */
  items: unknown[];
  page: PagedListPage;
  cursor?: never;
}
/**
 * 翻页信息。不回传当前页码。totalPage 等于 ceil(totalRecord / pageSize)，总数为 0 时为 0（x-totalPageEqualsCeil）。
 */
export interface PagedListPage {
  /**
   * 总条数。
   */
  totalRecord: number;
  /**
   * 每页条数，回显请求值，至少 1。
   */
  pageSize: number;
  /**
   * 总页数。
   */
  totalPage: number;
}

/**
 * 一个服务的专有业务码清单。OK 与 HTTP_<数字> 形式的码是结构保留字，不得使用；比较按字节精确进行，不做大小写归一。专有码是否要避开某组通用码由使用方显式检查：把那组码传给参考资源出口的检查函数，不传就不比。
 */
export interface ServiceErrorCodes {
  /**
   * 服务标识：小写字母开头，只含小写字母、数字、短横线，最长 64 个字符。
   */
  service: string;
  /**
   * 专有码，至少 1 项；code 在清单内不重复（x-uniqueItemsBy）。
   *
   * @minItems 1
   */
  codes: [ServiceErrorCode, ...ServiceErrorCode[]];
}
/**
 * 一个专有码。stage 为 execute 时不得有 httpStatus 与 additionalHttpStatuses；为 accept 或 both 时必须有 httpStatus。additionalHttpStatuses 不含主状态（x-arrayExcludesProperty）。
 */
export interface ServiceErrorCode {
  /**
   * 码：整体大写下划线或整体小写下划线写法，字母开头，不以下划线结尾，不含连续下划线，最长 128 个字符。
   */
  code: string;
  /**
   * accept：受理时同步返回；execute：异步执行阶段产生；both：两者都有。
   */
  stage: "accept" | "execute" | "both";
  /**
   * 主 HTTP 状态，4xx 或 5xx。
   */
  httpStatus?: number;
  /**
   * 同一个码在不同情形下的其他 HTTP 状态：至少 1 项、不重复、不含主状态。
   *
   * @minItems 1
   */
  additionalHttpStatuses?: [number, ...number[]];
  /**
   * 原样重试是否可能成功。
   */
  retryable: boolean;
  /**
   * not_executed：确定没有执行；unknown：可能已产生副作用。
   */
  outcome: "not_executed" | "unknown";
  /**
   * 一句话含义，1–1000 个字符。
   */
  meaning: string;
}

/**
 * 成功外壳。成功与否、新建还是已受理以 HTTP 状态码为准，code 不随 200 / 201 / 202 变化。
 */
export interface SuccessEnvelope {
  /**
   * 成功码，恒为 OK。
   */
  code: "OK";
  /**
   * 说明，可以为空串。
   */
  message: string;
  /**
   * 结果对象或 null；标量结果也包成对象（如 {"count": 3}）。
   */
  data: {
    [k: string]: unknown;
  } | null;
}
