"""模型与源定义的对应：导出的 JSON Schema、子类重新声明字段时的源约束。

子类可以重新声明生成模型里的字段（加上限、加默认值、收窄类型、改线上字段名），
但只能收紧，不能放宽：

- 运行时：重新声明的字段除了按新声明校验，还要满足源定义对该字段的约束
  （``source_constraint_errors``，由基类的校验器调用）；
- 导出：该字段的结构是源定义与新声明的交集（``source_json_schema``）。

两边因此对同一个值给出同样的结论。
"""

from copy import copy
from typing import Annotated, Any, get_args
from weakref import WeakKeyDictionary

from pydantic import (
    BaseModel,
    GetJsonSchemaHandler,
    RootModel,
    TypeAdapter,
    ValidationError,
)
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, ErrorDetails, to_json

from ._definitions import bundled_schema, source_of

_GENERATED_MODULES = f"{__package__}._generated."


def _generated_class(model: type[BaseModel]) -> type[BaseModel] | None:
    """继承链上第一个能按类名（即定义的 title）找到源定义的生成类。"""
    return next(
        (
            klass
            for klass in model.__mro__
            if klass.__module__.startswith(_GENERATED_MODULES)
            and source_of(klass.__name__) is not None
        ),
        None,
    )


def _has_type_arguments(model: type[BaseModel]) -> bool:
    """模型或其父类给了泛型类型参数（PagedList[User]，或 class UserPage(PagedList[User])）。"""
    return any(
        getattr(klass, "__pydantic_generic_metadata__", {}).get("args")
        for klass in model.__mro__
    )


def _wire_name(name: str, field: FieldInfo) -> str:
    return field.alias or name


def _redeclared(model: type[BaseModel]) -> dict[str, FieldInfo]:
    """子类重新声明了的字段 → 生成类里的原字段。

    改了类型、默认值、约束、说明、线上字段名等任一项都算；泛型类型参数处
    （``__schema_type_params__``）不算，它们由类型参数决定。
    """
    generated_class = _generated_class(model)
    if generated_class is None or issubclass(model, RootModel):
        return {}
    type_params = getattr(model, "__schema_type_params__", ())
    originals = generated_class.__pydantic_fields__
    return {
        name: originals[name]
        for name, field in model.__pydantic_fields__.items()
        if name in originals
        and name not in type_params
        and _declaration(field) != _declaration(originals[name])
    }


_NAMING_ATTRIBUTES = (
    "alias",
    "alias_priority",
    "validation_alias",
    "serialization_alias",
)


def describes_parameter(update: Any) -> Any:
    """标出「只改参数说明」的 json_schema_extra（查询参数模型用），不算重新声明字段。"""
    update.__describes_parameter__ = True
    return update


def _declaration(field: FieldInfo) -> str:
    """字段的声明（类型、默认值、约束、说明等），不含线上字段名与参数说明；
    只改了这两样不算重新声明。"""
    unnamed = copy(field)
    for attribute in _NAMING_ATTRIBUTES:
        setattr(unnamed, attribute, None)
    if getattr(unnamed.json_schema_extra, "__describes_parameter__", False):
        unnamed.json_schema_extra = None
    return repr(unnamed)


def _renamed(model: type[BaseModel]) -> dict[str, str]:
    """改了线上字段名的字段：原线上名 → 新线上名（只有查询参数模型允许，见 check_wire_names）。"""
    generated_class = _generated_class(model)
    if generated_class is None or issubclass(model, RootModel):
        return {}
    originals = generated_class.__pydantic_fields__
    return {
        _wire_name(name, originals[name]): _wire_name(name, field)
        for name, field in model.__pydantic_fields__.items()
        if name in originals
        and _wire_name(name, field) != _wire_name(name, originals[name])
    }


def _models_in(tp: Any) -> list[type[BaseModel]]:
    """类型里直接出现的模型类（含 X | None 这类联合里的）。"""
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return [tp]
    return [model for arg in get_args(tp) for model in _models_in(arg)]


def _narrows_model(field: FieldInfo, original: FieldInfo) -> bool:
    """子类把嵌套模型字段换成了原模型的子类（如 page: MyPage，MyPage 继承 PagedListPage）。"""
    originals = _models_in(original.annotation)
    declared = _models_in(field.annotation)
    return bool(originals and declared) and all(
        any(issubclass(model, base) for base in originals) for model in declared
    )


# ---- 线上字段名：只有查询参数模型可以改 ----


