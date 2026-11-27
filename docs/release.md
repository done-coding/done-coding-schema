# 发布

> 文档定位：规范 · 两个包怎么以同一个版本发出去。是否发布、何时发布由维护者决定。

## 触发

一个工作流 `.github/workflows/oidc-release.yml`，按合并请求合入的分支决定发什么：

| 合并请求合入      | 产出                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| `release` 分支    | 正式版：npm `latest`，PyPI 正式版本                                                                     |
| `prerelease` 分支 | 预发布：npm `alpha` dist-tag（如 `1.0.1-alpha.0`），PyPI 预发布版本（如 `1.0.1a0`，`pip` 默认不会装到） |

工作流取自 done-coding-template-hub 的 monorepo 模板，本仓在其上加了 Python 包的部分（文件头注释列出了差异）。

## 流程

两个分支的步骤相同，只是定版本的方式与上传目标不同：

1. 同步 master 到发布分支，`pnpm install`。
2. `lerna version --force-publish` 按约定式提交定出 npm 包的新版本（预发布用 `prerelease --preid alpha`）；`--force-publish` 保证只改了 Python 包时也出版本，正式版另加 `--conventional-graduate` 让预发布版本转为正式版本，原因见「本机发布」第 1 步。仓根 `package.json` 的 `version` 生命周期脚本（`scripts/sync-python-version.mjs`）在提交前把同一版本写进 `python/pyproject.toml` 与 `python/uv.lock`，两个包的版本落在同一个版本提交和同一个标签上。
3. 构建两个包并跑 `pnpm check`（样例校验、生成物一致、两包版本一致、许可证副本一致、两语言测试、构建产物检查），再跑 `pnpm check:min-versions`（见下），任一不过即停，不上传任何包。
4. 核对版本形态：正式版只接受 `X.Y.Z`，预发布只接受预发布版本。PyPI 没有 dist-tag，上传即成为可安装的版本，这一步防止把预发布当正式版上传。
5. `lerna publish from-package` 上传 npm 包；`uv publish --trusted-publishing always` 上传 Python 包（wheel 与 sdist）。两边都走可信发布，不用长期令牌。
6. 推送发布分支与标签（正式版另将 master 快进到 release、把 prerelease 重置到 master）。

## 前提（维护者在托管平台上配置）

npm 与 PyPI 都用可信发布：工作流声明 `id-token: write`，上传时用 GitHub 签发的临时凭据，不存长期令牌，也不设 `NODE_AUTH_TOKEN` / `NPM_TOKEN` / `UV_PUBLISH_TOKEN`。缺下面任一项，上传以认证错误失败，不会改用别的凭据。

| 前提                   | 在哪配                                                                                                                    | 填什么                                                                                                                                                                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| npm 可信发布           | npmjs.com 上 `@done-coding/schema-api` 的 Settings → Trusted Publisher → GitHub Actions                                   | Organization or user `done-coding`，Repository `done-coding-schema`，Workflow filename `oidc-release.yml`，Environment name 留空；Allowed actions 勾选 Allow npm publish（不勾则只能发到待审区，要人工批准），Allow npm dist-tag 不勾（dist-tag 在发包时一并设定） |
| PyPI 可信发布          | PyPI 上项目 `done-coding-schema-api` 的 Manage → Publishing → 添加 GitHub 发布者（项目已存在，不用「pending publisher」） | 所有者 `done-coding`，存储库 `done-coding-schema`，工作流 `oidc-release.yml`，环境名称留空                                                                                                                                                                         |
| `RELEASE_GITHUB_TOKEN` | GitHub 仓库 Settings → Secrets and variables → Actions                                                                    | 检出、推送发布分支与标签、快进 master；需要对这些分支的写权限                                                                                                                                                                                                      |

- 两边的登记都只写文件名，带扩展名，拼写与大小写须完全一致；改工作流文件名就要在两边重新登记。npm 的登记建好后不能修改，填错只能删掉重建。
- 环境名称留空，因为工作流没有声明 `environment:`；登记里填了而工作流没有同名环境，上传会被拒。
- npm 要求包的 `package.json` 里 `repository.url` 与该 GitHub 仓库一致（本仓写作 `https://github.com/done-coding/done-coding-schema.git`）。
- 工具版本：npm 可信发布要求 npm 11.5.1 及以上、lerna 9（lerna 7 没有这部分实现）。工作流把 npm 升到 `NPM_VERSION`，仓里的 lerna 是 9.0.7。
- 只在 GitHub 托管的 runner 上运行（不支持自托管 runner）。

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

2. `pnpm check` 全过；再跑 `pnpm check:min-versions`（必做）；按上一节构建到仓外的输出目录，核对两包版本相同、都带 `LICENSE`、文件清单没有意外增减。

   `pnpm check:min-versions`（`scripts/check-min-versions.py`）在最低支持版本上跑全部 Python 测试：构建 wheel，建临时虚拟环境，装 wheel 与最低版本依赖，把测试与样例拷到临时目录跑 pytest（并确认导入的是装好的 wheel），用完清理。最低版本只取自 `python/pyproject.toml`：Python 取 `requires-python` 的下界，运行时依赖取 `dependencies` 各项下界所在次版本的最新修订版（如 `pydantic>=2.11` 装 `pydantic~=2.11.0`），测试工具取 `dependency-groups.dev` 锁定的版本；FastAPI 不是运行时依赖，最低测试版本写在脚本里（`FASTAPI_MINIMUM`）。要联网装包、耗时较长，所以不并进 `pnpm check`，也不在提交钩子里。

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
