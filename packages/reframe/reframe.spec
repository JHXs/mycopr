%global package_version 1.15.1

Name:           reframe
Version:        %{package_version}
Release:        1%{?dist}
Summary:        DRM/KMS based remote desktop for Linux that supports Wayland/NVIDIA/headless/login…

License:        Apache-2.0
URL:            https://reframe.alynx.one/

# 源代码配置
# 使用 git 并包含子模块
%global         forgeurl https://github.com/AlynxZhou/reframe
%global         commit v%{version}

Source0:        %{forgeurl}/archive/%{commit}/%{name}-%{version}.tar.gz
Source1:        https://github.com/AlynxZhou/mvmath/archive/master/mvmath-master.tar.gz

# 构建依赖
BuildRequires:  meson
BuildRequires:  gcc
BuildRequires:  git
BuildRequires:  pkgconfig

# 运行时和构建时依赖
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(epoxy)
BuildRequires:  pkgconfig(libvncserver)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(gtk4)

# 可选依赖 neatvnc 及其依赖
BuildRequires:  pkgconfig(neatvnc)
BuildRequires:  pkgconfig(aml)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libavcodec)

# 运行时依赖
Requires:       glib2%{?_isa}
Requires:       libepoxy%{?_isa}
Requires:       libvncserver%{?_isa}
Requires:       libxkbcommon%{?_isa}
Requires:       libdrm%{?_isa}
Requires:       systemd-libs%{?_isa}
Requires:       gtk4%{?_isa}

# 可选运行时依赖
Suggests:       neatvnc%{?_isa}

%description
ReFrame is a DRM/KMS based remote desktop for Linux that supports Wayland,
NVIDIA, headless setups, and login sessions. It aims to provide a modern
remote desktop experience using native Linux graphics technologies.

%prep
# 解压主源代码
%autosetup -n %{name}-%{version}
# 解压子模块
tar -xzf %{SOURCE1} -C deps/mvmath --strip-components=1

%build
# 使用 Meson 构建系统
%meson -D neatvnc=true
%meson_build

%install
%meson_install

%files
%license LICENSE
%doc README.md
%config(noreplace) %{_sysconfdir}/%{name}/example.conf

# 可执行文件
%{_bindir}/reframe-server
%{_bindir}/reframe-session
%{_bindir}/reframe-streamer

# 库文件
%{_libdir}/libreframe-common.so
%{_libdir}/libreframe-mvmath.so
%dir %{_libdir}/reframe
%dir %{_libdir}/reframe/vnc
%{_libdir}/reframe/vnc/libreframe-libvncserver.so
%{_libdir}/reframe/vnc/libreframe-neatvnc.so

# systemd 单元
%{_unitdir}/reframe-server@.service
%{_unitdir}/reframe-streamer@.service
%{_unitdir}/reframe@.socket

# sysusers / tmpfiles 配置
%{_sysusersdir}/reframe-sysusers.conf
%{_tmpfilesdir}/reframe-tmpfiles.conf

# 桌面自动启动（路径是 /etc/xdg/autostart）
%config(noreplace) %{_sysconfdir}/xdg/autostart/reframe-session.desktop

%changelog
