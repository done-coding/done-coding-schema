"""随包分发的定义文件：与仓根 schemas/ 逐字节一致，按名可取路径与字典。"""

from pathlib import Path

import pytest

from done_coding_schema_api import load_schema, schema_names, schema_path

ROOT_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


def test_every_definition_is_shipped_verbatim() -> None:
    expected = sorted(
        path.name.removesuffix(".schema.json")
        for path in ROOT_SCHEMAS.glob("*.schema.json")
    )
    assert list(schema_names()) == expected
    for name in schema_names():
        shipped = schema_path(name).read_bytes()
        assert shipped == (ROOT_SCHEMAS / f"{name}.schema.json").read_bytes()


def test_load_schema_returns_fresh_dict() -> None:
    schema = load_schema("error-body")
    assert schema["$id"] == "error-body.schema.json"
    schema["title"] = "改掉"
    assert load_schema("error-body")["title"] == "ErrorBody"


def test_unknown_name_lists_available_names() -> None:
    with pytest.raises(KeyError, match="paged-list"):
        schema_path("paged_list")
