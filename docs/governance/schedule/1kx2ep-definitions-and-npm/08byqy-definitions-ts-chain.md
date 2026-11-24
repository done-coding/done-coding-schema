---
id: 08byqy
title: 首版结构的定义、样例、TS 生成链与 npm 包骨架
modules: [definition, toolchain, npm-package]
created: 2026-11-24
parent: ""
---

# 首版结构的定义、样例、TS 生成链与 npm 包骨架

## 为什么

通用结构要有一份唯一的定义，各语言的代码从它生成。本条写出首版定义，并打通「定义 → TS 类型」这条生成链，后面两批只是往上加语言和发布流程。

## 交付

1. `schemas/` 下首版结构的定义，一个结构一个文件。
2. 每个结构的合法、不合法样例，以及一条跑样例校验的命令。
3. 一个 npm 成员包：导出由定义生成的 TS 类型、业务码常量与定义文件本身。
4. 生成命令与一致性检查命令。

## 规格（用户 2026-11-24 定，照此写定义）

通用约定：字段名一律小驼峰；时间用带时区的 RFC 3339 文本；除特别说明外，对象不接受未声明的字段。

### 成功外壳

```
{ code: "OK", message: string, data: 对象 | null }
```

- `code` 恒为 `"OK"`。成功与否、新建还是已受理，以 HTTP 状态码为准，`code` 不随 200 / 201 / 202 变化。
- `data` 是对象或 null；标量结果也包成对象（如 `{count: 3}`）。
- 三个字段都必有。

### 错误体

```
{
  code: string,
  message: string,
  data: null,
  error: {
    retryable: boolean,
    outcome: "not_executed" | "unknown",
    fields?: [ { in, code, message, pointer?, parameter? } ]
  },
  requestId: string,
  detail?: string
}
```

- `code`：业务码，开放字符串，只限格式：字母开头，只含字母、数字、下划线，1–128 个字符。**不锁成通用码的枚举**。
- `error.retryable`：原样重试是否可能成功。
- `error.outcome`：`not_executed` 表示确定没有执行；`unknown` 表示可能已产生副作用。
- `error.fields`：逐项指出出错的输入。`in` 取 `body` / `query` / `path` / `header` / `cookie`；`pointer` 指请求体内的位置，`parameter` 指参数名。
- 必有：`code`、`message`、`data`、`error`（含 `retryable`、`outcome`）、`requestId`；`fields` 的每一项必有 `in`、`code`、`message`。

### 三种列表

三种列表的数据都放 `items`；翻页信息各放各的位置，`page` 与 `cursor` 不同时出现。一个接口只选一种，由接口自己的文档声明。它们都是成功外壳的 `data`。

```
一次性列表   { items }
页码式       { items, page:   { totalRecord, pageSize, totalPage } }
游标式       { items, cursor: { next?, hasMore } }
```

- **一次性列表**：只用于条数有一个由定义决定、不随业务数据增长的上限的结果。上限由各接口在自己的契约里声明；超过上限应报错（`LIST_LIMIT_EXCEEDED`），不截断。
- **页码式**：`totalRecord` 整数 ≥ 0；`pageSize` 整数 1–100，回显请求值；`totalPage` 整数 ≥ 0，等于 `ceil(totalRecord / pageSize)`，总数为 0 时为 0。三项必有，`page` 里不接受其他字段（**不回传当前页码**）。
- **游标式**：`hasMore` 布尔，必有；`next` 字符串，对调用方不透明，没有更多时可省略。不带总数。取数方向（往更早还是往更新）由各接口声明，不进通用定义。
- 接口可以在 `items` 与 `page` / `cursor` 旁声明附带字段（如本页汇总），但不得重复表达翻页信息。

### 列表的请求参数

线上以点号命名的查询参数传递；定义约束的是「解码后的对象」，以后若增加请求体传法可以共用。

页码式（前缀 `page.`）：

| 参数 | 约束 |
|---|---|
| `page.page` | 整数 ≥ 1，缺省 1 |
| `page.pageSize` | 整数 1–100，缺省 10 |
| `page.query` | 模糊搜索词，最多 200 字符 |
| `page.orderBy` | 逗号分隔的「小驼峰字段名 [asc\|desc]」，缺省方向 asc，最多 200 字符 |

