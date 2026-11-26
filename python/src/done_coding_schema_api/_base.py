"""生成模型的基类与整数类型（手写，生成器以 --base-class 引用，生成的整数字段用 JsonInt）。"""

from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    GetJsonSchemaHandler,
    RootModel,
    Strict,
    ValidationError,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, InitErrorDetails, PydanticCustomError

from ._definitions import bundled_schema, source_of

Loc = tuple[str | int, ...]

_GENERATED_MODULES = f"{__package__}._generated."


def source_json_schema(
    model: type[BaseModel], core_schema: CoreSchema, handler: GetJsonSchemaHandler
) -> JsonSchemaValue:
    """模型导出的 JSON Schema = 对应的源定义（展开引用后原样带出，x- 约束一并保留）。

    - 沿继承链找到生成的类，按类名（即定义的 title）定位源定义；找不到则用 pydantic 的默认结果；
    - 泛型已给类型参数时，``__schema_type_params__`` 列出的字段（items 的元素、data）
      换成类型参数生成的结构；
    - 子类另外声明、源定义里没有的字段，按 pydantic 的默认结果补进 properties。
    """
    source = next(
        (
            located
            for klass in model.__mro__
            if klass.__module__.startswith(_GENERATED_MODULES)
            and (located := source_of(klass.__name__)) is not None
        ),
        None,
    )
    if source is None:
        return handler(core_schema)
    schema = bundled_schema(*source)
    properties = schema.get("properties", {})
    typed = (
        getattr(model, "__schema_type_params__", ())
        if getattr(model, "__pydantic_generic_metadata__", {}).get("args")
        else ()
    )
    # RootModel 的 root 是整体本身，不是字段。
    declared = (
        []
        if issubclass(model, RootModel)
        else [field.alias or name for name, field in model.__pydantic_fields__.items()]
    )
    extra = [name for name in declared if name not in properties]
    if not typed and not extra:
        return schema
    default = handler.resolve_ref_schema(handler(core_schema))
    generated = default.get("properties", {})
    for name in typed:
        if name == "items":
            properties["items"] = {
                **properties["items"],
                "items": generated["items"]["items"],
            }
        else:
            description = properties[name].get("description")
            properties[name] = {
                **({"description": description} if description else {}),
                **generated[name],
            }
    for name in extra:
        schema.setdefault("properties", properties)[name] = generated[name]
        if name in default.get("required", []):
            schema.setdefault("required", []).append(name)
    return schema


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
      Python 里也可以用字段名（in_）构造；
    - 导出的 JSON Schema（model_json_schema()、FastAPI 生成的 OpenAPI）就是源定义，
      见 source_json_schema。
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