def _wire_names(model: type[BaseModel], name: str) -> tuple[str, str]:
    """字段实际的线上名：(校验时认的名字, 输出时用的名字)。"""
    field = model.__pydantic_fields__[name]
    config = model.model_config
    validation: Any = name
    if config.get("validate_by_alias", True):
        alias = (
            field.validation_alias
            if field.validation_alias is not None
            else field.alias
        )
        validation = alias if alias is not None else name
    serialization = name
    if config.get("serialize_by_alias", False):
        serialization = field.serialization_alias or field.alias or name
    # validation_alias 可以是 AliasPath / AliasChoices，按 repr 比较。
    return repr(validation), serialization


def _allowed_wire_names(
    generated_class: type[BaseModel], name: str, prefix: str | None
) -> set[tuple[str, str]]:
    """一个字段允许的线上名：定义里的原名；查询参数模型另可用「前缀.原名」。"""
    original = _wire_names(generated_class, name)
    if not prefix:
        return {original}
    wire = f"{prefix}.{original[1]}"
    candidates = {original[1], wire}
    return {(repr(v), s) for v in candidates for s in candidates}


def check_wire_names(model: type[BaseModel]) -> None:
    """子类不得随意改线上字段名，在类定义时报错。

    - 包体结构（成功外壳、错误体、三种列表、专有码清单及其嵌套）：一律不得改。定义里有
      按名字引用字段的地方（if/then/else、x- 检查关键字），改了名，导出的结构与运行时校验
      就对不上；线上字段名本身也是这个包要统一的东西。
    - 查询参数模型（带 x-paramPrefix 的页码式与游标式请求参数）：线上名只能是定义里的原名，
      或「前缀.原名」（如 page.pageSize，即 PAGED_LIST_REQUEST_PARAMS 里的值）。

    alias、validation_alias、serialization_alias、alias_generator，以及关掉
    validate_by_alias / serialize_by_alias，凡让线上名变了的都按上面的规则核对。
    用校验器或序列化器自己改键名的写法不在检查之内，导出也不会反映。
    """
    generated_class = _generated_class(model)
    if generated_class is None or generated_class is model:
        return
    prefix = bundled_schema(*source_of(generated_class.__name__)).get(  # type: ignore[misc]
        "x-paramPrefix"
    )
    renamed = [
        name
        for name in generated_class.__pydantic_fields__
        if name in model.__pydantic_fields__
        and _wire_names(model, name)
        not in _allowed_wire_names(generated_class, name, prefix)
    ]
    if not renamed:
        return
    original = {name: _wire_names(generated_class, name)[1] for name in renamed}
    if prefix:
        details = "、".join(
            f"{name}（只能是 {original[name]!r} 或 {prefix + '.' + original[name]!r}）"
            for name in renamed
        )
        raise TypeError(
            f"{model.__name__}：{generated_class.__name__} 是查询参数模型，"
            f"子类只能按前缀 {prefix}. 改线上字段名：{details}。"
        )
    details = "、".join(f"{name}（定义里是 {original[name]!r}）" for name in renamed)
    raise TypeError(
        f"{model.__name__}：{generated_class.__name__} 是包体结构，子类不能改线上字段名：{details}。"
        "只有查询参数模型（PagedListRequest、CursorListRequest）可以按前缀改名。"
    )


# ---- 运行时：重新声明的字段仍要满足源定义 ----

_ADAPTERS: "WeakKeyDictionary[type[BaseModel], dict[str, TypeAdapter[Any]]]" = (
    WeakKeyDictionary()
)


def _declared_type(field: FieldInfo) -> Any:
    """字段的类型连同约束（Field(ge=1) 等），可交给 TypeAdapter 单独校验。"""
    if not field.metadata:
        return field.annotation
    return Annotated[(field.annotation, *field.metadata)]


def _source_adapters(model: type[BaseModel]) -> dict[str, TypeAdapter[Any]]:
    """字段名 → 按原字段声明（类型与约束）校验的适配器；每个类算一次。"""
    if model not in _ADAPTERS:
        _ADAPTERS[model] = {
            name: TypeAdapter(_declared_type(original))
            for name, original in _redeclared(model).items()
        }
    return _ADAPTERS[model]


