---
id: fa959d
title: 包内置的码与数值不成为隐式默认；结构与参考资源分两层出口
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-27
parent: ""
---

# 包内置的码与数值不成为隐式默认

原则（维护者定）：使用方只引入结构时，不受任何内置的码或数值约束；要用内置的那组须显式引入。结构定义里不出现具体配置值。

- 两层出口：主入口只放结构；npm `./reference` 与 Python `done_coding_schema_api.reference` 放通用码、码表、路径与参数名常量、码表定义文件、参考数值。主入口不再导出它们，不留别名；两种语言各一条测试核对。
- 清理：页码式请求 page / pageSize 的 default、pageSize 与响应 pageSize、游标 limit 的 maximum 100；专有码不再自动排除通用码（OK 与 `HTTP_<数字>` 保留），改由参考资源出口的显式入口检查；码表 `default` 换成 x- 标注，「缺省值」改称「参考值」；`default_error_detail` 改名 `reference_error_detail` 移到参考资源出口。
- 缺陷：导出的 JSON Schema 反映使用方子类的改动与非参数化子类的元素类型；校验器去掉写死的 pageSize 上限。
- 样例与 README 同步；发第三个预发布版。
