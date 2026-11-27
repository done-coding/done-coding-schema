---
id: sr81xt
title: 后端接入意见修正与第四个预发布版
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-27
source: 甲方当轮下发（后端使用方按 0.0.1a2 接入的意见；前端使用方追加一条）
after: ""
---

# 后端接入意见修正与第四个预发布版

单批次，串首即串末。条目 `xol5qj`。

授权：维护者在本会话确认「按派单全部改」（规则 8：pattern 改写、错误类型改名）与「授权发第四个预发布版」（npm `0.0.1-alpha.3` 标签 alpha、PyPI `0.0.1a3`）；推送由维护者本人做。这一版同时带上已提交未发布的 fkd941、4kzjn6、mlijyx 三批。

不变：导入路径与已有名字（ⓑ 的错误类型名除外）；orderBy 不写方向即 asc 保留。

共享骨架独占：仓根 `package.json`、`pnpm-lock.yaml`。

## 任务

| 序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| ⓐ | 定义的 pattern 在 Ajv、Python jsonschema、包的模型下同结论；jsonschema 作第三个裁判 | 完成 | f1b128a |
| ⓑ | items_exceed_page 拆成 items_exceed_page_size / items_exceed_total_record | 完成 | f1b128a |
| ⓒ | 子类覆盖嵌套模型字段后导出不写重，required 顺序不变 | 完成 | f1b128a |
| ⓓ | 内置页码式与游标式查询参数模型，解码规则写进定义 | 完成 | f1b128a、c1d8522 |
| ⓔ | typesVersions：moduleResolution node 下取得到 ./reference 的类型 | 完成 | 5bd1784 |
| 发布 | 第四个预发布版：检查、构建、上传、线上核对 | 完成 | 1948a40，见进度记录 |
| 收口 | 快照、归档。收工 | 完成 | 归档提交 |

## 进度记录

- 2026-11-27 承接：上一批 `mlijyx` 已归档（8ad25c6）。
- 2026-11-27 npm 标签（维护者定）：预发布版只上 alpha 标签，发布命令显式带 `--tag alpha`，不挪 latest，与 `.github/workflows/` 一致（预发布工作流 `--dist-tag alpha`，只有正式版工作流设 latest）。下发方曾转达「每个预发布版都挪 latest」，维护者先同意，随后核对工作流后否决，以后者为准。latest 仍是首次发布时自动设上的 0.0.1-alpha.0，npm 不能删 latest，等正式版接管。
- 2026-11-27 ⓐ 做法：改写定义里的 pattern，让各方言都表示同一个意思（不走「包提供校验函数」的退路）。理由：定义是唯一来源，应当可移植，使用方拿任何 2020-12 校验器直接判都该得到同样结论。
  - 结尾锚点：所有以 `$` 收尾的 pattern（含 patternProperties 的键、`not` 里的 `^HTTP_[0-9]+$`）改为 `$(?![\s\S])`。ECMA-262 下与 `$` 同义；Python 的 re 下不再放过结尾换行。
  - 空白（自加，同一类可移植问题）：`\S` 在三种引擎下不一致。U+001C 到 U+001F 在 Python 的 re 下算空白，U+0085 在 Python 与 Rust 下算空白，U+FEFF 只在 ECMA-262 下算空白。所以改成按 ECMA-262 列明的显式字符类 `[^\t\n\v\f\r    -     　﻿]`。三种引擎实测结论一致；可接受的值以 ECMA-262 为准，与此前 Ajv 的判定相同。
  - 生成模型：pydantic 默认的 Rust 正则引擎不支持前瞻（实测编译报错），而它的 `$` 本来就只匹配文本结尾。所以生成器（`gen-python.mjs` 的 `toModelPattern`）把结尾的 `$(?![\s\S])` 换回 `$`，其余一字不差；剩下任何前瞻或后顾都直接报错。TS 类型不带 pattern，不受影响。
  - 一致性测试：`python/tests/test_patterns.py` 核对生成模型的 pattern 恰为定义的 pattern 只换了结尾锚点；对每个 pattern 取 10 个边界值，比较 Python re 按定义写法判与 Rust 引擎按生成写法判，结论都相同。
  - 第三个裁判：`python/tests/test_examples.py` 用 jsonschema 拿包里的定义文件直接判全部样例。通用校验器不认 x- 检查关键字，所以只因 x- 被拒的样例，它判合法才算一致；另有一条测试确认放宽的只落在页码式列表与专有码清单。
  - 样例新增：列表筛选字段名末尾换行、`HTTP_<数字>` 加末尾换行两个反例；requestId 含 U+FEFF、message 只有 U+FEFF 两个反例；requestId 含 U+001C、message 只有 U+0085 两个合法例。其余以 `$` 收尾的字段原本就有「末尾换行」反例。
  - `models.py` 的保留码检查改为 `fullmatch`，不再借 `$` 判结尾。
