# COPR 打包仓库

收纳了 Fedora COPR 打包项目及自动化维护工具。

## 软件包状态

由 `python scripts/generate_readme_status.py` 自动生成。

<!-- AUTO-GENERATED:STATUS_TABLE:START -->
| Package | Status |
| --- | --- |
| `cc-switch-cli` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/cc-switch-cli/package/cc-switch-cli/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/cc-switch-cli/package/cc-switch-cli/) |
| `maple-mono-nf-cn-unhinted` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/nerd-fonts/package/maple-mono-nf-cn-unhinted/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/nerd-fonts/package/maple-mono-nf-cn-unhinted/) |
| `obsidian` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/obsidian/package/obsidian/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/obsidian/package/obsidian/) |
| `proxybridge` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/proxybridge/package/proxybridge/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/proxybridge/package/proxybridge/) |
| `reframe` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/reframe/package/reframe/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/reframe/package/reframe/) |
| `um-cli` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/um-cli/package/um-cli/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/um-cli/package/um-cli/) |
| `ge-proton` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/mycopr/package/ge-proton/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/mycopr/package/ge-proton/) |
| `cto2api` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/cto2api/package/cto2api/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/cto2api/package/cto2api/) |
| `krunner-pinyin-search` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/krunner-pinyin-search/package/krunner-pinyin-search/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/krunner-pinyin-search/package/krunner-pinyin-search/) |
| `zotero` | [![Copr build status](https://copr.fedorainfracloud.org/coprs/ikunji/mycopr/package/zotero/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ikunji/mycopr/package/zotero/) |
<!-- AUTO-GENERATED:STATUS_TABLE:END -->

## 目录结构与脚本说明

项目使用 Python 脚本结合 GitHub Actions 实现自动检测上游更新并触发构建。

### 核心脚本 (`scripts/`)

- **`common.py`**: 核心逻辑库。包含了获取 GitHub (Release/Commit)、AUR、Gitea 上游数据的逻辑，以及版本号转换（Transform）和更新检测算法。
- **`check_upstream.py`**: 自动更新检测器。由 GitHub Actions 调用，遍历 `packages/packages.toml`，识别需要更新的包并生成构建矩阵。
- **`update_spec.py`**: Spec 文件修改器。负责按照 `transforms` 配置更新 `.spec` 中的 `%global` 宏，必要时自动生成 Changelog 条目，并在非 commit 类包上重置 `Release`。
- **`generate_readme_status.py`**: README 状态表生成器。根据 `packages/packages.toml` 和各个 `.spec` 里的 `Name:` 自动生成 Copr build status 表。

### 配置文件

- **`packages/packages.toml`**: 软件包清单。定义了每个包的类型、上游仓库、对应的 `.spec` 文件路径以及目标 COPR 仓库。
- **`packages/`**: 所有软件包目录的统一根目录。每个包的 `.spec` 和辅助文件都放在这里。

当前支持的 `type`:

- `github_release`
- `github_commit`
- `aur`
- `gitea_release`

## 如何新增一个软件包

要将一个新的软件包加入自动化更新流程，请遵循以下步骤：

1. **准备打包文件**：
   - 在 `packages/` 下为新包创建一个目录（例如 `packages/my-app/`）。
   - 在该目录下编写 `.spec` 文件以及所需的辅助文件（如 `.patch`、安装脚本等）。

2. **配置自动化信息**：
   - 编辑 `packages/packages.toml`，按以下格式添加配置：

     ```toml
     [my-app]
     type = "github_release"     # 支持: github_release, github_commit, aur, gitea_release
     repo = "owner/repo"         # 上游仓库路径
     spec = "packages/my-app/my-app.spec" # spec 文件路径
     copr_repos = ["user/repo"]  # 目标 Copr 仓库
     # 可选：版本号转换规则
     # transforms = { package_version = "strip_v, dot" }
     ```

   常用字段说明：

   - `repo`: GitHub/Gitea 仓库路径，或 AUR 包名。
   - `spec`: 对应 spec 文件的相对路径。
   - `copr_repos`: 需要触发构建的 Copr 仓库列表。
   - `transforms`: 指定上游数据如何映射到 spec 中的 `%global` 变量。常用规则包括 `strip_v`、`dot`、`strip:TEXT`。
   - `update_changelog`: 仅在需要为 commit 类包自动追加 `%changelog` 条目时启用。
   - `reset_release`: 默认为 `true`。对 release 类包更新后会重置 `Release: 1%{?dist}`；commit 类包通常不需要。

   `github_commit` 类型通常需要显式声明要更新的宏，例如：

   ```toml
   [my-git-package]
   type = "github_commit"
   repo = "owner/repo"
   spec = "packages/my-git-package/my-git-package.spec"
   copr_repos = ["user/repo"]
   transforms = { git_commit = "raw", git_short = "raw", commit_date = "raw" }
   update_changelog = true
   ```

   对应的 spec 中通常需要存在这些 `%global` 宏：

   ```spec
   %global git_commit ...
   %global git_short ...
   %global commit_date ...
   ```

3. **测试本地更新**：
   - 你可以使用 `uv run scripts/check_upstream.py --force` 来查看脚本是否能正确识别并抓取数据。
   - 你也可以用 `uv run scripts/update_spec.py --pkg <包名> --upstream-data '<JSON>'` 单独测试 spec 更新逻辑。

4. **提交代码**：
   - 提交你的新目录和对 `packages/packages.toml` 的修改。GitHub Actions 会在下次定时任务或手动触发时自动处理构建。

## 本地构建方式 (手动)

如果需要本地调试构建：

```bash
git clone <仓库地址>
cd copr
sudo dnf install -y mock rpmdevtools rpm-build spectool
# 将当前用户加入 mock 组（首次使用需要重新登录）
sudo usermod -aG mock $USER

# 下载 spec 中声明的源码到当前目录
spectool -g -R packages/<子项目目录>/<spec文件名>

# 使用 mock 构建 SRPM
mock -r fedora-rawhide-x86_64 --buildsrpm \
  --spec packages/<子项目目录>/<spec文件名> \
  --sources .
  
cp /var/lib/mock/fedora-rawhide-x86_64/result/*.src.rpm .

# 使用 mock 构建二进制 RPM
mock -r fedora-rawhide-x86_64 --rebuild ./xxx.src.rpm
```

## 备注

这个仓库主要用于维护打包文件和自动化流程，不包含上游应用的完整源码。
