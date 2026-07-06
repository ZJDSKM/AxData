# AxData 发布打包验证

本文记录 AxData 发布到 PyPI 前的本地验证流程，以及 GitHub Release 与 PyPI 同步发布方式。

## 包边界

AxData 仓库是 workspace，不建议把根目录的 `axdata-workspace` 当作用户包发布。

面向 PyPI 的候选包包括：

| 包名 | 目录 | 用途 |
| --- | --- | --- |
| `axdata-core` | `libs/axdata_core` | 核心协议、存储、查询、插件、CLI 和采集框架 |
| `axdata` | `packages/axdata-sdk` | 用户侧 Python SDK 和 `import axdata` 入口 |
| `axdata-source-tdx` | `packages/axdata-source-tdx` | 通达信数据源 Provider |
| `axdata-source-tdx-ext` | `packages/axdata-source-tdx-ext` | 通达信扩展行情 Provider |
| `axdata-source-tencent` | `packages/axdata-source-tencent` | 腾讯财经 Provider |
| `axdata-source-cninfo` | `packages/axdata-source-cninfo` | 巨潮 Provider |

`axdata` 用户主包依赖 `axdata-core[parquet]`，并带上本地诊断和 API 运行所需的 FastAPI、uvicorn、pydantic、python-multipart 等依赖；直接安装 `axdata-core` 仍保持更轻量，插件开发者可按需安装 `axdata-core[parquet]`。

普通用户发布后的推荐安装入口是：

```powershell
python -m pip install axdata
```

`axdata` 会同时安装当前默认数据源插件：`axdata-source-tdx`、`axdata-source-tdx-ext`、`axdata-source-tencent` 和 `axdata-source-cninfo`。TDX/TDX Ext 插件安装后应默认可用，用户不需要在快速开始里手动执行 `plugin enable`。

发布顺序应先发 `axdata-core`，再发数据源插件包，最后发 `axdata`。GitHub Actions 的 release workflow 已按这个顺序执行。

## 本地 PyPI Readiness

运行：

```powershell
.\.venv\Scripts\python scripts\pypi_readiness.py --json
```

脚本会在临时目录内完成：

- 复制各候选包源码，避免在仓库源码目录生成 `dist/`、`build/` 或 `*.egg-info`。
- 为每个候选包构建 wheel 和 sdist。
- 运行 `twine check` 检查包元数据和 README 渲染。
- 创建全新的安装 venv，从本地 wheel 安装候选包。
- 验证 `import axdata`、`import axdata_core` 和各数据源插件模块。
- 验证 Provider entry point、包内 `axdata-provider.json` 和关键资源文件。
- 验证 `axdata` 的 wheel 元数据包含当前默认数据源插件依赖。
- 验证随项目提供的 TDX/TDX Ext Provider 安装后默认进入 enabled 状态。
- 运行 `axdata --help`、`axdata init`、`axdata doctor`、`axdata status`、`axdata plugin list`。

保留临时目录以便排错：

```powershell
$work = "$env:TEMP\axdata-pypi-readiness"
.\.venv\Scripts\python scripts\pypi_readiness.py --work-dir $work --json
```

如果只想跳过 `twine check`：

```powershell
.\.venv\Scripts\python scripts\pypi_readiness.py --skip-twine-check --json
```

## GitHub Release 同步 PyPI

仓库内的 `.github/workflows/release.yml` 负责发布自动化：

- 发布 GitHub Release 时触发。
- 先运行 PyPI readiness，确认 wheel、sdist、README 元数据、安装和插件发现都正常。
- 构建 6 个候选包的 wheel 和 sdist。
- 把构建产物附加到 GitHub Release。
- 使用 PyPI Trusted Publishing 按顺序上传到 PyPI：先 `axdata-core`，再数据源插件包，最后 `axdata`。

发布标签必须和包版本一致。例如当前所有候选包版本都是 `0.1.0`，则 GitHub Release 标签应为 `v0.1.0` 或 `0.1.0`。PyPI 不允许覆盖已发布的同名同版本文件；如果要重新发布，需要先提升版本号。

### 首次发布前的 PyPI 设置

当前 workflow 使用 PyPI Trusted Publishing，不需要在 GitHub 仓库里保存 PyPI token。首次发布前，需要在 PyPI 为以下项目配置 Trusted Publisher：

| PyPI 项目 | GitHub owner | GitHub repo | Workflow | Environment |
| --- | --- | --- | --- | --- |
| `axdata-core` | `electkismet` | `AxData` | `release.yml` | `pypi` |
| `axdata-source-tdx` | `electkismet` | `AxData` | `release.yml` | `pypi` |
| `axdata-source-tdx-ext` | `electkismet` | `AxData` | `release.yml` | `pypi` |
| `axdata-source-tencent` | `electkismet` | `AxData` | `release.yml` | `pypi` |
| `axdata-source-cninfo` | `electkismet` | `AxData` | `release.yml` | `pypi` |
| `axdata` | `electkismet` | `AxData` | `release.yml` | `pypi` |

如果这些 PyPI 项目还没有创建，需要在 PyPI 创建对应项目或配置 pending publisher；最终以 PyPI 后台可用选项为准。

### 发布前检查

正式发布前建议按顺序确认：

1. `main` 分支干净，CI 通过。
2. 6 个候选包的 `pyproject.toml` 版本号一致。
3. 本地 PyPI readiness 通过。
4. PyPI 已为 6 个项目配置 Trusted Publisher。
5. GitHub Release 标签等于当前包版本，例如 `v0.1.0`。

可以先只跑构建检查，不上传 PyPI：

```powershell
gh workflow run release.yml --repo electkismet/AxData --ref main -f publish=false
```

确认无误后，在 GitHub 创建并发布 Release。发布 Release 后，workflow 会自动上传 PyPI：

```powershell
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --repo electkismet/AxData --title "AxData v0.1.0" --notes "Initial public release"
```

如需手动重跑真实发布，必须从标签触发：

```powershell
gh workflow run release.yml --repo electkismet/AxData --ref v0.1.0 -f publish=true
```

## 本地脚本不包含的动作

该脚本不做：

- 不上传 PyPI。
- 不上传 TestPyPI。
- 不创建 GitHub release。
- 不修改 git remote。
- 不推送代码。
- 不请求真实数据源。

真正发布前还应先在 TestPyPI 演练一次完整安装链路，并确认包名、版本号、依赖、README 渲染、命令行入口和插件发现都符合预期。
