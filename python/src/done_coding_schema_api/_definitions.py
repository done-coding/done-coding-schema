"""随包分发的 JSON Schema 定义文件：按名取路径或已解析的字典。

包内 ``schemas/`` 与 npm 包的 ``schemas/`` 是同一批文件，逐字节照抄仓根 ``schemas/``
（由 pnpm gen 生成，构建检查核对 wheel 与 sdist 里的副本）。
"""

import json
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

_SUFFIX = ".schema.json"


def _directory() -> Path:
    return Path(str(files(__package__).joinpath("schemas")))


@cache
def schema_names() -> tuple[str, ...]:
    """全部定义的名字（文件名去掉 .schema.json），如 ``"error-body"``。"""
    return tuple(
        sorted(
            path.name.removesuffix(_SUFFIX)
            for path in _directory().iterdir()
            if path.name.endswith(_SUFFIX)
        )
    )


def schema_path(name: str) -> Path:
    """定义文件的路径，如 ``schema_path("error-body")`` → ``…/schemas/error-body.schema.json``。

    文件的 ``$id`` 即文件名，跨文件 ``$ref`` 也写文件名；整体登记到校验器时以 ``$id`` 为键。
    名字不存在时抛 KeyError 并列出全部名字。
    """
    if name not in schema_names():
        raise KeyError(f"没有名为 {name!r} 的定义；可用：{', '.join(schema_names())}")
    return _directory() / f"{name}{_SUFFIX}"


def load_schema(name: str) -> dict[str, Any]:
    """已解析的定义（每次返回新的字典，改动不影响包内文件与其他调用方）。"""
    return json.loads(schema_path(name).read_text(encoding="utf-8"))
