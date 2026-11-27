"""查询参数模型：页码式与游标式请求参数按线上的查询串形态收取。

请求参数的定义（``PagedListRequest``、``CursorListRequest``）约束的是解码后的对象；
线上是 ``page.pageSize=20`` 这样的查询串。这里把「线上名」与「解码」写死一次，
规则都取自定义：

- 线上名：``<x-paramPrefix>.<字段名>``（如 ``page.pageSize``），裸名不收；
  前缀外的参数不归它管，忽略；前缀下未声明的参数不合法；
- 整数：只收整串匹配定义里 ``x-queryIntegerPattern`` 的十进制数字串（``"02"``、``"+2"``、
  ``" 2"``、``"2.0"``、``"1e1"``、空串都不收），解码后再按定义的上下界校验；
- 导出：``model_json_schema()`` 与 FastAPI 为每个参数生成的说明都按定义写
  （``minimum`` / ``maximum``，可选参数不写成可为 null）。

使用方可以继承它声明自己的默认值与上限（子类只能收紧），不必再写别名与解码。
"""

import re
from collections.abc import Callable, Mapping
from copy import copy
from functools import cache
from typing import Any

from pydantic import ConfigDict, model_validator

from ._base import SchemaModel
from ._definitions import bundled_schema, source_of
from ._generated.cursor_list_request import CursorListRequest
from ._generated.paged_list_request import PagedListRequest
from ._source import _generated_class, describes_parameter


@cache
def _rules(title: str) -> tuple[str, frozenset[str], re.Pattern[str]]:
    """定义里的规则：(前缀, 整数参数的线上名, 整数串的写法)。"""
    definition = bundled_schema(*source_of(title))  # type: ignore[misc]
    prefix = definition["x-paramPrefix"]
    integers = frozenset(
        f"{prefix}.{name}"
        for name, prop in definition["properties"].items()
        if prop.get("type") == "integer"
    )
    return prefix, integers, re.compile(definition["x-queryIntegerPattern"])


def _prefixed(prefix: str) -> Callable[[str], str]:
    return lambda name: f"{prefix}.{name}"


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
        """只取本前缀下的参数；整数参数按定义的写法解码，不合写法的原样留给类型校验拒绝。"""
        generated_class = _generated_class(cls)
        if generated_class is None or not isinstance(data, Mapping):
            return data
        prefix, integers, integer_text = _rules(generated_class.__name__)
        decoded: dict[str, Any] = {}
        for key, value in data.items():
            if not (isinstance(key, str) and key.startswith(f"{prefix}.")):
                continue
            if (
                key in integers
                and isinstance(value, str)
                and integer_text.search(value)
            ):
                value = int(value)
            decoded[key] = value
        return decoded

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        if _generated_class(cls) is None:
            return
        # FastAPI 把查询参数模型逐字段展开成参数，用的是字段自己的声明；这里让每个参数的
        # 说明就是导出结构里的那一项（定义与子类声明的交集）。
        properties = cls.model_json_schema()["properties"]
        for name, field in list(cls.__pydantic_fields__.items()):
            described = copy(field)
            described.json_schema_extra = _replace_schema(
                properties[field.alias or name]
            )
            cls.__pydantic_fields__[name] = described


class PagedListQuery(_QueryParams, PagedListRequest):
    """页码式列表的查询参数：``page.page``、``page.pageSize``、``page.query``、``page.orderBy``。

    FastAPI 里写 ``params: Annotated[PagedListQuery, Query()]``；要声明自己的每页条数，
    继承它并重新声明字段即可，如 ``pageSize: JsonInt = Field(default=20, le=50)``。
    """

    model_config = ConfigDict(
        alias_generator=_prefixed(_rules("PagedListRequest")[0]),
        validate_by_name=False,
    )


class CursorListQuery(_QueryParams, CursorListRequest):
    """游标式列表的查询参数：``cursor.after``、``cursor.limit``。用法同 ``PagedListQuery``。"""

    model_config = ConfigDict(
        alias_generator=_prefixed(_rules("CursorListRequest")[0]),
        validate_by_name=False,
    )
