---
id: fkd941
title: alpha.2 评审跟进：子类约束与导出同结论、公开 JsonInt、查询参数线上名、保留码比对值
modules: [pypi-package, npm-package]
created: 2026-11-27
source: 甲方当轮下发（alpha.2 评审）
after: ""
---

# alpha.2 评审跟进

单批次，串首即串末。条目 `l6482g`。

范围：只改、只提交，不单独发版；与使用方意见合成下一个预发布版时由下发方通知。使用方按 alpha.2 接入，本批不改导入路径和已有名字，只允许新增。

共享骨架独占：无。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 子类重新声明的字段：导出与运行时同结论 | 完成 | af5ef7e |
| ⓑ | 公开 JsonInt，README 与测试示例改用它 | 完成 | af5ef7e、fbfd795 |
| ⓒ | 查询参数示例产出定义规定的线上参数名 | 完成 | af5ef7e（测试）、fbfd795（README） |
| ⓓ | 保留码检查两种语言都比对码的字符串值 | 完成 | a95e046 |
| ⓔ | 写明 orderBy 不写方向即 asc 是有意保留 | 完成 | 本文件与 af5ef7e 提交说明 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `5imv7n` 已归档（f2297f2）。
- 2026-11-27 ⓔ：页码式请求 orderBy「不写方向即 asc」有意保留——它是排序语法本身的含义，不是配置值，不属于「内置值不成为隐式默认」的清理范围（下发方定性）。
- 2026-11-27 ⓐ 选第一条路（源约束对子类仍强制生效，子类只能收紧）。理由：结构的约束不该被子类放宽；第二条路会让导出丢掉定义里的约束，使用方照导出实现的客户端反而比定义宽。代价在预期内：一个新模块，没有改动生成物和已有名字。
  - 新模块 `python/src/done_coding_schema_api/_source.py`：导出钩子与「重新声明的字段」判断都从 `_base.py` 移到这里，`_base.py` 只留基类、`JsonInt` 与报错收集。
  - 运行时：基类新增 after 校验器，把重新声明的字段值按线上形态转成 JSON，再用原字段的类型加约束（TypeAdapter）校验；出错位置为 `(线上字段名, …)`，错误类型沿用 pydantic 的（如 `greater_than_equal`）。
  - 导出：字段结构取源定义与新声明的交集。界（minimum / maximum / minLength 等）取更严者；说明类关键字用新声明的；其余取值冲突的关键字（如两份 pattern）放进 `allOf`；改了线上字段名时按新名字导出；是否必填按新声明。
  - 整数（自定）：源字段用了 `JsonInt` 的，子类即使写普通 `int`，也先把值为整数的浮点归一成 int（基类的 before 校验器）。否则 `12.0` 这一类值导出说合法、运行时却拒绝，而 JSON Schema 无法写出「整数但不能写成 12.0」。
  - 测试：`python/tests/test_subclass.py` 共 8 个子类、37 个值，用 jsonschema 4.26.0（新开发依赖，MIT，传递依赖都是 MIT）拿导出的结构逐值判，要求与模型结论相同；另断言放宽 `ge=0` 后仍拒绝 0、导出 `minimum: 1`，以及两份 pattern 落进 `allOf`、必填字段加默认后不再必填。原测试里没写 `ge=1` 却断言导出带 `minimum: 1` 的那条，现在与运行时一致了。
- 2026-11-27 ⓑ：`JsonInt` 加进包顶层 `__all__`，这是新增的名字；README、包 README 与测试示例都改用它。
- 2026-11-27 ⓒ 可行写法：
  - 子类设 `alias_generator=lambda name: PAGED_LIST_REQUEST_PARAMS[name]` 与 `validate_by_name=False`，再加一个 before 校验器，把 `page.page`、`page.pageSize` 的纯数字字符串解码成 int。原因是查询参数都是字符串，而模型是严格类型。
  - FastAPI 的 OpenAPI 参数名因此是 `page.page`、`page.pageSize`、`page.query`、`page.orderBy`。测试不加 HTTP 客户端依赖，直接调 ASGI 应用：合法请求返回 200；`pageSize` 为 0、51、abc，带 `page.limit`，用裸字段名 `pageSize`，都返回 422。
  - 导出钩子为此支持改名字段：按新线上名导出，约束仍是交集。
- 2026-11-27 ⓓ：两种语言都改为比对码的值，传映射或对象时取值。TS 用 `Symbol.iterator` 判断传进来的是不是可迭代集合，不是就取 `Object.values`。两边加同一组键值不同的数据（`MISSING` → `NOT_FOUND`）：结论都是命中 `NOT_FOUND` 和 `QUOTA_USED_UP`，不命中键名 `MISSING`。
- 2026-11-27 检查：`pnpm check` 退出码 0。样例结果不变；TS 11 个测试；Python 754 个测试；构建产物与 wheel / sdist 检查通过。另用 Python 3.10.20 加 pydantic 2.11.10 装本机构建的 wheel，跑全部 754 个测试，全部通过。README 的 Python 片段在本机原样运行通过。本批不发版。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：
  - `pypi-package` 一行补上 `_source.py`、`JsonInt` 顶层公开；
  - 「导出即定义」一条改为「导出即定义，子类只能收紧」，删去「已知限制：重新声明字段会替换原字段的校验」，改写查询参数一句；
  - 分层契约补上保留码检查比对的是码的值；
  - 技术基线的开发依赖补上 jsonschema。
  - 移出的历史内容：无。
- 收工。

## 交付清单

- af5ef7e：ⓐⓑⓒ 实现与测试（含开发依赖 jsonschema），提交说明写明 ⓔ。
- a95e046：ⓓ。
- fbfd795：README。
- 归档提交：快照与本批归档。
