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
| 发布 | 第三个预发布版：检查、构建、上传、线上核对 | 待做 | |
| 收口 | 快照、归档。收工 | 待做 | |

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
