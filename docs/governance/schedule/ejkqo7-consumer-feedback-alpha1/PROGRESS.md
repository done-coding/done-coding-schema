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
| ⓓ | 页码式列表条数约束 | 进行中 | |
| ⓔ | 校验器报错位置指到具体字段 | 待做 | |
| ⓐ | Python 包带定义文件与取用函数 | 待做 | |
| ⓑ | 模型导出的 JSON Schema 为源定义 | 待做 | |
| ⓕⓗ | 有意为之的约束写进 README；跨语言一致性样例 | 待做 | |
| ⓕ′ | 通用码的 retryable / outcome 改为缺省值（更正） | 待做 | |
| ⓖ | 不加个人信息过滤等规则 | 完成 | 不改动 |
| 发布 | 第二个预发布版：检查、构建、上传、线上核对 | 待做 | |
| 收口 | 快照、归档。收工 | 待做 | |

## 进度记录

- 2026-11-26 承接：上一批 `aat17s` 已归档（f303361）。
- 2026-11-26 ⓕ 核对：这几条都已写在定义里，不需要补。页码式 `cursor: false`、一次性列表 `page: false` 与 `cursor: false`；错误体 code `not: {const: "OK"}`；通用码锁在 `common-error-codes.schema.json` 的 allOf if/then 里，错误体经 allOf 引用；字段错误 message `maxLength: 1000`；字段指针 pattern 以 `^…$` 锚定，按 ECMA-262 语义 `$` 只匹配文本末尾。现有样例已覆盖这些情形的反例，本批补「字段错误 message 恰 1000 字符」这一条正例。
- 2026-11-26 更正（下发方补发）：撤销 ⓕ 里「通用码的 retryable、outcome 必须与码表一致」，改为码表只给缺省值，错误体里可以覆盖；通用码的 HTTP 状态不动；跨语言样例加 SERVICE_UNAVAILABLE 配 outcome 为 not_executed、配 retryable 为 false 两例，均合法。这条推翻了维护者在 1kx2ep 答复 2 里定的锁定，所以先在本会话向维护者确认：维护者选「按更正改为缺省值」。同时确认授权发第二个预发布版（只发预发布，推送仍由维护者做）。
- 2026-11-26 ⓒ 整数：`_base.py` 新增 `JsonInt = Annotated[int, BeforeValidator(值为整数的浮点 → int), Strict()]`。生成工具只能产出 `StrictInt`，所以 `gen-python.mjs` 在生成后把它换成 `JsonInt`，并改写导入行；找不到导入行时直接报错。涉及 `PagedListPage` 的三个字段、`PagedListRequest.page/pageSize`、`CursorListRequest.limit`、`ServiceErrorCode.httpStatus` 和 `AdditionalHttpStatus`（RootModel 不继承基类配置，所以靠 `Strict()` 保持严格）。12.5、"12"、布尔、inf、nan 仍然拒绝。样例新增 4 个合法例（各整数字段写成 21.0 / 2.0 / 20.0 / 409.0 这类值）和 4 个布尔反例；测试另验归一后类型是 int，输出也是整数。TS 侧不用改：JSON 解析后 12.0 就是 12，ajv 判为 integer。
