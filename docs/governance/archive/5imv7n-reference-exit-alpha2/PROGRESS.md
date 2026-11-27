---
id: 5imv7n
title: 结构与参考资源分层出口、隐式默认清理与第三个预发布版
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-27
source: 甲方当轮下发
after: ""
---

# 结构与参考资源分层出口、隐式默认清理与第三个预发布版

单批次，串首即串末。条目 `fa959d`。

共享骨架独占：仓根 `package.json`、`pnpm-lock.yaml`。

授权：维护者在本会话确认「按派单全部改」（规则 8 的契约改动）与「授权发第三个预发布版」（npm `0.0.1-alpha.2` 标签 alpha、PyPI `0.0.1a2`）；推送由维护者本人做。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| 三 | 七处隐式默认清理（定义为源，两种语言同改） | 完成 | d13195e |
| 二 | 两层出口：结构（主入口）与参考资源（`./reference`、`.reference`） | 完成 | d13195e |
| 四ⓗ | 导出的 JSON Schema 反映使用方子类 | 完成 | 4f3663f |
| 四ⓘ | 校验器去掉写死的 pageSize 上限 | 完成 | d13195e |
| 五 | 样例与 README | 完成 | d13195e（样例）、94c7143（README） |
| 发布 | 第三个预发布版：检查、构建、上传、线上核对 | 完成 | 7bfe568，见进度记录 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `ejkqo7` 已归档（0ce0c36），工作树干净。
- 2026-11-27 定义清理（ⓐ–ⓖ）：
  - 页码式请求去掉 page 的 `default: 1`、pageSize 的 `default: 10` 与 `maximum: 100`；页码式响应 `page.pageSize`、游标 `limit` 去掉 `maximum: 100`，`minimum: 1` 都保留。说明文字改为「不带时的含义（与上限）由接口自己声明」。
  - 专有码清单去掉 `not $ref common-error-codes#/$defs/code`，Python `_check_service_code` 去掉通用码比较；OK 与 `HTTP_<数字>` 保留。
  - 码表 retryable / outcome 的 `default` 换成 `x-referenceValue`；码表与错误体的说明改成「参考值，包不替使用方填写，使用方可显式引用」。
- 2026-11-27 自定的细节（同类写法，未改字段名、未增减结构）：
  - 错误体去掉 `allOf: [{$ref: common-error-codes}]`。这条引用在上一批改为缺省值后已不校验任何东西，留着会让结构定义带上码表的具体值，主入口的结构定义集合也离不开码表文件。去掉后接受与拒绝的实例完全不变。
  - 参考资源靠定义里的顶层标注 `x-referenceResource: true` 区分，生成器与 Python 取用函数都读它。
  - 移出的 1、10、100 放进新的参考资源定义 `list-reference-values.schema.json`（`x-referenceValues`，不约束任何结构），生成常量 `PAGED_LIST_REFERENCE_VALUES = {page: 1, pageSize: 10, maxPageSize: 100}` 与 `CURSOR_LIST_REFERENCE_VALUES = {maxLimit: 100}`。值来自定义，守规则 7。
  - 新增标注关键字 `x-referenceResource`、`x-referenceValue`、`x-referenceValues`，在校验器里登记为标注。
  - 样例检查改为：不含任何约束的定义（两份参考资源）不强制要求样例；写了照常校验。
- 2026-11-27 两层出口：
  - npm：主入口 `src/index.ts` 只导出类型、`SUCCESS_CODES` / `SuccessCode`、结构定义（各 `xxxSchema` 与 `schemas`）。新出口 `src/reference.ts` 对应 `"./reference"`（types / import / require 齐全，vite 双入口），导出通用码、码表、六组路径与参数名常量、两组参考数值、`commonErrorCodesSchema`、`listReferenceValuesSchema`、`referenceSchemas`、`findReservedCodes`。
  - Python：顶层只有结构；`done_coding_schema_api.reference` 导出同一批常量、`reference_error_detail`（原 `default_error_detail`，不留别名）、`find_reserved_codes`、`reference_schema_names` / `reference_schema_path` / `load_reference_schema`。顶层的 `schema_names` / `schema_path` / `load_schema` 只认结构定义，拿参考资源名会报 KeyError 并指明去哪取。
  - ⓕ 的显式入口：TS `findReservedCodes(list, reserved)` 返回 `{index, code}[]`；Python `find_reserved_codes(codes, reserved)` 返回 `ReservedCodeHit(index, code)` 列表。按字节比较，传空集合即不比。
  - 检查：TS `test/exports.test.ts` 核对两个出口的运行时导出名不重叠、参考资源名都不在主入口；`test/generics.type-test.ts` 用 `@ts-expect-error` 核对类型层面也取不到。Python `tests/test_exports.py` 核对 `__all__` 与属性。
- 2026-11-27 ⓗ：`_base.source_json_schema` 改为：
  - 子类重新声明的已有字段（FieldInfo 与生成类的不同）在源定义该字段上叠加 pydantic 为新声明生成的关键字（去掉 title），是否必填按新声明；
  - 泛型类型参数沿整条继承链找，`class UserPage(PagedList[User])` 的 items 也带元素类型。
  - 测试断言具体字段：`pageSize` 导出为源定义加 `default: 20`、`maximum: 50`；`ErrorBody.code` 收窄后带 enum，pattern 与 `not OK` 仍在；必填字段加了默认值后不再必填；FastAPI 的 `UserPage` 组件 items 引用 User，`OrderFailure` 组件 code 带 enum。
  - 发现两点，写进 README，回报下发方：① Pydantic 里子类重新声明字段会整体替换原字段的校验，例如 `Field(default=20, le=50)` 之后 `pageSize=0` 也被接受；导出的结构仍带源定义的 `minimum: 1`。README 的示例因此写成 `Field(default=20, ge=1, le=50)`。② FastAPI 把查询参数模型逐字段展开时，用的是字段自身的声明，不经模型导出：子类写的默认值和上限看得到，源定义的下限看不到，可选字段仍写成可为 null。这是上一批起就有的情况，本批没有改。
