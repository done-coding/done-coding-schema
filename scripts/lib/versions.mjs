// npm 包与 Python 包的版本号：同一个版本，两种写法。
import fs from "node:fs";
import path from "node:path";
import { ROOT } from "./schemas.mjs";

export const NPM_MANIFEST = path.join(ROOT, "packages", "api", "package.json");
export const PY_PROJECT = path.join(ROOT, "python", "pyproject.toml");

/** npm 预发布标识 → PEP 440 预发布段。 */
const PRE_RELEASE = { alpha: "a", beta: "b", rc: "rc" };

/**
 * npm（SemVer）版本 → PEP 440 版本：1.2.3 → 1.2.3；1.2.3-alpha.0 → 1.2.3a0；
 * 1.2.3-beta.1 → 1.2.3b1；1.2.3-rc.2 → 1.2.3rc2。其他写法两边无法一一对应，直接报错。
 */
export function toPep440(npmVersion) {
  const match = /^(\d+\.\d+\.\d+)(?:-(alpha|beta|rc)\.(\d+))?$/.exec(
    npmVersion,
  );
  if (!match) {
    throw new Error(
      `npm 版本 ${npmVersion} 无法对应到 Python 版本：只支持 X.Y.Z 与 X.Y.Z-(alpha|beta|rc).N`,
    );
  }
  const [, release, tag, number] = match;
  return tag ? `${release}${PRE_RELEASE[tag]}${number}` : release;
}

export const readNpmVersion = () =>
  JSON.parse(fs.readFileSync(NPM_MANIFEST, "utf8")).version;

/** 只读 pyproject.toml 的 [project] 表里的 version。 */
export function readPythonVersion() {
  const text = fs.readFileSync(PY_PROJECT, "utf8");
  const table = text.split(/^\[/m).find((part) => part.startsWith("project]"));
  const match = table?.match(/^version\s*=\s*"([^"]+)"\s*$/m);
  if (!match) {
    throw new Error(
      `${path.relative(ROOT, PY_PROJECT)}：[project] 里没有 version`,
    );
  }
  return match[1];
}
