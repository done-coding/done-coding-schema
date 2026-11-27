// 交给各语言生成工具的「形状」：深拷贝定义，去掉只用于校验的关键字。
//
// if / then / else / not / allOf / propertyNames 与 x- 标注不改变字段与字段类型，
// 留着反而会让生成工具产出无意义的交叉类型或错误的模型；它们表达的约束由各语言
// 的薄包装补上（TS 只表达形状，Python 在 models.py 里补校验）。

const VALIDATION_ONLY_KEYWORDS = new Set([
  "if",
  "then",
  "else",
  "not",
  "allOf",
  "propertyNames",
  "$comment",
]);

/** 键是字段名而不是关键字的位置。 */
const NAME_MAPS = new Set(["properties", "patternProperties", "$defs"]);

/**
 * @param {unknown} node
 * @param {{dropFalseProperties?: boolean}} [options]
 *   dropFalseProperties：去掉值为 false 的字段（「不得出现」的字段）。
 *   TS 保留它们生成 `?: never`；Python 生成工具会把它们生成成任意值，故去掉、由包装层拒绝。
 */
export function shapeOf(node, options = {}) {
  if (Array.isArray(node)) return node.map((child) => shapeOf(child, options));
  if (node === null || typeof node !== "object") return node;
  return Object.fromEntries(
    Object.entries(node)
      .filter(
        ([key]) => !VALIDATION_ONLY_KEYWORDS.has(key) && !key.startsWith("x-"),
      )
      .map(([key, value]) => [
        key,
        NAME_MAPS.has(key)
          ? Object.fromEntries(
              Object.entries(value)
                .filter(
                  ([, child]) =>
                    !(options.dropFalseProperties && child === false),
                )
                .map(([name, child]) => [name, shapeOf(child, options)]),
            )
          : shapeOf(value, options),
      ]),
  );
}

/** 只给描述对象结构的定义生成类型与模型（通用失败码表只作约束与常量来源）。 */
export const hasModelOutput = (schema) => schema.type === "object";