- 2026-11-27 ⓑ：Python 的错误类型拆为 `items_exceed_page_size` 与 `items_exceed_total_record`，旧名不保留。定义校验器的 `x-itemsWithinPage` 报错在 params 里加 `errorType`，取同样的两个名字；5 个相关样例的预期 params 写上 errorType，Python 测试逐例核对报的类型与之相同。
- 2026-11-27 ⓒ：
  - 复现确认写重：`page` 同时带指向子类的 `$ref` 和整份原定义。
  - 修法：子类把嵌套模型字段换成原模型的子类时，只引用子类的导出（子类本身就是交集），保留原字段的说明；换成无继承关系的模型时仍取交集，不能只引用它，否则会比定义宽。
  - required 一律按源定义的顺序重建，子类另加的排在后面。
  - 测试断言：`page` 只有 `$ref` 与 `description` 两个键；子类定义里 `maximum: 100`、`minimum: 1`、`x-totalPageEqualsCeil` 都在；required 顺序与源定义一致；套进 SuccessEnvelope 后同样成立；首个必填字段被收窄时顺序不变；导出与运行时逐值同结论。
- 2026-11-27 ⓓ：
  - 新模块 `python/src/done_coding_schema_api/_query.py`，新增 `PagedListQuery`、`CursorListQuery`，从包顶层导出。规则全部取自定义：
    - 前缀取 `x-paramPrefix`；
    - 整数参数取 type 为 integer 的字段；
    - 整数写法取定义里新增的标注 `x-queryIntegerPattern`（`^(?:0|[1-9][0-9]*)$(?![\s\S])`），定义的说明里写明「02、+2、空格、2.0、1e1、空串都不合法」。
  - 解码：before 校验器只取本前缀下的参数，前缀外的忽略；整数串整串匹配才转成 int，不合写法的原样留给严格类型拒绝。前缀下未声明的参数由 extra forbid 报 `extra_forbidden`；裸名不收（被忽略）。
  - 继承收紧：别名生成器与解码都可继承，子类重新声明字段即可，如 `pageSize: JsonInt = Field(default=20, le=50)`。
  - OpenAPI：FastAPI 把查询参数模型逐字段展开，用的是字段自己的声明。所以在类定义时，把每个字段的 `json_schema_extra` 设成「整体换成导出结构里的那一项」，这一项是定义与子类声明的交集。这个改动标成只改参数说明，不算重新声明。
  - 发现并修掉 fkd941 留下的问题：只改了别名的字段原先被当成重新声明，导出里叠进 pydantic 为 `X | None` 生成的 `anyOf`/null 和原样的 `ge`。现在只改名不算重新声明；新声明的结构先规整再求交集：去 null 分支，单分支展开，`ge`/`le` 等原样约束名换成 `minimum`/`maximum` 等，`default: null` 不写。另外让交集认出生成模型里换了结尾锚点的 pattern 与定义是同一个。
  - FastAPI 实测：
    - `?page.page=2&page.pageSize=20` 返回 200，值为 int；
    - OpenAPI 参数名是线上名，参数说明逐项等于定义（去掉 title），子类的写成 `minimum: 1`、`maximum: 50`、`default: 20`；
    - 全部参数里没有 `ge`、`le`、`anyOf`；
    - `02`、`+2`、`2.0`、空串、0、`page.limit` 都返回 422。
    - 在 FastAPI 0.162.5 与使用方用的 0.140.7 下都通过。0.140.7 有一处限制：查询参数模型要是接口唯一的查询参数才会展开；与其他查询参数并存时，整个模型会被当成一个名为 `params` 的参数。README 已写明，测试也不再混用。
  - README 的查询参数一节改为只讲内置模型，手写 alias_generator 加 before 校验器的示例已删。
  - ⓓ⑥ 筛选参数现状（本单不改）：
    - 线上名 `filter.<字段>.<操作>` 要映射成嵌套对象 `{字段: {操作: 值}}`，包里没有现成的查询参数模型。FastAPI 也展开不了这种键是动态的 RootModel。
    - 查询串里的值都是字符串，而定义允许 eq 为字符串、数字或布尔，又没有解码规则：`filter.count.eq=3` 只会是字符串 "3"，数字和布尔在查询串里表达不出来。
    - 顺带发现：`ListFilter` 的 eq 传整数 3 会输出成 3.0（生成成了浮点）。
- 2026-11-27 ⓔ：
  - `packages/api/package.json` 加 `typesVersions: {"*": {"reference": ["types/reference.d.ts"]}}`。不加时 node10 复现 TS2307，加后通过。
  - 自加：exports 的 require 条件改配 `.d.cts` 声明，由 vite-plugin-dts 的 afterBuild 照抄 `.d.ts` 生成。原因是本包是 `"type": "module"`，`.d.ts` 一律按 ES 模块解读，node16 下的 CommonJS 使用方原先会报 TS1479。属纯新增，import 条件与主入口不变。
  - 新检查 `scripts/check-type-resolution.mjs`：在临时空项目里按 node10、node16（CommonJS）、node16（ES 模块）、bundler 各跑一次 tsc，从主入口和 `/reference` 取 `PAGED_LIST_REQUEST_PARAMS.pageSize` 等字面量类型，已并入 `pnpm check:bundle`。
  - 另记：声明文件里用了 `Iterable`，使用方的 lib 需要 ES2015 以上（不开 skipLibCheck 时）。
