// 定义校验器：Ajv（JSON Schema 2020-12）+ 本仓定义里用到的 x- 关键字。
//
// x- 关键字分两类：
// - 标注（不参与校验）：供生成器读取的元数据；
// - 补充检查：标准 JSON Schema 写不出的跨字段约束。其他校验器会忽略它们，
//   各语言包需要按这里的语义另行实现（Python 包在薄包装里补）。
import Ajv2020 from "ajv/dist/2020.js";

export const ANNOTATION_KEYWORDS = [
  "x-httpStatus",
  "x-paramPrefix",
  "x-pathConstants",
  // 参考资源：x-referenceResource 标出整份定义是参考资源（不约束任何结构，
  // 从参考资源出口导出）；x-referenceValue / x-referenceValues 是参考值，不是默认值。
  "x-referenceResource",
  "x-referenceValue",
  "x-referenceValues",
];

const isNonNegativeInteger = (value) => Number.isInteger(value) && value >= 0;
const isPlainObject = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);

/** 补充检查：返回出错项（不含 keyword / parentSchema，由外层补上）。 */
export const CHECK_KEYWORDS = {
  /** 页码式：totalPage 等于 ceil(totalRecord / pageSize)。 */
  "x-totalPageEqualsCeil": {
    type: "object",
    schemaType: "boolean",
    check(enabled, data, instancePath) {
      const { totalRecord, pageSize, totalPage } = data;
      // 任一项本身不合法时交给标准关键字报错，这里不重复报。
      if (
        !enabled ||
        !isNonNegativeInteger(totalRecord) ||
        !isNonNegativeInteger(totalPage) ||
        !Number.isInteger(pageSize) ||
        pageSize < 1
      ) {
        return [];
      }
      const expected = Math.ceil(totalRecord / pageSize);
      return totalPage === expected
        ? []
        : [
            {
              instancePath: `${instancePath}/totalPage`,
              params: { expected },
              message: `totalPage 应为 ceil(totalRecord / pageSize) = ${expected}`,
            },
          ];
    },
  },
  /** 页码式：items 条数不超过 page.pageSize，也不超过 page.totalRecord。 */
  "x-itemsWithinPage": {
    type: "object",
    schemaType: "boolean",
    check(enabled, data, instancePath) {
      const { items, page } = data;
      if (!enabled || !Array.isArray(items) || !isPlainObject(page)) return [];
      // 上限本身不合法时交给标准关键字报错，这里不重复报。
      const limits = {
        pageSize:
          Number.isInteger(page.pageSize) && page.pageSize >= 1
            ? page.pageSize
            : undefined,
        totalRecord: isNonNegativeInteger(page.totalRecord)
          ? page.totalRecord
          : undefined,
      };
      return Object.entries(limits)
        .filter(([, limit]) => limit !== undefined && items.length > limit)
        .map(([by, limit]) => ({
          instancePath: `${instancePath}/items`,
          params: { by, limit, count: items.length },
          message: `items 有 ${items.length} 条，超过 ${by}（${limit}）`,
        }));
    },
  },
  /** 数组内各项的某个字段不重复。 */
  "x-uniqueItemsBy": {
    type: "array",
    schemaType: "string",
    check(property, data, instancePath) {
      const firstIndex = new Map();
      const errors = [];
      data.forEach((item, index) => {
        if (item === null || typeof item !== "object" || !(property in item)) {
          return;
        }
        const value = item[property];
        if (firstIndex.has(value)) {
          errors.push({
            instancePath: `${instancePath}/${index}/${property}`,
            params: { property, duplicateOf: firstIndex.get(value) },
            message: `${property} 与第 ${firstIndex.get(value)} 项重复`,
          });
        } else {
          firstIndex.set(value, index);
        }
      });
      return errors;
    },
  },
  /** 对象里的数组字段不含另一个字段的值。 */
  "x-arrayExcludesProperty": {
    type: "object",
    schemaType: "object",
    check({ array, property }, data, instancePath) {
      const list = data[array];
      if (!Array.isArray(list) || !(property in data)) return [];
      return list.includes(data[property])
        ? [
            {
              instancePath: `${instancePath}/${array}`,
              params: { array, property, value: data[property] },
              message: `${array} 不能包含 ${property} 的值`,
            },
          ]
        : [];
    },
  },
};

/**
 * 建一个已登记全部定义的校验器。
 * @param {Record<string, any>[]} schemas
 * @param {{verbose?: boolean}} [options] verbose 时错误带 parentSchema（覆盖率统计要用）
 */
export function createValidator(schemas, { verbose = false } = {}) {
  const ajv = new Ajv2020({
    allErrors: true,
    strict: true,
    // then / else 里的 required 引用的是外层声明的字段，这是 if/then 的正常写法。
    strictRequired: false,
    // if / then 子结构不重复写 type。
    strictTypes: false,
    verbose,
  });
  for (const keyword of ANNOTATION_KEYWORDS) ajv.addKeyword(keyword);
  for (const [keyword, { type, schemaType, check }] of Object.entries(
    CHECK_KEYWORDS,
  )) {
    ajv.addKeyword({
      keyword,
      type,
      schemaType,
      errors: true,
      validate: function validate(value, data, parentSchema, dataCxt) {
        const errors = check(value, data, dataCxt?.instancePath ?? "");
        validate.errors = errors.map((error) => ({
          keyword,
          ...error,
          ...(verbose ? { parentSchema, schema: value, data } : {}),
        }));
        return errors.length === 0;
      },
    });
  }
  for (const schema of schemas) ajv.addSchema(schema);
  return ajv;
}
