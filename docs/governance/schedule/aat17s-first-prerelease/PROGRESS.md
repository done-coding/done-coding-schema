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
| ⓑ | 定版本（版本提交与标签） | 完成 | ba32c3a，标签 `@done-coding/schema-api@0.0.1-alpha.0` |
| ⓒ | `pnpm check`、仓外构建、核对文件清单 | 完成 | 见进度记录 |
| ⓓ | 上传：先 npm 后 PyPI | 完成 | 见进度记录 |
| ⓔ | 线上核对与空目录安装 | 完成 | 见进度记录 |
| ⓕ | 推送 master、`feat/schema-v0` 与版本标签 | 待做 | |
| ⓖ | 快照、`docs/release.md`「本机发布」、归档。收工 | 待做 | |

## 进度记录

- 2026-11-26 承接：上一串 `p1rbxy` 已归档（aa49790）；维护者在本会话确认授权本次推送与预发布。
- 2026-11-26 环境：GitHub（SSH、HTTPS）与 npm 官方源可达；`upload.pypi.org` 两次连接超时（`pypi.org` 可达），上传时再试。远端仓为空。
- 2026-11-26 ⓐ 许可证：仓根 `LICENSE`（MIT，版权行 `Copyright (c) 2026 done-coding`）。打包只收包目录内文件，故 `packages/api/LICENSE`、`python/LICENSE` 各放一份副本：npm 自动收包根的 `LICENSE`，Python 在 `pyproject.toml` 写 `license-files = ["LICENSE"]`。新增 `pnpm check:license`（`scripts/check-license.mjs`）要求副本与仓根逐字节相同，已接入 `pnpm check`；改坏副本时退出码 1（实测）。
  - 核对：`npm pack --dry-run` 含 `LICENSE`；wheel 含 `dist-info/licenses/LICENSE`，METADATA 有 `License-Expression: MIT`、`License-File: LICENSE`；sdist 根含 `LICENSE`。
  - sdist 里的 `pyproject.toml.orig` 是构建后端 uv_build 的固定做法：把原文件留作 `.orig`，另写一份规范化的 `pyproject.toml`（两者只差格式与注释），不是仓内多出的文件，保留。
- 2026-11-26 ⓑ 定版本：`npx lerna version prerelease --yes --preid alpha --no-push --message "chore(prerelease): publish [skip ci]"`（与预发布工作流同参数）。npm 0.0.0 → 0.0.1-alpha.0；`version` 生命周期脚本把 Python 同步为 0.0.1a0。版本提交 ba32c3a 含 `packages/api/package.json`、`packages/api/CHANGELOG.md`、`python/pyproject.toml`、`python/uv.lock`，标签 `@done-coding/schema-api@0.0.1-alpha.0` 打在该提交上。lerna 顺带把 package.json 的 devDependencies 排序并删掉两个空对象（`peerDependencies`、`dependencies`），不影响发布内容。
- 2026-11-26 ⓒ 检查与构建：`pnpm check` 退出码 0（179 条约束全覆盖、生成物 24 个一致、版本一致 0.0.1-alpha.0 / 0.0.1a0、许可证副本一致、TS 4 个测试、Python 603 个测试、构建产物无 Node 专用依赖、wheel 构建），检查后工作树干净。仓外输出目录（会话临时目录）：
  - npm `done-coding-schema-api-0.0.1-alpha.0.tgz`：`LICENSE`、`README.md`、`package.json`、`es/index.mjs`、`lib/index.cjs`、`types/index.d.ts`、`schemas/` 10 份定义；无运行时依赖。
  - wheel `done_coding_schema_api-0.0.1a0-py3-none-any.whl`：包内 5 个文件 + `_generated/` 11 个模块，`dist-info/licenses/LICENSE`；METADATA 版本 0.0.1a0、`License-Expression: MIT`。
  - sdist `done_coding_schema_api-0.0.1a0.tar.gz`：`PKG-INFO`、`pyproject.toml`（及后端留的 `.orig`）、`LICENSE`、`README.md`、`src/` 同上。
  - 名字未被占：npm `@done-coding/schema-api`、PyPI `done-coding-schema-api` 查询均 404；`upload.pypi.org` 此时可达。
- 2026-11-26 ⓓ 上传（令牌只经环境变量传给发布命令，npmrc 放仓外临时目录、只写 `${NODE_AUTH_TOKEN}` 占位）：
  - npm：`npm publish <tgz> --tag alpha --access public --registry https://registry.npmjs.org/` 成功，`+ @done-coding/schema-api@0.0.1-alpha.0`，16 个文件，shasum 748976ac87a0cb968411fd2f74c9fd4a93dc1e2d。本机 npm 默认源是镜像，故显式写官方源。
  - PyPI：`uv publish --check-url https://pypi.org/simple/ <whl> <tar.gz>` 两个文件上传成功。
- 2026-11-26 ⓔ 线上核对：
  - npm dist-tags：`alpha` = `latest` = 0.0.1-alpha.0，license MIT。首次发布时注册表会把 `latest` 也指向这个版本（`latest` 不能删除），所以在发布正式版前，不带标签的 `npm install` 也会装到这个预发布版本。
  - PyPI：项目 `done-coding-schema-api` 唯一版本 0.0.1a0，`license_expression` MIT，文件为 wheel 与 sdist；从 PyPI 下载的 wheel 与本机构建的 sha256 相同（ce734909…）。
  - 空目录（npm）：`npm install @done-coding/schema-api@alpha typescript@5.9.3`（官方源）装到 0.0.1-alpha.0，包内带 `LICENSE`。npm 包 README 的 TS 片段原样 `tsc` 通过（`moduleResolution: Bundler`，`strict`，`skipLibCheck: false`）。追加把 `totalRecord` 拼成 `totalRecords` 后报 TS2551。运行时 ESM 导入得到 `page.pageSize` 与 10 份定义，CJS `require` 也得到 `page.pageSize`。
  - 空目录（pip）：Python 3.12 新虚拟环境，`pip install --pre --index-url https://pypi.org/simple/ done-coding-schema-api` 装到 0.0.1a0（pydantic 2.14.4），dist-info 带 `licenses/LICENSE`。Python 包 README 片段原样运行通过；仓根 README 的 Python 例子原样运行，输出 `甲`、`429`、`page.pageSize`，与注释一致；`totalPage` 与 `ceil(totalRecord/pageSize)` 不符的请求被拒。下载过程中 files.pythonhosted.org 断连，第二次安装成功。
- 2026-11-26 ⓖ（部分）：`docs/release.md` 新增「本机发布」一节，记录这次实际用的步骤（令牌只写占位，不写文件位置）。
