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


# ---- 模型导出 JSON Schema 用：按标题找到源定义，并展开成不带引用的单个结构 ----

# 只在定义文档层面有意义的关键字：展开引用后去掉，嵌进 OpenAPI 等文档时不改变解析基准。
_DOCUMENT_KEYWORDS = ("$schema", "$id", "$defs")


@cache
def _titles() -> dict[str, tuple[str, str]]:
    """定义里的 title（即生成模型的类名）→ (定义名, 文件内 JSON Pointer)。"""
    index: dict[str, tuple[str, str]] = {}
    for name in schema_names():
        document = load_schema(name)
        nodes = [("", document)] + [
            (f"/$defs/{key}", node) for key, node in document.get("$defs", {}).items()
        ]
        for pointer, node in nodes:
            if isinstance(node, dict) and "title" in node:
                index[node["title"]] = (name, pointer)
    return index


def source_of(title: str) -> tuple[str, str] | None:
    return _titles().get(title)


def _resolve(document: Any, pointer: str) -> Any:
    for token in pointer.split("/")[1:] if pointer else []:
        document = document[token.replace("~1", "/").replace("~0", "~")]
    return document


def _inline(node: Any, document: dict[str, Any]) -> Any:
    """展开 $ref（文件内与跨文件），去掉文档层面的关键字。定义里没有递归引用。"""
    if isinstance(node, list):
        return [_inline(child, document) for child in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        target, _, pointer = node["$ref"].partition("#")
        if target:
            document = load_schema(target.removesuffix(_SUFFIX))
        resolved = _inline(_resolve(document, pointer), document)
        siblings = {key: value for key, value in node.items() if key != "$ref"}
        return {**resolved, **_inline(siblings, document)}
    return {
        key: _inline(value, document)
        for key, value in node.items()
        if key not in _DOCUMENT_KEYWORDS
    }


def bundled_schema(name: str, pointer: str = "") -> dict[str, Any]:
    """定义（或其中 pointer 处的子结构）展开全部引用后的独立 JSON Schema。"""
    document = load_schema(name)
    return _inline(_resolve(document, pointer), document)
