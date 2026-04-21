# 禁用 debug 包和 strip 相关 BRP，避免破坏预编译的 .NET 二进制文件
%global debug_package %{nil}
%global _build_id_links none
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
%global appid net.steampp.app
%global package_version 3.1.0

Name:           watt-toolkit
Version:        %{package_version}
Release:        2%{?dist}
Summary:        A cross-platform Steam toolbox
Summary(zh_CN): 一个开源跨平台的多功能 Steam 工具箱

License:        GPL-3.0-only
URL:            https://steampp.net/
ExclusiveArch:  x86_64
Source0:        https://github.com/BeyondDimension/SteamTools/releases/download/%{version}/Steam++_v%{version}_linux_x64.tgz
Source1:        watt-toolkit.desktop
Source2:        watt-toolkit
Source3:        environment_check.sh

# 核心运行时依赖
Requires:       dotnet-runtime-10.0
Requires:       aspnetcore-runtime-10.0
Requires:       nss-tools
Requires:       libcap
# 图形与 UI 框架 (Avalonia/Skia) 所需依赖
Requires:       fontconfig
Requires:       freetype
Requires:       libX11
Requires:       libXcursor
Requires:       libXext
Requires:       libXi
Requires:       libXrandr
Requires:       libXrender
Requires:       libICE
Requires:       libSM
Requires:       hicolor-icon-theme
# 补充底层库
Requires:       expat
Requires:       zlib
Requires:       libpng
Requires:       harfbuzz
Requires:       brotli
Requires:       glib2
Requires:       graphite2
Requires:       pcre2
Requires:       libgcc
Requires:       libstdc++
Requires:       icu

%description
An open-source, cross-platform, multi-functional Steam toolbox.
Includes features such as achievement unlocking, local acceleration, and inventory management.

%description -l zh_CN
一个开源跨平台的多功能 Steam 工具箱。
包含成就解锁、本地加速、库存管理等功能。

%prep
%autosetup -c

%build
# 二进制包无需编译

%install
mkdir -p %{buildroot}%{_libdir}/%{name}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps

# 安装程序文件
cp -a assemblies/. %{buildroot}%{_libdir}/%{name}/
cp -a native/linux-x64/. %{buildroot}%{_libdir}/%{name}/
cp -a modules %{buildroot}%{_libdir}/%{name}/

# 保留上游权限，仅修正已知需要执行权限的文件
chmod 755 %{buildroot}%{_libdir}/%{name}/modules/Accelerator/Steam++.Accelerator

# 安装图标和 Desktop 文件
install -Dm644 Icons/Watt-Toolkit.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{appid}.desktop

# 安装环境检查脚本
mkdir -p %{buildroot}%{_libdir}/%{name}/script
install -Dm755 %{SOURCE3} %{buildroot}%{_libdir}/%{name}/script/environment_check.sh

# 安装启动脚本并修正硬编码路径
sed 's|/usr/lib/watt-toolkit|%{_libdir}/%{name}|g' %{SOURCE2} > %{buildroot}%{_libdir}/%{name}/Steam++.sh
chmod 755 %{buildroot}%{_libdir}/%{name}/Steam++.sh
ln -sr %{buildroot}%{_libdir}/%{name}/Steam++.sh %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}
%exclude %{_libdir}/%{name}/modules/Accelerator/Steam++.Accelerator
%{_libdir}/%{name}/
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png
# 设置网络绑定权限
%caps(cap_net_bind_service=eip) %{_libdir}/%{name}/modules/Accelerator/Steam++.Accelerator

%changelog
* Tue Apr 21 2026 Hansel <hansel@example.com> - 3.1.0-2
- Limit BRP overrides to strip-related steps instead of disabling __os_install_post
- Restrict builds to x86_64 and make English the default package metadata
- Fix %caps file listing and use a relative launcher symlink

* Fri Apr 17 2026 Hansel <hansel@example.com> - 3.1.0-1
- Fix "Arithmetic overflow" by disabling binary stripping
- Add missing X11/GUI dependencies for Avalonia
- Fix ICUs dependency for .NET runtime
