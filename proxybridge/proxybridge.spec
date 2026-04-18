%global debug_package %{nil}
%global _debugsource_packages 0
%global forgeurl        https://github.com/InterceptSuite/ProxyBridge
%global package_version 3.2.0
%global upstream_name   ProxyBridge

Name:           proxybridge
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Universal proxy client for Linux applications

License:        MIT
URL:            %{forgeurl}
Source0:        %{forgeurl}/releases/download/v%{version}/ProxyBridge-Linux-v%{version}.tar.gz
Source1:        proxybridge.desktop
Source2:        proxybridge-gui-launcher
Source3:        proxybridge.png

BuildRequires:  patchelf

Requires:       iptables
Requires:       polkit
Provides:       proxybridge
Conflicts:      proxybridge
ExclusiveArch:  x86_64

%description
ProxyBridge is a Proxifier-like utility for Linux that redirects TCP and UDP
traffic from selected applications through SOCKS5 or HTTP proxies.

This package installs the prebuilt upstream Linux release binaries, including
the CLI, GTK GUI, shared library, and the configuration directory.

%prep
# Release tarball has files at archive root, so create a working directory
# before unpacking Source0 into it.
%setup -q -c -n %{name}-%{version}

%build
# no build steps needed

%install
install -Dpm0755 %{upstream_name} %{buildroot}%{_bindir}/%{upstream_name}

install -Dpm0755 %{upstream_name}GUI %{buildroot}%{_bindir}/%{upstream_name}GUI

install -Dpm0755 libproxybridge.so %{buildroot}%{_libdir}/libproxybridge.so
install -d -m 0755 %{buildroot}%{_sysconfdir}/proxybridge
install -Dpm0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dpm0755 %{SOURCE2} %{buildroot}%{_bindir}/proxybridge-gui-launcher
install -Dpm0644 %{SOURCE3} %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/%{name}.png

# Upstream binaries ship with invalid RUNPATH entries. Remove them so Fedora's
# check-rpaths QA passes; the shared library is installed into %{_libdir}.
patchelf --remove-rpath %{buildroot}%{_bindir}/%{upstream_name}
patchelf --remove-rpath %{buildroot}%{_bindir}/%{upstream_name}GUI

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%{_bindir}/%{upstream_name}
%{_bindir}/%{upstream_name}GUI
%{_bindir}/proxybridge-gui-launcher
%{_libdir}/libproxybridge.so
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%dir %{_sysconfdir}/proxybridge

%changelog
* Sat Apr 18 2026 Ikunji <ikunji@duck.com> - 3.2.0-1
- Package upstream Linux release binaries for Copr