def source_constraint_errors(instance: BaseModel) -> list[tuple[str, ErrorDetails]]:
    """重新声明的字段的值不满足源定义时的出错项：(线上字段名, 出错详情)。

    值先按线上形态输出成 JSON 再按原字段校验，与「拿定义校验线上数据」一致。
    """
    model = type(instance)
    found: list[tuple[str, ErrorDetails]] = []
    for name, adapter in _source_adapters(model).items():
        value = getattr(instance, name)
        try:
            adapter.validate_json(to_json(value, by_alias=True))
        except ValidationError as error:
            wire = _wire_name(name, model.__pydantic_fields__[name])
            found += [(wire, detail) for detail in error.errors()]
    return found


def integral_float_to_int(value: Any) -> Any:
    """值为整数的浮点（JSON 里的 12.0）按 JSON Schema 算整数，归一成 int。"""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _is_integer_marker(item: Any) -> bool:
    return getattr(item, "func", None) is integral_float_to_int


def _uses_json_int(tp: Any, seen: frozenset[Any] = frozenset()) -> bool:
    """类型（含嵌套的模型、列表、联合）里有没有 JsonInt。"""
    if tp in seen:
        return False
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return any(
            _uses_json_int(_declared_type(field), seen | {tp})
            for field in tp.__pydantic_fields__.values()
        )
    metadata = getattr(tp, "__metadata__", ())
    return any(_is_integer_marker(item) for item in metadata) or any(
        _uses_json_int(arg, seen) for arg in get_args(tp)
    )


_INTEGER_KEYS: "WeakKeyDictionary[type[BaseModel], frozenset[str]]" = (
    WeakKeyDictionary()
)


def _integer_keys(model: type[BaseModel]) -> frozenset[str]:
    """源字段用了 JsonInt、被子类重新声明了的字段（线上名与 Python 名）。"""
    if model not in _INTEGER_KEYS:
        _INTEGER_KEYS[model] = frozenset(
            key
            for name, original in _redeclared(model).items()
            if _uses_json_int(_declared_type(original))
            for key in (name, _wire_name(name, model.__pydantic_fields__[name]))
        )
    return _INTEGER_KEYS[model]


