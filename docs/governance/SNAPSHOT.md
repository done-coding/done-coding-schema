# 现状快照

> 文档定位：快照 · 覆盖更新，只写当前事实。领域划分见 `MODULES.md`，目标与边界见 `../PROJECT.md`，使用说明见仓根 `README.md`，发布流程见 `../release.md`；过程记录在 `archive/`，不作现状引用。

## 领域一行摘要

| 领域 | 现状 |
|---|---|
| `definition` | `schemas/` 下 11 份 JSON Schema 2020-12 定义：9 份结构（成功外壳、错误体、一次性 / 页码式 / 游标式列表、页码式与游标式请求参数、筛选参数、专有码清单），各配 `schemas/examples/<结构名>.json` 合法与不合法样例；2 份参考资源（通用失败码表、列表的参考数值，带 `x-referenceResource`，不约束任何结构，不强制样例，码表另有合法样例）。结构里没有具体配置值：页码、每页条数、每批条数无默认值与上限，专有码只拦 `OK` 与 `HTTP_<数字>`。 |
| `toolchain` | `scripts/`：`pnpm check:examples` 样例校验与约束覆盖统计；`pnpm gen` 生成 npm 包的类型、常量与定义模块和 Python 包的模型、常量与定义文件，常量与定义模块按结构层 / 参考资源层各出一份（生成后把整数字段的 `StrictInt` 换成 `_base.JsonInt`）；`pnpm check:generated` 生成物一致性；`pnpm check:versions` 两包版本一致；`pnpm check:license` 两包的许可证副本与仓根 `LICENSE` 一致；`pnpm check:bundle` 构建产物无 Node 依赖；`pnpm check:python` Python 测试；`pnpm check:wheel`（`scripts/check-python-dist.py`）构建后核对 wheel 与 sdist 里的定义文件与仓根逐字节一致并带 LICENSE；`pnpm check` 汇总；`sync-python-version.mjs` 在发布定版本时把 npm 包版本同步给 Python 包。`.github/workflows/` 的正式版与预发布工作流同时构建、检查并上传两个包（尚未在 GitHub 上实际运行过，已有的预发布版是本机发布的）。 |
| `npm-package` | `packages/api` = `@done-coding/schema-api`（npm 上有预发布版 0.0.1-alpha.0 至 0.0.1-alpha.2；dist-tag `alpha` 指向 0.0.1-alpha.2，`latest` 仍指向首次发布的 0.0.1-alpha.0；另有注册表放的占位版本 0.0.0-stage）：主入口 `src/index.ts` 导出生成的类型、`SUCCESS_CODES` 与结构定义模块（`schemas`）；参考资源出口 `src/reference.ts`（`./reference`）导出通用失败码与码表、路径与参数名常量、参考数值、参考资源定义（`referenceSchemas`）与 `findReservedCodes`（`src/reserved-codes.ts`）；`./schemas/*` 为全部定义文件；`src/generics.ts` 为成功外壳与三种列表的薄泛型包装。 |
| `pypi-package` | `python/` = `done-coding-schema-api`（导入名 `done_coding_schema_api`，PyPI 上有预发布版 0.0.1a0 至 0.0.1a2，`pip install --pre` 装到 0.0.1a2）：`_generated/` 为生成的 Pydantic 模型与常量（`constants.py` 结构层、`reference_constants.py` 参考资源层）；`schemas/` 为随包分发的定义文件，结构定义经顶层 `schema_names()` / `schema_path()` / `load_schema()` 取用，参考资源定义经 `reference` 子模块的 `reference_schema_*` / `load_reference_schema()` 取用（`_definitions.py`）；`models.py` 为薄包装（成功外壳与三种列表的泛型、生成工具表达不了的约束）；`reference.py` 为参考资源出口（常量、`reference_error_detail()`、`find_reserved_codes()`）；`_base.py` 为生成模型的基类、`JsonInt`、报错收集与 JSON Schema 导出钩子。 |

## 跨领域契约

