# done-coding-schema-api

跨前后端通用接口结构的 Pydantic 模型与常量：成功外壳、错误体、三种列表（一次性 / 页码式 / 游标式）、列表请求参数与业务码，由与 npm 包 `@done-coding/schema-api` 同一份 JSON Schema 定义生成，两包同版本。

## 使用

```bash
pip install done-coding-schema-api
```

需要 Python 3.10 及以上、Pydantic v2（2.11 及以上）。

```python
from pydantic import BaseModel

from done_coding_schema_api import PagedList, SuccessEnvelope


class User(BaseModel):
    id: str
    name: str


UserPage = SuccessEnvelope[PagedList[User]]  # 可直接用作接口的返回类型
```

模型是严格类型的，结构里的跨字段约束（如 `totalPage` 等于 `ceil(totalRecord / pageSize)`）也已包含在内；校验报错指到具体字段。`model_json_schema()` 与 FastAPI 生成的 OpenAPI 导出的就是定义本身。包里另带全部 JSON Schema 定义文件：`schema_path("error-body")` 取路径，`load_schema("error-body")` 取已解析的字典。

各结构的说明、怎么选列表、业务码与版本规则见仓库 README：<https://github.com/done-coding/done-coding-schema#readme>
