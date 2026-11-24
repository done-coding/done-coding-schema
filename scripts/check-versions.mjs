// 版本一致检查：npm 包与 Python 包从同一个提交构建，版本必须相同（Python 侧按 PEP 440 写法，
// 如 npm 的 1.2.3-alpha.0 对应 1.2.3a0），不同时退出码 1。
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";
import {
  NPM_MANIFEST,
  PY_PROJECT,
  readNpmVersion,
  readPythonVersion,
  toPep440,
} from "./lib/versions.mjs";

const npmVersion = readNpmVersion();
const pythonVersion = readPythonVersion();
const expected = toPep440(npmVersion);

if (pythonVersion !== expected) {
  console.error("npm 包与 Python 包的版本号不一致：");
  console.error(`  - ${path.relative(ROOT, NPM_MANIFEST)}：${npmVersion}`);
  console.error(
    `  - ${path.relative(ROOT, PY_PROJECT)}：${pythonVersion}（应为 ${expected}）`,
  );
  console.error("在仓根运行 node scripts/sync-python-version.mjs 同步。");
  process.exit(1);
}
console.log(`版本一致：npm ${npmVersion} / Python ${pythonVersion}`);
