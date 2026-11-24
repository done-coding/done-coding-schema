---
id: k0l36c
title: PyPI 包：由同一份定义生成 Pydantic 模型
modules: [toolchain, pypi-package]
created: 2026-11-24
source: 用户 2026-11-24 立项（立项说明 docs/PROJECT.md）
after: 1kx2ep
---

# PyPI 包：由同一份定义生成 Pydantic 模型

批次串：`1kx2ep → k0l36c → p1rbxy`。本批接 `1kx2ep`。

目的：Python 这边从同一份定义拿模型，和 TS 那边保证是同一个东西。

共享骨架独占：沿用串首声明。

开工前先读：`docs/PROJECT.md`、条目 `7qc5mh`、上一批归档的 `PROGRESS.md`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 建 Python 包（`python/`，用 uv 管理）；没有现成的 Python 库模板，手写最小工程 | 完成 | `python/pyproject.toml` + `uv.lock`；`pnpm check:wheel` 出 wheel 与 sdist |
| ⓑ | 由定义生成 Pydantic 模型与常量并入仓，纳入上一批的一致性检查 | 完成 | `pnpm gen` 产出 24 个文件；手改生成的模型后 `pnpm check:generated` 退出码 1 |
| ⓒ | 用上一批的同一组样例验证：Python 模型的接受与拒绝结果与定义校验一致 | 完成 | `pnpm check:python`：603 项通过；生成模型的 46 条差异逐条登记 |
| ⓓ | 版本一致检查：npm 包与 Python 包版本号不一致时失败 | 完成 | `pnpm check:versions`；改成 0.0.1 时退出码 1 |
| ⓔ | 刷新领域状态与快照，归档本批 | 未开始 | |
| ⓕ | 本批交付归档后立刻、必须、立即开始下一批 `p1rbxy` | 未开始 | |

## 已定事项与取舍

| 项 | 定成什么 | 依据 |
|---|---|---|
| Python 版本 | `requires-python >= 3.10`；本机 3.12 开发 | Pydantic 2.14 要求 3.10 及以上；3.10 也实测过 |
| 运行时依赖 | `pydantic>=2.11,<3`、`typing-extensions>=4.12`（均 MIT） | 2.11 起有 `validate_by_name` / `serialize_by_alias`；下限 2.11.10 实测过 |
| 开发依赖 | datamodel-code-generator 0.92.0、pytest 9.2.0、ruff 0.16.9（均 MIT）；构建后端 uv_build 0.13（MIT OR Apache-2.0） | `[tool.uv] exclude-newer = "14 days"` 保证只装满 14 天的版本；ruff 与提交钩子里原有的版本一致 |
| 生成工具 | datamodel-code-generator 合用，没有换 | 条目指定先试它；严格类型、Literal、自定义基类等需要的能力都有 |
| 列表请求参数的别名 | 不需要 | 规格补充把请求参数定为「前缀下解码后的对象」（`page` / `pageSize` …），字段名本身就是合法标识符；只有错误体的 `in` 生成为 `in_` 加别名 |
| 模型输出字段名 | 与定义一致的小驼峰；`in_` 输出为 `in` | 基类 `serialize_by_alias=True` |
| 严格类型 | 生成时用 `--strict-types`，基类也开 `strict` | Pydantic 默认会把 `"10"` 转成 10，与定义的类型约束不一致 |
| 可选字段的显式 null | 基类拒绝 | 生成工具把可选字段写成 `X \| None = None`；定义里目前没有「可选且可为 null」的字段，以后若有，样例会报出来 |

## 生成模型与定义的差异（逐条登记，包装层补齐）

同一组样例（72 合法 / 226 不合法）跑生成模型时，有 46 条不合法样例被放过，全部是生成工具读不了的约束；`python/tests/test_examples.py` 的 `GENERATED_GAPS` 逐条登记，多一条或少一条测试都失败。包装层（`python/src/done_coding_schema_api/models.py`，对外导出的就是它）对全部样例的判决与定义一致（JSON 与 Python 两种输入各测一遍）。

| 约束 | 条数 | 包装层怎么补 |
|---|---|---|
| 通用码的重试与执行语义（错误体 if/then） | 23 | `ErrorBody._semantics` 按生成的 `COMMON_ERROR_CODE_TABLE` 检查 |
| 专有码清单：stage 条件、保留码与通用码（not）、`additionalHttpStatuses` 不重复（uniqueItems）与不含主状态、code 不重复 | 10 | `ServiceErrorCodes._codes` |
| 错误体：code 不能是 OK（not）；fields 项按 in 决定 pointer / parameter（if/then/else） | 5 | `ErrorBody._semantics` |
| 不得出现的 `page` / `cursor`（定义里写作 false） | 4 | 三种列表的 `before` 校验 |
| totalPage = ceil(totalRecord / pageSize)，含总数为 0 | 2 | `PagedList._total_page` |
| hasMore 为 true 时必须给 next | 1 | `CursorList._next_when_more` |
| 筛选条件至少一个操作（minProperties） | 1 | `ListFilter._conditions` |

另补了 6 个不合法样例（可选字段显式为 null：`detail`、`pointer`、`next`、`after`、`query`、`httpStatus`），定义校验照常拒绝。

## 进度记录

- 2026-11-25 承接：上一批 `1kx2ep` 已归档，归档提交 d0f020d。
- 2026-11-25 ⓐ–ⓓ 完成：
  - `python/` 用 uv 管理（`pyproject.toml`、`uv.lock`），包名 `done-coding-schema-api`，导入名 `done_coding_schema_api`，版本 0.0.0 与 npm 包一致。
  - `pnpm gen` 现在也生成 `python/src/done_coding_schema_api/_generated/`（9 个模型模块、`constants.py`、`__init__.py`）：模型由 datamodel-code-generator 生成（输入与 TS 侧同一份去掉校验关键字的形状，另去掉值为 false 的字段）；常量与 npm 包出自同一份数据（`scripts/lib/gen-constants.mjs` 的 `buildConstants`），用只读映射与 `Literal`。生成物经 ruff format 格式化，ruff lint 不检生成目录。
  - 手写部分：`_base.py`（生成模型的基类）、`models.py`（薄包装：泛型 + 生成工具表达不了的约束）、`__init__.py`（对外导出）。
  - 证据：`pnpm check` 退出码 0（含样例校验、24 个生成物一致、版本一致、TS 类型检查与 vitest、`pytest` 603 项、npm 构建产物检查、wheel 构建）。手改 `paged_list.py` 的一个上限 → `pnpm check:generated` 退出码 1，`pnpm gen` 后 0。`python/pyproject.toml` 版本改成 0.0.1 → `pnpm check:versions` 退出码 1，改回后 0。构建出的 wheel 装进隔离环境（非可编辑安装）跑全部测试：Python 3.12 + pydantic 2.14.3、Python 3.12 + pydantic 2.11.10、Python 3.10 + pydantic 2.14.3 均 603 项通过。
