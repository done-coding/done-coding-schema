// 由 schemas/ 的定义生成 npm 包里的类型、常量与定义文件，以及 Python 包里的模型、常量与定义文件。
//
//   node scripts/generate.mjs           写出全部生成物（并删掉不再生成的旧文件）
//   node scripts/generate.mjs --check   只比对：生成物被手改、或改了定义没重新生成时退出码 1
import fs from "node:fs";
import path from "node:path";
import * as prettier from "prettier";
import { generateConstants } from "./lib/gen-constants.mjs";
import {
  PYTHON_GENERATED_DIR,
  PYTHON_SCHEMA_DIR,
  buildPythonOutputs,
} from "./lib/gen-python.mjs";
import {
  generateSchemaFiles,
  generateSchemaModule,
} from "./lib/gen-schemas.mjs";
import { generateTypes } from "./lib/gen-types.mjs";
import { ROOT, loadSchemas } from "./lib/schemas.mjs";

const NPM_PACKAGE = path.join(ROOT, "packages", "api");
const TS_DIR = path.join(NPM_PACKAGE, "src", "generated");
const JSON_DIR = path.join(NPM_PACKAGE, "schemas");

const BANNER = [
  "// 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。",
  "// 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。",
  "",
].join("\n");

/** 生成物统一按仓库的 prettier 配置格式化，与提交时的格式化结果一致。 */
async function format(filePath, source) {
  const options = await prettier.resolveConfig(filePath);
  return prettier.format(source, { ...options, filepath: filePath });
}

/** @returns {Promise<Map<string, string>>} 绝对路径 → 内容 */
async function buildOutputs() {
  const entries = loadSchemas();
  const outputs = new Map();
  const add = async (filePath, source) =>
    outputs.set(filePath, await format(filePath, source));

  await add(
    path.join(TS_DIR, "types.ts"),
    BANNER + (await generateTypes(entries)),
  );
  await add(
    path.join(TS_DIR, "constants.ts"),
    BANNER + generateConstants(entries),
  );
  await add(
    path.join(TS_DIR, "schemas.ts"),
    BANNER + generateSchemaModule(entries),
  );
  for (const { file, content } of generateSchemaFiles(entries)) {
    await add(path.join(JSON_DIR, file), content);
    await add(path.join(PYTHON_SCHEMA_DIR, file), content);
  }
  for (const [filePath, content] of buildPythonOutputs(entries)) {
    outputs.set(filePath, content);
  }
  return outputs;
}

/** 生成目录里现有的文件（用来发现不再生成的旧文件）。 */
const existingFiles = () =>
  [TS_DIR, JSON_DIR, PYTHON_GENERATED_DIR, PYTHON_SCHEMA_DIR].flatMap((dir) =>
    fs.existsSync(dir)
      ? fs
          .readdirSync(dir, { withFileTypes: true })
          // 运行时缓存（如 __pycache__/）不是生成物。
          .filter((entry) => entry.isFile())
          .map((entry) => path.join(dir, entry.name))
      : [],
  );

const relative = (filePath) => path.relative(ROOT, filePath);

async function main() {
  const check = process.argv.includes("--check");
  const outputs = await buildOutputs();
  const stale = existingFiles().filter((filePath) => !outputs.has(filePath));

  if (check) {
    const problems = [
      ...[...outputs]
        .filter(
          ([filePath, content]) =>
            !fs.existsSync(filePath) ||
            fs.readFileSync(filePath, "utf8") !== content,
        )
        .map(([filePath]) => `与定义不一致：${relative(filePath)}`),
      ...stale.map((filePath) => `不再由定义生成：${relative(filePath)}`),
    ];
    if (problems.length) {
      console.error(
        "生成物与定义不一致（生成物被手改，或改了定义没重新生成）：",
      );
      for (const problem of problems) console.error(`  - ${problem}`);
      console.error("在仓根运行 pnpm gen 重新生成。");
      process.exit(1);
    }
    console.log(`生成物与定义一致（${outputs.size} 个文件）。`);
    return;
  }

  for (const [filePath, content] of outputs) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content);
  }
  for (const filePath of stale) fs.rmSync(filePath);
  console.log(
    `已生成 ${outputs.size} 个文件${stale.length ? `，删除旧文件 ${stale.length} 个` : ""}。`,
  );
}

main();
