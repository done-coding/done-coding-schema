// 由定义生成 Python 包里的 Pydantic 模型（datamodel-code-generator）与常量。
// 生成工具在 python/ 的开发依赖里，经 uv 调用；输出统一用 ruff format 格式化。
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { REFERENCE, STRUCTURE, buildConstants } from "./gen-constants.mjs";
import { ROOT, baseName } from "./schemas.mjs";
import { hasModelOutput, shapeOf } from "./shape.mjs";

export const PYTHON_PROJECT = path.join(ROOT, "python");
const PACKAGE = "done_coding_schema_api";
export const PYTHON_GENERATED_DIR = path.join(
  PYTHON_PROJECT,
  "src",
  PACKAGE,
  "_generated",
);
/** Python 包里随包分发的定义文件（与 npm 包的 schemas/ 同一批，逐字节照抄）。 */
export const PYTHON_SCHEMA_DIR = path.join(
  PYTHON_PROJECT,
  "src",
  PACKAGE,
  "schemas",
);

const BANNER = [
  "# 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。",
  "# 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。",
  "",
].join("\n");

const DATAMODEL_OPTIONS = [
  "--input-file-type=jsonschema",
  "--output-model-type=pydantic_v2.BaseModel",
  "--target-python-version=3.10",
  "--use-title-as-name",
  "--use-annotated",
  "--field-constraints",
  "--use-double-quotes",
  "--disable-timestamp",
  "--use-schema-description",
  "--use-field-description",
  // 标量一律严格类型（不做 "10" → 10 这类转换），RootModel 不继承基类也一样严格。
  "--strict-types",
  "str",
  "int",
  "float",
  "bool",
  // 枚举生成 Literal：严格模式下 Literal 接受字符串，Enum 只接受枚举实例。
  "--enum-field-as-literal=all",
  // 手写基类：严格类型、列表顶层保留附带字段、输出用线上字段名，见 _base.py。
  `--base-class=${PACKAGE}._base.SchemaModel`,
  "--formatters=ruff-format",
];