游标式（前缀 `cursor.`）：

| 参数 | 约束 |
|---|---|
| `cursor.after` | 上一批返回的 `next`；首批不带 |
| `cursor.limit` | 整数 1–100 |

`cursor.after`、`cursor.limit` 这两个名字是建议值：有更合适的命名先报用户再定，不自行改。

筛选：`filter.<字段>.<操作>`，字段为小驼峰，首版操作只有 `eq`（如 `filter.status.eq=active`）。某个接口可筛选哪些字段，由接口自己声明。

前缀下出现未声明的参数应视为不合法，不静默忽略。

### 字段路径常量

组件库这类使用方不只要类型，还要在运行时知道「去哪个路径取值、请求参数叫什么」。所以 npm 包除类型外，还要导出各列表结构的**字段路径常量**，由定义生成，不手写：

- 请求参数名与响应字段路径分开两组导出（当前页码只是请求参数，响应里没有；每页条数两边都有）。例如页码式：请求一组含 `page.page`、`page.pageSize`、`page.query`、`page.orderBy`；响应一组含 `items`、`page.totalRecord`、`page.pageSize`、`page.totalPage`。游标式、一次性列表同理，另有筛选参数的前缀。
- 常量的值必须是**字面量类型**（TS 里 `as const`），使用方才能拿它们做类型推导。
- 常量与类型出自同一份定义：定义里改了字段名，常量与类型一起变，一致性检查覆盖这两者。
- Python 包同样导出这组常量。

### 通用业务码

成功一组，只有 `OK`。失败一组如下，各带固定的 HTTP 状态、能否重试、是否已执行：

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

导出方式：

- 成功码与失败码**分两组常量**导出，不合在一个枚举里（成功外壳的 `code` 只能是 `OK`，错误体的 `code` 永远不是 `OK`）。
- 另导出「通用业务码 → HTTP 状态、能否重试、outcome」这张表。
- 不另出 HTTP 状态码的枚举。
- 包不提供任何定制开关。

### 专有业务码清单的格式

一个服务把自己的专有码写成一份清单：`{ service, codes: [...] }`，`service` 为小写标识，`codes` 不为空。每一项：

| 字段 | 约束 |
|---|---|
| `code` | 全大写或全小写的下划线写法，字母开头，不以下划线结尾，不含连续下划线；清单内不重复 |
| `stage` | `accept`（受理时同步返回）/ `execute`（异步执行阶段产生）/ `both` |
| `httpStatus` | `accept`、`both` 必有，取 4xx 或 5xx；`execute` 不得有 |
| `additionalHttpStatuses` | 可选；同一个码在不同情形下的其他状态，不为空、不重复、不含主状态；`execute` 不得有 |
| `retryable` | 布尔 |
| `outcome` | `not_executed` / `unknown` |
| `meaning` | 一句话含义，必有 |

不得重新定义通用码；`OK` 与 `HTTP_<数字>` 形式的码保留，不得使用；不接受未声明的字段。

## 怎么算完成

- 样例校验命令通过：合法样例全过，不合法样例全被拒，且拒绝原因是预期的那一条。上面每条约束至少有一个不合法样例对应。
- 生成的 TS 类型通过类型检查；写一个最小用例，用错字段名、把页码式当游标式读时类型检查报错。
- 手改一个生成文件后跑一致性检查，退出码非 0；重新生成后恢复为 0。
- npm 包能在本机构建；构建产物不含 Node 专用依赖。

## 自己定与不能动

- 自己定：目录内部结构、定义文件怎么拆、用哪个校验库与生成工具、测试怎么写。生成工具先试 json-schema-to-typescript（MIT）；不合用时写下比较再换，写明许可证。
- 不能动：上面规格里的字段名、取值范围、结构的增减。发现规格自相矛盾、有遗漏或写不成定义，停下报用户，不自行取舍。
- 不发布、不 push。依赖只引入发布满 14 天的版本。
- 本仓公开：文档、提交说明与代码里不写不公开的项目名、内部路径或内部决策编号。

## 上报条件

- 规格有矛盾或遗漏；
- 生成工具表达不了某个结构（例如带点号的查询参数名）；
- 预计工作量明显超出一个会话。
