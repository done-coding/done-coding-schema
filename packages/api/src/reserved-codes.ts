import type { ServiceErrorCodes } from "./generated/types";

/** 专有码清单里撞上保留码集合的一项：index 是它在 codes 里的位置。 */
export interface ReservedCodeHit {
  index: number;
  code: string;
}

/**
 * 找出专有码清单里与 reserved 重名的项。结构本身只把 OK 与 HTTP_<数字> 当保留字；
 * 要让专有码避开某组通用码（如包里的 COMMON_ERROR_CODES，或自己的一组），把那组码传进来。
 * 按字节比较，不做大小写归一；reserved 为空就什么也不比。
 *
 * 用法：findReservedCodes(list, Object.values(COMMON_ERROR_CODES))，返回空数组即没有撞码。
 */
export function findReservedCodes(
  list: Pick<ServiceErrorCodes, "codes">,
  reserved: Iterable<string>,
): ReservedCodeHit[] {
  const set = new Set(reserved);
  return list.codes.flatMap(({ code }, index) =>
    set.has(code) ? [{ index, code }] : [],
  );
}
