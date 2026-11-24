// 类型层面的检查，由 pnpm typecheck（tsc）执行，不在运行时跑。
// 每个 @ts-expect-error 都断言下一行必须报类型错误；不报错时 tsc 失败。
import type * as Generated from "../src/generated/types";
import type {
  BoundedList,
  CursorList,
  ErrorBody,
  PagedList,
  SuccessEnvelope,
} from "../src";
import {
  CURSOR_LIST_REQUEST_PARAMS,
  PAGED_LIST_REQUEST_PARAMS,
  PAGED_LIST_RESPONSE_PATHS,
} from "../src";

type Equal<A, B> =
  (<T>() => T extends A ? 1 : 2) extends <T>() => T extends B ? 1 : 2
    ? true
    : false;
type Expect<T extends true> = T;

/** 包装层取默认类型参数时与生成类型完全一致：生成物的字段变了而包装没跟上时这里报错。 */
export type WrapperMatchesGenerated = [
  Expect<Equal<SuccessEnvelope, Generated.SuccessEnvelope>>,
  Expect<Equal<BoundedList, Generated.BoundedList>>,
  Expect<Equal<PagedList, Generated.PagedList>>,
  Expect<Equal<CursorList, Generated.CursorList>>,
];

interface User {
  id: string;
  name: string;
}

declare const users: SuccessEnvelope<PagedList<User>>;

export const userName: string = users.data.items[0].name;
export const totalRecord: number = users.data.page.totalRecord;

// @ts-expect-error 字段名写错
export const typo = users.data.page.totalRecords;

// @ts-expect-error 页码式的 page 不回传当前页码
export const currentPage = users.data.page.page;

// @ts-expect-error 元素的字段名写错
export const itemTypo = users.data.items[0].nmae;

// @ts-expect-error 把页码式当游标式读：页码式没有 cursor
export const next = users.data.cursor.next;

// @ts-expect-error 把页码式当游标式用
export const asCursor: CursorList<User> = users.data;

// @ts-expect-error 把页码式当一次性列表用：一次性列表不带 page
export const asBounded: BoundedList<User> = users.data;

export const bad: SuccessEnvelope = {
  // @ts-expect-error 成功码只能是 OK
  code: "SUCCESS",
  message: "",
  data: null,
};

declare const failure: ErrorBody;

// @ts-expect-error 错误体字段名写错
export const retriable = failure.error.retriable;

// 字段路径常量是字面量类型，可以拿来做类型推导。
export const pageSizeParam: "page.pageSize" =
  PAGED_LIST_REQUEST_PARAMS.pageSize;
export const totalRecordPath: "page.totalRecord" =
  PAGED_LIST_RESPONSE_PATHS.totalRecord;
export const limitParam: "cursor.limit" = CURSOR_LIST_REQUEST_PARAMS.limit;

// @ts-expect-error 当前页码只是请求参数，响应路径里没有
export const pagePath = PAGED_LIST_RESPONSE_PATHS.page;
