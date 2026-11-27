---
id: luao74
title: 第五个预发布版（正式版候选）
modules: [npm-package, pypi-package]
created: 2026-11-27
source: 甲方当轮下发
after: ""
---

# 第五个预发布版（正式版候选）

单批次，串首即串末。没有条目：只把已提交未发布的 nxksq8（59e0788、39c23e2、9c89254）发成 npm `0.0.1-alpha.4` / PyPI `0.0.1a4`，不加别的改动。

授权：维护者在本会话确认「授权发 alpha.4」。npm 只上 alpha 标签，latest 不挪；推送由维护者本人做。正式版的范围（是否拿掉筛选结构与查询参数模型）未定，本批不涉及。

共享骨架独占：无。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| 发布 | 检查、定版本、构建、上传、线上核对 | 完成 | d01ded1，见进度记录 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `nxksq8` 已归档（9c89254）；自 alpha.3 标签以来只有 nxksq8 的提交。
- 2026-11-27 定版本：`lerna version prerelease` 第一次回报「No changed packages to version」，没有生成提交与标签。原因：nxksq8 只改了 `python/` 与仓根 README，lerna 只按 `packages/` 下的 npm 包判断改动。这次误构建出的 alpha.3 产物没有上传。加 `--force-publish` 重跑：npm 0.0.1-alpha.3 → 0.0.1-alpha.4，Python 0.0.1a3 → 0.0.1a4；版本提交 d01ded1，标签 `@done-coding/schema-api@0.0.1-alpha.4`，CHANGELOG 记为 Version bump only。预发布工作流里用的是同一条命令，遇到只改 Python 的情形也会停住，这条另行回报，本批不改工作流。
- 2026-11-27 发布前检查：在版本提交上跑 `pnpm check`，退出码 0；样例、TS 11 个测试、Python 1268 个测试、类型解析与产物检查都通过。仓外构建：npm 22 个文件，wheel 与 sdist 各含 11 份定义与 LICENSE，解开扫过没有本机路径。
- 2026-11-27 上传：npm `+ @done-coding/schema-api@0.0.1-alpha.4`，显式带 `--tag alpha`；PyPI 的 wheel 与 sdist 上传成功。令牌只经环境变量传入，npmrc 里只有占位，用完删除。
- 2026-11-27 PyPI 核对：0.0.1a4 的 sha256 与本机构建相同（wheel caacccf7…，sdist 139d1434…）。空目录 `--prerelease allow` 装到 0.0.1a4（pydantic 2.14.4，另装 fastapi 0.162.5）：
  - ErrorBody 子类加字段在类定义时报 TypeError；列表顶层加 summary 可以，导出里有它；
  - `pageSize=50` 与直接构造 `PagedListQuery(pageSize=5)` 都报 `bare_parameter_name`，提示「pageSize 应写作 page.pageSize」；
  - README 的 Python 片段原样运行通过，`OrderQuery` 收 `status` 与 `minAmount`，OpenAPI 参数名为四个线上名加 status、minAmount。
- 2026-11-27 npm 核对：上传后约一分钟可见。dist-tags 为 `alpha` = 0.0.1-alpha.4、`latest` 仍是 0.0.1-alpha.0（不挪）；线上 shasum 与本机构建相同（86931ea5…）。空目录 `@alpha` 装到 0.0.1-alpha.4：README 的 TS 片段在 bundler 下 tsc 通过；moduleResolution node 的项目从 `/reference` 取到字面量类型，tsc 通过；ESM 与 CJS 的导出核对、Ajv 判各例都通过。
- 2026-11-27 相对 0.0.1a3 的变化（都只在 Python 包；npm 包内容与 alpha.3 相同，只有版本号变了）：
  - 封闭结构的子类不得新增字段，类定义时报 TypeError；
  - 查询参数模型的子类可以加前缀外的参数，按自己的声明校验；
  - 与字段同名的裸名报 `bare_parameter_name`，HTTP 下为 422。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：npm-package / pypi-package 两行与版本一条改为 alpha.4 / a4（正式版候选），并补上「只改 Python 时定版本须加 --force-publish」。移出的历史内容：无。
- 收工。推送由维护者本人做：分支 `master`、`feat/schema-v0`，标签 `@done-coding/schema-api@0.0.1-alpha.0` 至 `0.0.1-alpha.4`。

## 交付清单

- f8845f2：开批次。
- d01ded1：版本提交（0.0.1-alpha.4 / 0.0.1a4），发布的是 nxksq8 的 59e0788、39c23e2、9c89254。
- 归档提交：快照与本批归档。

## 结果

- 第五个预发布版（正式版候选）已在 npm（alpha）与 PyPI 发布，空目录各装一次验证通过。
