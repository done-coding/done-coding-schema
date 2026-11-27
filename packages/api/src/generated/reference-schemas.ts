// 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
// 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
import type { SchemaDocument } from "./schemas";
/** CommonErrorCodes：common-error-codes.schema.json */
export const commonErrorCodesSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "common-error-codes.schema.json",
  title: "CommonErrorCodes",
  description:
    "通用失败码表（参考资源）：每个码给出 HTTP 状态（x-httpStatus），以及能否重试与是否已执行的参考值（x-referenceValue）。本表不约束任何结构：错误体不引用它，包不替使用方填写；使用方可显式引用表中值。$defs/code 列出全部通用失败码，须与 allOf 各项一一对应。",
  "x-referenceResource": true,
  $defs: {
    code: {
      description: "通用失败码。",
      enum: [
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
      ],
    },
  },
  allOf: [
    {
      description: "请求不符合接口契约",
      "x-httpStatus": 400,
      if: {
        properties: {
          code: {
            const: "INVALID_REQUEST",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "未登录，或令牌无效、过期",
      "x-httpStatus": 401,
      if: {
        properties: {
          code: {
            const: "UNAUTHENTICATED",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "已认证但无权执行",
      "x-httpStatus": 403,
      if: {
        properties: {
          code: {
            const: "FORBIDDEN",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "资源不存在，或调用方无权得知其存在",
      "x-httpStatus": 404,
      if: {
        properties: {
          code: {
            const: "NOT_FOUND",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "接口路径不存在",
      "x-httpStatus": 404,
      if: {
        properties: {
          code: {
            const: "ROUTE_NOT_FOUND",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "接口不支持该 HTTP 方法",
      "x-httpStatus": 405,
      if: {
        properties: {
          code: {
            const: "METHOD_NOT_ALLOWED",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "资源状态冲突",
      "x-httpStatus": 409,
      if: {
        properties: {
          code: {
            const: "CONFLICT",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "请求过于频繁，可稍后重试",
      "x-httpStatus": 429,
      if: {
        properties: {
          code: {
            const: "RATE_LIMITED",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": true,
              },
              outcome: {
                "x-referenceValue": "not_executed",
              },
            },
          },
        },
      },
    },
    {
      description: "服务内部错误，可能已产生副作用",
      "x-httpStatus": 500,
      if: {
        properties: {
          code: {
            const: "INTERNAL_ERROR",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "unknown",
              },
            },
          },
        },
      },
    },
    {
      description: "一次性列表的结果超出接口声明的上限",
      "x-httpStatus": 500,
      if: {
        properties: {
          code: {
            const: "LIST_LIMIT_EXCEEDED",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": false,
              },
              outcome: {
                "x-referenceValue": "unknown",
              },
            },
          },
        },
      },
    },
    {
      description: "服务或其依赖暂不可用",
      "x-httpStatus": 503,
      if: {
        properties: {
          code: {
            const: "SERVICE_UNAVAILABLE",
          },
        },
        required: ["code"],
      },
      then: {
        properties: {
          error: {
            properties: {
              retryable: {
                "x-referenceValue": true,
              },
              outcome: {
                "x-referenceValue": "unknown",
              },
            },
          },
        },
      },
    },
  ],
};
/** ListReferenceValues：list-reference-values.schema.json */
export const listReferenceValuesSchema: SchemaDocument = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "list-reference-values.schema.json",
  title: "ListReferenceValues",
  description:
    "列表的参考数值（参考资源）：只是参考，不约束任何结构。结构定义里页码、每页条数、每批条数都没有默认值和上限，包不替使用方填写；要用这些数值须在自己的代码里显式引用，或声明自己的值。",
  "x-referenceResource": true,
  "x-referenceValues": {
    PAGED_LIST_REFERENCE_VALUES: {
      description:
        "页码式列表的参考数值：page 是请求不带页码时可参考的页码，pageSize 是请求不带每页条数时可参考的条数，maxPageSize 是每页条数可参考的上限。",
      value: {
        page: 1,
        pageSize: 10,
        maxPageSize: 100,
      },
    },
    CURSOR_LIST_REFERENCE_VALUES: {
      description: "游标式列表的参考数值：maxLimit 是每批条数可参考的上限。",
      value: {
        maxLimit: 100,
      },
    },
  },
};
/** 全部参考资源定义，键为定义的 $id（即文件名）。 */
export const referenceSchemas = {
  "common-error-codes.schema.json": commonErrorCodesSchema,
  "list-reference-values.schema.json": listReferenceValuesSchema,
} as const;
