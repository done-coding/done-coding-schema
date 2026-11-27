"""定义里的 pattern 与生成模型里的 pattern：只差结尾锚点的写法。

定义用 ``$(?![\\s\\S])`` 表示真正的文本结尾（Ajv、Python re 下都不放过结尾换行）；
pydantic 默认的 Rust 正则引擎不支持前瞻，而它的 ``$`` 本来就只匹配文本结尾，
所以生成器把结尾的 ``$(?![\\s\\S])`` 换回 ``$``，其余一字不差。
"""

import ast
import re
from pathlib import Path
from typing import Annotated, Any

import pytest
from pydantic import Field, TypeAdapter, ValidationError

import done_coding_schema_api
from done_coding_schema_api import load_schema, schema_names

TRUE_END = r"$(?![\s\S])"
GENERATED_DIR = Path(done_coding_schema_api.__file__).parent / "_generated"


def _definition_patterns(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                found.add(value)
            elif key == "patternProperties":
                found |= set(value)
                found |= _definition_patterns(value)
            else:
                found |= _definition_patterns(value)
    elif isinstance(node, list):
        for child in node:
            found |= _definition_patterns(child)
    return found


def _to_model(pattern: str) -> str:
    return pattern[: -len(TRUE_END)] + "$" if pattern.endswith(TRUE_END) else pattern


def _generated_patterns() -> set[str]:
    found: set[str] = set()
    for path in GENERATED_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.keyword) and node.arg == "pattern":
                found.add(ast.literal_eval(node.value))
    return found


DEFINITION_PATTERNS = set().union(
    *(_definition_patterns(load_schema(name)) for name in schema_names())
)
# 只出现在校验关键字（not）里的 pattern 不进生成模型，由包装层另行检查。
VALIDATION_ONLY = {r"^HTTP_[0-9]+$(?![\s\S])"}


def test_every_anchored_pattern_uses_the_true_end() -> None:
    for pattern in DEFINITION_PATTERNS:
        if pattern.startswith("^"):
            assert pattern.endswith(TRUE_END), pattern
        assert r"\S" not in pattern.replace(r"[\s\S]", ""), pattern


def test_generated_patterns_differ_only_in_the_end_anchor() -> None:
    assert _generated_patterns() == {
        _to_model(pattern) for pattern in DEFINITION_PATTERNS - VALIDATION_ONLY
    }


@pytest.mark.parametrize("pattern", sorted(DEFINITION_PATTERNS))
@pytest.mark.parametrize(
    "value",
    [
        "a",
        "a\\n",
        "A_1\\n",
        "req-01",
        "req\\u001c01",
        "req\\ufeff01",
        "\\u0085",
        "\\ufeff",
        "/a/b",
        "name asc",
    ],
)
def test_definition_and_model_patterns_agree(pattern: str, value: str) -> None:
    """同一个值，Python re（通用校验器）按定义的写法判，与 Rust 引擎按生成的写法判，结论相同。"""
    text = value.encode().decode("unicode_escape")
    by_definition = re.search(pattern, text) is not None
    adapter = TypeAdapter(Annotated[str, Field(pattern=_to_model(pattern))])
    try:
        adapter.validate_python(text)
        by_model = True
    except ValidationError:
        by_model = False
    assert by_definition is by_model
