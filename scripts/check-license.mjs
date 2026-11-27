// 许可证一致检查：npm 包与 Python 包各带一份仓根 LICENSE 的副本（打包只收包目录内的文件），
// 副本须与仓根逐字节相同，不同或缺失时退出码 1。
import fs from "node:fs";
import path from "node:path";
import { ROOT } from "./lib/schemas.mjs";

const SOURCE = path.join(ROOT, "LICENSE");
const COPIES = [
  path.join(ROOT, "packages", "api", "LICENSE"),
  path.join(ROOT, "python", "LICENSE"),
];

const expected = fs.readFileSync(SOURCE);
const stale = COPIES.filter(
  (copy) => !fs.existsSync(copy) || !fs.readFileSync(copy).equals(expected),
);

if (stale.length > 0) {
  console.error("以下许可证副本缺失或与仓根 LICENSE 不同：");
  for (const copy of stale) console.error(`  - ${path.relative(ROOT, copy)}`);
  console.error("从仓根 LICENSE 复制过去。");
  process.exit(1);
}
console.log(`许可证副本一致：${COPIES.length} 份`);
