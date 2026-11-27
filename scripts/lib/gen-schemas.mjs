// 把定义文件随 npm 包导出：一份 TS 模块（打包器直接引入，结构与参考资源分两个模块），
// 一份原样的 JSON 文件。
import { baseName, isReferenceResource } from "./schemas.mjs";

const camelCase = (name) =>
  name.replace(/-([a-z0-9])/g, (_, char) => char.toUpperCase());

/** 定义文件对应的导出名，如 error-body.schema.json → errorBodySchema。 */
export const exportNameOf = (file) => `${camelCase(baseName(file))}Schema`;

const SCHEMA_DOCUMENT = [
  "/** 一份 JSON Schema 定义文档。 */",
  "export interface SchemaDocument {",
  "  readonly [keyword: string]: unknown;",
  "}",
];

/**
 * 结构层（主入口）：结构定义各一个导出，加全部结构定义的集合 schemas。
 * 参考资源层（参考资源出口）：参考资源定义各一个导出，加集合 referenceSchemas。
 * @param {{file: string, schema: Record<string, any>}[]} entries
 * @param {boolean} reference 是否生成参考资源层
 * @returns {string} 未格式化的 TS 源码
 */
export function generateSchemaModule(entries, reference) {
  const selected = entries.filter(
    ({ schema }) => isReferenceResource(schema) === reference,
  );
  const blocks = reference
    ? ['import type { SchemaDocument } from "./schemas";']
    : [...SCHEMA_DOCUMENT];
  for (const { file, schema } of selected) {
    blocks.push(
      `/** ${schema.title ?? file}：${file} */`,
      `export const ${exportNameOf(file)}: SchemaDocument = ${JSON.stringify(schema, null, 2)};`,
    );
  }
  blocks.push(
    reference
      ? "/** 全部参考资源定义，键为定义的 $id（即文件名）。 */"
      : "/** 全部结构定义，键为定义的 $id（即文件名），可整体登记到校验器里。 */",
    `export const ${reference ? "referenceSchemas" : "schemas"} = {`,
    ...selected.map(
      ({ file }) => `  ${JSON.stringify(file)}: ${exportNameOf(file)},`,
    ),
    "} as const;",
  );
  return blocks.join("\n");
}

/** JSON 文件逐字节照抄 schemas/ 下的定义。 */
export const generateSchemaFiles = (entries) =>
  entries.map(({ file, text }) => ({ file, content: text }));
