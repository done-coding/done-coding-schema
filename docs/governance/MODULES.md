# 领域清单

## 领域模块

> 领域清单唯一真源；治理工具从本表第一列解析合法的 `modules` 取值。2026-11-24 立项时按已确认的能力范围登记，均未实现；路径下出现第一份实现代码时把状态改为 `active`。

| 模块 | 类型 | 一行摘要 | status | paths |
|---|---|---|---|---|
| `definition` | 垂直 | 通用接口结构的定义与样例：一个结构一份 JSON Schema，各带合法与不合法样例 | not_implemented | `schemas/` |
| `toolchain` | 垂直 | 生成与检查：由定义生成各语言代码，核对生成物与定义一致、各包版本一致 | not_implemented | `scripts/` |
| `npm-package` | 垂直 | npm 包：生成的 TS 类型连同定义文件一起导出 | not_implemented | `packages/` |
| `pypi-package` | 垂直 | PyPI 包：生成的 Pydantic 模型 | not_implemented | `python/` |

无横向（调度）领域。

共享骨架：仓根的 `package.json`、`pnpm-workspace.yaml`、`pnpm-lock.yaml`、`.github/workflows/`。批次要改它们时在 `PROGRESS.md` 写明独占。
