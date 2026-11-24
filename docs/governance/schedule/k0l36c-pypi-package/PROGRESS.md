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
| ⓐ | 建 Python 包（`python/`，用 uv 管理）；没有现成的 Python 库模板，手写最小工程 | 未开始 | |
| ⓑ | 由定义生成 Pydantic 模型与常量并入仓，纳入上一批的一致性检查 | 未开始 | |
| ⓒ | 用上一批的同一组样例验证：Python 模型的接受与拒绝结果与定义校验一致 | 未开始 | |
| ⓓ | 版本一致检查：npm 包与 Python 包版本号不一致时失败 | 未开始 | |
| ⓔ | 刷新领域状态与快照，归档本批 | 未开始 | |
| ⓕ | 本批交付归档后立刻、必须、立即开始下一批 `p1rbxy` | 未开始 | |

## 进度记录

（随手写在这里）
