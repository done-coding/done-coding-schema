---
id: izzrx0
title: 最低支持版本的测试落成仓内脚本
modules: [toolchain, pypi-package]
created: 2026-11-27
source: 甲方当轮下发（qor3um 核收后补充）
after: ""
---

# 最低支持版本的测试落成仓内脚本

单批次，串首即串末。没有条目。只改、只提交，不单独发版；不扩别的范围，正式版范围等维护者定。

共享骨架独占：仓根 `package.json`、`.github/workflows/`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| 脚本 | 建临时环境、装本机构建的 wheel 与最低版本依赖、跑全部 Python 测试、用完清理；package.json 一条命令 | 完成 | 7c7d61a |
| 一致 | 最低版本与 pyproject 声明的支持范围写在一处或加一致性检查 | 完成 | 7c7d61a（写在一处） |
| 文档 | docs/release.md 发布前必做；两个工作流发布前调用；README 写明经过测试的版本 | 完成 | 7c7d61a |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `qor3um` 已归档（cc28123）。
- 2026-11-27 脚本：`scripts/check-min-versions.py`，仓根命令 `pnpm check:min-versions`（`uv run --project python --frozen python scripts/check-min-versions.py`）。
  - 步骤：uv build 出 wheel；`uv venv --python <最低版本>` 建临时环境；装 wheel 与最低版本依赖；把 `python/tests` 与 `schemas` 按原相对布局拷到临时目录；先打印装到的版本并断言导入的是 site-packages 里的包；再跑 pytest。
  - 收尾：临时目录用 TemporaryDirectory，跑完自动删除，实测没有残留。失败时退出码 1，并写明是哪条命令失败。
- 2026-11-27 一致性：选「写在一处」。
  - Python 取 `requires-python` 的下界；
  - 运行时依赖取 `dependencies` 各项下界所在次版本的最新修订版（`pydantic>=2.11,<3` → `pydantic~=2.11.0`，实装 2.11.10；`typing-extensions>=4.12` → `~=4.12.0`）；
  - 测试工具取 `dependency-groups.dev` 锁定的 pytest 与 jsonschema；
  - FastAPI 不是运行时依赖，pyproject 里没有它的下界，最低测试版本作为脚本常量 `FASTAPI_MINIMUM = "0.140.7"`；
  - 下界没写成「>=主.次」时脚本直接报错，不会悄悄跳过。
- 2026-11-27 文档与工作流：
  - `docs/release.md`「流程」第 3 步与「本机发布」第 2 步写成必做，并说明最低版本从哪里取、为什么不在 `pnpm check` 里；
  - 两个工作流在「Build and check」步骤里 `pnpm check` 之后调用 `pnpm check:min-versions`，注释写明用途。工作流没有在线上跑过，按文档写，未线上实测；
  - 仓根 README 的开发命令表加这一行；两份 README 的支持范围处加「最低版本（Python 3.10、pydantic 2.11、FastAPI 0.140）与当前锁定版本经过测试，中间版本没有逐个测试」。
- 2026-11-27 检查：`pnpm check:min-versions` 退出码 0，Python 3.10.20、pydantic 2.11.10、FastAPI 0.140.7 下 1286 个测试通过。pytest 有 1 条警告，来自 anyio 的 pytest 插件（pytest 10 将移除 CallSpec2 别名），与本仓无关。`pnpm check` 退出码 0。本批不发版。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：toolchain 一行补上 `pnpm check:min-versions`；技术基线的 Python 一条补上最低版本测试的来源与做法。移出的历史内容：无。
- 收工。

## 交付清单

- 7c7d61a：脚本、命令、两个工作流、docs/release.md、两份 README。
- 归档提交：快照与本批归档。
