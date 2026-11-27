// 把 npm 包的版本同步到 Python 包（pyproject.toml 与 uv.lock）。
// 发布流程里由 lerna 的 version 生命周期调用：lerna 改完 npm 包版本、提交之前运行，
// 再把改动加进同一个版本提交，保证两个包同一提交、同一版本。
import { spawnSync } from "node:child_process";
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";
import { readNpmVersion, toPep440 } from "./lib/versions.mjs";

const version = toPep440(readNpmVersion());
const result = spawnSync(
  "uv",
  ["version", "--project", path.join(ROOT, "python"), "--no-sync", version],
  { stdio: "inherit" },
);
if (result.error || result.status !== 0) {
  console.error(`同步 Python 包版本失败：${result.error?.message ?? ""}`);
  process.exit(1);
}
