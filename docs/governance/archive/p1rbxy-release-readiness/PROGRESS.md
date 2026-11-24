---
id: p1rbxy
title: 发布准备与接入说明
modules: [toolchain, npm-package, pypi-package]
created: 2026-11-24
source: 用户 2026-11-24 立项（立项说明 docs/PROJECT.md）
after: k0l36c
---

# 发布准备与接入说明

批次串：`1kx2ep → k0l36c → p1rbxy`。本批是串末。

目的：两个语言的包能以同一个版本一次发出去，使用方照着说明就能引入。

共享骨架独占：沿用串首声明；本批另独占 `.github/workflows/`。

开工前先读：`docs/PROJECT.md`、条目 `gwwvzi`、前两批归档的 `PROGRESS.md`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 发布流程：模板自带的流程只管 npm，补上 Python 包的构建与上传步骤；两个包同一提交、同一版本号 | 完成 | 两个工作流改为「定版本 → 构建与检查 → 核对版本形态 → npm → PyPI」；临时克隆里演练 `lerna version` 4 种情形，两包版本均落在同一提交 |
| ⓑ | 本机演练一次构建（只构建，不上传），核对两个包的内容与版本 | 完成 | 见下「本机构建演练」 |
| ⓒ | README：这套结构是什么、TS 与 Python 各怎么引入和使用、版本与兼容规则 | 完成 | 空目录照做：TS、Python 各一次走通（用本机构建产物） |
| ⓓ | 刷新领域状态与快照，归档本批 | 完成 | 见下「交付」；`done-coding harness check` 通过 |
| ⓔ | 收工。发布由维护者决定，不在本串内执行 | 完成 | 未发布、未 push |

## 本机构建演练（2026-11-25，只构建，不上传）

命令：`pnpm -F @done-coding/schema-api build`、`pnpm pack`、`uv build --project python`，产物放在会话临时目录，未入仓。

| 包 | 文件 | 版本 | 文件清单 |
|---|---|---|---|
| npm `@done-coding/schema-api` | `done-coding-schema-api-0.0.0.tgz` | 0.0.0 | `package.json`、`README.md`、`es/index.mjs`、`lib/index.cjs`、`types/index.d.ts`、`schemas/` 下 10 份定义；无运行时依赖 |
| PyPI `done-coding-schema-api` | `done_coding_schema_api-0.0.0-py3-none-any.whl` | 0.0.0 | `done_coding_schema_api/` 下 `__init__.py`、`_base.py`、`models.py`、`py.typed`、`_generated/` 11 个模块；依赖 `pydantic>=2.11,<3`、`typing-extensions>=4.12`，Python ≥ 3.10 |
| 同上（sdist） | `done_coding_schema_api-0.0.0.tar.gz` | 0.0.0 | `pyproject.toml`、`README.md`、`PKG-INFO`、`src/` 下同上源码；另有构建后端自带的 `pyproject.toml.orig` |

`node scripts/check-versions.mjs`：版本一致（npm 0.0.0 / Python 0.0.0）。

## 进度记录

