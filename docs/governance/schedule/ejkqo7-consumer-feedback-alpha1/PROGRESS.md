---
id: ejkqo7
title: 接入反馈修正与第二个预发布版
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-26
source: 甲方当轮下发（首个后端使用方的接入反馈）
after: ""
---

# 接入反馈修正与第二个预发布版

单批次，串首即串末。条目 `7tf5h6`。

共享骨架独占：仓根 `package.json`、`pnpm-lock.yaml`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓒ | 整数字段接受值为整数的浮点 | 完成 | 见进度记录 |
| ⓓ | 页码式列表条数约束 | 完成 | 见进度记录 |
| ⓔ | 校验器报错位置指到具体字段 | 完成 | 见进度记录 |
| ⓐ | Python 包带定义文件与取用函数 | 完成 | 见进度记录（README 随 ⓕⓗ 一并写） |
| ⓑ | 模型导出的 JSON Schema 为源定义 | 完成 | 见进度记录 |
| ⓕⓗ | 有意为之的约束写进 README；跨语言一致性样例 | 待做 | |
| ⓕ′ | 通用码的 retryable / outcome 改为缺省值（更正） | 完成 | 见进度记录 |
| ⓖ | 不加个人信息过滤等规则 | 完成 | 不改动 |
| 发布 | 第二个预发布版：检查、构建、上传、线上核对 | 待做 | |
| 收口 | 快照、归档。收工 | 待做 | |

## 进度记录

- 2026-11-26 承接：上一批 `aat17s` 已归档（f303361）。
- 2026-11-26 ⓕ 核对：这几条都已写在定义里，不需要补。页码式 `cursor: false`、一次性列表 `page: false` 与 `cursor: false`；错误体 code `not: {const: "OK"}`；通用码锁在 `common-error-codes.schema.json` 的 allOf if/then 里，错误体经 allOf 引用；字段错误 message `maxLength: 1000`；字段指针 pattern 以 `^…$` 锚定，按 ECMA-262 语义 `$` 只匹配文本末尾。现有样例已覆盖这些情形的反例，本批补「字段错误 message 恰 1000 字符」这一条正例。
- 2026-11-26 更正（下发方补发）：撤销 ⓕ 里「通用码的 retryable、outcome 必须与码表一致」，改为码表只给缺省值，错误体里可以覆盖；通用码的 HTTP 状态不动；跨语言样例加 SERVICE_UNAVAILABLE 配 outcome 为 not_executed、配 retryable 为 false 两例，均合法。这条推翻了维护者在 1kx2ep 答复 2 里定的锁定，所以先在本会话向维护者确认：维护者选「按更正改为缺省值」。同时确认授权发第二个预发布版（只发预发布，推送仍由维护者做）。
- 2026-11-26 ⓒ 整数：`_base.py` 新增 `JsonInt = Annotated[int, BeforeValidator(值为整数的浮点 → int), Strict()]`。生成工具只能产出 `StrictInt`，所以 `gen-python.mjs` 在生成后把它换成 `JsonInt`，并改写导入行；找不到导入行时直接报错。涉及 `PagedListPage` 的三个字段、`PagedListRequest.page/pageSize`、`CursorListRequest.limit`、`ServiceErrorCode.httpStatus` 和 `AdditionalHttpStatus`（RootModel 不继承基类配置，所以靠 `Strict()` 保持严格）。12.5、"12"、布尔、inf、nan 仍然拒绝。样例新增 4 个合法例（各整数字段写成 21.0 / 2.0 / 20.0 / 409.0 这类值）和 4 个布尔反例；测试另验归一后类型是 int，输出也是整数。TS 侧不用改：JSON 解析后 12.0 就是 12，ajv 判为 integer。
- 2026-11-26 ⓕ′ 码表改为缺省值：
  - 定义：`common-error-codes.schema.json` 各 if/then 里的 `retryable`、`outcome` 从 `const` 改为 `default`（只作标注，不再校验）。表的结构不变，`x-httpStatus` 不动，错误体照旧经 allOf 引用码表。两份定义的说明文字改为「缺省值，可以覆盖」。
  - 生成器从 `default` 读表；`COMMON_ERROR_CODE_TABLE` 照常导出，注释改称缺省值。
  - Python：去掉 `ErrorBody` 里按码表核对的校验，新增 `default_error_detail(code)`，按码取缺省的 `ErrorDetail`，不是通用码时返回 None。
  - 样例：原来 23 个「与码表不符」的反例改为合法例，名字改成「覆盖码表缺省值」。其中 SERVICE_UNAVAILABLE 两例就是下发方要的「outcome 覆盖为 not_executed」和「retryable 覆盖为 false」。`GENERATED_GAPS` 去掉对应的 23 条。
  - 码表已没有约束，写不出反例，`check-examples.mjs` 改为只对含约束的定义要求有不合法样例。约束总数从 179 条降到 157 条，全部有反例覆盖。
  - README 业务码一节改为缺省值的说法，并写了覆盖的例子与 `default_error_detail`。
