import fs from "node:fs";
import path from "node:path";
import {
  COMMON_ERROR_CODES,
  COMMON_ERROR_CODE_TABLE,
  LIST_FILTER_PARAMS,
  PAGED_LIST_REQUEST_PARAMS,
  SUCCESS_CODES,
  schemas,
} from "../src";

const jsonDir = path.resolve(__dirname, "../schemas");

describe("包的运行时导出", () => {
  it("导出的定义与包里的 JSON 定义文件一一对应、内容相同", () => {
    const files = fs.readdirSync(jsonDir).sort();
    expect(Object.keys(schemas).sort()).toEqual(files);
    for (const file of files) {
      const json = JSON.parse(
        fs.readFileSync(path.join(jsonDir, file), "utf8"),
      );
      expect(schemas[file as keyof typeof schemas]).toEqual(json);
    }
  });

  it("成功码与通用失败码分两组，互不包含", () => {
    expect(SUCCESS_CODES).toEqual({ OK: "OK" });
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
