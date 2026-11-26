// 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
// 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
/** 一份 JSON Schema 定义文档。 */
export interface SchemaDocument {
  readonly [keyword: string]: unknown;
}
/** BoundedList：bounded-list.schema.json */
export const boundedListSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "bounded-list.schema.json",
  title: "BoundedList",
  description:
    "一次性列表，作成功外壳的 data。只用于条数有一个由定义决定、不随业务数据增长的上限的结果（如下拉选项）；上限由各接口在自己的契约里声明，超过上限报 LIST_LIMIT_EXCEEDED，不截断。顶层允许接口自己声明的附带字段，但不得带翻页信息。",
  "x-pathConstants": "BOUNDED_LIST_RESPONSE_PATHS",
  type: "object",
  properties: {
    items: {
      description: "列表数据。",
      type: "array",
    },
    page: false,
    cursor: false,
  },
  required: ["items"],
};
/** CursorListRequest：cursor-list-request.schema.json */
export const cursorListRequestSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "cursor-list-request.schema.json",
  title: "CursorListRequest",
  description:
    "游标式列表的请求参数。线上以 cursor. 前缀的查询参数传递（如 cursor.limit=20），本定义约束解码后的对象；前缀下未声明的参数不合法。",
  "x-paramPrefix": "cursor",
  "x-pathConstants": "CURSOR_LIST_REQUEST_PARAMS",
  type: "object",
  properties: {
    after: {
      description: "上一批返回的 next，1–1024 个字符；首批不带。",
      type: "string",
      minLength: 1,
      maxLength: 1024,
    },
    limit: {
      description:
        "本批最多取多少条，至少 1；不带时取多少条、上限多少由接口自己声明。",
      type: "integer",
      minimum: 1,
    },
  },
  additionalProperties: false,
};
/** CursorList：cursor-list.schema.json */
export const cursorListSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "cursor-list.schema.json",
  title: "CursorList",
  description:
    "游标式列表，作成功外壳的 data：消息流这类接着往下取的列表，不带总数。取数方向由各接口声明。顶层允许接口自己声明的附带字段，但不得重复表达翻页信息；不带 page。",
  "x-pathConstants": "CURSOR_LIST_RESPONSE_PATHS",
  type: "object",
  properties: {
    items: {
      description: "本批数据。",
      type: "array",
    },
    cursor: {
      $ref: "#/$defs/cursor",
    },
    page: false,
  },
  required: ["items", "cursor"],
  $defs: {
    cursor: {
      title: "CursorListCursor",
      description: "接着取的位置。hasMore 为 true 时必须给 next。",
      type: "object",
      properties: {
        next: {
          description:
            "下一批的游标，对调用方不透明，1–1024 个字符；没有更多时可省略。",
          type: "string",
          minLength: 1,
          maxLength: 1024,
        },
        hasMore: {
          description: "是否还有更多。",
          type: "boolean",
        },
      },
      required: ["hasMore"],
      additionalProperties: false,
      if: {
        properties: {
          hasMore: {
            const: true,
          },
        },
        required: ["hasMore"],
      },
      then: {
        required: ["next"],
      },
    },
  },
};
/** ErrorBody：error-body.schema.json */
export const errorBodySchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "error-body.schema.json",
  title: "ErrorBody",
  description:
    "错误体。HTTP 状态表达大类，包体带业务码、说明、能否重试、是否已执行与出错字段定位。retryable 与 outcome 由服务按实际情形填写，包不替使用方填写；通用失败码表给了一组参考值，使用方可显式引用。",
  type: "object",
  properties: {
    code: {
      description:
        "业务码，开放字符串：字母开头，只含字母、数字、下划线，1–128 个字符；不能是 OK。使用方遇到不认识的码按 HTTP 状态归类处理。",
      type: "string",
      pattern: "^[A-Za-z][A-Za-z0-9_]{0,127}$",
      not: {
        const: "OK",
      },
    },
    message: {
      description: "说明，不能是纯空白。",
      type: "string",
      maxLength: 1000,
      pattern: "\\S",
    },
    data: {
      description: "错误体恒为 null。",
      type: "null",
    },
    error: {
      $ref: "#/$defs/errorDetail",
    },
    requestId: {
      description: "请求标识，1–128 个字符，不含空白字符。",
      type: "string",
      pattern: "^\\S{1,128}$",
    },
    detail: {
      description: "补充说明，可选，不限长。",
      type: "string",
    },
  },
  required: ["code", "message", "data", "error", "requestId"],
  additionalProperties: false,
  $defs: {
    errorDetail: {
      title: "ErrorDetail",
      description: "错误的处置信息。",
      type: "object",
      properties: {
        retryable: {
          description: "原样重试是否可能成功。",
          type: "boolean",
        },
        outcome: {
          description:
            "not_executed：确定没有执行；unknown：可能已产生副作用。",
          enum: ["not_executed", "unknown"],
        },
        fields: {
          description: "逐项指出出错的输入；可以是空数组。",
          type: "array",
          items: {
            $ref: "#/$defs/errorField",
          },
        },
      },
      required: ["retryable", "outcome"],
      additionalProperties: false,
    },
    errorField: {
      title: "ErrorField",
      description:
        "一项出错的输入。in 为 body 时用 pointer 定位、不能有 parameter；其他位置用 parameter 定位、不能有 pointer。",
      type: "object",
      properties: {
        in: {
          description: "出错输入所在的位置。",
          enum: ["body", "query", "path", "header", "cookie"],
        },
        code: {
          description:
            "字段级错误码：字母开头，只含字母、数字、下划线、点、短横线，1–128 个字符。",
          type: "string",
          pattern: "^[A-Za-z][A-Za-z0-9_.\\-]{0,127}$",
        },
        message: {
          description: "说明，不能是纯空白。",
          type: "string",
          maxLength: 1000,
          pattern: "\\S",
        },
        pointer: {
          description: "请求体内的位置，RFC 6901 JSON Pointer。",
          type: "string",
          pattern:
            "^(?:(?:/(?:[^~/]|~[01])*)*/(?:(?:[^~/]|~[01])*(?:[^~/\\n]|~[01]))?)?$",
        },
        parameter: {
          description: "参数名，1–256 个字符。",
          type: "string",
          minLength: 1,
          maxLength: 256,
        },
      },
      required: ["in", "code", "message"],
      additionalProperties: false,
      if: {
        properties: {
          in: {
            const: "body",
          },
        },
        required: ["in"],
      },
      then: {
        required: ["pointer"],
        properties: {
          parameter: false,
        },
      },
      else: {
        required: ["parameter"],
        properties: {
          pointer: false,
        },
      },
    },
  },
};
/** ListFilter：list-filter.schema.json */
export const listFilterSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "list-filter.schema.json",
  title: "ListFilter",
  description:
    "列表的筛选参数。线上写作 filter.<字段>.<操作>（如 filter.status.eq=active），本定义约束解码后的对象 {<字段>: {<操作>: 值}}；字段为小驼峰，可筛选哪些字段由接口自己声明。首版操作只有 eq。前缀下未声明的参数不合法。",
  "x-paramPrefix": "filter",
  "x-pathConstants": "LIST_FILTER_PARAMS",
  type: "object",
  patternProperties: {
    "^[a-z][a-zA-Z0-9]*$": {
      $ref: "#/$defs/condition",
    },
  },
  additionalProperties: false,
  $defs: {
    condition: {
      title: "ListFilterCondition",
      description: "一个字段上的筛选条件，至少一个操作。",
      type: "object",
      properties: {
        eq: {
          description: "等于；值为标量。",
          type: ["string", "number", "boolean"],
        },
      },
      minProperties: 1,
      additionalProperties: false,
    },
  },
};
/** PagedListRequest：paged-list-request.schema.json */
export const pagedListRequestSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "paged-list-request.schema.json",
  title: "PagedListRequest",
  description:
    "页码式列表的请求参数。线上以 page. 前缀的查询参数传递（如 page.pageSize=20），本定义约束解码后的对象；前缀下未声明的参数不合法。",
  "x-paramPrefix": "page",
  "x-pathConstants": "PAGED_LIST_REQUEST_PARAMS",
  type: "object",
  properties: {
    page: {
      description: "页码，从 1 开始；不带时的含义由接口自己声明。",
      type: "integer",
      minimum: 1,
    },
    pageSize: {
      description: "每页条数，至少 1；不带时的含义与上限由接口自己声明。",
      type: "integer",
      minimum: 1,
    },
    query: {
      description: "模糊搜索词，最多 200 个字符。",
      type: "string",
      maxLength: 200,
    },
    orderBy: {
      description:
        "排序：逗号分隔，每段是小驼峰字段名，后面可跟一个空格加 asc 或 desc（缺省 asc）；逗号后可有一个空格；最多 200 个字符。",
      type: "string",
      maxLength: 200,
      pattern:
        "^[a-z][a-zA-Z0-9]*(?: (?:asc|desc))?(?:, ?[a-z][a-zA-Z0-9]*(?: (?:asc|desc))?)*$",
    },
  },
  additionalProperties: false,
};
/** PagedList：paged-list.schema.json */
export const pagedListSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "paged-list.schema.json",
  title: "PagedList",
  description:
    "页码式列表，作成功外壳的 data：给人翻页的表格，能跳页、有总数。顶层允许接口自己声明的附带字段，但不得重复表达翻页信息；不带 cursor。items 的条数不超过 page.pageSize，也不超过 page.totalRecord（x-itemsWithinPage）。",
  "x-pathConstants": "PAGED_LIST_RESPONSE_PATHS",
  type: "object",
  properties: {
    items: {
      description: "当前页的数据。",
      type: "array",
    },
    page: {
      $ref: "#/$defs/page",
    },
    cursor: false,
  },
  required: ["items", "page"],
  "x-itemsWithinPage": true,
  $defs: {
    page: {
      title: "PagedListPage",
      description:
        "翻页信息。不回传当前页码。totalPage 等于 ceil(totalRecord / pageSize)，总数为 0 时为 0（x-totalPageEqualsCeil）。",
      type: "object",
      properties: {
        totalRecord: {
          description: "总条数。",
          type: "integer",
          minimum: 0,
        },
        pageSize: {
          description: "每页条数，回显请求值，至少 1。",
          type: "integer",
          minimum: 1,
        },
        totalPage: {
          description: "总页数。",
          type: "integer",
          minimum: 0,
        },
      },
      required: ["totalRecord", "pageSize", "totalPage"],
      additionalProperties: false,
      if: {
        properties: {
          totalRecord: {
            const: 0,
          },
        },
        required: ["totalRecord"],
      },
      then: {
        properties: {
          totalPage: {
            const: 0,
          },
        },
      },
      "x-totalPageEqualsCeil": true,
    },
  },
};
/** ServiceErrorCodes：service-error-codes.schema.json */
export const serviceErrorCodesSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "service-error-codes.schema.json",
  title: "ServiceErrorCodes",
  description:
    "一个服务的专有业务码清单。OK 与 HTTP_<数字> 形式的码是结构保留字，不得使用；比较按字节精确进行，不做大小写归一。专有码是否要避开某组通用码由使用方显式检查：把那组码传给参考资源出口的检查函数，不传就不比。",
  type: "object",
  properties: {
    service: {
      description:
        "服务标识：小写字母开头，只含小写字母、数字、短横线，最长 64 个字符。",
      type: "string",
      pattern: "^[a-z][a-z0-9\\-]{0,63}$",
    },
    codes: {
      description:
        "专有码，至少 1 项；code 在清单内不重复（x-uniqueItemsBy）。",
      type: "array",
      minItems: 1,
      items: {
        $ref: "#/$defs/code",
      },
      "x-uniqueItemsBy": "code",
    },
  },
  required: ["service", "codes"],
  additionalProperties: false,
  $defs: {
    code: {
      title: "ServiceErrorCode",
      description:
        "一个专有码。stage 为 execute 时不得有 httpStatus 与 additionalHttpStatuses；为 accept 或 both 时必须有 httpStatus。additionalHttpStatuses 不含主状态（x-arrayExcludesProperty）。",
      type: "object",
      properties: {
        code: {
          description:
            "码：整体大写下划线或整体小写下划线写法，字母开头，不以下划线结尾，不含连续下划线，最长 128 个字符。",
          type: "string",
          maxLength: 128,
          pattern:
            "^(?:[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*|[a-z][a-z0-9]*(?:_[a-z0-9]+)*)$",
          allOf: [
            {
              not: {
                const: "OK",
              },
            },
            {
              not: {
                type: "string",
                pattern: "^HTTP_[0-9]+$",
              },
            },
          ],
        },
        stage: {
          description:
            "accept：受理时同步返回；execute：异步执行阶段产生；both：两者都有。",
          enum: ["accept", "execute", "both"],
        },
        httpStatus: {
          description: "主 HTTP 状态，4xx 或 5xx。",
          type: "integer",
          minimum: 400,
          maximum: 599,
        },
        additionalHttpStatuses: {
          description:
            "同一个码在不同情形下的其他 HTTP 状态：至少 1 项、不重复、不含主状态。",
          type: "array",
          minItems: 1,
          uniqueItems: true,
          items: {
            type: "integer",
            minimum: 400,
            maximum: 599,
          },
        },
        retryable: {
          description: "原样重试是否可能成功。",
          type: "boolean",
        },
        outcome: {
          description:
            "not_executed：确定没有执行；unknown：可能已产生副作用。",
          enum: ["not_executed", "unknown"],
        },
        meaning: {
          description: "一句话含义，1–1000 个字符。",
          type: "string",
          minLength: 1,
          maxLength: 1000,
        },
      },
      required: ["code", "stage", "retryable", "outcome", "meaning"],
      additionalProperties: false,
      if: {
        properties: {
          stage: {
            const: "execute",
          },
        },
        required: ["stage"],
      },
      then: {
        properties: {
          httpStatus: false,
          additionalHttpStatuses: false,
        },
      },
      else: {
        required: ["httpStatus"],
      },
      "x-arrayExcludesProperty": {
        array: "additionalHttpStatuses",
        property: "httpStatus",
      },
    },
  },
};
/** SuccessEnvelope：success-envelope.schema.json */
export const successEnvelopeSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "success-envelope.schema.json",
  title: "SuccessEnvelope",
  description:
    "成功外壳。成功与否、新建还是已受理以 HTTP 状态码为准，code 不随 200 / 201 / 202 变化。",
  type: "object",
  properties: {
    code: {
      description: "成功码，恒为 OK。",
      const: "OK",
    },
    message: {
      description: "说明，可以为空串。",
      type: "string",
      maxLength: 1000,
    },
    data: {
      description: '结果对象或 null；标量结果也包成对象（如 {"count": 3}）。',
      type: ["object", "null"],
      additionalProperties: true,
    },
  },
  required: ["code", "message", "data"],
  additionalProperties: false,
};
/** 全部结构定义，键为定义的 $id（即文件名），可整体登记到校验器里。 */
export const schemas = {
  "bounded-list.schema.json": boundedListSchema,
  "cursor-list-request.schema.json": cursorListRequestSchema,
  "cursor-list.schema.json": cursorListSchema,
  "error-body.schema.json": errorBodySchema,
  "list-filter.schema.json": listFilterSchema,
  "paged-list-request.schema.json": pagedListRequestSchema,
  "paged-list.schema.json": pagedListSchema,
  "service-error-codes.schema.json": serviceErrorCodesSchema,
  "success-envelope.schema.json": successEnvelopeSchema,
} as const;
