// 由定义生成 TS 类型（json-schema-to-typescript）。
//
// 类型只表达结构的形状。只用于校验的关键字（if / then / else / not / allOf /
// propertyNames）与 x- 标注在交给生成工具前去掉：它们不改变字段与字段类型，
// 留着反而会让生成工具产出无意义的交叉类型。
import { compile } from "json-schema-to-typescript";

const VALIDATION_ONLY_KEYWORDS = new Set([
  "if",
  "then",
  "else",
  "not",
  "allOf",
  "propertyNames",
  "$comment",
]);

/** 深拷贝并去掉只用于校验的关键字。 */
function shapeOf(node) {
  if (Array.isArray(node)) return node.map(shapeOf);
  if (node === null || typeof node !== "object") return node;
  return Object.fromEntries(
    Object.entries(node)
      .filter(
        ([key]) => !VALIDATION_ONLY_KEYWORDS.has(key) && !key.startsWith("x-"),
      )
      .map(([key, value]) => [
        key,
        // properties / patternProperties / $defs 下的键是字段名，不是关键字。
        ["properties", "patternProperties", "$defs"].includes(key)
          ? Object.fromEntries(
              Object.entries(value).map(([name, child]) => [
                name,
                shapeOf(child),
              ]),
            )
          : shapeOf(value),
      ]),
  );
}

/** 只给描述对象结构的定义生成类型（通用失败码表只作约束与常量来源）。 */
export const hasTypeOutput = (schema) => schema.type === "object";

/**
 * @param {{file: string, schema: Record<string, any>}[]} entries
 * @returns {Promise<string>} 未格式化的 TS 源码
 */
export async function generateTypes(entries) {
  const parts = [];
  for (const { file, schema } of entries.filter(({ schema }) =>
    hasTypeOutput(schema),
  )) {
    const shape = shapeOf(schema);
    // 形状里的引用都应是文件内引用；跨文件引用目前只出现在校验关键字里。
    if (/"\$ref":"(?!#)/.test(JSON.stringify(shape))) {
      throw new Error(`${file}：类型生成只支持文件内引用`);
    }
    parts.push(
      await compile(shape, schema.title, {
        bannerComment: "",
        // 未声明 additionalProperties 的对象（列表顶层允许附带字段）不生成索引签名：
        // TS 的对象类型本身允许多出字段，加了索引签名反而让写错字段名不报错。
        additionalProperties: false,
        format: false,
        declareExternallyReferenced: true,
        unreachableDefinitions: false,
      }),
    );
  }
  return parts.join("\n");
}
