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
2. `lerna version` 按约定式提交定出 npm 包的新版本（预发布用 `prerelease --preid alpha`）。仓根 `package.json` 的 `version` 生命周期脚本（`scripts/sync-python-version.mjs`）在提交前把同一版本写进 `python/pyproject.toml` 与 `python/uv.lock`，两个包的版本落在同一个版本提交和同一个标签上。
3. 构建两个包并跑 `pnpm check`（样例校验、生成物一致、两包版本一致、两语言测试、构建产物检查），任一不过即停，不上传任何包。
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

## 中途失败

- 第 3、4 步失败：什么都没上传，修好后重新合并即可。
- npm 已上传、PyPI 失败：在同一个标签的提交上补传 Python 包（`uv build --project python` 后 `uv publish --check-url https://pypi.org/simple/ python/dist/*`），不要另起版本号；`--check-url` 会跳过已上传的文件。
- 不要为了「补齐」单独改某一个包的版本号：`pnpm check:versions` 与提交钩子会拦下两包版本不一致。
