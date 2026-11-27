"""查询参数模型：页码式与游标式请求参数按线上的查询串形态收取。

请求参数的定义（``PagedListRequest``、``CursorListRequest``）约束的是解码后的对象；
线上是 ``page.pageSize=20`` 这样的查询串。这里把「线上名」与「解码」写死一次，
规则都取自定义：

- 线上名：``<x-paramPrefix>.<字段名>``（如 ``page.pageSize``）；与字段同名的裸名报错并
  指出应写的线上名；前缀下未声明的参数不合法；其余参数不归它管，忽略；
- 整数：只收整串匹配定义里 ``x-queryIntegerPattern`` 的十进制数字串（``"02"``、``"+2"``、
  ``" 2"``、``"2.0"``、``"1e1"``、空串都不收），解码后再按定义的上下界校验；
- 导出：``model_json_schema()`` 与 FastAPI 为每个参数生成的说明都按定义写
  （``minimum`` / ``maximum``，可选参数不写成可为 null）。

使用方可以继承它声明自己的默认值与上限（子类只能收紧），不必再写别名与解码；接口自己的
其他查询参数也可以声明在子类里（线上名在前缀之外，按子类自己的声明校验）。
"""

import re
from collections.abc import Callable, Mapping
from copy import copy
from functools import cache
from typing import Any, NamedTuple

from pydantic import ConfigDict, model_validator

from ._base import ConstraintErrors, SchemaModel
from ._definitions import bundled_schema, source_of
from ._generated.cursor_list_request import CursorListRequest
from ._generated.paged_list_request import PagedListRequest
from ._source import _generated_class, describes_parameter


class _Rules(NamedTuple):
    """定义里的规则。"""

    prefix: str
    fields: frozenset[str]  # 定义里的字段名，也是它们的裸名
    integers: frozenset[str]  # 整数参数的线上名
    integer_text: re.Pattern[str]  # 整数串的写法


@cache
def _rules(title: str) -> _Rules:
    definition = bundled_schema(*source_of(title))  # type: ignore[misc]
    prefix = definition["x-paramPrefix"]
    properties = definition["properties"]
    return _Rules(
        prefix=prefix,
        fields=frozenset(properties),
        integers=frozenset(
            f"{prefix}.{name}"
            for name, prop in properties.items()
            if prop.get("type") == "integer"
        ),
        integer_text=re.compile(definition["x-queryIntegerPattern"]),
    )


def _wire_names_for(title: str) -> Callable[[str], str]:
    """定义里的字段加前缀；子类另加的前缀外字段保持原名。"""
    rules = _rules(title)
    return lambda name: f"{rules.prefix}.{name}" if name in rules.fields else name


def _replace_schema(target: dict[str, Any]) -> Callable[[dict[str, Any]], None]:
    def update(schema: dict[str, Any]) -> None:
        schema.clear()
        schema.update(target)

    return describes_parameter(update)


class _QueryParams(SchemaModel):
    """查询参数模型的公共部分：解码与每个参数的说明。"""

    @model_validator(mode="before")
    @classmethod
    def _decode_query(cls, data: Any) -> Any:
        """按线上名收取参数。

        - 本前缀下的参数照收（未声明的交给 extra forbid 拒绝），整数参数按定义的写法解码，
          不合写法的原样留给类型校验拒绝；
        - 子类另加的前缀外字段按它自己的声明收取，不走前缀与整数解码；
        - 与本模型字段同名的裸名（如 pageSize）报错并指出应写的线上名，不静默丢弃；
        - 其余参数不归它管，忽略。
        """
        generated_class = _generated_class(cls)
        if generated_class is None or not isinstance(data, Mapping):
            return data
        rules = _rules(generated_class.__name__)
        external = {
            field.alias or name
            for name, field in cls.__pydantic_fields__.items()
            if name not in rules.fields
        }
        errors = ConstraintErrors(cls.__name__)
        decoded: dict[str, Any] = {}
        for key, value in data.items():
            if not isinstance(key, str):
                continue
            if key in external:
                decoded[key] = value
            elif key.startswith(f"{rules.prefix}."):
                if (
                    key in rules.integers
                    and isinstance(value, str)
                    and rules.integer_text.search(value)
                ):
                    value = int(value)
                decoded[key] = value
            elif key in rules.fields:
                errors.add(
                    (key,),
                    "bare_parameter_name",
                    f"{key} 应写作 {rules.prefix}.{key}",
                    value,
                )
        errors.raise_if_any()
        return decoded

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        generated_class = _generated_class(cls)
        if generated_class is None:
            return
        # FastAPI 把查询参数模型逐字段展开成参数，用的是字段自己的声明；这里让定义里那些
        # 参数的说明就是导出结构里的那一项（定义与子类声明的交集）。子类另加的前缀外字段
        # 照它自己的声明。
        fields = _rules(generated_class.__name__).fields
        properties = cls.model_json_schema()["properties"]
        for name, field in list(cls.__pydantic_fields__.items()):
            if name not in fields:
                continue
            described = copy(field)
            described.json_schema_extra = _replace_schema(
                properties[field.alias or name]
            )
            cls.__pydantic_fields__[name] = described


class PagedListQuery(_QueryParams, PagedListRequest):
    """页码式列表的查询参数：``page.page``、``page.pageSize``、``page.query``、``page.orderBy``。

    FastAPI 里写 ``params: Annotated[PagedListQuery, Query()]``；要声明自己的每页条数，
    继承它并重新声明字段即可，如 ``pageSize: JsonInt = Field(default=20, le=50)``。
    接口自己的其他查询参数（如 ``status``）也声明在同一个子类里，线上名在前缀之外。
    """

    model_config = ConfigDict(
        alias_generator=_wire_names_for("PagedListRequest"),
        validate_by_name=False,
    )


class CursorListQuery(_QueryParams, CursorListRequest):
    """游标式列表的查询参数：``cursor.after``、``cursor.limit``。用法同 ``PagedListQuery``。"""

    model_config = ConfigDict(
        alias_generator=_wire_names_for("CursorListRequest"),
        validate_by_name=False,
    )
