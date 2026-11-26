"""随包分发的定义文件：与仓根 schemas/ 逐字节一致，按名可取路径与字典；
结构定义从包顶层取，参考资源定义只从 reference 子模块取。"""

import json
from pathlib import Path

import pytest

from done_coding_schema_api import load_schema, schema_names, schema_path
from done_coding_schema_api.reference import (
    load_reference_schema,
    reference_schema_names,
    reference_schema_path,
)

ROOT_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


def _root_names(reference: bool) -> list[str]:
    return sorted(
        path.name.removesuffix(".schema.json")
        for path in ROOT_SCHEMAS.glob("*.schema.json")
        if (
            json.loads(path.read_text(encoding="utf-8")).get("x-referenceResource")
            is True
        )
        is reference
    )


def test_every_definition_is_shipped_verbatim() -> None:
    assert list(schema_names()) == _root_names(reference=False)
    assert list(reference_schema_names()) == _root_names(reference=True)
    assert list(reference_schema_names()) == [
        "common-error-codes",
        "list-reference-values",
    ]
    for name in schema_names():
        shipped = schema_path(name).read_bytes()
        assert shipped == (ROOT_SCHEMAS / f"{name}.schema.json").read_bytes()
    for name in reference_schema_names():
        shipped = reference_schema_path(name).read_bytes()
        assert shipped == (ROOT_SCHEMAS / f"{name}.schema.json").read_bytes()


def test_load_schema_returns_fresh_dict() -> None:
    schema = load_schema("error-body")
    assert schema["$id"] == "error-body.schema.json"
    schema["title"] = "改掉"
    assert load_schema("error-body")["title"] == "ErrorBody"
    table = load_reference_schema("common-error-codes")
    assert table["x-referenceResource"] is True


def test_unknown_name_lists_available_names() -> None:
    with pytest.raises(KeyError, match="paged-list"):
        schema_path("paged_list")


def test_layers_do_not_mix() -> None:
    # 参考资源定义不能从结构的取用函数拿到，反之亦然；报错指明该去哪取。
    with pytest.raises(KeyError, match="reference"):
        schema_path("common-error-codes")
    with pytest.raises(KeyError, match="包顶层"):
        reference_schema_path("error-body")
