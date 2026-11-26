---
id: 7tf5h6
title: 按首个后端使用方的接入反馈修正两个包
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-26
parent: ""
---

# 按首个后端使用方的接入反馈修正两个包

来源：首个后端使用方拿 0.0.1a0 与它原有定义逐条比对，结论是现在不能发正式版。各条以哪边为准已由维护者一方定好。原则：JSON 定义文件是唯一来源，两种语言的包对同一份数据给出相同的合法与否结论。

- ⓐ Python 包带上全部 JSON 定义文件（与 npm 包同一批），提供按名取路径与取已解析字典的函数，README 写明；构建检查加「包内定义文件齐全且与仓内逐字一致」。
- ⓑ 模型导出的 JSON Schema 就是对应的源定义（泛型参数处替换 items、data 的元素定义）；可选字段不再导成可为 null。测试：导出结果与源定义在约束上一致；FastAPI 以 response_model 生成的 OpenAPI 里可选字段不含 null。
- ⓒ 整数以 JSON Schema 为准：值为整数的浮点（如 12.0）放行并归一成 int；12.5、字符串、布尔仍拒绝。涉及所有整数字段。
- ⓓ 页码式列表：items 条数不超过 pageSize，也不超过 totalRecord（JSON Schema 表达不了；Python 校验器实现，README「定义文件表达不了的约束」一节列明，TS 侧只在文档说明）。
- ⓔ 手写校验器的报错位置指到具体字段（如 ("page","totalPage")；互斥约束指到多出来的字段）。
- ⓕ 保持不变并在 README 写明是有意为之：页码式顶层不带 cursor、一次性列表顶层不带 page 或 cursor；错误体 code 不为 OK；通用码 retryable / outcome 与码表一致；字段错误 message 上限 1000；字段指针整串匹配。核对这些在定义里已表达，能表达而未表达的补进定义，表达不了的列进上面那一节。
- ⓖ 不加个人信息过滤与「detail 必须等于 message」类规则。
- ⓗ 跨语言一致性样例：同一批边界数据（至少覆盖 ⓒⓓⓕ 正反例），TS 侧用定义加 ajv 判、Python 侧用模型判，逐例相同，进 `pnpm check`。

发布：`pnpm check` 全过后按 `docs/release.md`「本机发布」发下一个预发布版（版本号以脚本算出为准），先 npm 后 PyPI，线上核对、空目录各装一次。推送由维护者本人做。

边界：不发正式版本号；不改字段名、不增减结构；令牌不打印、不落文件。
