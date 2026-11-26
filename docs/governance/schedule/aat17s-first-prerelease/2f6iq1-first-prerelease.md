---
id: 2f6iq1
title: 两个包的首次预发布（本机发布）
modules: [toolchain, npm-package, pypi-package]
created: 2026-11-26
parent: ""
---

# 两个包的首次预发布（本机发布）

目的：尽快把 npm 包与 PyPI 包的预发布版发出去，让使用方能装。发布流程在 GitHub 上跑通留到正式版，本次不做。

范围（维护者 2026-11-26 授权，只到预发布）：

- 仓根补 MIT 许可证（版权行 `Copyright (c) 2026 done-coding`），npm 包、wheel、sdist 都带上。
- 用本仓定版本脚本在本机把两包定到同一个预发布版本，生成版本提交与标签；版本号以脚本算出为准。
- `pnpm check` 全过；构建到仓外目录，核对文件清单、版本一致、带许可证、没有多余文件。
- 先 npm（`--tag alpha --access public`）后 PyPI（`uv publish`，wheel + sdist）；npm 已传而 PyPI 失败时按 `docs/release.md`「中途失败」补传，不另起版本号。
- 核对两处版本一致；空目录各装一次线上包，跑通 README 最小例子。
- 推送 master、`feat/schema-v0` 与版本标签；不建 prerelease / release 分支。
- 快照写明已有预发布版、本机发布、GitHub 工作流仍未实际运行；`docs/release.md` 补「本机发布」一节。

边界：不发正式版本号；令牌只经环境变量传给发布命令，不打印、不落仓内文件。

停下的情形：npm 要一次性验证码或无权限、PyPI 鉴权失败或项目名被占、推送被拒、需要改结构定义本身才能发；同一步重试不超过两次。
