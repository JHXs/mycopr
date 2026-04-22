%global debug_package %{nil}
%global __os_install_post %{nil}
%global _build_id_links none
%global package_version 14.0.02
%global package_date 2026/02

%ifarch x86_64
%global upstream_arch AMD64
%endif
%ifarch aarch64
%global upstream_arch ARM64
%endif

Name:           steamcommunity302
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Steam and GitHub reverse proxy acceleration tool
Summary(zh_CN): 羽翼城制作的 Steam、Github 等反代加速工具

License:        CC-BY-NC-4.0
URL:            https://www.dogfight360.com/blog/18682/
Source0:        https://www.dogfight360.com/blog/wp-content/uploads/%{package_date}/steamcommunity_302_Linux_%{upstream_arch}_V%{version}.tar.gz
Source1:        302_icon.ico
Source2:        s302
Source3:        Steamcommunity_302.desktop

ExclusiveArch:  x86_64 aarch64

Requires:       nss
Requires:       libnetfilter_queue
Requires:       gtk3
Requires:       glibc
Requires:       libgcc
Requires:       libstdc++
Requires:       zlib
Requires:       sudo
Requires:       /usr/bin/xhost

Recommends:     zenity
Suggests:       kdialog
Suggests:       iptables
Suggests:       nftables
Suggests:       firewalld
Suggests:       ufw

%description
Steamcommunity 302 is a reverse proxy acceleration tool for Steam, GitHub,
and related services. Use the s302 command to start it.

%description -l zh_CN
羽翼城制作的 Steam、Github 等反代加速工具，使用 s302 命令启动。

%prep
%autosetup -n Steamcommunity_302

%build
# Upstream ships prebuilt binaries.

%install
install -d %{buildroot}/opt/%{name}
cp -a ./ %{buildroot}/opt/%{name}/

chmod 0755 \
    %{buildroot}/opt/%{name}/Steamcommunity_302 \
    %{buildroot}/opt/%{name}/steamcommunity_302.cli \
    %{buildroot}/opt/%{name}/steamcommunity_302.caddy

install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/pixmaps/%{name}.ico
install -Dm755 %{SOURCE2} %{buildroot}%{_bindir}/s302
install -Dm644 %{SOURCE3} %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%{_bindir}/s302
/opt/%{name}/
%{_datadir}/pixmaps/%{name}.ico
%{_datadir}/applications/%{name}.desktop

%changelog
* Wed Apr 22 2026 Hansel <hansel@example.com> - 14.0.02-1
- init package
