// 把定义文件随 npm 包导出：一份 TS 模块（打包器直接引入），一份原样的 JSON 文件。
import { baseName } from "./schemas.mjs";

const camelCase = (name) =>
  name.replace(/-([a-z0-9])/g, (_, char) => char.toUpperCase());

/** 定义文件对应的导出名，如 error-body.schema.json → errorBodySchema。 */
export const exportNameOf = (file) => `${camelCase(baseName(file))}Schema`;

/**
 * @param {{file: string, schema: Record<string, any>}[]} entries
 * @returns {string} 未格式化的 TS 源码
 */
export function generateSchemaModule(entries) {
  const blocks = [
    "/** 一份 JSON Schema 定义文档。 */",
    "export interface SchemaDocument {",
    "  readonly [keyword: string]: unknown;",
    "}",
  ];
  for (const { file, schema } of entries) {
    blocks.push(
      `/** ${schema.title ?? file}：${file} */`,
      `export const ${exportNameOf(file)}: SchemaDocument = ${JSON.stringify(schema, null, 2)};`,
    );
  }
  blocks.push(
    "/** 全部定义，键为定义的 $id（即文件名），可整体登记到校验器里。 */",
    "export const schemas = {",
    ...entries.map(
      ({ file }) => `  ${JSON.stringify(file)}: ${exportNameOf(file)},`,
    ),
    "} as const;",
  );
  return blocks.join("\n");
}

/** JSON 文件逐字节照抄 schemas/ 下的定义。 */
export const generateSchemaFiles = (entries) =>
  entries.map(({ file, text }) => ({ file, content: text }));
