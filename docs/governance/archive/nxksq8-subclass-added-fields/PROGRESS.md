---
id: nxksq8
title: 子类新增字段按源定义的开放性处理；查询参数的裸名不静默丢弃
modules: [pypi-package]
created: 2026-11-27
source: 甲方当轮下发（alpha.3 评审）
after: ""
---

# 子类新增字段按源定义的开放性处理；查询参数的裸名不静默丢弃

单批次，串首即串末。条目 `2flbmi`。

范围：只改、只提交，不单独发版，与使用方复跑意见合成下一个预发布版。不改导入路径和已有名字。筛选参数本单不动（下发方定）。

共享骨架独占：无。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 子类新增字段：封闭结构类定义时报错；开放结构导出与运行时同结论；查询参数模型只可加前缀外字段 | 完成 | 59e0788、39c23e2 |
| ⓑ | 查询参数里与字段同名的裸名报错并指出线上名；与前缀外字段重名时类定义报错 | 完成 | 59e0788、39c23e2 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `sr81xt` 已归档（63a4997）。
- 2026-11-27 定义的开放性（实查）：只有三种列表的顶层（BoundedList、PagedList、CursorList）没写 additionalProperties，允许附带字段；其余结构（成功外壳、错误体及 ErrorDetail / ErrorField、PagedListPage、CursorListCursor、专有码清单及其项、两份请求参数、筛选参数）都写了 `additionalProperties: false`。
- 2026-11-27 ⓐ：`_source.check_added_fields` 在类定义时检查（基类 `__pydantic_init_subclass__` 调用，与改名检查并列）：
  - 封闭结构：子类新增字段报 TypeError，写明子类、结构名和新增的字段，并说明只有三种列表顶层允许附带字段。
  - 开放结构：可以新增。导出把新字段按 pydantic 的结果补进 properties，必填的进 required；运行时 extra=allow，新字段按声明校验。
  - 查询参数模型：线上名在本前缀下的新字段报 TypeError；线上名与本模型字段裸名相同的也报 TypeError，提示应写的线上名。
  - 前缀外字段（自定）：别名生成器改为只给定义里的字段加前缀，子类另加的字段线上名就是字段名，不必写别名。
- 2026-11-27 ⓐ 的查询参数部分：
  - 解码时，前缀外的新字段按线上名原样收取，交给它自己的声明校验，不走前缀与整数解码；FastAPI 参数说明的替换也只作用于定义里的字段。
  - 查询串的值都是字符串，而基类是严格类型，所以前缀外的整数参数要写 `Field(strict=False)`。README 与测试都按这个写法（`minAmount: Annotated[int | None, Field(strict=False, ge=0)] = None`）。
  - 这也解决了 FastAPI 旧版本「查询参数模型须是接口唯一查询参数」的限制：把接口的其他查询参数都声明在这个子类里。
- 2026-11-27 ⓑ：解码时，与本模型字段同名的裸名报 `bare_parameter_name`，位置 `(裸名,)`，信息「pageSize 应写作 page.pageSize」；其余前缀外、不同名的参数照旧忽略。直接构造（`PagedListQuery(pageSize=5)`）走同一个校验器，同样报错。
- 2026-11-27 测试：
  - `test_subclass.py`：ErrorBody、ErrorField、PagedListPage 加字段被拒；列表顶层加 `summary`，再套成 `SuccessEnvelope[PagedList[SummaryPage]]` 三层，8 个值用 jsonschema 拿导出判与运行时同结论，导出里 summary 与 note 都在。
    - 注：测试里使用方自己的 `Summary` 模型设为严格；宽松的 pydantic 模型会把 "1" 转成 1，与任何 JSON Schema 都不同结论，这是使用方模型的性质，不是包的。
  - `test_query.py`：
    - 六个裸名在 model_validate 与直接构造下都报错并给出线上名；
    - 前缀内新字段与裸名同名的新字段被拒；
    - 前缀外新字段可用：`OrderSearchQuery` 加 `status` 与 `minAmount`。实测 OpenAPI 参数名是四个线上名加 status、minAmount，pageSize 说明为 1–50 且没有 anyOf；`page.page=2&status=paid&minAmount=100` 返回 200；`minAmount=abc`、`-1`、`page.pageSize=51`、`pageSize=10`、`page.foo=1` 都返回 422。
  - FastAPI 0.162.5 与 0.140.7 下都通过。
- 2026-11-27 检查：`pnpm check` 退出码 0。TS 11 个测试；Python 1268 个测试；类型解析与产物检查通过。另用 Python 3.10.20、pydantic 2.11.10、FastAPI 0.140.7 装本机构建的 wheel，1268 个测试全部通过。本批不发版。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：
  - 「导出即定义，子类只能收紧」一条补上：新增字段以源定义的开放性为准；查询参数模型只可加前缀外字段；裸名报错。
  - pypi-package 一行的 `_query.py` 说明补上裸名与前缀外字段。
  - 移出的历史内容：无。
- 收工。

## 交付清单

- 59e0788：实现与测试。
- 39c23e2：README。
- 归档提交：快照与本批归档。
