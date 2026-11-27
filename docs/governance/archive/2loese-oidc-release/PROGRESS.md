---
id: 2loese
title: 发布流程对齐模板：单个 oidc-release 工作流，npm 与 PyPI 可信发布
modules: [toolchain]
created: 2026-11-28
source: 甲方当轮下发（维护者本人：CI/CD 对齐 done-coding-request 与模板的单工作流，加 Python 发布）
after: ""
---

# 发布流程对齐模板：单个 oidc-release 工作流

单批次，串首即串末。没有条目。只改、只提交，不发版；不动包内容，正式版范围仍等维护者定。Python 发布部分先在本仓试行，稳定后由维护者安排吸收进 template-hub，本批不动 template-hub。

共享骨架独占：仓根 `package.json`、`pnpm-lock.yaml`、`.github/workflows/`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 以 template-hub 当前 `oidc-release.yml` 为底本换掉两个旧工作流 | 完成 | 3071251 |
| ⓑ | 加 Python 增量：uv、构建与检查、版本形态、`uv publish` | 完成 | 3071251 |
| ⓒ | 定版本参数：`--force-publish`，正式版加 `--conventional-graduate` | 完成 | 3071251 |
| ⓓ | lerna 7 → 9.0.7，`engines.node`、`packageManager`、锁文件 | 完成 | 3071251 |
| ⓔ | 本机试跑两条定版本路径（不发布） | 完成 | 记于下 |
| ⓕ | `docs/release.md` 按单工作流与可信发布重写 | 完成 | 3071251 |
| ⓖ | 检查、快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-28 起因：本仓 11-24 从 template-hub 远端 `origin/master`（`8edf826`，11-11）创建，那时模板还是双工作流加 `NPM_TOKEN`；模板 11-16 改成单个 `oidc-release.yml`（npm 可信发布，lerna 9），该提交只在 template-hub 本机、未推送。
- 2026-11-28 依赖：`lerna` 7.4.2 → 9.0.7（MIT，2026-03-13 发布，满 14 天），钉死版本与 done-coding-request、模板一致；`engines.node` `>=18.0.0` → `>=20.19.0`（lerna 9 要求 `^20.19.0 || ^22.12.0 || >=24.0.0`）；补 `packageManager: pnpm@12.15.0`（本机版本；工作流的 `pnpm/action-setup` 按它装）。pnpm 12 因此在锁文件头部写入 `packageManagerDependencies` 一节；`postinstall` 的 prettier 统一格式后 `pnpm install --frozen-lockfile` 不再改动锁文件。
- 2026-11-28 npm 包 `repository.url` 由 `git@github.com:…` 改为 `https://github.com/done-coding/done-coding-schema.git`：npm 可信发布要求它与 GitHub 仓库一致，写法同 done-coding-request。
- 2026-11-28 试跑（ⓔ）：在临时工作区与临时分支上应用本批改动，`pnpm install --frozen-lockfile --offline` 后用本地 lerna 9.0.7（`--no-commit-hooks`，其余参数与工作流相同）：
  - 预发布：`0.0.1-alpha.4 → 0.0.1-alpha.5`，`version` 生命周期脚本照常运行，`pyproject.toml` 与 `uv.lock` 同为 `0.0.1a5`，都在同一个版本提交里，标签 `@done-coding/schema-api@0.0.1-alpha.5`，工作树干净；
  - 正式版（同一基点）：`0.0.1-alpha.4 → 0.0.1`，Python 包 `0.0.1`，同一提交，标签 `@done-coding/schema-api@0.0.1`；
  - 两个试跑标签、临时分支与工作区已删除，仓内没有残留。
  - 第一次试跑作废：临时工作区没装上依赖，`npx lerna` 自动下载了 lerna 10.1.3；且锁文件未经 prettier 格式化，版本提交带进了锁文件。修正后按上面重跑。
- 2026-11-28 工作流：`.github/workflows/oidc-release.yml`，删除 `release-publish.yml`、`prerelease-publish.yml`。与模板相比只多 Python 部分，且把定版本拆成单独步骤，顺序为定版本 → 构建与检查（`pnpm check`、`pnpm check:min-versions`）→ 按分支核对版本形态 → npm（预发布 `alpha`，正式 `latest`）→ PyPI（`--trusted-publishing always`，拿不到 OIDC 凭据即失败）→ 推送。不设任何长期令牌。未在 GitHub 上运行过；`lerna publish from-package` 经 OIDC 上传在本机无法试，没有验证。
- 2026-11-28 文档：`docs/release.md` 触发与「前提」两节重写：npm 与 PyPI 各登记一条可信发布者，文件名 `oidc-release.yml`，环境名称留空，npm 勾 Allow npm publish、不勾 Allow npm dist-tag；不再需要 `NPM_TOKEN`。「本机发布」一节（令牌方式）不变。
- 2026-11-28 检查：`pnpm check` 退出码 0；`npx lerna run build` 成功且工作树干净；工作流 YAML 解析通过，并与模板逐行比对，差异只有上面列的几处；改动文件 prettier 通过。`npx eslint .` 报「No files matching the pattern」，本仓 ESLint 没有覆盖到任何文件，本批也没有改 JS / TS 代码。
- 2026-11-28 快照替换（`SNAPSHOT.md`）：toolchain 一行「正式版与预发布两个工作流」→ 单个 `oidc-release.yml`、两边可信发布；技术基线「Node ≥ 18」→「Node ≥ 20.19，packageManager pnpm 12.15.0」；发布一条补上 lerna 9.0.7、npm 可信发布、`--trusted-publishing always`、登记项指向 `docs/release.md`。移出的历史内容：无。
- 收工。

## 交付清单

- 3071251：工作流、`package.json`、`packages/api/package.json`、锁文件、`docs/release.md`、本批进度。
- 归档提交：快照与本批归档。
