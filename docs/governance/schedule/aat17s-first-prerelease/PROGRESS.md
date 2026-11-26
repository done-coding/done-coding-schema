---
id: aat17s
title: 首次预发布（本机发布）
modules: [toolchain, npm-package, pypi-package]
created: 2026-11-26
source: 甲方当轮下发（维护者 2026-11-26 授权推送与预发布）
after: ""
---

# 首次预发布（本机发布）

单批次，串首即串末。条目 `2f6iq1`。

共享骨架独占：仓根 `package.json`、`LICENSE`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 补 LICENSE，三种发布物都带上 | 完成 | 见进度记录 |
| ⓑ | 定版本（版本提交与标签） | 待做 | |
| ⓒ | `pnpm check`、仓外构建、核对文件清单 | 待做 | |
| ⓓ | 上传：先 npm 后 PyPI | 待做 | |
| ⓔ | 线上核对与空目录安装 | 待做 | |
| ⓕ | 推送 master、`feat/schema-v0` 与版本标签 | 待做 | |
| ⓖ | 快照、`docs/release.md`「本机发布」、归档。收工 | 待做 | |

## 进度记录

- 2026-11-26 承接：上一串 `p1rbxy` 已归档（aa49790）；维护者在本会话确认授权本次推送与预发布。
- 2026-11-26 环境：GitHub（SSH、HTTPS）与 npm 官方源可达；`upload.pypi.org` 两次连接超时（`pypi.org` 可达），上传时再试。远端仓为空。
- 2026-11-26 ⓐ 许可证：仓根 `LICENSE`（MIT，版权行 `Copyright (c) 2026 done-coding`）。打包只收包目录内文件，故 `packages/api/LICENSE`、`python/LICENSE` 各放一份副本：npm 自动收包根的 `LICENSE`，Python 在 `pyproject.toml` 写 `license-files = ["LICENSE"]`。新增 `pnpm check:license`（`scripts/check-license.mjs`）要求副本与仓根逐字节相同，已接入 `pnpm check`；改坏副本时退出码 1（实测）。
  - 核对：`npm pack --dry-run` 含 `LICENSE`；wheel 含 `dist-info/licenses/LICENSE`，METADATA 有 `License-Expression: MIT`、`License-File: LICENSE`；sdist 根含 `LICENSE`。
  - sdist 里的 `pyproject.toml.orig` 是构建后端 uv_build 的固定做法：把原文件留作 `.orig`，另写一份规范化的 `pyproject.toml`（两者只差格式与注释），不是仓内多出的文件，保留。
