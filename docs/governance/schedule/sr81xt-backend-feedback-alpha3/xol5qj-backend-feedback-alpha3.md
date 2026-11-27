---
id: xol5qj
title: 后端接入意见四条与 reference 子路径的 node10 类型解析
modules: [definition, toolchain, npm-package, pypi-package]
created: 2026-11-27
parent: ""
---

# 后端接入意见四条与 reference 子路径的 node10 类型解析

- ⓐ 以 $ 收尾的 pattern 在 Python 的 re 下放过结尾换行，定义在 Python jsonschema 下比模型松。要求同一份定义在 Ajv、Python jsonschema、包的模型下对全部样例同结论，并把 jsonschema 加为第三个裁判。
- ⓑ 两条条数检查共用 items_exceed_page，拆成两个错误类型，旧名不保留。
- ⓒ 子类覆盖嵌套模型字段后导出写重、required 顺序变了。
- ⓓ 包内置页码式与游标式的查询参数模型：线上名固定为「前缀.原名」，整数解码规则写死并写进定义，可继承收紧，FastAPI 下 OpenAPI 干净。
- ⓔ "./reference" 在 TypeScript moduleResolution "node" 下解析不到类型。
