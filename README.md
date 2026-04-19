# COPR 打包仓库

收纳了 Fedora COPR 打包项目及自动化维护工具。

## 目录结构与脚本说明

项目使用 Python 脚本结合 GitHub Actions 实现自动检测上游更新并触发构建。

### 核心脚本 (`scripts/`)

- **`common.py`**: 核心逻辑库。包含了获取 GitHub (Release/Commit)、AUR、Gitea 上游数据的逻辑，以及版本号转换（Transform）和更新检测算法。
- **`check_upstream.py`**: 自动更新检测器。由 GitHub Actions 调用，遍历 `packages.toml`，识别需要更新的包并生成构建矩阵。
- **`update_spec.py`**: Spec 文件修改器。负责解析上游数据并精确修改 `.spec` 文件中的版本、Commit SHA、日期，并自动生成 Changelog 条目。

### 配置文件

- **`packages.toml`**: 软件包清单。定义了每个包的类型、上游仓库、对应的 `.spec` 文件路径以及目标 COPR 仓库。

## 如何新增一个软件包

要将一个新的软件包加入自动化更新流程，请遵循以下步骤：

1. **准备打包文件**：
   - 在根目录下为新包创建一个目录（例如 `my-app/`）。
   - 在该目录下编写 `.spec` 文件以及所需的辅助文件（如 `.patch`、安装脚本等）。

2. **配置自动化信息**：
   - 编辑根目录下的 `packages.toml`，按以下格式添加配置：

     ```toml
     [my-app]
     type = "github_release"      # 支持: github_release, github_commit, github_commit_complex, aur, gitea_release
     repo = "owner/repo"          # 上游仓库路径
     spec = "my-app/my-app.spec"   # spec 文件路径
     copr_repos = ["user/repo"]   # 目标 Copr 仓库
     # 可选：版本号转换规则
     # transforms = { package_version = "strip_v, dot" } 
     ```

3. **测试本地更新**：
   - 你可以使用 `uv run scripts/check_upstream.py --force` 来查看脚本是否能正确识别并抓取数据。

4. **提交代码**：
   - 提交你的新目录和对 `packages.toml` 的修改。GitHub Actions 会在下次定时任务或手动触发时自动处理构建。

## 本地构建方式 (手动)

如果需要本地调试构建：

```bash
git clone <仓库地址>
cd copr/<子项目目录>
sudo dnf install -y rpmdevtools rpm-build uv
# 确保安装了 copr-cli
uv sync
# 手动构建
rpmbuild -bb <spec文件名>
```

## 备注

这个仓库主要用于维护打包文件和自动化流程，不包含上游应用的完整源码。
