"""生成模型的基类与整数类型（手写，生成器以 --base-class 引用，生成的整数字段用 JsonInt）。"""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Strict, model_validator


def _integral_float_to_int(value: Any) -> Any:
    """值为整数的浮点（JSON 里的 12.0）按 JSON Schema 算整数，归一成 int。"""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


JsonInt = Annotated[int, BeforeValidator(_integral_float_to_int), Strict()]
"""定义里 type: integer 的字段。

与 JSON Schema 的 integer 一致：接受整数与值为整数的浮点（12.0 → 12）；12.5、
字符串 "12"、布尔仍拒绝。Strict() 让它在不继承基类配置的 RootModel 里也一样严格。
"""


class SchemaModel(BaseModel):
    """所有生成模型的基类。

    - strict：不做 "10" → 10、"true" → True 这类类型转换，与定义的类型约束一致；
    - extra="allow"：定义里未声明 additionalProperties 的对象（三种列表的顶层）
      保留接口自己声明的附带字段；声明了 additionalProperties: false 的模型由生成的
      model_config 覆盖为 forbid；
    - serialize_by_alias / validate_by_name：输出用线上字段名（如 ErrorField 的 in），
      Python 里也可以用字段名（in_）构造。
    """

    model_config = ConfigDict(
        strict=True,
        extra="allow",
        serialize_by_alias=True,
        validate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_null_for_optional(cls, data: Any) -> Any:
        """可选字段在定义里都不可为 null：不需要时省略，不接受显式 null。

        生成工具把可选字段写成 `X | None = None`，会放过显式 null；这里补上。
        """
        if isinstance(data, dict):
            for name, field in cls.model_fields.items():
                if field.is_required():
                    continue
                for key in {name, field.alias or name}:
                    if key in data and data[key] is None:
                        raise ValueError(f"{key} 不能为 null；不需要时省略该字段")
        return data
