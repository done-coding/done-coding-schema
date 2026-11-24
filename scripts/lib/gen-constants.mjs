// 由定义生成常量：业务码、通用失败码表、列表的字段路径。值一律字面量（as const）。

const SUCCESS_SCHEMA = "success-envelope.schema.json";
const COMMON_CODES_SCHEMA = "common-error-codes.schema.json";

const literal = (value) => JSON.stringify(value, null, 2);

const docComment = (lines) =>
  ["/**", ...lines.map((line) => ` * ${line}`), " */"].join("\n");

function resolveLocal(schema, node) {
  if (!node?.$ref) return node;
  if (!node.$ref.startsWith("#/")) {
    throw new Error(`字段路径只支持文件内引用：${node.$ref}`);
  }
  return node.$ref
    .slice(2)
    .split("/")
    .reduce((current, token) => current[token], schema);
}

/** 通用失败码表：从约束里读出每个码的固定语义，并核对与 $defs/code 一致。 */
export function readCommonErrorCodes(schema) {
  const rows = schema.allOf.map((entry) => {
    const error = entry.then.properties.error.properties;
    return {
      code: entry.if.properties.code.const,
      httpStatus: entry["x-httpStatus"],
      retryable: error.retryable.const,
      outcome: error.outcome.const,
      meaning: entry.description,
    };
  });
  const listed = schema.$defs.code.enum;
  const fromRows = rows.map(({ code }) => code);
  if (JSON.stringify(listed) !== JSON.stringify(fromRows)) {
    throw new Error(
      `${COMMON_CODES_SCHEMA}：$defs/code 与 allOf 各项的码不一致（顺序也须一致）`,
    );
  }
  for (const row of rows) {
    if (!Number.isInteger(row.httpStatus) || !row.meaning) {
      throw new Error(
        `${COMMON_CODES_SCHEMA}：${row.code} 缺 x-httpStatus 或 description`,
      );
    }
  }
  return rows;
}

/** 响应：沿 properties 走到叶子，键取叶子字段名，值为点号路径。 */
function responsePaths(schema, node = schema, prefix = "", out = {}) {
  for (const [name, raw] of Object.entries(node.properties ?? {})) {
    if (raw === false) continue;
    const child = resolveLocal(schema, raw);
    const path = `${prefix}${name}`;
    if (child.type === "object" && child.properties) {
      responsePaths(schema, child, `${path}.`, out);
    } else {
      if (name in out) {
        throw new Error(
          `${schema.$id}：字段名 ${name} 在多个位置出现，常量键会冲突`,
        );
      }
      out[name] = path;
    }
  }
  return out;
}

/** 请求：线上参数名 = 前缀 + 点 + 字段名；按字段筛选的结构给出前缀与操作名。 */
function requestParams(schema) {
  const prefix = schema["x-paramPrefix"];
  if (schema.patternProperties) {
    const [condition] = Object.values(schema.patternProperties).map((node) =>
      resolveLocal(schema, node),
    );
    return {
      prefix: `${prefix}.`,
      operators: Object.fromEntries(
        Object.keys(condition.properties).map((op) => [op, op]),
      ),
    };
  }
  return Object.fromEntries(
    Object.keys(schema.properties).map((name) => [name, `${prefix}.${name}`]),
  );
}

/**
 * @param {{file: string, schema: Record<string, any>}[]} entries
 * @returns {string} 未格式化的 TS 源码
 */
export function generateConstants(entries) {
  const byFile = new Map(entries.map(({ file, schema }) => [file, schema]));
  const blocks = [];

  const successCode = byFile.get(SUCCESS_SCHEMA).properties.code.const;
  blocks.push(
    docComment(["成功码。成功外壳的 code 只能是这一组里的值。"]),
    `export const SUCCESS_CODES = ${literal({ [successCode]: successCode })} as const;`,
    "export type SuccessCode = (typeof SUCCESS_CODES)[keyof typeof SUCCESS_CODES];",
  );

  const rows = readCommonErrorCodes(byFile.get(COMMON_CODES_SCHEMA));
  blocks.push(
    docComment([
      "通用失败码。错误体的 code 是开放字符串，这里只列通用的一组；",
      "各服务可以有自己的专有码，遇到不认识的码按 HTTP 状态归类处理。",
    ]),
    `export const COMMON_ERROR_CODES = ${literal(
      Object.fromEntries(rows.map(({ code }) => [code, code])),
    )} as const;`,
    "export type CommonErrorCode = (typeof COMMON_ERROR_CODES)[keyof typeof COMMON_ERROR_CODES];",
    docComment([
      "通用失败码 → HTTP 状态、能否重试、是否已执行（outcome）与含义。",
    ]),
    `export const COMMON_ERROR_CODE_TABLE = ${literal(
      Object.fromEntries(rows.map(({ code, ...rest }) => [code, rest])),
    )} as const;`,
  );

  for (const { schema } of entries) {
    const name = schema["x-pathConstants"];
    if (!name) continue;
    const isRequest = Boolean(schema["x-paramPrefix"]);
    const value = isRequest ? requestParams(schema) : responsePaths(schema);
    blocks.push(
      docComment([
        isRequest
          ? `${schema.title} 的线上参数名（由定义 ${schema.$id} 生成）。`
          : `${schema.title} 响应里各字段的路径（由定义 ${schema.$id} 生成）。`,
      ]),
      `export const ${name} = ${literal(value)} as const;`,
    );
  }

  return blocks.join("\n");
}
