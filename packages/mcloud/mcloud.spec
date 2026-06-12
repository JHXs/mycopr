# 禁用 debug 包和 strip 相关 BRP，避免破坏预编译二进制文件
%global debug_package %{nil}
%global _build_id_links none
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
# 不让 /opt/apps 下的上游自带私有库参与自动 Provides，避免污染同一 COPR 项目的 buildroot
%global __provides_exclude_from ^/opt/apps/%{appid}/.*$
%global __requires_exclude ^libQt5.*\.so.*$
%global __requires_exclude ^libicu.*\.so.*$
# 跳过上游预编译二进制的 RPATH/RUNPATH 检查
%global __brp_check_rpaths %{nil}

%global appid       com.cmic.mcloud
%global kylinv      111
%global package_version 1.1.1

Name:           mcloud
Version:        %{package_version}
Release:        1%{?dist}
Summary:        中国移动云盘
Summary(en):    China Mobile Cloud Drive

License:        LicenseRef-Proprietary
URL:            https://yun.139.com/
Source0:        https://yun.mcloud.139.com/mCloudPc/kylinV%{kylinv}/com.cmic.mcloud_%{version}_amd64.deb
Source1:        mcloud-wrapper
Source2:        com.cmic.mcloud.desktop

ExclusiveArch:  x86_64

Requires:       qt5-qtbase
Requires:       qt5-qtmultimedia
Requires:       hicolor-icon-theme

%description
中国移动云盘 - China Mobile Cloud Drive desktop client.

This package repackages the upstream prebuilt binary release.

%description -l zh_CN
中国移动云盘桌面客户端。

本软件包重新打包了上游发布的预编译二进制文件。

%prep
# 从 deb 包中提取 data.tar.xz
ar p %{SOURCE0} data.tar.xz | xz -d > data.tar
tar -xf data.tar --exclude='*icons_mac*'

%build
# 上游提供预编译二进制文件，无需编译

%install
# 创建目标目录
install -d %{buildroot}/opt/apps/%{appid}
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_datadir}/applications
install -d %{buildroot}%{_datadir}/icons/hicolor/512x512/apps

# 安装应用文件
cp -a opt/apps/%{appid}/* %{buildroot}/opt/apps/%{appid}/

# 移除上游自带的 Qt 库，使用系统提供的版本
rm -f %{buildroot}/opt/apps/%{appid}/processes/libQt5*.so*

# 安装图标
install -Dm644 usr/share/icons/hicolor/512x512/apps/%{appid}.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png

# 安装 desktop 文件
install -Dm644 %{SOURCE2} \
    %{buildroot}%{_datadir}/applications/%{appid}.desktop

# 安装 wrapper 启动脚本
install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/mcloud

%files
%{_bindir}/mcloud
/opt/apps/%{appid}/
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png

%changelog
* Thu Jun 11 2026 Hansel <hansel@example.com> - 1.1.1-1
- Initial package for China Mobile Cloud Drive