- **定义是唯一来源**：类型、常量与包内定义文件都由 `schemas/` 生成，生成物不手改（仓根 `AGENTS.md` 规则 7）；`pnpm check:generated` 与提交钩子拦截不一致。
- **结构与参考资源分层**：包内置的码与数值不成为隐式默认。结构定义不引用参考资源定义，结构里不出现具体配置值；参考资源（通用失败码表的 HTTP 状态 `x-httpStatus` 与 `retryable` / `outcome` 参考值 `x-referenceValue`、列表的参考数值 `x-referenceValues`）只从参考资源出口导出，包不替使用方填写，要用须显式引入。主入口不导出任何参考资源，两种语言各有测试核对（`packages/api/test/exports.test.ts` 与 `generics.type-test.ts`、`python/tests/test_exports.py`）。
- **定义的引用方式**：每份定义的 `$id` 等于文件名，跨文件 `$ref` 写文件名；目前只有文件内引用。
- **补充检查关键字**：标准 JSON Schema 写不出的跨字段约束写成 `x-totalPageEqualsCeil`、`x-itemsWithinPage`、`x-uniqueItemsBy`、`x-arrayExcludesProperty`，语义与实现在 `scripts/lib/validator.mjs`；其他校验器会忽略它们，Python 包在 `models.py` 里实现同样的检查，报错位置指到具体字段（`_base.ConstraintErrors`）。README「定义文件表达不了的约束」一节列出它们。
- **生成器读取的标注**：`x-httpStatus`（通用码的 HTTP 状态）、`x-paramPrefix`（请求参数的线上前缀）、`x-pathConstants`（字段路径常量名）、`x-referenceResource`（整份定义是参考资源）、`x-referenceValue` / `x-referenceValues`（参考值）。
- **泛型包装**：只替换 `data` / `items` 的类型，不新增、不改名、不放宽字段。TS 侧其余字段经 `Omit` 取自生成类型，`packages/api/test/generics.type-test.ts` 断言二者一致；Python 侧继承生成模型，嵌套结构的约束在顶层模型上检查。
- **Python 与定义的一致性**：`python/tests/test_examples.py` 用 `schemas/examples/` 同一组样例，要求对外导出的模型与定义（Ajv + x- 关键字的判定）逐条一致，生成模型的差异须与 `GENERATED_GAPS` 登记的恰好相同。整数按 JSON Schema 判定（`12.0` 合法并归一成 int）。
- **导出即定义**：Python 模型的 `model_json_schema()`（及 FastAPI 以请求体或返回类型生成的 OpenAPI）是对应源定义展开引用后的结构加上子类的改动（`_base.source_json_schema`，按类名即定义 title 定位）：泛型类型参数（含继承参数化泛型的子类）替换 `items` 元素与 `data`；子类重新声明的字段在源定义该字段上叠加新声明的关键字；`python/tests/test_json_schema.py` 逐项核对。已知限制：Pydantic 里重新声明字段会替换原字段的校验（导出仍带源定义的约束）；FastAPI 的查询参数模型逐字段展开，不经模型导出。
- **版本**：npm 包与 Python 包同一版本号、同一版本提交与标签；npm 预发布 `X.Y.Z-(alpha|beta|rc).N` 对应 PEP 440 `X.Y.Z(a|b|rc)N`（`scripts/lib/versions.mjs`），`pnpm check:versions` 按此把关。当前最新预发布：npm 0.0.1-alpha.2 / PyPI 0.0.1a2（同一版本提交，标签 `@done-coding/schema-api@0.0.1-alpha.2`）；此前 0.0.1-alpha.0、0.0.1-alpha.1；无正式版。

## 技术基线

- pnpm workspace，Node ≥ 18；`pnpm-workspace.yaml` 的 `minimumReleaseAge` 只装发布满 14 天的版本。
- 校验：Ajv 8（JSON Schema 2020-12，strict，关闭 `strictRequired` / `strictTypes`）；类型生成：json-schema-to-typescript；npm 包构建：Vite 库模式（es / cjs / 合并后的 d.ts）。
- Python：uv 管理（`python/uv.lock`，`exclude-newer = "14 days"`），requires-python ≥ 3.10，运行时依赖 pydantic ≥ 2.11；模型生成：datamodel-code-generator（严格类型、Literal、自定义基类）；构建后端 uv_build；ruff 检查手写代码。生成模型的基类开严格类型（整数字段用 `JsonInt` 接受值为整数的浮点）、列表顶层保留附带字段、可选字段不接受显式 null。开发依赖另有 FastAPI（只用于 OpenAPI 测试）。
- 正则一律按 ECMA-262 语义（`$` 只匹配文本末尾）；带格式的字符串不接受末尾换行。
- 发布：lerna（独立版本模式，约定式提交）定版本，`lerna publish from-package` 上传 npm；`uv publish` 经 PyPI 可信发布上传 Python 包；上传前跑 `pnpm check` 并核对版本形态。凭据由维护者在 GitHub 与 PyPI 上配置。工作流未实际运行过；目前的预发布版按 `docs/release.md`「本机发布」由维护者授权在本机发出。
- 许可证：MIT，仓根 `LICENSE`，npm 包、wheel 与 sdist 都带全文。
