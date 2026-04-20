%global debug_package %{nil}
%global _debugsource_packages 0
%global __provides_exclude_from ^%{_libdir}/obsidian/.*$
%global __requires_exclude ^lib(EGL|GLESv2|ffmpeg|vk_swiftshader|vulkan)\.so.*$
%global forgeurl        https://github.com/obsidianmd/obsidian-releases
%global package_version 1.12.7

Name:           obsidian
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Markdown knowledge base application

License:        LicenseRef-Proprietary
URL:            https://obsidian.md/
Source0:        %{forgeurl}/releases/download/v%{version}/obsidian-%{version}.tar.gz

Requires:       hicolor-icon-theme

ExclusiveArch:  x86_64

%description
Obsidian is a local-first knowledge base and note-taking application built on
Markdown files.

%prep
%autosetup -n %{name}-%{version}

%build
# Upstream ships prebuilt binaries.

%install
# 创建文件夹
install -d %{buildroot}%{_libdir}/%{name}
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_datadir}/applications
install -d %{buildroot}%{_datadir}/icons/hicolor/512x512/apps

cp -a . %{buildroot}%{_libdir}/%{name}/

find %{buildroot}%{_libdir}/%{name}/resources/app.asar.unpacked -type f \
    \( -name '*.js' -o -name '*.json' -o -name '*.mm' \) -exec chmod 0644 {} +

ln -sf %{_libdir}/%{name}/obsidian %{buildroot}%{_bindir}/obsidian
ln -sf %{_libdir}/%{name}/obsidian-cli %{buildroot}%{_bindir}/obsidian-cli

install -Dm644 resources/icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

cat > %{buildroot}%{_datadir}/applications/%{name}.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Obsidian
Comment=Markdown knowledge base
Exec=%{_bindir}/obsidian %U
Icon=%{name}
Terminal=false
Categories=Office;Utility;
MimeType=x-scheme-handler/obsidian;
StartupNotify=true
StartupWMClass=obsidian
EOF

%files
%license LICENSE.electron.txt
%license LICENSES.chromium.html
%{_bindir}/obsidian
%{_bindir}/obsidian-cli
%{_libdir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

%changelog
* Mon Apr 20 2026 Hansel <hansel@example.com> - 1.12.7-1
- Package upstream prebuilt Obsidian release for x86_64
