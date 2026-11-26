# done-coding-schema

HTTP JSON 接口里前后端都要认的通用结构：成功外壳、错误体、三种列表、列表的请求参数与业务码。结构只在这里定义一次（JSON Schema），各语言的类型与模型由定义生成，发布成包：

| 语言 | 包 | 内容 |
|---|---|---|
| TypeScript / JavaScript | npm [`@done-coding/schema-api`](https://www.npmjs.com/package/@done-coding/schema-api) | 类型、业务码与字段路径常量、定义文件；可在浏览器端引入 |
| Python | PyPI [`done-coding-schema-api`](https://pypi.org/project/done-coding-schema-api/)（导入名 `done_coding_schema_api`） | Pydantic v2 模型与常量 |

两个包从同一个提交构建、用同一个版本号。定义文件在 [`schemas/`](schemas/)，每个结构配有合法与不合法样例（[`schemas/examples/`](schemas/examples/)）。

## 通用约定

- 字段名一律小驼峰；时间用带时区的 RFC 3339 文本。
- 除特别说明外，对象不接受未声明的字段。
- 带格式的字符串（业务码、请求标识、排序参数等）不接受末尾换行。

## 结构

### 成功外壳

```json
{ "code": "OK", "message": "", "data": { "id": "u1" } }
```

所有成功响应都用它。`code` 恒为 `OK`；成功与否、新建还是已受理以 HTTP 状态码为准，`code` 不随 200 / 201 / 202 变化。`data` 是对象或 `null`，标量结果也包成对象（如 `{"count": 3}`）。`message` 最长 1000 个字符，可以为空串。

### 错误体

```json
{
  "code": "INVALID_REQUEST",
  "message": "请求参数不合法",
  "data": null,
  "error": {
    "retryable": false,
    "outcome": "not_executed",
    "fields": [
      { "in": "query", "code": "out_of_range", "message": "超出范围", "parameter": "page.pageSize" },
      { "in": "body", "code": "required", "message": "必填", "pointer": "/items/0/name" }
    ]
  },
  "requestId": "req-01"
}
```

所有失败响应都用它，HTTP 状态表达大类。

- `code`：业务码，字母开头、只含字母数字下划线，1–128 个字符，不能是 `OK`。
- `error.retryable`：原样重试是否可能成功；`error.outcome`：`not_executed` 表示确定没有执行，`unknown` 表示可能已产生副作用。
- `error.fields`（可选）：逐项指出出错的输入。`in` 为 `body` 时用 `pointer`（RFC 6901 JSON Pointer）定位、不能有 `parameter`；其他位置用 `parameter` 定位、不能有 `pointer`。
- `requestId`：1–128 个非空白字符；`detail`（可选）：补充说明，不限长。

### 三种列表

三种列表都是成功外壳的 `data`，数据都放 `items`，翻页信息各放各的位置。一个接口只选一种，在接口自己的文档里声明。顶层允许接口声明附带字段（如本页汇总），但不得重复表达翻页信息。

**一次性列表**：条数有一个由定义决定、不随业务数据增长的上限（如下拉选项）。上限由接口声明，超过上限报 `LIST_LIMIT_EXCEEDED`，不截断。

```json
{ "items": [{ "value": "a", "label": "甲" }] }
```

**页码式**：给人翻页的表格，能跳页、有总数。`totalPage` 等于 `ceil(totalRecord / pageSize)`，总数为 0 时为 0；`pageSize` 回显请求值；不回传当前页码。

```json
{ "items": [{ "id": 1 }], "page": { "totalRecord": 21, "pageSize": 10, "totalPage": 3 } }
```

**游标式**：消息流这类接着往下取的列表，不带总数。`hasMore` 为 `true` 时必须给 `next`；`next` 对调用方不透明，下一批原样带回。取数方向由接口声明。

```json
{ "items": [{ "id": 1 }], "cursor": { "next": "eyJpZCI6MX0", "hasMore": true } }
```

**怎么选**

| 场景 | 选 |
|---|---|
| 结果条数有固定上限（选项、枚举、配置项） | 一次性列表 |
| 给人看的表格，要总数、要跳页 | 页码式 |
| 数据持续增长、只需接着往下取（消息流、日志、动态） | 游标式 |

### 列表的请求参数

线上以点号命名的查询参数传递；定义约束的是按前缀解码后的对象。前缀下出现未声明的参数视为不合法。

| 线上参数 | 约束 |
|---|---|
| `page.page` | 整数 ≥ 1，缺省 1 |
| `page.pageSize` | 整数 1–100，缺省 10 |
| `page.query` | 模糊搜索词，最多 200 个字符 |
| `page.orderBy` | 逗号分隔的「小驼峰字段名 [asc\|desc]」，缺省 asc，逗号后可有一个空格，最多 200 个字符，如 `createdAt desc, name` |
| `cursor.after` | 上一批返回的 `next`，首批不带 |
| `cursor.limit` | 整数 1–100，缺省值由接口自定 |
| `filter.<字段>.eq` | 按字段等值筛选，字段为小驼峰，值为标量（如 `filter.status.eq=active`）；可筛选哪些字段由接口声明 |

### 业务码

通用码分两组：成功一组只有 `OK`；失败一组如下，各带固定的 HTTP 状态、能否重试与 outcome（错误体里用到通用码时必须与此一致）。

| 码 | HTTP | 可重试 | outcome | 含义 |
|---|---|---|---|---|
| `INVALID_REQUEST` | 400 | 否 | not_executed | 请求不符合接口契约 |
| `UNAUTHENTICATED` | 401 | 否 | not_executed | 未登录，或令牌无效、过期 |
| `FORBIDDEN` | 403 | 否 | not_executed | 已认证但无权执行 |
| `NOT_FOUND` | 404 | 否 | not_executed | 资源不存在，或调用方无权得知其存在 |
| `ROUTE_NOT_FOUND` | 404 | 否 | not_executed | 接口路径不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 否 | not_executed | 接口不支持该 HTTP 方法 |
| `CONFLICT` | 409 | 否 | not_executed | 资源状态冲突 |
| `RATE_LIMITED` | 429 | 是 | not_executed | 请求过于频繁，可稍后重试 |
| `INTERNAL_ERROR` | 500 | 否 | unknown | 服务内部错误，可能已产生副作用 |
| `LIST_LIMIT_EXCEEDED` | 500 | 否 | unknown | 一次性列表的结果超出接口声明的上限 |
| `SERVICE_UNAVAILABLE` | 503 | 是 | unknown | 服务或其依赖暂不可用 |

**专有码怎么加**：错误体的 `code` 是开放字符串，服务可以有自己的码，写成一份清单（定义见 [`schemas/service-error-codes.schema.json`](schemas/service-error-codes.schema.json)）：

```json
{
  "service": "order-service",
  "codes": [
    { "code": "ORDER_LOCKED", "stage": "accept", "httpStatus": 409, "retryable": false, "outcome": "not_executed", "meaning": "订单已锁定，不能修改" },
    { "code": "PAYMENT_TIMEOUT", "stage": "execute", "retryable": true, "outcome": "unknown", "meaning": "支付超时" }
  ]
}
```

码用整体大写或整体小写的下划线写法；`stage` 为 `accept`（受理时同步返回）或 `both` 时必须有 `httpStatus`，`execute`（异步执行阶段产生）不得有。不得重新定义通用码；`OK` 与 `HTTP_<数字>` 保留不用；比较按字节进行，不做大小写归一。

**遇到不认识的码**：按 HTTP 状态归类处理（4xx 按调用方问题、5xx 按服务端问题），再参考 `error.retryable` 与 `error.outcome` 决定能否重试。

## TypeScript

```bash
npm install @done-coding/schema-api
```

类型（成功外壳与三种列表可带元素类型）与常量：

```ts
import {
  COMMON_ERROR_CODE_TABLE,
  PAGED_LIST_REQUEST_PARAMS,
  PAGED_LIST_RESPONSE_PATHS,
  type ErrorBody,
  type PagedList,
  type SuccessEnvelope,
} from "@done-coding/schema-api";

interface User {
  id: string;
  name: string;
}

// 页码式列表的成功响应
export async function listUsers(page: number): Promise<SuccessEnvelope<PagedList<User>>> {
  const params = new URLSearchParams({ [PAGED_LIST_REQUEST_PARAMS.page]: String(page) });
  const response = await fetch(`/api/users?${params}`);
  if (!response.ok) {
    const failure = (await response.json()) as ErrorBody;
    throw new Error(`${failure.code}: ${failure.message}`);
  }
  return response.json();
}

// 常量都是字面量类型
const totalPath: "page.totalRecord" = PAGED_LIST_RESPONSE_PATHS.totalRecord;
const retryable: boolean = COMMON_ERROR_CODE_TABLE.RATE_LIMITED.retryable;
```

接口在列表顶层声明的附带字段用交叉类型补：`PagedList<User> & { summary: Summary }`。

**拿定义文件自己做校验**：定义以 `schemas` 导出（键为定义的 `$id`），也可按路径取 JSON 文件，如 `@done-coding/schema-api/schemas/error-body.schema.json`。定义用 JSON Schema 2020-12，例如用 [Ajv](https://ajv.js.org/)：

```ts
import Ajv2020 from "ajv/dist/2020";
import { schemas } from "@done-coding/schema-api";

// 定义里带 x- 开头的扩展关键字，关闭 strict 让 Ajv 忽略它们
const ajv = new Ajv2020({ strict: false });
for (const schema of Object.values(schemas)) ajv.addSchema(schema);

const validateErrorBody = ajv.getSchema("error-body.schema.json")!;
validateErrorBody({ code: "OK", message: "x", data: null, error: { retryable: false, outcome: "unknown" }, requestId: "r" }); // false
```

标准 JSON Schema 写不出的三条跨字段约束以扩展关键字标注，通用校验器不会检查，需要时自行补上：`x-totalPageEqualsCeil`（`totalPage` 等于 `ceil(totalRecord / pageSize)`）、`x-uniqueItemsBy`（专有码清单内 `code` 不重复）、`x-arrayExcludesProperty`（`additionalHttpStatuses` 不含 `httpStatus`）。

## Python

```bash
pip install done-coding-schema-api
```

需要 Python 3.10 及以上、Pydantic v2（2.11 及以上）。模型是严格类型的（不做 `"10"` → `10` 这类转换），上面三条跨字段约束也已包含在内。

```python
from pydantic import BaseModel

from done_coding_schema_api import (
    COMMON_ERROR_CODE_TABLE,
    PAGED_LIST_REQUEST_PARAMS,
    ErrorBody,
    PagedList,
    SuccessEnvelope,
)


class User(BaseModel):
    id: str
    name: str


# 声明接口的返回类型，例如 FastAPI 的 response_model=SuccessEnvelope[PagedList[User]]
UserPage = SuccessEnvelope[PagedList[User]]

result = UserPage.model_validate_json(
    '{"code": "OK", "message": "", "data": {"items": [{"id": "u1", "name": "甲"}],'
    ' "page": {"totalRecord": 1, "pageSize": 10, "totalPage": 1}}}'
)
print(result.data.items[0].name)  # 甲

failure = ErrorBody.model_validate(
    {
        "code": "RATE_LIMITED",
        "message": "请求过于频繁",
        "data": None,
        "error": {"retryable": True, "outcome": "not_executed"},
        "requestId": "req-02",
    }
)
print(COMMON_ERROR_CODE_TABLE[failure.code]["httpStatus"])  # 429
print(PAGED_LIST_REQUEST_PARAMS["pageSize"])  # page.pageSize
```

输出用线上字段名（如出错字段的 `in`，Python 里的属性名是 `in_`）；列表顶层的附带字段原样保留。

## 版本与兼容

- 两个包同一版本号，遵循语义化版本。npm 的预发布版本 `X.Y.Z-alpha.N` 在 PyPI 上写作 `X.Y.ZaN`（`beta` → `b`、`rc` → `rc`）。
- **破坏性改动升主版本**：改字段名、删字段、收紧取值范围、给开放字段加枚举限制、增减结构。
- 其他向后兼容的新增（如新增结构、新增可选字段）升次版本；不改变结构的修正升修订版本。
- 对象默认不接受未声明的字段：用旧版本校验新版本服务返回的数据时，新加的字段会被拒绝，升级时先升使用方再升服务方。

## 本包不做什么

- 不带定制开关：不提供「传入自定义成功码」之类的入口，包只描述这一套结构。后端不按这套结构的项目不引本包，在自己的请求层里适配。
- 不定义具体业务资源、界面展示元数据、系统间事件与凭据格式；不另出 HTTP 状态码枚举（各语言都有现成的）。

## 开发

| 命令 | 作用 |
|---|---|
| `pnpm install`、`uv sync --project python` | 安装依赖 |
| `pnpm gen` | 由 `schemas/` 生成两个包里的类型、模型与常量（生成物不手改） |
| `pnpm check` | 样例校验、生成物一致、版本一致、许可证副本一致、两语言测试与构建产物检查 |

发布流程见 [`docs/release.md`](docs/release.md)。
