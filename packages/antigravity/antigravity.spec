%global debug_package %{nil}
%global _debugsource_packages 0
%global __strip /bin/true
%global _build_id_links none
%global __provides_exclude_from ^/opt/Antigravity/.*$
%global __requires_exclude ^lib(EGL|GLESv2|ffmpeg|vk_swiftshader|vulkan)\.so.*$
%global package_version 2.0.10
%global upstream_build 5119448496078848

Name:           antigravity
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Google Antigravity multi-agent orchestration platform

License:        LicenseRef-Google-Antigravity
URL:            https://antigravity.google/product/antigravity-2
Source0:        https://storage.googleapis.com/antigravity-public/antigravity-hub/%{version}-%{upstream_build}/linux-x64/Antigravity.tar.gz#/Antigravity-%{version}-x86_64.tar.gz
Source1:        antigravity.desktop
Source2:        antigravity.png
Source3:        https://storage.googleapis.com/antigravity-public/antigravity-hub/%{version}-%{upstream_build}/linux-arm/Antigravity.tar.gz#/Antigravity-%{version}-aarch64.tar.gz

ExclusiveArch:  x86_64 aarch64

Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       cairo
Requires:       cups-libs
Requires:       dbus-libs
Requires:       expat
Requires:       glib2
Requires:       gtk3
Requires:       hicolor-icon-theme
Requires:       libX11
Requires:       libXScrnSaver
Requires:       libXcomposite
Requires:       libXcursor
Requires:       libXdamage
Requires:       libXext
Requires:       libXfixes
Requires:       libXi
Requires:       libXrandr
Requires:       libXtst
Requires:       libdrm
Requires:       libxcb
Requires:       libxkbcommon
Requires:       mesa-libgbm
Requires:       nspr
Requires:       nss
Requires:       pango
Requires:       systemd-libs

%description
Google Antigravity is a multi-agent orchestration platform for agentic
software development workflows.

This package installs the upstream prebuilt Linux release under
/opt/Antigravity and provides a command-line symlink and desktop entry.

%prep
%setup -q -c -T -n %{name}-%{version}
%ifarch x86_64
%{__tar} -xzf %{SOURCE0}
%endif
%ifarch aarch64
%{__tar} -xzf %{SOURCE3}
%endif

%build
# Upstream ships prebuilt binaries.

%install
install -dm0755 %{buildroot}/opt
cp -a Antigravity-* %{buildroot}/opt/Antigravity

install -dm0755 %{buildroot}%{_bindir}
ln -sr %{buildroot}/opt/Antigravity/antigravity %{buildroot}%{_bindir}/%{name}

install -Dpm0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dpm0644 %{SOURCE2} %{buildroot}%{_datadir}/pixmaps/%{name}.png
install -Dpm0644 %{buildroot}/opt/Antigravity/LICENSE.electron.txt %{buildroot}%{_licensedir}/%{name}/LICENSE.electron.txt
install -Dpm0644 %{buildroot}/opt/Antigravity/LICENSES.chromium.html %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

%files
%license %{_licensedir}/%{name}/LICENSE.electron.txt
%license %{_licensedir}/%{name}/LICENSES.chromium.html
%{_bindir}/%{name}
/opt/Antigravity/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/pixmaps/%{name}.png

%changelog
* Tue Jun 02 2026 Hansel <hansel@example.com> - 2.0.10-1
- Initial package for Google Antigravity
