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
| ⓐ | 按条目 `08byqy` 的规格写首版结构的定义，每个结构配合法、不合法两组样例；样例校验结果与预期一致 | 未开始 | |
| ⓑ | 用成员包模板 `npm-common-member` 建 npm 包（答案见「已定事项」）；由定义生成 TS 类型与常量并入仓，包同时导出定义文件；能在浏览器端引入 | 未开始 | |
| ⓒ | 一致性检查：手改生成物或改了定义未重新生成时失败；接进仓的检查命令 | 未开始 | |
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

## 进度记录

（随手写在这里）
