# done-coding-schema-api

跨前后端通用接口结构的 Pydantic 模型：成功外壳、错误体、三种列表（一次性 / 页码式 / 游标式）、列表请求参数与业务码，由与 npm 包 `@done-coding/schema-api` 同一份 JSON Schema 定义生成，两包同版本。

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

模型是严格类型的，结构里的跨字段约束（如 `totalPage` 等于 `ceil(totalRecord / pageSize)`）也已包含在内；校验报错指到具体字段。`model_json_schema()` 与 FastAPI 生成的 OpenAPI 导出的就是定义本身；子类重新声明字段只能收紧，导出的是定义与子类声明的交集，运行时同样两者都检查；包体结构的子类不能改线上字段名，只有查询参数模型可以按前缀改名；不要用校验器或序列化器自己改线上键名，导出不会反映。子类里的整数字段用 `JsonInt`（认 `12` 与 `12.0`）。包里另带 JSON Schema 定义文件：`schema_path("error-body")` 取路径，`load_schema("error-body")` 取已解析的字典。

包顶层只有结构。通用失败码与码表、字段路径与参数名、参考数值（每页条数等）、参考资源定义文件在子模块 `done_coding_schema_api.reference`：只是参考，不随结构生效，要用须显式引入，如 `from done_coding_schema_api.reference import COMMON_ERROR_CODES`。

各结构的说明、怎么选列表、业务码与版本规则见仓库 README：<https://github.com/done-coding/done-coding-schema#readme>
