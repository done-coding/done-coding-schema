---
id: 1kx2ep
title: 首版结构的定义、样例、TS 生成链与 npm 包骨架
modules: [definition, toolchain, npm-package]
created: 2026-11-24
source: 用户 2026-11-24 立项（立项说明 docs/PROJECT.md）
after: ""
---

# 首版结构的定义、样例、TS 生成链与 npm 包骨架

批次串：`1kx2ep → k0l36c → p1rbxy`。本批是串首。

目的：通用接口结构只有一份定义，各语言代码由它生成。

共享骨架独占：仓根 `package.json`、`pnpm-workspace.yaml`、`pnpm-lock.yaml`（本串独占，串内不并行）。

开工前先读：`docs/PROJECT.md`、条目 `08byqy`、仓根 `AGENTS.md`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 按条目 `08byqy` 的规格写首版结构的定义，每个结构配合法、不合法两组样例；样例校验结果与预期一致 | 完成 | `pnpm check:examples` 退出码 0：72 合法 / 220 不合法，179 条约束全覆盖 |
| ⓑ | 用成员包模板 `npm-common-member` 建 npm 包（答案见「已定事项」）；由定义生成 TS 类型与常量并入仓，包同时导出定义文件；能在浏览器端引入 | 完成 | `pnpm gen`；`pnpm -F @done-coding/schema-api typecheck` 与 vitest 通过；`pnpm check:bundle` 退出码 0 |
| ⓒ | 一致性检查：手改生成物或改了定义未重新生成时失败；接进仓的检查命令 | 完成 | `pnpm check` 退出码 0；三种失配实测均失败、重新生成后恢复 |
| ⓓ | 刷新领域状态与快照，归档本批 | 未开始 | |
| ⓔ | 本批交付归档后立刻、必须、立即开始下一批 `k0l36c` | 未开始 | |

## 已定事项（用户 2026-11-24）

| 项 | 值 |
|---|---|
| npm 包名 | `@done-coding/schema-api`（成员包模板的答案：组织 `done-coding`、系列 `schema`、包名 `api`） |
| PyPI 包名 | `done-coding-schema-api`；导入名 `done_coding_schema_api` |
| 远程仓库 | `git@github.com:done-coding/done-coding-schema.git`，已登记为 `origin`；成员包模板里的远程仓库地址填它 |
| 发布源 | npm 公共源、PyPI 公共源 |
| 成员包描述 | 跨前后端通用接口结构的类型、常量与定义文件 |
| 仓根 `AGENTS.md` | 标题、定位与项目规则 6–9 已按本仓写好，照此执行 |
| 建仓工具的本机记录 | `.done-coding/template.lock.json` 不入库（已在 `.gitignore`） |

2026-11-24 查过：这两个包名在 npm 公共源与 PyPI 上都还没有被占用。

## 用户答复（2026-11-25）

开工前就规格写不成定义与未写明的细节问过一次，答复如下；规格补充已原样追加进条目 `08byqy`。

1. 跨字段约束（totalPage = ceil、专有码清单内 code 不重复、additionalHttpStatuses 不含主状态）：定义只用标准 JSON Schema，这三条用 `x-` 关键字声明，由样例校验命令另行检查；Python 侧在薄包装里补同样的检查。
2. 错误体 code：拒绝 `OK`；code 是通用码时 `error.retryable`、`error.outcome` 必须与码表一致。
3. 细节默认：`cursor.limit` 无缺省、不必填；`filter.*.eq` 的值只允许标量；`hasMore` 为 true 时必须给 `next`；保留码与通用码按字节比较、区分大小写；请求只校验 `page.` / `cursor.` / `filter.` 前缀之下；小驼峰约定不校验业务数据与附带字段的键名。错误体 fields 与专有码清单的细节以规格补充为准。
4. 之后规格没写到的长度、字符格式、可否为空：参照同类字段自己定，记入下面「自定细节」；只有改字段名、增减结构或字段、两条已写明的规格互相矛盾时才停下来问。

## 自定细节

| 字段 / 范围 | 定成什么 | 依据 |
|---|---|---|
| 全部 `pattern` | 按 JSON Schema 规定的 ECMA-262 语义解释（`$` 只匹配文本末尾）；字符类不含换行，所以带格式的字符串末尾换行一律不合法 | 规格补充「带格式的字符串不接受末尾换行」 |
| 错误体 `error.fields[].pointer` | RFC 6901 语法，且最后一个字符不能是换行（引用片段中间的换行按 RFC 允许） | 同上 |
| 错误体 `error.fields[].message` | 最长 1000 | 同类：错误体 `message` 最长 1000 |
| `page.query` | 可以为空串 | 同类：成功外壳 `message` 可为空串；搜索词为空等于不搜 |
| `page.orderBy` | 至少一段，不能为空串 | 带格式字段，格式本身要求「每段是字段名」 |
| 小驼峰 | `[a-z][a-zA-Z0-9]*`；用于 `orderBy` 与筛选的字段名 | 通用约定「字段名一律小驼峰」 |
| 筛选的字段名 | 不另设长度上限 | 同类：`orderBy` 里的字段名也不单独设上限 |
| 筛选条件对象 | 至少一个操作 | 线上形式 `filter.<字段>.<操作>` 解码后不会出现没有操作的字段 |
| `filter.*.eq` 的值 | 字符串、数字、布尔，不限长度 | 已确认只允许标量；同类：`detail` 不限长 |
| `page.page` / `page.pageSize` 缺省值 | 用 `default` 标注 1 / 10 | 原规格表 |
| 三种列表的 `items` | 元素类型不限；元素类型由 TS 泛型包装给出 | 规格未限定元素 |
| 一次性列表带 `page` 或 `cursor`、页码式带 `cursor`、游标式带 `page` | 不合法 | 「page 与 cursor 不同时出现」「不得重复表达翻页信息」 |
| `totalRecord` 为 0 时 `totalPage` 为 0 | 用标准 if/then 写，ceil 那条用 `x-totalPageEqualsCeil`；两者同时不满足时两条都报 | 标准写法能写的都写进去，其他校验器也能拦住这一半 |
| 专有码 `additionalHttpStatuses` | `stage` 为 execute 时不得有 | 原规格表；规格补充没提这条，二者不矛盾，沿用 |
| 规格补充里专有码 `code` 那行有缺字（「不含␣␣字节精确比较」） | 按原规格「不含连续下划线」，加上已确认的「与 OK、HTTP_<数字>、通用码按字节比较，不做大小写归一」理解 | 原规格与答复 3 |
| 定义文件互相引用 | 每个文件的 `$id` 等于文件名，跨文件 `$ref` 写文件名 | 不绑定任何外部域名；拿到包里的定义文件即可用 |