- 2026-11-27 样例：
  - 改为合法 4 例（原依赖上限 100 或通用码的反例）：请求 `pageSize 500`、游标 `limit 500`、响应 `pageSize 500`、专有码清单出现 `NOT_FOUND`。
  - 新增不合法 2 例：请求与响应的 `pageSize` 为 12.5。
  - 「请求不带 page、pageSize」原本就是合法例，只改了名字。
  - 合计：合法 106、不合法 209，约束 154 条全覆盖（上一版 102 / 211 / 158）。
- 2026-11-27 发布前检查：`pnpm check` 退出码 0。样例结果同上；生成物 39 个一致；TS 10 个测试；Python 710 个测试；构建产物无 Node 专用依赖；wheel 与 sdist 各含 11 份定义与 LICENSE。
- 2026-11-27 发布（按 `docs/release.md`「本机发布」）：
  - 定版本：npm 0.0.1-alpha.1 → 0.0.1-alpha.2，Python 0.0.1a1 → 0.0.1a2；版本提交 7bfe568，标签 `@done-coding/schema-api@0.0.1-alpha.2`。在版本提交上再跑 `pnpm check`，退出码 0。
  - 最低支持版本另验：Python 3.10.20 加 pydantic 2.11.10，装本机构建的 wheel（确认导入的是装好的包）跑全部 710 个测试，全部通过。
  - 仓外构建：npm 20 个文件（新增 `es/reference.mjs`、`lib/reference.cjs`、`types/reference.d.ts` 与参考数值定义）；wheel 与 sdist 各含 11 份定义与 LICENSE，wheel 含 `reference.py` 与 `_generated/reference_constants.py`。三个包解开后扫过，没有本机路径。
  - 上传：npm `+ @done-coding/schema-api@0.0.1-alpha.2`（tag alpha）；PyPI 的 wheel 与 sdist 上传成功。令牌只经环境变量传入，npmrc 里只有占位，用完删除。
- 2026-11-27 线上核对：
  - npm dist-tags：`alpha` = 0.0.1-alpha.2，`latest` 仍是 0.0.1-alpha.0；线上 shasum 与本机构建相同（9eb6f61d…）。
  - PyPI 0.0.1a2，license MIT，sha256 与本机构建相同（wheel 39ed51bb…，sdist 7bf732c3…）。
  - 空目录（npm）：`@done-coding/schema-api@alpha` 装到 0.0.1-alpha.2。README 的 6 段 TS 用 tsc 检查通过；另一个反例文件证明主入口取不到 `COMMON_ERROR_CODES`（`@ts-expect-error` 生效）。ESM 与 CJS 两种方式都取不到主入口的 `COMMON_ERROR_CODES`，`./reference` 两种方式都取得到。用主入口的结构定义加 Ajv 判：请求与响应 `pageSize` 500、`limit` 500、请求不带 page / pageSize、专有码 `NOT_FOUND` 都合法；`pageSize` 0 与 12.5 不合法；错误体 code 为 OK 仍不合法。`findReservedCodes` 传入通用码时指出撞码，不传就不比。
  - 空目录（pip）：Python 3.12 新环境，`--prerelease allow` 装到 0.0.1a2（pydantic 2.14.4），另装 fastapi 0.162.5。仓根 README 的 5 段 Python 与包 README 片段原样运行通过，其中专有码检查那段按预期抛出撞码。包顶层取不到 `COMMON_ERROR_CODES` 与 `default_error_detail`，`.reference` 取得到。`OrderPageRequest` 导出 `pageSize` 为源定义加 `default: 20`、`maximum: 50`；FastAPI 里 `class UserPage(PagedList[User])` 的 items 引用 User。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：
  - `definition` 一行：10 份定义 → 9 份结构加 2 份参考资源，并写明结构里没有具体配置值。
  - `toolchain` 一行：补上生成物按结构层与参考资源层各出一份。
  - `npm-package` 与 `pypi-package` 两行：版本更新到 alpha.2 / a2，导出内容改为两层出口；`default_error_detail` 改为 `reference.py` 里的 `reference_error_detail`。
  - 契约：「错误体经 allOf 引用码表、只给缺省值（default）」改为新增的「结构与参考资源分层」一条；引用方式一条改为目前只有文件内引用；标注里补上三个 `x-reference*`；「导出即定义」补上子类改动与已知限制；版本一条改为 alpha.2。
  - 移出的历史内容：无，旧事实直接替换。
- 收工。推送仍由维护者本人做：分支 `master`、`feat/schema-v0`，标签 `@done-coding/schema-api@0.0.1-alpha.0`、`0.0.1-alpha.1`、`0.0.1-alpha.2`。

## 交付清单

- d13195e：定义清理与两层出口（含样例、生成器、两种语言的包与测试）。
- 4f3663f：导出的 JSON Schema 反映使用方子类。
- 94c7143：README。
- 3ae4ff5：实现进度记录。
- 7bfe568：版本提交（0.0.1-alpha.2 / 0.0.1a2）。
- 归档提交：快照与本批归档。

## 结果

- 第三个预发布版已在 npm（alpha）与 PyPI 发布，空目录各装一次验证通过。