- 2026-11-27 发布前检查：`pnpm check` 退出码 0。
  - 样例：合法 108、不合法 213，约束 154 条全覆盖。
  - 测试：TS 11 个；Python 1245 个，其中 jsonschema 裁判 321 例，pattern 对照 102 例。
  - 构建与类型解析检查通过。
  - 另用 Python 3.10.20 加 pydantic 2.11.10 加 FastAPI 0.140.7 装本机构建的 wheel，1245 个测试全部通过。
- 2026-11-27 发布（按 `docs/release.md`「本机发布」）：
  - 定版本：npm 0.0.1-alpha.2 → 0.0.1-alpha.3，Python 0.0.1a2 → 0.0.1a3；版本提交 1948a40，标签 `@done-coding/schema-api@0.0.1-alpha.3`。在版本提交上再跑 `pnpm check`，退出码 0。
  - 仓外构建：npm 22 个文件，新增 `types/index.d.cts`、`types/reference.d.cts`，package.json 带 typesVersions；wheel 与 sdist 各含 11 份定义与 LICENSE，wheel 含 `_query.py`。三个包解开后扫过，没有本机路径。
  - 上传：npm `+ @done-coding/schema-api@0.0.1-alpha.3`，命令显式带 `--tag alpha`；PyPI 的 wheel 与 sdist 上传成功。令牌只经环境变量传入，npmrc 里只有占位，用完删除。
- 2026-11-27 线上核对：
  - npm dist-tags：`alpha` = 0.0.1-alpha.3，`latest` 仍是 0.0.1-alpha.0（按维护者决定不挪）；线上 shasum 与本机构建相同（b7151184…）。
  - PyPI 0.0.1a3，sha256 与本机构建相同（wheel c94b1f42…，sdist 0f8bab6a…）。
  - 空目录（npm @alpha，装到 0.0.1-alpha.3）：README 的 6 段 TS 在 bundler 下 tsc 通过；另建 moduleResolution node 的项目，从 `/reference` 取得到 `PAGED_LIST_REQUEST_PARAMS.pageSize` 的字面量类型，tsc 通过；ESM 与 CJS 的导出核对、Ajv 判派单各例都通过；Ajv 判 requestId 为 `r\n`、`r\ufeff` 都不合法。
  - 空目录（pip，`--prerelease allow` 装到 0.0.1a3，pydantic 2.14.4，另装 fastapi 0.162.5 与 jsonschema 4.26.0）：
    - 同一错误体，requestId 为 `r`、`r\n`、`r\ufeff` 时，jsonschema 拿 `load_schema` 的定义判与 `ErrorBody` 判结论相同（合法、不合法、不合法）；
    - 条数同时超两种上限时报 `items_exceed_page_size` 与 `items_exceed_total_record`；
    - `PagedListQuery` 解码 `page.page=2`、`page.pageSize=20` 为整数并忽略前缀外参数，`02`、`+2`、` 2`、`2.0`、`1e1`、空串全拒；
    - README 的 Python 片段原样运行通过，`OrderQuery` 的 OpenAPI 参数名为四个线上名，pageSize 的说明为 `minimum: 1`、`maximum: 50`、`default: 20`，不含 `anyOf` 与 `ge`。
- 2026-11-27 快照替换（`SNAPSHOT.md`）：
  - npm-package / pypi-package 两行：版本更新到 alpha.3 / a3，并写明 latest 不挪；pypi-package 补 `_query.py`。
  - toolchain 一行：补上类型解析检查与生成器的 pattern 转换。
  - 标注一条：补 `x-queryIntegerPattern`。
  - 「Python 与定义的一致性」一条：补 jsonschema 第三个裁判与 errorType。
  - 版本一条改为 alpha.3。
  - 技术基线：npm 构建补 d.cts 与 typesVersions；「正则一律按 ECMA-262 语义（`$` 只匹配文本末尾）」改为各方言同义的写法与生成器的转换。
  - 移出的历史内容：无。
- 收工。推送仍由维护者本人做：分支 `master`、`feat/schema-v0`，标签 `@done-coding/schema-api@0.0.1-alpha.0` 至 `0.0.1-alpha.3`。

## 交付清单

- f1b128a：ⓐⓑⓒⓓ（定义、生成器、校验器、Python 包与测试）。
- c1d8522：README。
- 5bd1784：ⓔ（typesVersions、d.cts、类型解析检查）。
- 5ab4d14：实现进度记录。
- 1948a40：版本提交（0.0.1-alpha.3 / 0.0.1a3）。
- 归档提交：快照与本批归档。

## 结果

- 第四个预发布版已在 npm（alpha）与 PyPI 发布，空目录各装一次验证通过。