## 补充检查关键字

标准 JSON Schema 写不出的三条约束，用下面的 `x-` 关键字写在定义里；其他校验器会把它们当作注释忽略，本仓的样例校验命令（`scripts/lib/validator.mjs`）实现了它们。

| 关键字 | 位置 | 含义 |
|---|---|---|
| `x-totalPageEqualsCeil: true` | 页码式的 `page` 对象 | `totalPage` 等于 `ceil(totalRecord / pageSize)` |
| `x-uniqueItemsBy: "code"` | 专有码清单的 `codes` 数组 | 各项的 `code` 不重复 |
| `x-arrayExcludesProperty: {array, property}` | 专有码清单的每一项 | `additionalHttpStatuses` 不含 `httpStatus` 的值 |

另有只供生成器读取的标注：`x-httpStatus`（通用码的 HTTP 状态）、`x-paramPrefix`（请求参数的线上前缀）、`x-pathConstants`（生成的字段路径常量名）。

## 进度记录

- 2026-11-25 ⓑ（先行部分）：用 `npm-common-member` 模板在 `packages/api` 建出 `@done-coding/schema-api` 骨架（模板 commit 8edf826）；根引入 ajv 8.20.0、json-schema-to-typescript 16.0.0（均为 MIT）；`pnpm-workspace.yaml` 加 `minimumReleaseAge`，只装发布满 14 天的版本。提交 cbf64a6。
- 2026-11-25 ⓐ 完成：`schemas/` 下 10 份定义（成功外壳、错误体、通用失败码表、三种列表、两种列表请求参数、筛选参数、专有码清单），样例在 `schemas/examples/`。`pnpm check:examples`：合法样例 72 个全过，不合法样例 220 个全被拒且原因与预期逐条一致；定义里 179 条约束全部至少有一个不合法样例触发（脚本自动统计，有一条没覆盖就失败）。故意改坏一条预期原因、改宽一条定义各试一次，检查都失败（退出码 1）。提交 2130029。
- 2026-11-25 ⓑ 完成：`pnpm gen`（`scripts/generate.mjs`）由定义生成 `packages/api/src/generated/` 下的类型（json-schema-to-typescript）、常量（业务码、通用失败码表、请求参数名与响应字段路径，均 `as const`）与定义模块，并把定义文件逐字节照抄到 `packages/api/schemas/`（包导出 `./schemas/*`）。成功外壳与三种列表的泛型版本手写在 `src/generics.ts`（只换 `data` / `items` 的类型，其余字段经 `Omit` 取自生成类型）。证据：`pnpm typecheck` 退出码 0（包装层与生成类型逐一相等；写错字段名、把页码式当游标式或一次性列表读、成功码写错、响应路径里取当前页码，共 9 处都确实报错）；vitest 4 项通过；`pnpm check:bundle` 构建后扫描 es / lib，无 Node 内置模块与未声明依赖；另用 esbuild 以 `--platform=browser` 打包入口并运行成功；用构建出的 `types/index.d.ts` 写使用方代码做类型检查（`skipLibCheck: false`）通过。提交 9a7a90f。
- ⓑ 的取舍：json-schema-to-typescript 生成时去掉只用于校验的关键字（if / then / else / not / allOf / propertyNames 与 x- 标注），它们不改变字段形状；未声明 `additionalProperties` 的对象不生成索引签名，免得写错字段名也不报错。字段路径常量没有现成的生成工具，由生成脚本读定义直接产出（本仓独有的粘合逻辑）。npm 包 `exports` 里 `types` 条件移到最前，否则按条件顺序匹配的解析方式找不到类型声明。
- 2026-11-25 ⓒ 完成：`pnpm check:generated`（`generate.mjs --check`）在内存里重新生成并与仓里的生成物逐字节比对，多出的旧文件也算不一致。仓根 `pnpm check` 依次跑样例校验、一致性检查、类型检查（含包装层与生成类型的相等断言）、vitest、构建与产物检查；提交时 lint-staged 对 `schemas/` 与生成目录的改动也跑样例校验与一致性检查。实测：ⓐ 手改 `types.ts` 一个字段名 → 退出码 1，`pnpm gen` 后 0；ⓑ 只改定义的一句描述不重新生成 → 退出码 1，列出 3 个不一致的生成物；ⓒ 生成类型里页码式的 `items` 改名而包装没跟上 → `pnpm typecheck` 报 `generics.type-test.ts(27,10)`、退出码 2。三处改动都已还原；`pnpm check` 全程退出码 0。
