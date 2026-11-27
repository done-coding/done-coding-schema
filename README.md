# done-coding-schema

HTTP JSON 接口里前后端都要认的通用结构：成功外壳、错误体、三种列表、列表的请求参数与业务码。结构只在这里定义一次（JSON Schema），各语言的类型与模型由定义生成，发布成包：

| 语言 | 包 | 内容 |
|---|---|---|
| TypeScript / JavaScript | npm [`@done-coding/schema-api`](https://www.npmjs.com/package/@done-coding/schema-api) | 类型、成功码、结构定义文件；参考资源在子路径 `@done-coding/schema-api/reference`；可在浏览器端引入 |
| Python | PyPI [`done-coding-schema-api`](https://pypi.org/project/done-coding-schema-api/)（导入名 `done_coding_schema_api`） | Pydantic v2 模型、成功码、结构定义文件；参考资源在子模块 `done_coding_schema_api.reference` |

两个包从同一个提交构建、用同一个版本号。定义文件在 [`schemas/`](schemas/)，每个结构配有合法与不合法样例（[`schemas/examples/`](schemas/examples/)）。

**结构与参考资源分两个出口**：主入口只有结构，只引入结构时不受任何内置的码或数值约束。通用失败码与码表、列表的字段路径与参数名、参考数值（如每页 10 条、上限 100）都是参考资源，放在参考资源出口；包不替使用方填写，要用须显式引入、显式写进自己的代码（见「使用方怎样显式声明自己的配置」）。

## 通用约定

- 字段名一律小驼峰；时间用带时区的 RFC 3339 文本。
- 除特别说明外，对象不接受未声明的字段。
- 带格式的字符串（业务码、请求标识、排序参数等）不接受末尾换行。
- 整数按 JSON Schema 的语义判定：`12` 与 `12.0` 都是整数，`12.5`、字符串 `"12"`、布尔不是。

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

**页码式**：给人翻页的表格，能跳页、有总数。`totalPage` 等于 `ceil(totalRecord / pageSize)`，总数为 0 时为 0；`items` 的条数不超过 `pageSize`，也不超过 `totalRecord`；`pageSize` 回显请求值；不回传当前页码。

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
| `page.page` | 整数 ≥ 1；不带时的含义由接口自己声明 |
| `page.pageSize` | 整数 ≥ 1；不带时的含义与上限由接口自己声明 |
| `page.query` | 模糊搜索词，最多 200 个字符 |
| `page.orderBy` | 逗号分隔的「小驼峰字段名 [asc\|desc]」，不写方向即 asc，逗号后可有一个空格，最多 200 个字符，如 `createdAt desc, name` |
| `cursor.after` | 上一批返回的 `next`，首批不带 |
| `cursor.limit` | 整数 ≥ 1；不带时取多少条、上限多少由接口自己声明 |
| `filter.<字段>.eq` | 按字段等值筛选，字段为小驼峰，值为标量（如 `filter.status.eq=active`）；可筛选哪些字段由接口声明 |

结构不规定页码、每页条数、每批条数的默认值和上限，页码式列表响应里的 `pageSize` 也不设上限。参考资源出口有一组参考数值（`PAGED_LIST_REFERENCE_VALUES`：`page` 1、`pageSize` 10、`maxPageSize` 100；`CURSOR_LIST_REFERENCE_VALUES`：`maxLimit` 100），只是参考，不随结构生效。

### 业务码

通用码分两组：成功一组只有 `OK`，是成功外壳 `code` 的约束，属于结构，从主入口导出（`SUCCESS_CODES`）。失败一组如下，各带 HTTP 状态，以及能否重试与 outcome 的**参考值**。这张表是参考资源：错误体不引用它，包不替使用方填写，错误体里配任何合法的 `retryable` 与 `outcome` 都合法；使用方可显式引用表中值，能确定更具体的情形时照常改写（如同是 `SERVICE_UNAVAILABLE`，在执行前就拒绝的可标 `not_executed`，因配置缺失而不可用、重试无用的可标不可重试）。码表在参考资源出口：TS 与 Python 都是常量 `COMMON_ERROR_CODE_TABLE`；Python 另有 `reference_error_detail(code)` 按码取参考的 `error`（不是通用码时返回 `None`）。

| 码 | HTTP | 可重试（参考） | outcome（参考） | 含义 |
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

码用整体大写或整体小写的下划线写法；`stage` 为 `accept`（受理时同步返回）或 `both` 时必须有 `httpStatus`，`execute`（异步执行阶段产生）不得有。`OK` 与 `HTTP_<数字>` 是结构保留字，不能用；比较按字节进行，不做大小写归一。结构不拿专有码与通用码比：清单里出现 `NOT_FOUND` 也合法；要让专有码避开某组通用码，见「使用方怎样显式声明自己的配置」。

**遇到不认识的码**：按 HTTP 状态归类处理（4xx 按调用方问题、5xx 按服务端问题），再参考 `error.retryable` 与 `error.outcome` 决定能否重试。

## 有意为之的约束

下面几条常被问到，都是有意的，定义文件里都写着，任何 JSON Schema 2020-12 校验器都会检查：

- **三种列表靠顶层字段互相区分**：页码式顶层不得带 `cursor`，游标式不得带 `page`，一次性列表两者都不得带。同一份数据只能是其中一种，调用方不用猜。
- **错误体的 `code` 不能是 `OK`**：`OK` 是成功码，失败响应用它会让只看 `code` 的调用方误判。
- **字段错误的 `message` 最长 1000 个字符**：与其他说明字段一致；更长的补充说明放错误体的 `detail`。
- **带格式的字段整串匹配，末尾带换行不合法**：定义里以 `$` 收尾的正则都写成 `$(?![\s\S])`，在 ECMA-262 与 Python 的 `re` 下都只匹配真正的文本结尾（Python 的 `$` 本来会放过结尾一个换行）；「不能是纯空白」「不含空白」用按 ECMA-262 列明的空白字符类，不用各引擎各有出入的 `\S`。所以 Ajv、Python 的 jsonschema 等任何 JSON Schema 2020-12 校验器拿定义文件直接判，与包的模型结论相同（`x-` 检查关键字除外，见下一节）。

通用失败码的 `retryable` 与 `outcome` 不在此列：码表给的是参考值，包不替使用方填写（见上文「业务码」）。

## 定义文件表达不了的约束

标准 JSON Schema 写不出跨字段的比较，下面几条在定义里用 `x-` 开头的扩展关键字标注：

| 约束 | 扩展关键字 | 所在定义 |
|---|---|---|
| `totalPage` 等于 `ceil(totalRecord / pageSize)` | `x-totalPageEqualsCeil` | 页码式列表的 `page` |
| `items` 的条数不超过 `pageSize`，也不超过 `totalRecord` | `x-itemsWithinPage` | 页码式列表 |
| 专有码清单内 `code` 不重复 | `x-uniqueItemsBy` | 专有码清单的 `codes` |
| `additionalHttpStatuses` 不含 `httpStatus` | `x-arrayExcludesProperty` | 专有码清单的一项 |

谁来检查：

- **Python 包**：模型里已实现，与定义的判定一致。
- **本仓的样例校验**：按同一语义实现（[`scripts/lib/validator.mjs`](scripts/lib/validator.mjs)）。两种语言的结论用同一组样例逐例核对（见「开发」）。
- **TypeScript / 其他校验器**：通用校验器会忽略这些关键字。拿定义文件自己校验时，需要的话照 `scripts/lib/validator.mjs` 补上。

## 使用方怎样显式声明自己的配置

包里的码和数值都不会自己生效。要用，就在自己的代码里写出来：引用包里的参考值，或写自己的值。

**Python 子类：包保证什么**

- **包自己的模型**：定义、导出的 JSON Schema（`model_json_schema()`、FastAPI 生成的 OpenAPI）、运行时校验三者同结论。这是硬保证，由测试逐例核对。
- **使用方子类，只保证下面这几种写法**，在这些写法下导出与运行时同结论，有测试：
  1. 重新声明已有字段，收紧上下界、加默认值、收窄取值（如 `Literal`）。定义对该字段的约束照常生效，不必重写，写了更宽的也放不宽。整数字段用 `JsonInt`（与定义一样认 `12` 和 `12.0`）。
  2. 在三种列表的顶层（`BoundedList`、`PagedList`、`CursorList`）新增附带字段（如 `summary`）；定义写明不得出现的名字（如页码式列表的 `cursor`）除外。
  3. 查询参数：用内置的 `PagedListQuery` / `CursorListQuery`（已按前缀命名，不用自己改名），在子类里新增前缀外的参数。
  4. 继承参数化的泛型，如 `class UserPage(PagedList[User])`。
- **其余写法一律不支持**，导出与运行时可能不一致，由使用方自负。类定义时的检查（改线上字段名、在封闭结构上新增字段等会报错）只是尽力而为的提醒，不是保证。明确不支持的做法：
  - 改 `model_config`（`extra`、`strict`、别名相关开关等）；
  - `computed_field`；
  - 用校验器或序列化器改键名；
  - 单独设 `validation_alias`。

**每页条数的默认值与上限**（Python）：用上面第 1 种写法，子类重新声明字段：

```python
from pydantic import Field

from done_coding_schema_api import JsonInt, PagedListRequest
from done_coding_schema_api.reference import PAGED_LIST_REFERENCE_VALUES


class OrderPageRequest(PagedListRequest):
    pageSize: JsonInt = Field(default=20, le=50)  # 自己的值；0 仍按定义拒绝


class AuditPageRequest(PagedListRequest):
    # 采用包里的参考值，也要显式写出来
    pageSize: JsonInt = Field(
        default=PAGED_LIST_REFERENCE_VALUES["pageSize"],
        le=PAGED_LIST_REFERENCE_VALUES["maxPageSize"],
    )
```

`OrderPageRequest.model_json_schema()`，以及 FastAPI 用它作请求体或返回类型时生成的 OpenAPI，导出的是定义与子类声明的交集：`pageSize` 带上 `default: 20`、`maximum: 50`，定义里的说明与 `minimum: 1` 保留。运行时的校验与导出的结构结论相同：导出写着的约束都会执行。

**用作查询参数**（Python）：用包里内置的查询参数模型 `PagedListQuery`、`CursorListQuery`，线上名与解码都已写好：

- 线上名固定为「前缀.字段名」：`page.page`、`page.pageSize`、`page.query`、`page.orderBy`、`cursor.after`、`cursor.limit`。写成与字段同名的裸名（如 `?pageSize=50`）会报错并指出应写的线上名（「pageSize 应写作 page.pageSize」，HTTP 下是 422），不会静默用默认值；前缀下未声明的参数（如 `page.limit`）不合法；其余参数不归它管，忽略；
- 整数参数只收十进制数字串（定义里的 `x-queryIntegerPattern`：`0` 或不以 0 开头的数字），解码后再按定义的上下界校验；`02`、`+2`、` 2`、`2.0`、`1e1`、空串都拒；
- 继承它声明自己的默认值与上限，规则同上（子类只能收紧），不必再写别名与解码；
- 接口自己的其他查询参数（如 `status`、`minAmount`）也声明在同一个子类里：线上名就是字段名，在前缀之外，按子类自己的声明校验，不走前缀与整数解码。不能新增前缀下的字段（如 `page.foo`），也不能与上面的裸名同名。前缀外的整数参数用包里的 `QueryInt`，与前缀内的整数同一套写法（`02`、`+2` 等同样拒）；前缀外其他类型（如布尔）的解码规则由使用方自己的声明决定。

```python
from typing import Annotated, Any

from fastapi import FastAPI, Query
from pydantic import Field

from done_coding_schema_api import JsonInt, PagedListQuery, QueryInt


class OrderQuery(PagedListQuery):
    pageSize: JsonInt = Field(default=20, le=50)
    status: str | None = None  # 接口自己的参数：?status=paid
    minAmount: Annotated[QueryInt | None, Field(ge=0)] = None  # ?minAmount=100


app = FastAPI()


@app.get("/orders")
def list_orders(params: Annotated[OrderQuery, Query()]) -> dict[str, Any]:
    return {"page": params.page, "pageSize": params.pageSize, "status": params.status}
    # ?page.page=2&status=paid → {"page": 2, "pageSize": 20, "status": "paid"}
```

FastAPI 生成的 OpenAPI 里，参数名就是上面的线上名；每个参数的说明取自定义与子类声明的交集，约束写成 `minimum` / `maximum`，可选参数不写成可为 null。FastAPI 0.140 等较早的版本里，查询参数模型要是接口唯一的查询参数才会展开成各个参数，所以把接口的其他查询参数都声明在这个子类里。不用 FastAPI 时，把查询串解析成「参数名 → 字符串」的映射后交给 `OrderQuery.model_validate(...)` 即可。

**每页条数的默认值与上限**（TypeScript）：类型只描述结构，取值由自己的代码决定：

```ts
import type { PagedListRequest } from "@done-coding/schema-api";
import { PAGED_LIST_REFERENCE_VALUES } from "@done-coding/schema-api/reference";

const PAGE_SIZE = { default: 20, max: 50 }; // 自己的值
// 或采用参考值：{ default: PAGED_LIST_REFERENCE_VALUES.pageSize, max: PAGED_LIST_REFERENCE_VALUES.maxPageSize }

export function pageRequest(page = 1, pageSize = PAGE_SIZE.default): PagedListRequest {
  return { page, pageSize: Math.min(pageSize, PAGE_SIZE.max) };
}
```

**自己的通用码集合**：引用包里的一组，再加自己的。

```ts
import { COMMON_ERROR_CODES } from "@done-coding/schema-api/reference";

export const OUR_COMMON_CODES = { ...COMMON_ERROR_CODES, QUOTA_USED_UP: "QUOTA_USED_UP" } as const;
```

```python
from done_coding_schema_api.reference import COMMON_ERROR_CODES

OUR_COMMON_CODES = {**COMMON_ERROR_CODES, "QUOTA_USED_UP": "QUOTA_USED_UP"}
```

**让专有码避开自己的通用码**：结构只拦 `OK` 与 `HTTP_<数字>`。要避开哪组码，把那组码传给参考资源出口的检查函数，不传就不比。可以传字符串的数组或集合，也可以传「名字 → 码」的对象 / 映射（比对的是码的值，不是键）；按字节比较，返回撞码的位置与码，空即没有撞码。

```ts
import type { ServiceErrorCodes } from "@done-coding/schema-api";
import { findReservedCodes } from "@done-coding/schema-api/reference";

declare const list: ServiceErrorCodes;
const hits = findReservedCodes(list, OUR_COMMON_CODES); // [{ index: 1, code: "NOT_FOUND" }]
```

```python
from done_coding_schema_api import ServiceErrorCodes
from done_coding_schema_api.reference import find_reserved_codes

codes = ServiceErrorCodes.model_validate(data)  # 结构校验
hits = find_reserved_codes(codes, OUR_COMMON_CODES)  # [ReservedCodeHit(index=1, code='NOT_FOUND')]
if hits:
    raise ValueError(f"专有码与通用码重名：{hits}")
```

## TypeScript

```bash
npm install @done-coding/schema-api
```

预发布版用 `npm install @done-coding/schema-api@alpha` 安装。TypeScript 的 `moduleResolution` 取 `node`（node10）、`node16` / `nodenext`（CommonJS 与 ES 模块项目都行）、`bundler` 都能解析主入口与 `/reference` 子路径的类型。

类型（成功外壳与三种列表可带元素类型）从主入口取，字段路径、参数名与码表从参考资源出口取：

```ts
import type { ErrorBody, PagedList, SuccessEnvelope } from "@done-coding/schema-api";
import {
  COMMON_ERROR_CODE_TABLE,
  PAGED_LIST_REQUEST_PARAMS,
  PAGED_LIST_RESPONSE_PATHS,
} from "@done-coding/schema-api/reference";

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

**拿定义文件自己做校验**：结构定义以 `schemas` 导出（键为定义的 `$id`）；参考资源定义（通用失败码表、列表的参考数值）以 `referenceSchemas` 从参考资源出口导出。也可按路径取 JSON 文件，如 `@done-coding/schema-api/schemas/error-body.schema.json`。定义用 JSON Schema 2020-12，例如用 [Ajv](https://ajv.js.org/)：

```ts
import Ajv2020 from "ajv/dist/2020";
import { schemas } from "@done-coding/schema-api";

// 定义里带 x- 开头的扩展关键字，关闭 strict 让 Ajv 忽略它们
const ajv = new Ajv2020({ strict: false });
for (const schema of Object.values(schemas)) ajv.addSchema(schema);

const validateErrorBody = ajv.getSchema("error-body.schema.json")!;
validateErrorBody({ code: "OK", message: "x", data: null, error: { retryable: false, outcome: "unknown" }, requestId: "r" }); // false
```

以 `x-` 开头的跨字段约束 Ajv 不会检查，见「定义文件表达不了的约束」。

## Python

```bash
pip install done-coding-schema-api
```

需要 Python 3.10 及以上、Pydantic v2（2.11 及以上）。最低版本（Python 3.10、pydantic 2.11、FastAPI 0.140）与当前锁定版本经过测试，中间版本没有逐个测试。模型是严格类型的：不做 `"10"` → `10` 这类转换；整数字段接受 `12.0` 并归一成 `12`（与 JSON Schema 一致）。「定义文件表达不了的约束」也已包含在内。

```python
from pydantic import BaseModel

from done_coding_schema_api import ErrorBody, PagedList, SuccessEnvelope
from done_coding_schema_api.reference import (
    COMMON_ERROR_CODE_TABLE,
    PAGED_LIST_REQUEST_PARAMS,
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

**校验报错指到具体字段**：如 `totalPage` 不对时位置是 `("page", "totalPage")`，嵌在成功外壳里则是 `("data", "page", "totalPage")`；「不得出现」的字段指到多出来的那个，如页码式列表带了 `cursor` 时是 `("cursor",)`。页码式列表的条数超限分两种错误类型：`items_exceed_page_size`（超过 `pageSize`）与 `items_exceed_total_record`（超过 `totalRecord`），定义校验器的报错在 `params.errorType` 里给出同样的名字。

**导出的 JSON Schema 就是定义本身**：`model_json_schema()` 以及 FastAPI 用 `response_model` 生成的 OpenAPI，导出的都是对应的定义（引用已展开，`x-` 约束原样带出），可选字段不会被写成可为 `null`。泛型只替换参数处：`PagedList[User]` 与 `class UserPage(PagedList[User])` 的 `items` 元素是 `User`，`SuccessEnvelope[X]` 的 `data` 是 `X`。子类重新声明已有字段（加上限、加默认、收窄类型；查询参数模型还可以按前缀改线上名）时，导出的是定义与子类声明的交集，运行时同样两者都检查，见「使用方怎样显式声明自己的配置」。

**定义文件**：包里带着与 npm 包同一批的定义文件，可以交给任何 JSON Schema 校验器。结构定义从包顶层取，参考资源定义从 `reference` 子模块取：

```python
from done_coding_schema_api import load_schema, schema_names, schema_path
from done_coding_schema_api.reference import load_reference_schema, reference_schema_names

schema_names()  # ('bounded-list', 'cursor-list', 'cursor-list-request', ...)
schema_path("error-body")  # 包内 error-body.schema.json 的路径
load_schema("error-body")["$id"]  # 'error-body.schema.json'（每次返回新的字典）
reference_schema_names()  # ('common-error-codes', 'list-reference-values')
load_reference_schema("common-error-codes")["title"]  # 'CommonErrorCodes'
```

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
| `pnpm check` | 样例校验、生成物一致、版本一致、许可证副本一致、两语言测试与构建产物检查（含 wheel 与 sdist 里的定义文件） |
| `pnpm check:min-versions` | 在最低支持版本（取自 `python/pyproject.toml` 的下界）的临时环境里装本机构建的 wheel，跑全部 Python 测试；要联网，耗时较长，发布前必跑，不在 `pnpm check` 里 |

**两种语言的一致性**：`schemas/examples/` 的每个样例先由定义判（Ajv 加 `x-` 关键字的实现，`pnpm check:examples`），再由 Python 包对外导出的模型判（JSON 与 Python 两种输入都测），再由 Python 的通用校验器 jsonschema 直接拿包里的定义文件判（只因 `x-` 检查关键字被拒的样例，它判合法才算一致）；后两者在 `python/tests/test_examples.py`。三方结论须逐例相同，否则 `pnpm check` 不过。样例里包括整数写成 `12.0`、列表条数到上限与超上限、三种列表互斥的字段、通用码配任意 `retryable` / `outcome`、每页条数 500、专有码与通用码同名这类边界。

发布流程见 [`docs/release.md`](docs/release.md)。
