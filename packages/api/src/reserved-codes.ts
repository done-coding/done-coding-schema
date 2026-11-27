import type { ServiceErrorCodes } from "./generated/types";

/** 专有码清单里撞上保留码集合的一项：index 是它在 codes 里的位置。 */
export interface ReservedCodeHit {
  index: number;
  code: string;
}

const isIterable = (value: object): value is Iterable<string> =>
  Symbol.iterator in value;

/**
 * 找出专有码清单里与 reserved 中的码重名的项。结构本身只把 OK 与 HTTP_<数字> 当保留字；
 * 要让专有码避开某组通用码（如包里的 COMMON_ERROR_CODES，或自己的一组），把那组码传进来：
 * 字符串的可迭代集合（数组、Set），或「名字 → 码」的对象（取值，不取键）。
 * 按字节比较，不做大小写归一；reserved 为空就什么也不比。
 *
 * 用法：findReservedCodes(list, COMMON_ERROR_CODES)，返回空数组即没有撞码。
 */
export function findReservedCodes(
  list: Pick<ServiceErrorCodes, "codes">,
  reserved: Iterable<string> | Readonly<Record<string, string>>,
): ReservedCodeHit[] {
  const set = new Set(
    isIterable(reserved) ? reserved : Object.values(reserved),
  );
  return list.codes.flatMap(({ code }, index) =>
    set.has(code) ? [{ index, code }] : [],
  );
}
