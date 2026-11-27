// npm 包类型解析检查：TypeScript 的 moduleResolution 取 node（node10）、node16、bundler 时，
// 都能从主入口与 "./reference" 子路径取到类型，常量仍是字面量类型。
// node10 不认 package.json 的 exports，靠 typesVersions 把 reference 指到它的声明文件。
// 先在包目录里 pnpm build 再运行；在临时目录里建一个只引用本包的空项目跑 tsc。
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";

const PACKAGE_DIR = path.join(ROOT, "packages", "api");
const pkg = JSON.parse(
  fs.readFileSync(path.join(PACKAGE_DIR, "package.json"), "utf8"),
);
const tsc = createRequire(path.join(PACKAGE_DIR, "package.json")).resolve(
  "typescript/bin/tsc",
);

const SOURCE = `import type { PagedList, SuccessEnvelope } from "${pkg.name}";
import { SUCCESS_CODES } from "${pkg.name}";
import {
  COMMON_ERROR_CODES,
  PAGED_LIST_REQUEST_PARAMS,
  findReservedCodes,
} from "${pkg.name}/reference";

export const pageSize: "page.pageSize" = PAGED_LIST_REQUEST_PARAMS.pageSize;
export const ok: "OK" = SUCCESS_CODES.OK;
export const notFound: "NOT_FOUND" = COMMON_ERROR_CODES.NOT_FOUND;
export type Users = SuccessEnvelope<PagedList<{ id: string }>>;
declare const list: Parameters<typeof findReservedCodes>[0];
export const hits = findReservedCodes(list, COMMON_ERROR_CODES);
`;

// type：使用方项目自身是 CommonJS 还是 ES 模块（node16 下决定走 exports 的 require 还是 import）。
const SETTINGS = {
  node10: { module: "commonjs", moduleResolution: "node10", type: "commonjs" },
  "node16（CommonJS）": {
    module: "node16",
    moduleResolution: "node16",
    type: "commonjs",
  },
  "node16（ES 模块）": {
    module: "node16",
    moduleResolution: "node16",
    type: "module",
  },
  bundler: { module: "esnext", moduleResolution: "bundler", type: "module" },
};

const failures = [];
for (const [label, { type, ...options }] of Object.entries(SETTINGS)) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "schema-types-"));
  try {
    const scope = path.join(
      dir,
      "node_modules",
      ...pkg.name.split("/").slice(0, -1),
    );
    fs.mkdirSync(scope, { recursive: true });
    fs.symlinkSync(
      PACKAGE_DIR,
      path.join(dir, "node_modules", pkg.name),
      "dir",
    );
    fs.writeFileSync(path.join(dir, "index.ts"), SOURCE);
    fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify({ type }));
    fs.writeFileSync(
      path.join(dir, "tsconfig.json"),
      JSON.stringify({
        compilerOptions: {
          ...options,
          target: "es2020",
          strict: true,
          noEmit: true,
          types: [],
        },
        files: ["index.ts"],
      }),
    );
    const result = spawnSync(process.execPath, [tsc, "-p", dir], {
      encoding: "utf8",
    });
    if (result.status !== 0) {
      failures.push(
        `moduleResolution ${label}：\n${result.stdout}${result.stderr}`,
      );
    }
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

if (failures.length) {
  console.error("类型解析检查失败：");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
console.log(
  `类型解析检查通过（moduleResolution ${Object.keys(SETTINGS).join(" / ")} 下主入口与 ./reference 都取得到字面量类型）。`,
);
