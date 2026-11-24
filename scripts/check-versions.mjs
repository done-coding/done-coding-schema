// 版本一致检查：npm 包与 Python 包从同一个提交构建，版本号必须相同，不同时退出码 1。
import fs from "node:fs";
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";

const NPM_MANIFEST = path.join(ROOT, "packages", "api", "package.json");
const PY_PROJECT = path.join(ROOT, "python", "pyproject.toml");

/** 只读 pyproject.toml 的 [project] 表里的 version。 */
function readPythonVersion(text) {
  const table = text.split(/^\[/m).find((part) => part.startsWith("project]"));
  const match = table?.match(/^version\s*=\s*"([^"]+)"\s*$/m);
  if (!match)
    throw new Error(
      `${path.relative(ROOT, PY_PROJECT)}：[project] 里没有 version`,
    );
  return match[1];
}

const versions = {
  [path.relative(ROOT, NPM_MANIFEST)]: JSON.parse(
    fs.readFileSync(NPM_MANIFEST, "utf8"),
  ).version,
  [path.relative(ROOT, PY_PROJECT)]: readPythonVersion(
    fs.readFileSync(PY_PROJECT, "utf8"),
  ),
};

const distinct = new Set(Object.values(versions));
if (distinct.size !== 1) {
  console.error("npm 包与 Python 包的版本号不一致：");
  for (const [file, version] of Object.entries(versions)) {
    console.error(`  - ${file}：${version}`);
  }
  process.exit(1);
}
console.log(`版本一致：${[...distinct][0]}`);
