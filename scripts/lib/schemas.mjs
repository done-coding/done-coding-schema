// 读取 schemas/ 下的定义文件与样例文件。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
);
export const SCHEMAS_DIR = path.join(ROOT, "schemas");
export const EXAMPLES_DIR = path.join(SCHEMAS_DIR, "examples");

const SCHEMA_SUFFIX = ".schema.json";

/** 结构名：文件名去掉 .schema.json。 */
export const baseName = (file) => file.slice(0, -SCHEMA_SUFFIX.length);

/**
 * 按文件名排序读出全部定义。
 * @returns {{file: string, schema: Record<string, any>, text: string}[]}
 */
export function loadSchemas() {
  return fs
    .readdirSync(SCHEMAS_DIR)
    .filter((file) => file.endsWith(SCHEMA_SUFFIX))
    .sort()
    .map((file) => {
      const text = fs.readFileSync(path.join(SCHEMAS_DIR, file), "utf8");
      const schema = JSON.parse(text);
      if (schema.$id !== file) {
        throw new Error(`${file}: $id 必须等于文件名，实际为 ${schema.$id}`);
      }
      return { file, schema, text };
    });
}

/** 读出某个结构的样例文件；不存在时返回 null。 */
export function loadExamples(file) {
  const examplesPath = path.join(EXAMPLES_DIR, `${baseName(file)}.json`);
  if (!fs.existsSync(examplesPath)) return null;
  return JSON.parse(fs.readFileSync(examplesPath, "utf8"));
}

/** 样例目录里的全部文件名（用来发现没有对应定义的样例文件）。 */
export function listExampleFiles() {
  return fs.existsSync(EXAMPLES_DIR)
    ? fs.readdirSync(EXAMPLES_DIR).filter((file) => file.endsWith(".json"))
    : [];
}
