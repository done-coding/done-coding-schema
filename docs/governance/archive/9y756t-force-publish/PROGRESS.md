---
id: 9y756t
title: 定版本统一加 --force-publish，只改 Python 时也出版本
modules: [toolchain]
created: 2026-11-27
source: 甲方当轮下发（alpha.4 发布时发现的流程缺陷）
after: ""
---

# 定版本统一加 --force-publish，只改 Python 时也出版本

单批次，串首即串末。没有条目。只改、只提交，不单独发版，随正式版带出。正式版范围仍等维护者定，本批不涉及。

共享骨架独占：`.github/workflows/`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| 改 | 两个工作流与 `docs/release.md` 的定版本命令加 `--force-publish` 并写明原因 | 完成 | ca0ec5e |
| 核 | npm 包无改动时 CHANGELOG 的写法 | 完成 | 不改，见进度记录 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `luao74` 已归档（969f04a）。
- 2026-11-27 改：预发布工作流、正式版工作流、`docs/release.md`「本机发布」第 1 步的定版本命令都加 `--force-publish`。工作流在「关键参数」注释里、文档在命令下方写明原因：两个包共用一个版本号，只改了 Python 包时 lerna 判 npm 包「无变化」不出版本，发布就此停住。`docs/release.md`「流程」第 2 步同步改写。
- 2026-11-27 实测（临时工作树加临时本地分支，造一个只改 Python 的提交，用 `--no-git-tag-version --ignore-scripts` 只看算出的版本，测完删除工作树和分支）：
  - 预发布不加 force：No changed packages；
  - 预发布加 force：0.0.1-alpha.4 → 0.0.1-alpha.5；
  - 正式版命令加 force：0.0.1-alpha.4 → 0.0.1-alpha.5，不是正式版本；
  - 正式版命令加 force 与 `--conventional-graduate`：0.0.1-alpha.4 → 0.0.1。
- 2026-11-27 顺带修（自定）：正式版命令在约定式提交下只会把预发布号加一，版本形态检查会拒绝，首个正式版发不出去。所以正式版工作流与文档的正式版命令另加 `--conventional-graduate`，当前已是正式版本时它不起作用。文档补上本机发正式版的定版本命令。
- 2026-11-27 核 CHANGELOG：npm 包无改动的版本记为「**Note:** Version bump only for package @done-coding/schema-api」（alpha.4 即如此），不是空条目，对 npm 包也属实。按最简单的方式不改，文档写明这一版的改动看同一版本区间的提交记录。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：版本一条里「本机定版本须加 --force-publish」改为两处定版本都加，正式版另加 --conventional-graduate；技术基线的发布一条补上这两个参数。移出的历史内容：无。
- 收工。

## 交付清单

- ca0ec5e：工作流与文档。
- 归档提交：快照与本批归档。
