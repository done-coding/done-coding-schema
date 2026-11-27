---
id: qor3um
title: 子类承诺收口、列表顶层不得新增定义里写作 false 的字段、公开查询整数类型
modules: [pypi-package]
created: 2026-11-27
source: 甲方当轮下发（alpha.4 评审）
after: ""
---

# 子类承诺收口、列表顶层不得新增定义里写作 false 的字段、公开查询整数类型

单批次，串首即串末。没有条目。只改、只提交，不单独发版；不改导入路径和已有名字。正式版范围仍等维护者定。

共享骨架独占：无。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| 一 | README「子类」一节按三条口径重写（硬保证、受支持写法、不支持写法） | 完成 | 4c0a6a1 |
| 二 | 列表顶层新增字段的线上名在源定义里写作 false 时，类定义报 TypeError | 完成 | df1fa3b |
| 三 | 公开按 x-queryIntegerPattern 解码的整数类型，README 示例改用它 | 完成 | df1fa3b、4c0a6a1 |
| 四 | 回答事实：pydantic 测试矩阵；错误体 detail 的约束 | 完成 | 见进度记录 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `9y756t` 已归档（f019681）。
- 2026-11-27 口径（下发方定）：包对自己的模型保证定义、导出、运行时三者同结论；对使用方子类只保证 README 明列的写法；其余写法不支持，类定义时的检查是尽力而为的提醒，不是保证。现有检查全部保留；extra="allow"、computed_field、validation_alias 单独设别名这几类绕法不再加检查，只列进「不支持」。
- 2026-11-27 四ⓐ pydantic 版本（实查）：`pnpm check` 跑的是 `python/uv.lock` 锁定的环境，即 Python 3.12.13、pydantic 2.14.3、FastAPI 0.162.5。最低支持组合 Python 3.10.20、pydantic 2.11.10（alpha.3 起另加 FastAPI 0.140.7）每批发布前在本机临时环境里装本机构建的 wheel 手工跑全部测试，没有进 `pnpm check`，工作流里也没有版本矩阵。
- 2026-11-27 四ⓑ 错误体 detail（原文）：`"detail": {"description": "补充说明，可选，不限长。", "type": "string"}`，不在 required 里；没有长度、格式或用途上的其他约束。README 写作「`detail`（可选）：补充说明，不限长」，「有意为之的约束」一节写着更长的补充说明放 `detail`。
- 2026-11-27 二：
  - 实查三种列表定义里写作 false 的名字：一次性列表是 page、cursor，页码式是 cursor，游标式是 page。
  - `_source.check_added_fields` 对开放结构新增的字段再查一次：线上名在源定义 properties 里是 false 的，报 TypeError，写明子类、结构名与字段。
  - 测试 4 例：BoundedList 加 page、加 cursor，PagedList 加 cursor，CursorList 加 page，都带默认值，都被拒。
- 2026-11-27 三：
  - 新增 `QueryInt = Annotated[int, BeforeValidator(按 x-queryIntegerPattern 解码), Strict()]`，规则取自定义（页码式与游标式两份定义里的 pattern 相同，测试核对），从包顶层导出，与查询参数模型同处。
  - 测试里的 `minAmount` 改为 `Annotated[QueryInt | None, Field(ge=0)]`，补 0、20、100 合法，以及 10 种写法（02、+2、空格、2.0、1e1、空串、-1、全角数字、末尾换行、true）在前缀内外都被拒；FastAPI 下 `minAmount=02`、`%2B2`、`2.0` 返回 422。
  - README 的前缀外整数示例改用它，并写明「前缀外其他类型（如布尔）的解码规则由使用方自己的声明决定」。
- 2026-11-27 一：仓根 README 新增「Python 子类：包保证什么」一小节，放在「使用方怎样显式声明自己的配置」里 Python 示例之前：
  - 包自己的模型：三者同结论，是硬保证；
  - 使用方子类：只保证四种写法；
  - 其余写法不支持，类定义时的检查只是尽力而为的提醒；点名的不支持做法有改 model_config（extra、strict、别名开关）、computed_field、用校验器或序列化器改键名、单独设 validation_alias。
  - 原先那段把规则一条条写在一起的说明已拆进这一小节；Python 包 README 改为一句话指向它。现有检查全部保留，没有新增针对这几类绕法的检查。
- 2026-11-27 检查：`pnpm check` 退出码 0。TS 11 个测试；Python 1286 个测试；类型解析与产物检查通过。另用 Python 3.10.20、pydantic 2.11.10、FastAPI 0.140.7 装本机构建的 wheel，1286 个测试全部通过。README 的 Python 片段原样运行通过。本批不发版。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：
  - 「导出即定义，子类只能收紧」一条改为先写口径（包自己的模型硬保证，子类只保证 README 明列的写法，其余不支持），再写检查。
  - 补上列表顶层不得新增写作 false 的字段，以及 QueryInt。
  - 移出的历史内容：无。
- 收工。

## 交付清单

- df1fa3b：二、三的实现与测试。
- 4c0a6a1：README（一、三）。
- 归档提交：快照与本批归档。
