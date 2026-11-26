// 样例校验：合法样例全过；不合法样例全被拒，且拒绝原因恰是预期的那几条；
// 定义里每条约束至少被一个不合法样例触发。
//
// 样例文件 schemas/examples/<结构名>.json：
// {
//   "valid":   [{ "name": "...", "data": ... }],
//   "invalid": [{ "name": "...", "data": ..., "errors": [
//     { "instancePath": "/page/pageSize", "keyword": "maximum", "params": { ... } }
//   ] }]
// }
// errors 列出预期的全部出错项（if 这类包装项不计）；params 只比对写出的键。
import { CHECK_KEYWORDS, createValidator } from "./lib/validator.mjs";
import {
  baseName,
  listExampleFiles,
  loadExamples,
  loadSchemas,
} from "./lib/schemas.mjs";

/** 只表示「条件分支没走通」的包装项，真正的原因在分支内另有一条。 */
const WRAPPER_KEYWORDS = new Set(["if"]);

/** 会产生出错项的约束关键字（除 required、additionalProperties、false 外）。 */
const CONSTRAINT_KEYWORDS = new Set([
  "type",
  "const",
  "enum",
  "pattern",
  "minLength",
  "maxLength",
  "minimum",
  "maximum",
  "minItems",
  "maxItems",
  "uniqueItems",
  "minProperties",
  "not",
  ...Object.keys(CHECK_KEYWORDS),
]);

const escapePointer = (token) =>
  String(token).replaceAll("~", "~0").replaceAll("/", "~1");

/** 取 file 内 JSON Pointer 指向的节点。 */
function resolvePointer(schema, pointer) {
  return pointer
    .split("/")
    .slice(1)
    .reduce(
      (node, token) =>
        node?.[token.replaceAll("~1", "/").replaceAll("~0", "~")],
      schema,
    );
}

/**
 * 一个关键字下要继续走进去的子结构：[文件, 指针, 节点]。
 * 不进 if（条件本身不是约束）与 not（not 内部的关键字不会单独报错）。
 */
function childrenOf({ file, pointer, keyword, value }, byFile) {
  switch (keyword) {
    case "additionalProperties":
      // false 已由 unitsOf 记为约束单元；true 不含约束。
      return typeof value === "object"
        ? [[file, `${pointer}/${keyword}`, value]]
        : [];
    case "items":
    case "then":
    case "else":
      return [[file, `${pointer}/${keyword}`, value]];
    case "properties":
    case "patternProperties":
      return Object.entries(value).map(([name, child]) => [
        file,
        `${pointer}/${keyword}/${escapePointer(name)}`,
        child,
      ]);
    case "allOf":
      return value.map((child, index) => [
        file,
        `${pointer}/allOf/${index}`,
        child,
      ]);
    case "$ref": {
      const [refFile, refPointer = ""] = value.split("#");
      const targetFile = refFile || file;
      const target = resolvePointer(byFile.get(targetFile), refPointer);
      if (target === undefined) {
        throw new Error(`${file}#${pointer}: 无法解析 $ref ${value}`);
      }
      return [[targetFile, refPointer, target]];
    }
    default:
      return [];
  }
}

/** 一个关键字自身构成的约束单元。 */
function unitsOf(location, keyword, value) {
  if (keyword === "required") {
    return value.map((name) => `${location}/required/${name}`);
  }
  if (keyword === "additionalProperties") {
    return value === false ? [`${location}/additionalProperties`] : [];
  }
  return CONSTRAINT_KEYWORDS.has(keyword) ? [`${location}/${keyword}`] : [];
}

/**
 * 从一个根定义出发，沿正向位置收集约束单元。
 * 每个单元记作 "<文件>#<指针>/<关键字>[/<字段>]"。
 */
function collectUnits(rootFile, byFile, locations) {
  const units = new Set();
  const visited = new Set();

  const visit = (file, pointer, node) => {
    const location = `${file}#${pointer}`;
    if (node === false) {
      units.add(`${location}/false`);
      return;
    }
    if (node === null || typeof node !== "object" || visited.has(location)) {
      return;
    }
    visited.add(location);
    locations.set(node, location);

    for (const [keyword, value] of Object.entries(node)) {
      unitsOf(location, keyword, value).forEach((unit) => units.add(unit));
      for (const child of childrenOf(
        { file, pointer, keyword, value },
        byFile,
      )) {
        visit(...child);
      }
    }
  };

  visit(rootFile, "", byFile.get(rootFile));
  return units;
}