def _normalize_integers(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_integers(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_integers(child) for child in value]
    return integral_float_to_int(value)


def adopt_source_integers(model: type[BaseModel], data: Any) -> Any:
    """子类重新声明的字段沿用源字段的整数语义：值为整数的浮点（12.0）先归一成 int，
    即使子类写的是普通 int。否则子类会拒绝 12.0，而定义与导出都认它是整数。"""
    keys = _integer_keys(model)
    if not keys or not isinstance(data, dict):
        return data
    return {
        key: _normalize_integers(value) if key in keys else value
        for key, value in data.items()
    }


# ---- 导出：源定义与子类改动的交集 ----

# 只是说明、不参与校验的关键字：子类写了就用子类的。
_ANNOTATIONS = frozenset(
    {"description", "default", "examples", "deprecated", "readOnly", "writeOnly"}
)
# 数值与长度的界：两边都有时取更严的那个。
_LOWER_BOUNDS = frozenset(
    {"minimum", "exclusiveMinimum", "minLength", "minItems", "minProperties"}
)
_UPPER_BOUNDS = frozenset(
    {"maximum", "exclusiveMaximum", "maxLength", "maxItems", "maxProperties"}
)


TRUE_END = r"$(?![\s\S])"


def _model_pattern(pattern: Any) -> Any:
    r"""定义的 pattern 在生成模型里的写法：结尾的 $(?![\s\S]) 换回 $（见仓根 gen-python.mjs）。"""
    if isinstance(pattern, str) and pattern.endswith(TRUE_END):
        return pattern[: -len(TRUE_END)] + "$"
    return pattern


# pydantic 对套了校验函数或联合的类型，会把约束按参数名原样写出（如 JsonInt | None 上的 ge）。
_PYDANTIC_CONSTRAINTS = {
    "ge": "minimum",
    "gt": "exclusiveMinimum",
    "le": "maximum",
    "lt": "exclusiveMaximum",
    "multiple_of": "multipleOf",
    "min_length": "minLength",
    "max_length": "maxLength",
}


def _normalize_declared(schema: dict[str, Any]) -> dict[str, Any]:
    """新声明的结构规整成标准写法：去掉 null 分支（可选字段不接受显式 null，基类会拒），
    只剩一个分支时展开；约束的参数名换成 JSON Schema 关键字；默认值 null 不写（即「不带」）。"""
    result = {
        _PYDANTIC_CONSTRAINTS.get(key, key): value
        for key, value in schema.items()
        if not (key == "default" and value is None)
    }
    branches = [b for b in result.pop("anyOf", []) if b != {"type": "null"}]
    if len(branches) == 1:
        for key, value in _normalize_declared(branches[0]).items():
            result.setdefault(key, value)
    elif branches:
        result["anyOf"] = [_normalize_declared(b) for b in branches]
    return result


def _intersect(source: dict[str, Any], declared: dict[str, Any]) -> dict[str, Any]:
    """源定义的字段结构与子类新声明的交集：同时满足两者的值才合法。"""
    declared = _normalize_declared(declared)
    merged = dict(source)
    conflicts: dict[str, Any] = {}
    for keyword, value in declared.items():
        if keyword == "title":
            continue
        if keyword not in merged or keyword in _ANNOTATIONS:
            merged[keyword] = value
        elif merged[keyword] == value or (
            keyword == "pattern" and _model_pattern(merged[keyword]) == value
        ):
            # 生成模型里的 pattern 只是结尾锚点换了写法，与定义是同一个 pattern。
            continue
        elif keyword in _LOWER_BOUNDS:
            merged[keyword] = max(merged[keyword], value)
        elif keyword in _UPPER_BOUNDS:
            merged[keyword] = min(merged[keyword], value)
        else:
            # 同一关键字两边取值不同（如两份 pattern）：都要满足，另放进 allOf。
            conflicts[keyword] = value
    if conflicts:
        merged["allOf"] = [*merged.get("allOf", []), conflicts]
    return merged


def source_json_schema(
    model: type[BaseModel], core_schema: CoreSchema, handler: GetJsonSchemaHandler
) -> JsonSchemaValue:
    """模型导出的 JSON Schema = 对应的源定义 + 子类的改动。

    - 沿继承链找到生成的类，按类名（即定义的 title）定位源定义，展开引用后原样带出，
      x- 约束一并保留；找不到则用 pydantic 的默认结果；
    - 泛型给了类型参数时（直接参数化或继承参数化的类），``__schema_type_params__``
      列出的字段（items 的元素、data）换成类型参数生成的结构；
    - 子类重新声明的已有字段：源定义该字段与新声明的交集（见 ``_intersect``），
      改了线上字段名时换成新名字，是否必填按新声明；
    - 子类另外声明、源定义里没有的字段，按 pydantic 的默认结果补进 properties。
    """
    generated_class = _generated_class(model)
    if generated_class is None:
        return handler(core_schema)
    schema = bundled_schema(*source_of(generated_class.__name__))  # type: ignore[misc]
    properties: dict[str, Any] = schema.get("properties", {})
    type_params = getattr(model, "__schema_type_params__", ())
    typed = type_params if _has_type_arguments(model) else ()
    redeclared = _redeclared(model)
    fields = {} if issubclass(model, RootModel) else model.__pydantic_fields__
    originals = generated_class.__pydantic_fields__
    extra = [
        _wire_name(name, field)
        for name, field in fields.items()
        if name not in originals
    ]
    if not typed and not redeclared and not extra and not _renamed(model):
        return schema
    default = handler.resolve_ref_schema(handler(core_schema))
    generated = default.get("properties", {})
    generated_required = set(default.get("required", []))
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
    renamed = _renamed(model)
    for name, original in redeclared.items():
        old, new = _wire_name(name, original), _wire_name(name, fields[name])
        if _narrows_model(fields[name], original):
            # 换成了原嵌套模型的子类：子类自己导出的就是交集，引用它即可，不再叠一份原定义。
            description = properties[old].get("description")
            properties[old] = {
                **({"description": description} if description else {}),
                **{k: v for k, v in generated[new].items() if k != "title"},
            }
        else:
            properties[old] = _intersect(properties[old], generated[new])
    # 是否必填按新声明；顺序保持源定义里的顺序，子类另加的排在后面。
    redeclared_keys = {
        _wire_name(name, original) for name, original in redeclared.items()
    }
    required = [
        renamed.get(key, key)
        for key in schema.get("required", [])
        if key not in redeclared_keys or renamed.get(key, key) in generated_required
    ]
    required += [
        _wire_name(name, fields[name])
        for name in redeclared
        if _wire_name(name, fields[name]) in generated_required
        and _wire_name(name, fields[name]) not in required
    ]
    properties = {renamed.get(key, key): value for key, value in properties.items()}
    for key in extra:
        properties[key] = generated[key]
        if key in generated_required:
            required.append(key)
    if properties:
        schema["properties"] = properties
    if required or "required" in schema:
        schema["required"] = required
    return schema
