// 由定义生成 TS 类型（json-schema-to-typescript）。类型只表达结构的形状，见 shape.mjs。
import { compile } from "json-schema-to-typescript";
import { hasModelOutput, shapeOf } from "./shape.mjs";

/**
 * @param {{file: string, schema: Record<string, any>}[]} entries
 * @returns {Promise<string>} 未格式化的 TS 源码
 */
export async function generateTypes(entries) {
  const parts = [];
  for (const { file, schema } of entries.filter(({ schema }) =>
    hasModelOutput(schema),
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
