# 发布

> 文档定位：规范 · 两个包怎么以同一个版本发出去。是否发布、何时发布由维护者决定。

## 触发

| 合并请求合入 | 工作流 | 产出 |
|---|---|---|
| `release` 分支 | `.github/workflows/release-publish.yml` | 正式版：npm `latest`，PyPI 正式版本 |
| `prerelease` 分支 | `.github/workflows/prerelease-publish.yml` | 预发布：npm `alpha` dist-tag（如 `1.0.1-alpha.0`），PyPI 预发布版本（如 `1.0.1a0`，`pip` 默认不会装到） |

## 流程

两个工作流的步骤相同，只是定版本的方式与上传目标不同：

1. 同步 master 到发布分支，`pnpm install`。
2. `lerna version --force-publish` 按约定式提交定出 npm 包的新版本（预发布用 `prerelease --preid alpha`）；`--force-publish` 保证只改了 Python 包时也出版本，正式版另加 `--conventional-graduate` 让预发布版本转为正式版本，原因见「本机发布」第 1 步。仓根 `package.json` 的 `version` 生命周期脚本（`scripts/sync-python-version.mjs`）在提交前把同一版本写进 `python/pyproject.toml` 与 `python/uv.lock`，两个包的版本落在同一个版本提交和同一个标签上。
3. 构建两个包并跑 `pnpm check`（样例校验、生成物一致、两包版本一致、许可证副本一致、两语言测试、构建产物检查），任一不过即停，不上传任何包。
4. 核对版本形态：正式版只接受 `X.Y.Z`，预发布只接受预发布版本。PyPI 没有 dist-tag，上传即成为可安装的版本，这一步防止把预发布当正式版上传。
5. `lerna publish from-package` 上传 npm 包；`uv publish` 上传 Python 包（wheel 与 sdist）。
6. 推送发布分支与标签（正式版另将 master 快进到 release、把 prerelease 重置到 master）。

## 凭据（维护者在托管平台上配置）

工作流只引用凭据，不读取、不打印。首次发布前需要：

| 凭据 | 在哪配 | 用途 |
|---|---|---|
| `NPM_TOKEN` | GitHub 仓库 Settings → Secrets and variables → Actions | 对 `@done-coding` 组织有发布权限的 npm 自动化令牌 |
| `RELEASE_GITHUB_TOKEN` | 同上 | 推送发布分支、master 与标签 |
| PyPI 可信发布 | PyPI 账号 → Publishing → 添加 GitHub 发布者（项目尚不存在时用「pending publisher」） | 项目名 `done-coding-schema-api`，Owner `done-coding`，仓库 `done-coding-schema`，工作流各登记一次：`release-publish.yml`、`prerelease-publish.yml`；Environment 留空。工作流已声明 `id-token: write`，`uv publish` 自动走可信发布，不需要长期令牌 |

不用可信发布时，改为在 PyPI 生成项目级 API 令牌，存为仓库密钥 `PYPI_TOKEN`，并在两个工作流的「Publish Python package」步骤加上 `env: UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}`。

## 本机演练（只构建，不上传）

```bash
pnpm install && uv sync --project python
pnpm check
node scripts/check-versions.mjs
pnpm -F @done-coding/schema-api build
(cd packages/api && pnpm pack --pack-destination <输出目录>)
uv build --project python --out-dir <输出目录>
```

核对输出目录里 npm 包（`.tgz`）与 Python 包（`.whl`、`.tar.gz`）的版本相同，文件清单与上一次发布相比没有意外的增减。

## 本机发布

不经工作流、由维护者在本机发布时的做法（首个预发布 `0.0.1-alpha.0` / `0.0.1a0` 即按此发出）。每次发布须维护者本人授权；令牌由维护者存在仓外、仅本人可读的文件里，只在发布命令的同一条 shell 里经命令替换读入环境变量，不打印、不写进仓内文件、`~/.npmrc` 或提交说明。

1. 在要发布的分支上、工作树干净时定版本（只在本地生成版本提交与标签，不推送）：

   ```bash
   # 预发布
   npx lerna version prerelease --force-publish --yes --preid alpha --no-push --message "chore(prerelease): publish [skip ci]"
   # 正式版
   npx lerna version --force-publish --conventional-graduate --yes --no-push --message "chore(release): publish [skip ci]"
   ```

   `version` 生命周期脚本会把同一版本同步给 Python 包，并放进同一个版本提交。

   `--force-publish` 不能省：两个包共用一个版本号，只改了 Python 包时 lerna 会判 npm 包「无变化」而不出版本，发布就此停住。加上它，任一边有改动都两个包一起出版本。这时 npm 包的 CHANGELOG 记为「Version bump only」（对 npm 包属实），这一版的改动看同一版本区间的提交记录。正式版的 `--conventional-graduate` 让当前的预发布版本（如 `0.0.1-alpha.4`）转为正式版本（`0.0.1`）；不加时约定式提交只会把预发布号加一（`0.0.1-alpha.5`），版本形态检查会拒绝。当前已是正式版本时它不起作用。

2. `pnpm check` 全过；按上一节构建到仓外的输出目录，核对两包版本相同、都带 `LICENSE`、文件清单没有意外增减。

3. 先上传 npm：在仓外临时目录放一个 npmrc，内容只有 `//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}`（由 npm 展开环境变量，文件里不落令牌），从该目录执行：

   ```bash
   NODE_AUTH_TOKEN="$(cat <npm 令牌文件>)" npm publish <输出目录>/<包名>-<版本>.tgz \
     --tag alpha --access public --registry https://registry.npmjs.org/ --userconfig <临时 npmrc>
   ```

   本机 npm 的默认源可能是镜像，`--registry` 须写官方源。正式版把 `--tag alpha` 换成默认的 `latest`。

4. 再上传 PyPI（wheel 与 sdist）：

   ```bash
   UV_PUBLISH_TOKEN="$(cat <PyPI 令牌文件>)" uv publish --check-url https://pypi.org/simple/ <输出目录>/*.whl <输出目录>/*.tar.gz
   ```

5. 核对：`npm view @done-coding/schema-api dist-tags --registry https://registry.npmjs.org/` 与 PyPI 项目页的版本一致；空目录各装一次线上包（npm 用对应 dist-tag，pip 装预发布加 `--pre`），跑通 README 的最小例子。新上传的包要过几分钟才查得到。

6. 推送分支与版本标签：`git push origin <分支>` 与 `git push origin <标签>`。

## 中途失败

- 第 3、4 步失败：什么都没上传，修好后重新合并即可。
- npm 已上传、PyPI 失败：在同一个标签的提交上补传 Python 包（`uv build --project python` 后 `uv publish --check-url https://pypi.org/simple/ python/dist/*`），不要另起版本号；`--check-url` 会跳过已上传的文件。
- 不要为了「补齐」单独改某一个包的版本号：`pnpm check:versions` 与提交钩子会拦下两包版本不一致。
