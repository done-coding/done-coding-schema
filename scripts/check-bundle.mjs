// npm 包构建产物检查：不引用 Node 内置模块，也不引用未声明为运行时依赖的包，
// 保证能在浏览器端引入。先在包目录里 pnpm build 再运行。
import fs from "node:fs";
import { builtinModules } from "node:module";
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";

const PACKAGE_DIR = path.join(ROOT, "packages", "api");
const OUTPUT_DIRS = ["es", "lib"];
const SPECIFIER_PATTERNS = [
  /\bfrom\s*["']([^"']+)["']/g,
  /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
  /\bimport\s*["']([^"']+)["']/g,
  /\brequire\s*\(\s*["']([^"']+)["']\s*\)/g,
];

const pkg = JSON.parse(
  fs.readFileSync(path.join(PACKAGE_DIR, "package.json"), "utf8"),
);
const runtimeDeps = new Set([
  ...Object.keys(pkg.dependencies ?? {}),
  ...Object.keys(pkg.peerDependencies ?? {}),
]);
const builtins = new Set(builtinModules);

const packageNameOf = (specifier) =>
  specifier.startsWith("@")
    ? specifier.split("/").slice(0, 2).join("/")
    : specifier.split("/")[0];

function filesUnder(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return filesUnder(full);
    return /\.(?:m|c)?js$/.test(entry.name) ? [full] : [];
  });
}

const problems = [];
let fileCount = 0;
for (const dir of OUTPUT_DIRS) {
  const full = path.join(PACKAGE_DIR, dir);
  if (!fs.existsSync(full)) {
    problems.push(`缺少构建产物目录 ${dir}/，先运行 pnpm build`);
    continue;
  }
  for (const file of filesUnder(full)) {
    fileCount += 1;
    const source = fs.readFileSync(file, "utf8");
    for (const pattern of SPECIFIER_PATTERNS) {
      for (const [, specifier] of source.matchAll(pattern)) {
        if (specifier.startsWith(".")) continue;
        const where = path.relative(ROOT, file);
        if (specifier.startsWith("node:") || builtins.has(specifier)) {
          problems.push(`${where} 引用了 Node 内置模块 ${specifier}`);
        } else if (!runtimeDeps.has(packageNameOf(specifier))) {
          problems.push(`${where} 引用了未声明的运行时依赖 ${specifier}`);
        }
      }
    }
  }
}

if (problems.length) {
  console.error("构建产物不适合在浏览器端引入：");
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}
console.log(`构建产物检查通过（${fileCount} 个文件，无 Node 专用依赖）。`);
