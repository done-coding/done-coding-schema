/**
 * 生成类型之上的一层薄泛型包装：只把 data、items 的元素类型换成类型参数，
 * 不新增、不改名、不放宽任何字段。其余字段经 Omit 原样取自生成类型，
 * 与生成类型的一致性由 test/generics.type-test.ts 在类型检查时核对。
 *
 * 用法：SuccessEnvelope<PagedList<User>>。
 * 接口在列表顶层声明的附带字段用交叉类型补：PagedList<User> & { summary: Summary }。
 */
import type * as Generated from "./generated/types";

/**
 * 成功外壳。TData 是结果对象的类型（或 null）；标量结果也要包成对象。
 * 约束写作 object 而非索引签名类型，是为了让 interface 声明的资源类型也能直接传入。
 */
export interface SuccessEnvelope<
  TData extends object | null = Generated.SuccessEnvelope["data"],
> extends Omit<Generated.SuccessEnvelope, "data"> {
  data: TData;
}

/** 一次性列表，TItem 是元素类型。 */
export interface BoundedList<TItem = unknown> extends Omit<
  Generated.BoundedList,
  "items"
> {
  items: TItem[];
}

/** 页码式列表，TItem 是元素类型。 */
export interface PagedList<TItem = unknown> extends Omit<
  Generated.PagedList,
  "items"
> {
  items: TItem[];
}

/** 游标式列表，TItem 是元素类型。 */
export interface CursorList<TItem = unknown> extends Omit<
  Generated.CursorList,
  "items"
> {
  items: TItem[];
}
