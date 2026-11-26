# @done-coding/schema-api

```
跨前后端通用接口结构的类型、常量与定义文件
```

成功外壳、错误体、三种列表（一次性 / 页码式 / 游标式）、列表请求参数与业务码的 TypeScript 类型与 JSON Schema 定义文件，由同一份定义生成；同版本的 Python 包为 PyPI 上的 `done-coding-schema-api`。

两个出口：主入口 `@done-coding/schema-api` 只有结构（类型、成功码、结构定义文件）；通用失败码与码表、字段路径与参数名、参考数值在 `@done-coding/schema-api/reference`，只是参考，不随结构生效，要用须显式引入。

## 使用

```bash
npm install @done-coding/schema-api
```

```ts
import type { PagedList, SuccessEnvelope } from "@done-coding/schema-api";
import { PAGED_LIST_REQUEST_PARAMS } from "@done-coding/schema-api/reference";

interface User {
  id: string;
  name: string;
}

declare const response: SuccessEnvelope<PagedList<User>>;
response.data.page.totalRecord; // number
PAGED_LIST_REQUEST_PARAMS.pageSize; // "page.pageSize"
```

结构定义文件以 `schemas` 导出，参考资源定义文件以 `referenceSchemas` 从 `./reference` 导出，也可按路径取：`@done-coding/schema-api/schemas/<结构名>.schema.json`。

各结构的说明、怎么选列表、业务码与版本规则见仓库 README：<https://github.com/done-coding/done-coding-schema#readme>