/** 在 python/ 的锁定环境里运行命令。 */
function uvRun(args, input) {
  const result = spawnSync(
    "uv",
    ["run", "--project", PYTHON_PROJECT, "--frozen", "--quiet", ...args],
    { input, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
  );
  if (result.error) {
    throw new Error(`无法运行 uv：${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`命令失败：uv run ${args.join(" ")}\n${result.stderr}`);
  }
  return result.stdout;
}

/** 用 python/ 的 ruff 配置格式化，与提交时的格式化结果一致。 */
export const formatPython = (source, filePath) =>
  uvRun(["ruff", "format", `--stdin-filename=${filePath}`, "-"], source);

const PYDANTIC_IMPORT = /^from pydantic import (?:\(([^)]*)\)|(.*))$/m;

/**
 * 整数字段改用 _base.JsonInt：JSON Schema 的 integer 接受值为整数的浮点（12.0），
 * pydantic 的 StrictInt 不接受。生成工具只能选 StrictInt，生成后替换。
 */
export function useJsonInt(source) {
  if (!/\bStrictInt\b/.test(source)) return source;
  const withoutImport = source.replace(
    PYDANTIC_IMPORT,
    (_, grouped, inline) => {
      const names = (grouped ?? inline)
        .split(",")
        .map((name) => name.trim())
        .filter((name) => name && name !== "StrictInt");
      return `from pydantic import ${names.join(", ")}\nfrom ${PACKAGE}._base import JsonInt`;
    },
  );
  if (withoutImport === source) {
    throw new Error("生成的模块用到 StrictInt，却找不到 pydantic 的导入行");
  }
  return withoutImport.replace(/\bStrictInt\b/g, "JsonInt");
}

/** 定义里表示「真正的文本结尾」的写法：`$` 后加前瞻，Python 的 re 下也不放过结尾换行。 */
export const TRUE_END = "$(?![\\s\\S])";

/**
 * 定义的 pattern → 生成模型用的 pattern。
 * pydantic 默认的正则引擎（Rust regex）不支持前瞻，而它的 `$` 本来就只匹配文本结尾，
 * 所以把结尾的 TRUE_END 换回 `$`；其余部分原样。剩下任何前瞻、后顾都直接报错。
 */
export function toModelPattern(pattern) {
  const converted = pattern.endsWith(TRUE_END)
    ? `${pattern.slice(0, -TRUE_END.length)}$`
    : pattern;
  if (/\(\?<?[=!]/.test(converted)) {
    throw new Error(`生成模型用的正则引擎不支持前瞻与后顾：${pattern}`);
  }
  return converted;
}

/** 形状里的 pattern 与 patternProperties 的键都换成生成模型用的写法。 */
function withModelPatterns(node) {
  if (Array.isArray(node)) return node.map(withModelPatterns);
  if (node === null || typeof node !== "object") return node;
  return Object.fromEntries(
    Object.entries(node).map(([key, value]) => {
      if (key === "pattern" && typeof value === "string") {
        return [key, toModelPattern(value)];
      }
      if (key === "patternProperties") {
        return [
          key,
          Object.fromEntries(
            Object.entries(value).map(([regex, child]) => [
              toModelPattern(regex),
              withModelPatterns(child),
            ]),
          ),
        ];
      }
      return [key, withModelPatterns(value)];
    }),
  );
}

/**
 * @returns {Map<string, string>} 模块文件名 → 未加 banner 的源码
 */
export function generatePythonModels(entries) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "schema-codegen-"));
  try {
    const input = path.join(tmp, "in");
    const output = path.join(tmp, "out");
    fs.mkdirSync(input);
    for (const { file, schema } of entries.filter(({ schema }) =>
      hasModelOutput(schema),
    )) {
      fs.writeFileSync(
        path.join(input, `${baseName(file)}.json`),
        JSON.stringify(
          withModelPatterns(shapeOf(schema, { dropFalseProperties: true })),
          null,
          2,
        ),
      );
    }
    uvRun([
      "datamodel-codegen",
      `--input=${input}`,
      `--output=${output}`,
      ...DATAMODEL_OPTIONS,
    ]);
    return new Map(
      fs
        .readdirSync(output)
        .filter((name) => name.endsWith(".py"))
        .sort()
        .map((name) => [
          name,
          useJsonInt(fs.readFileSync(path.join(output, name), "utf8")),
        ]),
    );
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

/** JSON 值 → Python 字面量；对象用只读映射。 */
function pyLiteral(value) {
  if (value === null) return "None";
  if (value === true) return "True";
  if (value === false) return "False";
  if (typeof value === "number" || typeof value === "string") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `(${value.map(pyLiteral).join(", ")},)`;
  const items = Object.entries(value).map(
    ([key, child]) => `${JSON.stringify(key)}: ${pyLiteral(child)}`,
  );
  return `MappingProxyType({${items.join(", ")}})`;
}

/** 常量：与 npm 包同一份数据；联合类型用 Literal。layer 选结构层或参考资源层。 */
export function generatePythonConstants(entries, layer) {
  const selected = buildConstants(entries).filter(
    (constant) => constant.layer === layer,
  );
  const uses = (pattern) =>
    selected.some(({ value, unionType }) =>
      pattern.test(`${unionType ? "Literal" : ""}${pyLiteral(value)}`),
    );
  const lines = [
    ...(uses(/MappingProxyType/) ? ["from types import MappingProxyType"] : []),
    `from typing import ${uses(/^Literal/) ? "Final, Literal" : "Final"}`,
    "",
  ];
  for (const { name, doc, value, unionType } of selected) {
    lines.push(
      "",
      `${name}: Final = ${pyLiteral(value)}`,
      `"""${doc.join("\n")}"""`,
    );
    if (unionType) {
      lines.push(
        `${unionType} = Literal[${Object.values(value)
          .map((item) => JSON.stringify(item))
          .join(", ")}]`,
      );
    }
  }
  return `${lines.join("\n")}\n`;
}

/**
 * @returns {Map<string, string>} 绝对路径 → 已格式化的内容
 */
export function buildPythonOutputs(entries) {
  const sources = generatePythonModels(entries);
  sources.set("constants.py", generatePythonConstants(entries, STRUCTURE));
  sources.set(
    "reference_constants.py",
    generatePythonConstants(entries, REFERENCE),
  );
  const outputs = new Map();
  for (const [name, source] of sources) {
    const filePath = path.join(PYTHON_GENERATED_DIR, name);
    outputs.set(filePath, formatPython(BANNER + source, filePath));
  }
  return outputs;
}