- 2026-11-26 ⓔ 报错位置：
  - `_base.ConstraintErrors` 收集出错项，用 `ValidationError.from_exception_data` 一次抛出，每项带 loc。外层模型会在前面补上自己的路径，pydantic 2.14 下实测成立，2.11 在发布前构建时验证。
  - 各手写校验改为逐项报告，不再碰到第一处就停。位置如下：
    - totalPage 报 `("page","totalPage")`。
    - 不得出现的 page / cursor 指到该字段本身。
    - hasMore 时缺 next 报 `("cursor","next")`。
    - 错误体 code 为 OK 报 `("code",)`。
    - fields 项的 pointer / parameter 指到 `("error","fields",i,"pointer"|"parameter")`。
    - 空筛选条件指到 `(字段名,)`。
    - 专有码清单的各项指到 `("codes",i,"code"|"httpStatus"|"additionalHttpStatuses")`。
    - 可选字段显式 null 指到该字段。
  - 错误类型（自定）：`field_forbidden`、`field_required`、`null_forbidden`、`total_page_mismatch`、`code_reserved`、`duplicate_value`、`array_contains_property`、`condition_empty`。
  - 新增 `tests/test_error_locations.py`，12 组用例逐项核对位置集合。
- 2026-11-26 ⓓ 条数约束：
  - 写法沿用同类的跨字段约束 `x-totalPageEqualsCeil`：在 `paged-list.schema.json` 顶层加补充检查关键字 `x-itemsWithinPage: true`，定义说明里写明这条约束。只加约束，不改字段，也不增减结构。理由：标准 JSON Schema 表达不了；写进定义，才能让仓内的定义校验（Ajv + x- 关键字）与 Python 对同一份数据给出相同结论（ⓗ）。普通校验器会忽略它，TS 侧在 README 说明。
  - `validator.mjs` 实现：条数超过 pageSize、超过 totalRecord 各报一项，位置 `/items`；上限本身不合法时不报，交给标准关键字。Python 在 `PagedList._page_consistency` 实现，位置 `("items",)`。
  - 样例：2 个合法例（条数恰等于 pageSize、恰等于 totalRecord），4 个反例（超 pageSize、超 totalRecord、总数为 0 却有数据、两者都超）。约束共 158 条，全部有反例覆盖。
- 2026-11-26 ⓐ 定义文件进 Python 包：
  - `pnpm gen` 把仓根 10 份定义原样写进 `python/src/done_coding_schema_api/schemas/`，与 npm 包 `schemas/` 是同一批文件，由 `check:generated` 核对。共 34 个生成物。
  - 新增 `_definitions.py`，从包根导出三个函数：`schema_names()`（全部名字）、`schema_path(name)`（返回 Path，名字不存在时 KeyError 并列出可用名字）、`load_schema(name)`（每次返回新的字典）。名字是文件名去掉 `.schema.json`，如 `"error-body"`。
  - `check:wheel` 改为 `scripts/check-python-dist.py`（只用标准库）：构建到临时目录，核对 wheel 与 sdist 各含全部定义文件、与仓根逐字节一致、不多不少，并带 LICENSE。手放一个多余的定义文件时退出码 1（实测）。
  - lint-staged：生成物核对覆盖 `python/src/*/schemas`；ruff 覆盖 `scripts/*.py`。
- 2026-11-26 ⓑ 导出即源定义：
  - `_base.source_json_schema` 作为 pydantic 的 `__get_pydantic_json_schema__` 钩子，接在 `SchemaModel`（全部生成模型与包装模型）和 `ListFilter`（RootModel）上。它沿继承链找到生成的类，按类名（即定义的 title）定位源定义。
  - `_definitions.bundled_schema` 把源定义里的引用展开：文件内引用与跨文件引用（错误体引用的码表、专有码引用的通用码列表）都展开，并去掉 `$schema`、`$id`、`$defs`。这样嵌进 OpenAPI 后，引用基准不会错。约束与 x- 关键字原样保留。
  - 泛型给了类型参数时，`__schema_type_params__` 列出的字段换成类型参数生成的结构：列表换 `items.items`，外壳换 `data`（保留 description）。子类另外声明的字段按 pydantic 默认结果补进 properties。
  - 测试 `tests/test_json_schema.py`（37 例）覆盖以下几方面：
    - 15 个对外模型在 validation、serialization 两种模式下，导出结果都与源定义逐项相同（测试里另写了展开 $ref 的比较，不复用实现里按标题查找的逻辑）。
    - x- 约束确实导出。
    - 三种列表与外壳的泛型只替换参数处，其余与源定义相同。
    - 子类补字段。
    - FastAPI 生成的 OpenAPI 里，没有任何可选字段允许 null；ErrorBody、ServiceErrorCodes 组件与 `model_json_schema()` 相同；`PagedList[User]` 的元素引用 `#/components/schemas/User`。
  - 已知限度：FastAPI 文档里会多出一个未被引用的 `PagedListPage` 组件。它来自泛型取默认结构时 pydantic 登记的嵌套模型，内容也是源定义，不影响引用。
  - 新增开发依赖 FastAPI 0.162.5（2026-11-11 发布，MIT）。传递依赖：Starlette 1.10.0（BSD-3-Clause）、anyio（MIT）、idna（BSD-3-Clause）、opentelemetry-api（Apache-2.0）、annotated-doc（MIT）。只用于测试，不进运行时依赖。