/** 把一条出错项映射到它触发的约束单元。 */
function unitOfError(error, locations, rootUnits) {
  if (error.keyword === "false schema") {
    // false 子结构没有对象身份，只能按 schemaPath 的尾部在本根可达单元里找。
    const suffix = error.schemaPath
      .replace(/\/false schema$/, "")
      .replace(/^[^#]*#/, "")
      .replace(/^[^/]+\.schema\.json/, "");
    const matches = [...rootUnits].filter((unit) =>
      unit.endsWith(`${suffix}/false`),
    );
    if (matches.length !== 1) {
      throw new Error(`无法唯一定位 false 子结构：${error.schemaPath}`);
    }
    return matches[0];
  }
  const location = locations.get(error.parentSchema);
  if (!location) return null;
  if (error.keyword === "required") {
    return `${location}/required/${error.params.missingProperty}`;
  }
  return `${location}/${error.keyword}`;
}

const sameParams = (expected = {}, actual = {}) =>
  Object.entries(expected).every(
    ([key, value]) => JSON.stringify(actual[key]) === JSON.stringify(value),
  );

const matches = (expected, actual) =>
  expected.instancePath === actual.instancePath &&
  expected.keyword === actual.keyword &&
  sameParams(expected.params, actual.params);

const describe = (error) =>
  `${error.instancePath || "(根)"} ${error.keyword} ${JSON.stringify(
    error.params ?? {},
  )}`;

/**
 * 合法样例必须有；不合法样例只在定义含约束时要求
 * （不含任何约束的定义，如只给缺省值的通用失败码表，写不出不合法样例）。
 */
const hasRequiredExamples = (examples, rootUnits) =>
  Boolean(examples?.valid?.length) &&
  (rootUnits.size === 0 || Boolean(examples?.invalid?.length));

function main() {
  const entries = loadSchemas();
  const byFile = new Map(entries.map(({ file, schema }) => [file, schema]));
  const ajv = createValidator(
    entries.map(({ schema }) => schema),
    { verbose: true },
  );
  const locations = new Map();
  const failures = [];
  const allUnits = new Set();
  const covered = new Set();
  let validCount = 0;
  let invalidCount = 0;

  const known = new Set(entries.map(({ file }) => `${baseName(file)}.json`));
  for (const exampleFile of listExampleFiles()) {
    if (!known.has(exampleFile)) {
      failures.push(`examples/${exampleFile}：没有对应的定义文件`);
    }
  }

  for (const { file } of entries) {
    const rootUnits = collectUnits(file, byFile, locations);
    rootUnits.forEach((unit) => allUnits.add(unit));
    const examples = loadExamples(file);
    if (!hasRequiredExamples(examples, rootUnits)) {
      failures.push(`${file}：缺少合法或不合法样例`);
      continue;
    }
    const validate = ajv.getSchema(file);

    for (const { name, data } of examples.valid) {
      validCount += 1;
      if (!validate(data)) {
        failures.push(
          `${file} 合法样例「${name}」被拒：${validate.errors
            .map(describe)
            .join("；")}`,
        );
      }
    }

    for (const { name, data, errors: expected } of examples.invalid) {
      invalidCount += 1;
      if (!expected?.length) {
        failures.push(`${file} 不合法样例「${name}」没写预期原因`);
        continue;
      }
      if (validate(data)) {
        failures.push(`${file} 不合法样例「${name}」被接受`);
        continue;
      }
      const actual = validate.errors.filter(
        (error) => !WRAPPER_KEYWORDS.has(error.keyword),
      );
      const remaining = [...actual];
      const missing = expected.filter((item) => {
        const index = remaining.findIndex((error) => matches(item, error));
        if (index === -1) return true;
        remaining.splice(index, 1);
        return false;
      });
      if (missing.length || remaining.length) {
        failures.push(
          `${file} 不合法样例「${name}」拒绝原因不符：\n` +
            `    预期未出现：${missing.map(describe).join("；") || "无"}\n` +
            `    多出：${remaining.map(describe).join("；") || "无"}`,
        );
        continue;
      }
      for (const error of actual) {
        const unit = unitOfError(error, locations, rootUnits);
        if (unit) covered.add(unit);
      }
    }
  }

  const uncovered = [...allUnits].filter((unit) => !covered.has(unit)).sort();
  for (const unit of uncovered) {
    failures.push(`约束没有不合法样例覆盖：${unit}`);
  }

  console.log(
    `定义 ${entries.length} 个；合法样例 ${validCount} 个，不合法样例 ${invalidCount} 个；约束 ${allUnits.size} 条，已覆盖 ${covered.size} 条。`,
  );
  if (failures.length) {
    console.error(`\n失败 ${failures.length} 项：`);
    for (const failure of failures) console.error(`  - ${failure}`);
    process.exit(1);
  }
  console.log("样例校验通过。");
}

main();