- 2026-11-25 承接：上一批 `k0l36c` 已归档，归档提交 46cc28b。
- 2026-11-25 ⓐ 发布流程：
  - 原流程用一步 `lerna publish` 定版本并上传 npm，版本提交里只有 npm 包。改为 `lerna version`（正式版沿用约定式提交定版本，预发布沿用 `prerelease --preid alpha`）+ `lerna publish from-package`；仓根 `package.json` 新增 `version` 生命周期脚本 `scripts/sync-python-version.mjs`，在 lerna 提交前用 `uv version` 把同一版本写进 `python/pyproject.toml` 与 `uv.lock` 并加入版本提交。npm 预发布 `X.Y.Z-(alpha|beta|rc).N` 对应 PEP 440 `X.Y.Z(a|b|rc)N`（`scripts/lib/versions.mjs`），版本检查按此比对。
  - 上传前跑 `pnpm check`（含版本一致检查）并核对版本形态：正式版只接受 `X.Y.Z`，预发布只接受预发布版本（PyPI 没有 dist-tag，防止预发布被当成正式版上传）。Python 包用 `uv publish` + PyPI 可信发布（工作流声明 `id-token: write`），`--check-url` 让重跑跳过已上传文件。新增 `astral-sh/setup-uv@v10.3.3`（MIT，2026-10-28 发布；v10.4.0 发布未满 14 天未用），uv 版本 0.11.32。
  - 演练（会话临时目录里的克隆，未推送）：正式版 0.0.0 → 0.1.0、0.1.0 → `prerelease --preid alpha` 得 0.1.1-alpha.0 / 0.1.1a0、预发布上再预发布得 0.2.0-alpha.0 / 0.2.0a0，版本提交都同时含 `packages/api/package.json`、`python/pyproject.toml`、`python/uv.lock`，标签打在该提交上，`check-versions` 通过。另验：工作流里的 pnpm 10.33.0 以 `--frozen-lockfile` 安装本仓锁文件成功；两个工作流 YAML 可解析。
  - 发现并记录：模板原预发布流程若改成只带 `--preid` 不带 `prerelease`，从正式版出发会得到正式版本号（演练 0.1.0 → 0.2.0）；本仓流程保留显式 `prerelease`，并由版本形态核对兜底。
  - 凭据只写说明不读取：`docs/release.md` 写明 `NPM_TOKEN`、`RELEASE_GITHUB_TOKEN` 与 PyPI 可信发布的登记项（及改用令牌的做法）。
- 2026-11-25 ⓒ README：仓根 `README.md` 重写（每个结构一段与最小例子、三种列表怎么选、请求参数、业务码与专有码、TS 与 Python 用法、拿定义文件自己校验、版本规则、本包不做什么、开发命令）；两个包各自的 README 写安装与最小用法并指回仓库 README。
  - 例子核对：README 里 6 段 JSON 例子逐段过定义校验，全部合法。
  - 空目录照做（用本机构建产物）：TS——新建 npm 项目，装本机 `.tgz` 与 ajv 8.20.0、typescript 5.9.3，README 的两段 TS 原样做类型检查通过（`moduleResolution: Bundler`，`skipLibCheck: false`），校验那段打包后运行：错误体 code 为 `OK` 得 false、合法错误体得 true；npm 包 README 的片段也通过类型检查。Python——新建虚拟环境装本机 wheel（pydantic 2.14.3），README 的片段原样运行，输出 `甲`、`429`、`page.pageSize` 与注释一致；Python 包 README 片段运行通过；另装 FastAPI 0.162.3 验证 `response_model=SuccessEnvelope[PagedList[User]]` 能正确输出并生成 OpenAPI 结构。
  - 证据：`pnpm check` 退出码 0；eslint、prettier 通过。
- 2026-11-25 ⓓ：领域状态不变（四个领域都已 active）。`SNAPSHOT.md` 替换的事实：头部指针补上 README 与发布流程文档；`toolchain` 一行补上版本同步脚本与两个发布工作流（注明未实际运行过）；「版本」契约由「同一版本号」改为「同一版本号、同一版本提交与标签」并写明预发布的对应写法、两包均未发布；技术基线补一条发布方式。没有移出的史料。共享骨架：本批改了 `.github/workflows/`（本批独占）与 `package.json`（串首独占，新增 `version` 生命周期脚本）。
- 留给维护者的事项（均不在本串内执行）：在 GitHub 配 `NPM_TOKEN`、`RELEASE_GITHUB_TOKEN`，在 PyPI 登记可信发布者（见 `docs/release.md`）；两个工作流未在 GitHub 上实际跑过；仓库没有 LICENSE 文件，两个包声明 MIT 但发布物里不含许可证全文，发布前宜补。

## 交付

条目 `gwwvzi`：8c3ffd1（发布流程、版本同步与对应规则、README 与发布说明）· 归档提交（快照、归档）。结果：两个包能以同一版本从同一提交构建，发布流程写全且上传前有版本一致与版本形态检查；README 接入步骤在空目录照做 TS、Python 各一次走通；未发布、未 push。
