%define debug_package %{nil}
%define __requires_exclude ^(libclearkey|libfreeblpriv3|liblgpllibs|libmozavcodec|libmozavutil|libmozgtk|libmozsandbox|libmozsqlite3|libmozwayland|libnspr4|libnss3|libnssckbi|libnssdbm3|libnssutil3|libplc4|libsmime3|libsoftokn3|libssl3|libxul|libgkcodecs)\.so
%global __provides_exclude_from %{_libdir}/%{name}
%global package_version 9.0.3

Name:		zotero
Version:	%{package_version}
Release:	1%{?dist}
Summary:	Zotero desktop application

License:	AGPLv3
URL:		https://www.zotero.org
Source0:	https://download.zotero.org/client/release/%{version}/Zotero-%{version}_linux-x86_64.tar.xz
Patch0:	    desktop.patch

ExclusiveArch: x86_64

%description
Zotero is a free, easy-to-use tool to help you collect, organize, cite, and share research.

%prep
%autosetup -n Zotero_linux-x86_64

%build

%install
mkdir -p %{buildroot}{%{_bindir},%{_libdir}/%{name}}
cp -rf %{_builddir}/Zotero_linux-x86_64/* %{buildroot}%{_libdir}/%{name}/
ln -sf %{_libdir}/%{name}/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm644 %{buildroot}%{_libdir}/%{name}/%{name}.desktop %{buildroot}/%{_datadir}/applications/%{name}.desktop
install -Dm644 %{buildroot}%{_libdir}/%{name}/icons/icon32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/%{name}.png
install -Dm644 %{buildroot}%{_libdir}/%{name}/icons/icon64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/%{name}.png
install -Dm644 %{buildroot}%{_libdir}/%{name}/icons/icon128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{name}.png
install -Dm644 %{buildroot}%{_libdir}/%{name}/icons/symbolic.svg %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps/zotero-symbolic.svg

%files
%{_bindir}/%{name}
%{_libdir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/zotero.png
%{_datadir}/icons/hicolor/symbolic/apps/zotero-symbolic.svg

%changelog
