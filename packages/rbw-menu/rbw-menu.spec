%global debug_package %{nil}
%global package_version 1.3

Name:           rbw-menu
Version:        %{package_version}
Release:        1%{?dist}
Summary:        GUI menu for rbw (Unofficial Bitwarden CLI)

License:        GPL-3.0-or-later
URL:            https://github.com/rbuchberger/rbw-menu
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  make

# 运行依赖
Requires:       rbw
Requires:       jq

# 可选依赖（Fedora用 Recommends）
Recommends:     wofi

%description
rbw-menu is a simple GUI menu frontend for rbw, an unofficial Bitwarden CLI.

%prep
%autosetup -n %{name}-%{version}

%build

%install
install -Dm 755 bin/rbw-menu %{buildroot}%{_bindir}/rbw-menu

%files
%license LICENSE.txt
%doc readme.md
%{_bindir}/rbw-menu

%changelog
* Tue Apr 21 2026 Your Name <you@example.com> - 1.3-1
- Initial package
