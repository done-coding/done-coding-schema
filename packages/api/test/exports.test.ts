import fs from "node:fs";
import path from "node:path";
import * as main from "../src";
import * as reference from "../src/reference";
import {
  COMMON_ERROR_CODES,
  COMMON_ERROR_CODE_TABLE,
  CURSOR_LIST_REFERENCE_VALUES,
  LIST_FILTER_PARAMS,
  PAGED_LIST_REFERENCE_VALUES,
  PAGED_LIST_REQUEST_PARAMS,
  findReservedCodes,
  referenceSchemas,
} from "../src/reference";

const jsonDir = path.resolve(__dirname, "../schemas");
const pkg = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "../package.json"), "utf8"),
);

describe("包的运行时导出", () => {
  it("结构定义与参考资源定义合起来与包里的 JSON 定义文件一一对应、内容相同", () => {
    const files = fs.readdirSync(jsonDir).sort();
    const all: Record<string, unknown> = {
      ...main.schemas,
      ...referenceSchemas,
    };
    expect(Object.keys(all).sort()).toEqual(files);
    for (const file of files) {
      const json = JSON.parse(
        fs.readFileSync(path.join(jsonDir, file), "utf8"),
      );
      expect(all[file]).toEqual(json);
      // 参考资源定义带 x-referenceResource 标记，结构定义不带。
      expect(file in referenceSchemas).toBe(
        json["x-referenceResource"] === true,
      );
    }
    expect(Object.keys(referenceSchemas).sort()).toEqual([
      "common-error-codes.schema.json",
      "list-reference-values.schema.json",
    ]);
  });

  it("主入口不含任何参考资源：两个出口的导出名不重叠", () => {
    const mainNames = Object.keys(main);
    for (const name of Object.keys(reference)) {
      expect(mainNames).not.toContain(name);
    }
    for (const name of [
      "COMMON_ERROR_CODES",
      "COMMON_ERROR_CODE_TABLE",
      "BOUNDED_LIST_RESPONSE_PATHS",
      "PAGED_LIST_REQUEST_PARAMS",
      "PAGED_LIST_RESPONSE_PATHS",
      "CURSOR_LIST_REQUEST_PARAMS",
      "CURSOR_LIST_RESPONSE_PATHS",
      "LIST_FILTER_PARAMS",
      "PAGED_LIST_REFERENCE_VALUES",
      "CURSOR_LIST_REFERENCE_VALUES",
      "commonErrorCodesSchema",
      "listReferenceValuesSchema",
      "referenceSchemas",
      "findReservedCodes",
    ]) {
      expect(mainNames).not.toContain(name);
      expect(Object.keys(reference)).toContain(name);
    }
    // 结构定义集合里也没有参考资源定义。
    expect(Object.keys(main.schemas)).not.toContain(
      "common-error-codes.schema.json",
    );
  });

  it("package.json 声明了两个出口，import / require 各有产物与类型声明", () => {
    for (const [subpath, entry] of [
      [".", "index"],
      ["./reference", "reference"],
    ]) {
      expect(pkg.exports[subpath]).toEqual({
        import: {
          types: `./types/${entry}.d.ts`,
          default: `./es/${entry}.mjs`,
        },
        require: {
          types: `./types/${entry}.d.cts`,
          default: `./lib/${entry}.cjs`,
        },
      });
    }
    // moduleResolution 为 node（node10）时不认 exports，靠 typesVersions 找到子路径的类型。
    expect(pkg.typesVersions).toEqual({
      "*": { reference: ["types/reference.d.ts"] },
    });
  });

  it("成功码与通用失败码分两组，互不包含", () => {
    expect(main.SUCCESS_CODES).toEqual({ OK: "OK" });
    expect(Object.values(COMMON_ERROR_CODES)).not.toContain("OK");
  });

  it("通用失败码表覆盖全部通用失败码", () => {
    expect(Object.keys(COMMON_ERROR_CODE_TABLE)).toEqual(
      Object.values(COMMON_ERROR_CODES),
    );
    expect(COMMON_ERROR_CODE_TABLE.RATE_LIMITED).toEqual({
      httpStatus: 429,
      retryable: true,
      outcome: "not_executed",
      meaning: "请求过于频繁，可稍后重试",
    });
  });

  it("参考数值只在参考资源出口", () => {
    expect(PAGED_LIST_REFERENCE_VALUES).toEqual({
      page: 1,
      pageSize: 10,
      maxPageSize: 100,
    });
    expect(CURSOR_LIST_REFERENCE_VALUES).toEqual({ maxLimit: 100 });
  });

  it("请求参数名带各自的前缀", () => {
    expect(Object.values(PAGED_LIST_REQUEST_PARAMS)).toEqual([
      "page.page",
      "page.pageSize",
      "page.query",
      "page.orderBy",
    ]);
    expect(LIST_FILTER_PARAMS).toEqual({
      prefix: "filter.",
      operators: { eq: "eq" },
    });
  });
});

describe("findReservedCodes：专有码显式避开某组码，比对的是码的值", () => {
  // 与 Python 的 tests/test_exports.py 同一组数据，两种语言结论须相同。
  const list = {
    codes: [
      { code: "ORDER_LOCKED" },
      { code: "NOT_FOUND" },
      { code: "not_found" },
      { code: "QUOTA_USED_UP" },
      { code: "MISSING" },
    ],
  } as unknown as Parameters<typeof findReservedCodes>[0];

  it("不传保留码就不比", () => {
    expect(findReservedCodes(list, [])).toEqual([]);
    expect(findReservedCodes(list, {})).toEqual([]);
  });

  it("传入包里的通用码（对象，取值）：按字节比较，指出撞码的位置", () => {
    expect(findReservedCodes(list, COMMON_ERROR_CODES)).toEqual([
      { index: 1, code: "NOT_FOUND" },
    ]);
    expect(findReservedCodes(list, Object.values(COMMON_ERROR_CODES))).toEqual([
      { index: 1, code: "NOT_FOUND" },
    ]);
  });

  it("键与值不同的集合：比对值，不比对键", () => {
    const own = { MISSING: "NOT_FOUND", QUOTA: "QUOTA_USED_UP" };
    expect(findReservedCodes(list, own)).toEqual([
      { index: 1, code: "NOT_FOUND" },
      { index: 3, code: "QUOTA_USED_UP" },
    ]);
    expect(findReservedCodes(list, new Set(["MISSING"]))).toEqual([
      { index: 4, code: "MISSING" },
    ]);
  });

  it("自己的一组码（引用包的一组再加自己的）", () => {
    const ours = { ...COMMON_ERROR_CODES, QUOTA_USED_UP: "QUOTA_USED_UP" };
    expect(findReservedCodes(list, ours)).toEqual([
      { index: 1, code: "NOT_FOUND" },
      { index: 3, code: "QUOTA_USED_UP" },
    ]);
  });
});
