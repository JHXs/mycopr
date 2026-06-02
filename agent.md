# 项目说明

这个项目用于将已有源码或上游发布的二进制软件包打包到 Fedora COPR。

## 打包要求

- 写完 `.spec` 文件后，先使用 `rpmspec -P path/to/package.spec` 检查 spec 是否能正常展开。
- 使用 `mock` 构建 SRPM/RPM，确认 spec 文件和依赖声明正确。
- 对预编译二进制包，注意禁用不合适的 debug/strip 处理，避免破坏上游二进制文件。
- 构建完成后，确认没有 unpackaged files、重复文件列表或明显的 RPM build warnings。
