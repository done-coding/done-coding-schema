// 结构出口（主入口）：生成的类型、成功码与结构定义文件；成功外壳与三种列表以泛型版本导出
// （同名覆盖生成的非泛型版本）。通用失败码、码表、路径与参数名、参考数值不在这里，
// 见参考资源出口 "@done-coding/schema-api/reference"：只引入结构时不受任何内置的码或数值约束。
export * from "./generated/types";
export * from "./generated/constants";
export * from "./generated/schemas";
export type {
  BoundedList,
  CursorList,
  PagedList,
  SuccessEnvelope,
} from "./generics";
