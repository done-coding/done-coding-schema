# 现状快照

> 文档定位：快照 · 覆盖更新，只写当前事实。领域划分见 `MODULES.md`，目标与边界见 `../PROJECT.md`；过程记录在 `archive/`，不作现状引用。

## 领域一行摘要

| 领域 | 现状 |
|---|---|
| `definition` | `schemas/` 下 10 份 JSON Schema 2020-12 定义（成功外壳、错误体、通用失败码表、一次性 / 页码式 / 游标式列表、页码式与游标式请求参数、筛选参数、专有码清单），每份配 `schemas/examples/<结构名>.json` 合法与不合法样例。 |
| `toolchain` | `scripts/`：`pnpm check:examples` 样例校验与约束覆盖统计；`pnpm gen` 生成 TS 类型、常量与定义模块；`pnpm check:generated` 生成物一致性；`pnpm check:bundle` 构建产物无 Node 依赖；`pnpm check` 汇总。 |
| `npm-package` | `packages/api` = `@done-coding/schema-api`（未发布）：导出生成的类型、业务码与字段路径常量（`as const`）、定义模块与 `./schemas/*` 定义文件；`src/generics.ts` 为成功外壳与三种列表的薄泛型包装。 |
| `pypi-package` | 未实现。 |

## 跨领域契约

- **定义是唯一来源**：类型、常量与包内定义文件都由 `schemas/` 生成，生成物不手改（仓根 `AGENTS.md` 规则 7）；`pnpm check:generated` 与提交钩子拦截不一致。
- **定义的引用方式**：每份定义的 `$id` 等于文件名，跨文件 `$ref` 写文件名；错误体经 `common-error-codes.schema.json` 锁定通用码的重试与执行语义。
- **补充检查关键字**：标准 JSON Schema 写不出的跨字段约束写成 `x-totalPageEqualsCeil`、`x-uniqueItemsBy`、`x-arrayExcludesProperty`，语义与实现在 `scripts/lib/validator.mjs`；其他校验器会忽略它们，各语言包须另行实现同样的检查。
- **生成器读取的标注**：`x-httpStatus`（通用码的 HTTP 状态）、`x-paramPrefix`（请求参数的线上前缀）、`x-pathConstants`（字段路径常量名）。
- **泛型包装**：只替换 `data` / `items` 的类型，其余字段经 `Omit` 取自生成类型；`packages/api/test/generics.type-test.ts` 断言二者一致。

## 技术基线

- pnpm workspace，Node ≥ 18；`pnpm-workspace.yaml` 的 `minimumReleaseAge` 只装发布满 14 天的版本。
- 校验：Ajv 8（JSON Schema 2020-12，strict，关闭 `strictRequired` / `strictTypes`）；类型生成：json-schema-to-typescript；npm 包构建：Vite 库模式（es / cjs / 合并后的 d.ts）。
- 正则一律按 ECMA-262 语义（`$` 只匹配文本末尾）；带格式的字符串不接受末尾换行。
