# =============================================================================
# RPM 解包重打包模板 (RPM Repackaging Template for Copr)
# =============================================================================
#
# 适用场景：上游只提供预编译 RPM，不提供源码压缩包。
# 本 spec 的策略是：
#   1. 将上游 RPM 作为 Source0 下载
#   2. 用 rpm2cpio | cpio 解包到 buildroot
#   3. 修复上游打包缺陷（路径、RPATH 等）
#   4. 重新打包成符合 Fedora/COPR 规范的 RPM
#
# 使用方法：将 "myapp" / "MyApp" 及各路径替换为实际软件信息。
# =============================================================================

# 禁用 debuginfo 子包（二进制来自上游，无调试符号可用）
%global debug_package %{nil}

# ---------------------------------------------------------------------------
# 元信息（Metadata）
# ---------------------------------------------------------------------------
Name:           myapp
Version:        1.0.0
Release:        1%{?dist}
Summary:        Short one-line description of MyApp

# 使用上游许可证标识符，可在 https://spdx.org/licenses/ 查询
License:        Apache-2.0
URL:            https://github.com/example/myapp

# Source0：上游发布的预编译 RPM（x86_64）
# 常见命名格式参考：
#   GitHub Releases: %{url}/releases/download/v%{version}/%{name}-%{version}.x86_64.rpm
#   或不带 v 前缀：  %{url}/releases/download/%{version}/%{name}-%{version}-1.x86_64.rpm
Source0:        %{url}/releases/download/v%{version}/%{name}-%{version}.x86_64.rpm

# ---------------------------------------------------------------------------
# 构建依赖（Build Dependencies）
# ---------------------------------------------------------------------------
# rpm2cpio / cpio 在 rpm-build 环境中通常已内置，无需额外声明。
# chrpath 用于修复 ELF 二进制中的无效 RPATH（若上游存在此问题则添加）
BuildRequires:  chrpath
BuildRequires:  cpio

# ---------------------------------------------------------------------------
# 运行时依赖（Runtime Dependencies）
# ---------------------------------------------------------------------------
# 根据实际情况添加，例如：
# Requires: libXcb, webkit2gtk4.0, ...
# Requires: %%{name}-data = %%{version}

# 仅支持 x86_64（若上游同时提供 aarch64，可参考 分架构参考-codex.spec 扩展）
ExclusiveArch:  x86_64

%description
MyApp is an example application.

This spec repackages the upstream prebuilt RPM for distribution via Copr.
No source compilation is performed.

# ---------------------------------------------------------------------------
# %prep：准备阶段
# ---------------------------------------------------------------------------
# 上游 RPM 直接在 %install 阶段解包，此处无需操作。
%prep
# Nothing to do — source RPM is extracted directly in %%install.

# ---------------------------------------------------------------------------
# %build：构建阶段
# ---------------------------------------------------------------------------
# 无源码编译，跳过。
%build
# Nothing to build.

# ---------------------------------------------------------------------------
# %install：安装阶段（核心）
# ---------------------------------------------------------------------------
%install
# 清理并重建 buildroot
rm -rf %{buildroot}
mkdir -p %{buildroot}

# 将上游 RPM 的全部文件解包到 buildroot
# rpm2cpio 将 RPM 转成 cpio 流；cpio -idmv 解包并保留目录结构
rpm2cpio %{SOURCE0} | cpio -idmv -D %{buildroot}

# ------------------------------------------------------------------
# 修复 1：去除无效 RPATH
# 上游二进制可能携带构建机器上的绝对路径（如 /workspace/...），
# 在目标系统中无意义，且会触发 rpmlint 警告，用 chrpath 删除。
# ------------------------------------------------------------------
find %{buildroot} -type f \( -name '*.so*' -o -perm -0111 \) \
    -exec sh -c '
        for bin; do
            if file "$bin" 2>/dev/null | grep -q ELF; then
                rpath=$(chrpath -l "$bin" 2>/dev/null || true)
                # 根据实际情况修改过滤关键字，例如 /workspace/ 或 /home/runner/
                if echo "$rpath" | grep -q "/workspace/"; then
                    chrpath -d "$bin"
                    echo "Stripped RPATH from: $bin"
                fi
            fi
        done
    ' sh {} +

# ------------------------------------------------------------------
# 修复 2：.desktop 文件不在标准路径
# 上游有时将 .desktop 放在 %{_datadir}/%{name}/files/ 而非
# %{_datadir}/applications/，导致桌面环境找不到应用入口。
# ------------------------------------------------------------------
mkdir -p %{buildroot}%{_datadir}/applications
install -m 644 \
    %{buildroot}%{_datadir}/%{name}/files/%{name}.desktop \
    %{buildroot}%{_datadir}/applications/%{name}.desktop

# ------------------------------------------------------------------
# 修复 3：可执行文件不在 PATH
# 上游有时将主程序安装在 %{_datadir}/%{name}/ 而非 %{_bindir}/，
# 用软链接将其暴露到 PATH 中。
# ------------------------------------------------------------------
mkdir -p %{buildroot}%{_bindir}
ln -s %{_datadir}/%{name}/%{name} %{buildroot}%{_bindir}/%{name}

# ------------------------------------------------------------------
# 修复 4：systemd service 文件不在标准路径（若有）
# ------------------------------------------------------------------
mkdir -p %{buildroot}/usr/lib/systemd/system
install -m 644 \
    %{buildroot}%{_datadir}/%{name}/files/%{name}.service \
    %{buildroot}/usr/lib/systemd/system/%{name}.service

# ---------------------------------------------------------------------------
# %files：声明打包文件列表
# ---------------------------------------------------------------------------
# 根据解包后的实际目录结构调整。
# 可用 `find %{buildroot} -not -type d | sort` 辅助确认路径。
%files
# 主可执行入口（软链接）
%{_bindir}/%{name}

# 主数据目录（二进制、资源文件等）
%{_datadir}/%{name}/

# 桌面菜单入口
%{_datadir}/applications/%{name}.desktop

# 图标（按实际分辨率和格式调整）
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/icons/hicolor/*/apps/%{name}.svg

# systemd 服务文件（若有）
/usr/lib/systemd/system/%{name}.service

# ---------------------------------------------------------------------------
# scriptlets：安装/卸载脚本
# ---------------------------------------------------------------------------

# 安装后：启用并启动服务（若有 systemd service）
%post
%systemd_post %{name}.service

# 卸载前：停止并禁用服务
%preun
%systemd_preun %{name}.service

# 卸载后：重载 systemd daemon
%postun
%systemd_postun_with_restart %{name}.service

# ---------------------------------------------------------------------------
# %changelog
# ---------------------------------------------------------------------------
%autochangelog
