# 项目说明

这个项目用于将已有源码或上游发布的二进制软件包打包到 Fedora COPR。

## 打包要求

- 写完 `.spec` 文件后，先使用 `rpmspec -P path/to/package.spec` 检查 spec 是否能正常展开。
- 使用 `mock` 构建 SRPM/RPM，确认 spec 文件和依赖声明正确。
- 对预编译二进制包，注意禁用不合适的 debug/strip 处理，避免破坏上游二进制文件。
- 构建完成后，确认没有 unpackaged files、重复文件列表或明显的 RPM build warnings。

## COPR 聚合项目注意事项

- 同一个 COPR 项目的已构建 RPM 会作为该项目后续构建的可用仓库参与依赖解析；它们不会全部自动安装，但任何错误的 `Provides`、`Obsoletes`、`Conflicts` 或过高版本号都可能污染后续 buildroot。
- 对从 `.deb`、`.tar.gz`、AppImage、Electron/Qt 闭源包等重打包的预编译二进制，必须检查 bundled 私有库是否被 RPM 自动生成了系统库 `Provides`，尤其是 `libsqlite3.so.*`、`libssl.so.*`、`libcrypto.so.*`、`libQt5*.so.*`、`libicu*.so.*` 等。
- 安装到 `/opt`、`/usr/lib/<app>` 或其他应用私有目录的 bundled `.so`，通常应排除自动 `Provides`，避免让 dnf 误认为该应用包可以替代 Fedora 官方系统库。例如：

  ```spec
  %global __provides_exclude_from ^/opt/apps/.*$
  ```

  如果私有库的自动依赖也会造成不合理依赖，可按需配合：

  ```spec
  %global __requires_exclude_from ^/opt/apps/.*$
  ```

  路径必须匹配实际 `%install` 后的安装位置；不要写成不存在的目录，否则规则不会生效。
- 重打包预编译二进制后，除了构建成功，还要检查生成的 RPM 元数据，确认没有向外提供私有库：

  ```bash
  rpm -qp --provides path/to/package.rpm
  rpm -qp --requires path/to/package.rpm
  ```

- 若某个包在聚合项目中构建失败，但在单独 COPR 项目或本地干净 `mock` 中成功，应优先排查同项目已有 RPM 是否污染依赖解析。重点查看 COPR 构建日志中 `copr_base` 仓库安装了哪些本项目包，以及是否错误替代了 Fedora 官方依赖。
- 如果发现某个已发布 RPM 污染了聚合项目 buildroot，应先删除该构建结果或修复后重建并重新生成仓库 metadata，再继续构建其他包。
