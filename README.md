# COPR 打包仓库

收纳了 Fedora COPR 打包项目：

- [krunner-pinyin-search](krunner-pinyin-search/README.md)：KDE KRunner 的拼音搜索插件打包。
- [um-cli-copr](um-cli-copr/README.md)：um-cli 的 COPR 打包。

## 构建方式

按各自目录中的说明构建。通常流程如下：

	git clone <仓库地址>
	cd copr/<子项目目录>
	sudo dnf install -y rpmdevtools rpm-build
	rpmdev-setuptree
	rpmbuild -bb <spec文件名>

## 安装方式

如果对应包已经发布到 COPR，可以直接启用仓库后安装。具体命令请以子项目 README 中的说明为准。

## 备注

这个仓库主要用于维护打包文件和构建说明，不包含上游应用的完整源码。

## CI/CD 规划

- [CI-CD-REFACTOR.md](docs/CI-CD-REFACTOR.md)：统一收敛 GitHub Actions 与 Copr 构建流程的改造目标和实施方案。

## Python 环境

仓库根目录使用 `uv` 管理 CI/CD 脚本依赖，见 [pyproject.toml](/home/hansel/Documents/ITProject/copr/pyproject.toml:1) 和 [uv.lock](/home/hansel/Documents/ITProject/copr/uv.lock:1)。
