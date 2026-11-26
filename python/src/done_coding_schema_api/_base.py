"""生成模型的基类与整数类型（手写，生成器以 --base-class 引用，生成的整数字段用 JsonInt）。"""

from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    GetJsonSchemaHandler,
    Strict,
    ValidationError,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, InitErrorDetails, PydanticCustomError

from ._source import (
    adopt_source_integers,
    integral_float_to_int,
    source_constraint_errors,
    source_json_schema,
)

Loc = tuple[str | int, ...]


class ConstraintErrors:
    """收集手写校验发现的出错项，一次抛出；每项的位置指到具体字段。

    在校验器里抛出的 ValidationError 原样上传，外层模型会在位置前加上自己的路径，
    如嵌在成功外壳里的页码式列表报 ("data", "page", "totalPage")。
    """

    def __init__(self, title: str) -> None:
        self._title = title
        self._errors: list[InitErrorDetails] = []

    def add(self, loc: Loc, error_type: str, message: str, value: Any) -> None:
        self._errors.append(
            InitErrorDetails(
                type=PydanticCustomError(error_type, message),
                loc=loc,
                input=value,
            )
        )

    def raise_if_any(self) -> None:
        if self._errors:
            raise ValidationError.from_exception_data(self._title, self._errors)


JsonInt = Annotated[int, BeforeValidator(integral_float_to_int), Strict()]
"""定义里 type: integer 的字段。

与 JSON Schema 的 integer 一致：接受整数与值为整数的浮点（12.0 → 12）；12.5、
字符串 "12"、布尔仍拒绝。Strict() 让它在不继承基类配置的 RootModel 里也一样严格。
使用方在子类里重新声明整数字段时也用它，如 ``pageSize: JsonInt = Field(default=20, le=50)``。
"""


class SchemaModel(BaseModel):
    """所有生成模型的基类。

    - strict：不做 "10" → 10、"true" → True 这类类型转换，与定义的类型约束一致；
    - extra="allow"：定义里未声明 additionalProperties 的对象（三种列表的顶层）
      保留接口自己声明的附带字段；声明了 additionalProperties: false 的模型由生成的
      model_config 覆盖为 forbid；
    - serialize_by_alias / validate_by_name：输出用线上字段名（如 ErrorField 的 in），
      Python 里也可以用字段名（in_）构造；
    - 导出的 JSON Schema（model_json_schema()、FastAPI 生成的 OpenAPI）是源定义加子类的改动；
      子类重新声明的字段仍要满足源定义，见 _source。
    """

    model_config = ConfigDict(
        strict=True,
        extra="allow",
        serialize_by_alias=True,
        validate_by_name=True,
    )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return source_json_schema(cls, core_schema, handler)

    @model_validator(mode="before")
    @classmethod
    def _reject_null_for_optional(cls, data: Any) -> Any:
        """可选字段在定义里都不可为 null：不需要时省略，不接受显式 null。

        生成工具把可选字段写成 `X | None = None`，会放过显式 null；这里补上。
        """
        if isinstance(data, dict):
            errors = ConstraintErrors(cls.__name__)
            for name, field in cls.model_fields.items():
                if field.is_required():
                    continue
                for key in sorted({name, field.alias or name}):
                    if key in data and data[key] is None:
                        errors.add(
                            (key,),
                            "null_forbidden",
                            "不能为 null；不需要时省略该字段",
                            None,
                        )
            errors.raise_if_any()
        return data

    @model_validator(mode="before")
    @classmethod
    def _adopt_source_integers(cls, data: Any) -> Any:
        """子类重新声明的整数字段沿用 JsonInt 的语义（12.0 → 12），见 _source。"""
        return adopt_source_integers(cls, data)

    @model_validator(mode="after")
    def _keep_source_constraints(self) -> Any:
        """子类重新声明的字段仍要满足源定义（子类只能收紧，不能放宽），
        与导出的结构（源定义与新声明的交集）同结论。"""
        errors = ConstraintErrors(type(self).__name__)
        for wire, detail in source_constraint_errors(self):
            errors.add(
                (wire, *detail["loc"]),
                detail["type"],
                f"不满足定义对该字段的约束：{detail['msg']}",
                detail["input"],
            )
        errors.raise_if_any()
        return self
