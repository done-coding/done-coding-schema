// 参考资源出口 "@done-coding/schema-api/reference"：通用失败码与码表、列表的路径与参数名、
// 参考数值、参考资源定义文件，以及让专有码避开某组码的检查函数。
// 这些只是参考，不随结构生效；包不替使用方填写，要用须显式引入、显式写进自己的代码。
export * from "./generated/reference-constants";
export * from "./generated/reference-schemas";
export type { ReservedCodeHit } from "./reserved-codes";
export { findReservedCodes } from "./reserved-codes";
