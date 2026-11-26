# Change Log

All notable changes to this project will be documented in this file.
See [Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [0.0.1-alpha.2](https://github.com/done-coding/done-coding-schema/compare/@done-coding/schema-api@0.0.1-alpha.1...@done-coding/schema-api@0.0.1-alpha.2) (2026-11-26)

- feat!: 包内置的码与数值不再成为隐式默认，结构与参考资源分两个出口 ([d13195e](https://github.com/done-coding/done-coding-schema/commit/d13195ebf0fbe309793d29f5c33c31cc6bea3c74))

### BREAKING CHANGES

- COMMON_ERROR_CODES、CommonErrorCode、
  COMMON_ERROR_CODE_TABLE 与六组路径、参数名常量只能从参考资源出口
  导入；default_error_detail 改名 reference_error_detail；pageSize、
  limit 超过 100 与专有码使用通用码名不再被拒；PagedListRequest 的
  page、pageSize 缺失时不再填 1 和 10。

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## [0.0.1-alpha.1](https://github.com/done-coding/done-coding-schema/compare/@done-coding/schema-api@0.0.1-alpha.0...@done-coding/schema-api@0.0.1-alpha.1) (2026-11-26)

### Features

- 通用失败码的 retryable 与 outcome 改为缺省值，错误体可以覆盖 ([f4b57ea](https://github.com/done-coding/done-coding-schema/commit/f4b57ea25139b2c794e44a4101c1ff0827849ef1))
- 页码式列表的 items 条数不超过 pageSize 与 totalRecord ([c97c37c](https://github.com/done-coding/done-coding-schema/commit/c97c37cce6bacf13f178b80b565053c7e926544d))

## 0.0.1-alpha.0 (2026-11-26)

### Features

- 发布流程同时构建上传 npm 与 Python 包，补齐接入说明 ([8c3ffd1](https://github.com/done-coding/done-coding-schema/commit/8c3ffd1a78f9546ec1049751a01d47348d125068))
- 由定义生成 TS 类型、常量与定义模块，npm 包导出它们 ([9a7a90f](https://github.com/done-coding/done-coding-schema/commit/9a7a90f7f4bb4397d78243f9df7e5a1790a09ec3))
