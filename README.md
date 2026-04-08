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
