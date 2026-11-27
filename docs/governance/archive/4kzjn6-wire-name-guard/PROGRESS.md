---
id: 4kzjn6
title: 包体结构的子类不得改线上字段名
modules: [pypi-package]
created: 2026-11-27
source: 甲方当轮下发（fkd941 评审复核）
after: ""
---

# 包体结构的子类不得改线上字段名

单批次，串首即串末。条目 `hiv0gy`。

范围：只改、只提交，不单独发版，并进下一个预发布版。不改导入路径和已有名字。

共享骨架独占：无。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 包体结构的子类改线上字段名时明确报错并指出字段 | 完成 | f780aec |
| ⓑ | 查询参数模型改名保持现状，补 CursorListRequest 测试 | 完成 | f780aec |
| ⓒ | README 写明只有查询参数模型可以按前缀改名 | 完成 | ea6f2c3 |
| ⓓ | 四个带按名引用的结构各一例改名被拒 | 完成 | f780aec |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `fkd941` 已归档（dd7af87）。
- 2026-11-27 ⓐ 在类定义时报错。基类 `SchemaModel.__pydantic_init_subclass__` 调用 `_source.check_wire_names`。理由：写错的子类导入时就失败，不会等到第一次校验或导出才暴露；而且只检查一次。
  - 比较的内容：每个已有字段的实际线上名，即「校验时认的名字」与「输出时用的名字」。前者取 validation_alias，否则 alias，关掉 validate_by_alias 时取字段名；后者取 serialization_alias，否则 alias，关掉 serialize_by_alias 时取字段名。与生成类不同就算改名。所以 alias、validation_alias（含 AliasChoices / AliasPath）、serialization_alias、alias_generator，以及关掉这两个配置，都会被拦下。
  - 报 TypeError，写明子类名、结构名、字段名和定义里的线上名。
  - 放行条件：源定义带 `x-paramPrefix` 的（PagedListRequest、CursorListRequest）照旧可以改名。收紧、加默认、继承参数化泛型都不改线上名，不受影响。
- 2026-11-27 ⓑⓓ 测试（`python/tests/test_subclass.py`）：
  - ⓓ：ErrorField 设 alias、ServiceErrorCode 设 serialization_alias、PagedListPage 用 alias_generator、CursorListCursor 设 validation_alias，各一例被拒；另有 ErrorField 关掉 serialize_by_alias 一例。
  - ⓑ：新增游标式查询参数模型 `OrderCursorQuery`。导出键为 `cursor.after`、`cursor.limit`（limit 取交集 1–50）；OpenAPI 参数名正确；实际请求返回 200 与 422；8 个值纳入「导出与运行时同结论」的逐值对照。
- 2026-11-27 检查：`pnpm check` 退出码 0。TS 11 个测试；Python 769 个测试；构建产物与 wheel / sdist 检查通过。另用 Python 3.10.20 加 pydantic 2.11.10 装本机构建的 wheel，769 个测试全部通过。本批不发版。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：「导出即定义，子类只能收紧」一条里，「改线上字段名时按新名字」改为「只有查询参数模型可以按前缀改线上名，包体结构的子类改名在类定义时报错」。移出的历史内容：无。
- 收工。

## 交付清单

- f780aec：包体结构的子类不得改线上字段名，以及测试。
- ea6f2c3：README。
- 归档提交：快照与本批归档。
