%global debug_package %{nil}
%global _pkgname RealiTLScanner
%global package_version 0.2.3

Name:           realitlscanner
Version:        %{package_version}
Release:        1%{?dist}
Summary:        A TLS server scanner for Reality

License:        MPL-2.0
URL:            https://github.com/XTLS/RealiTLScanner
Source0:        %{url}/archive/v%{version}/%{_pkgname}-%{version}.tar.gz

BuildRequires:  golang

%description
RealiTLScanner is a TLS server scanner designed for scanning Reality servers.

%prep
%autosetup -n %{_pkgname}-%{version}

%build
export CGO_ENABLED=0
export GOTOOLCHAIN=auto
go build -ldflags="-s -w" -o realitlscanner .

%install
install -Dpm 0755 realitlscanner %{buildroot}%{_bindir}/realitlscanner
install -Dpm 0644 LICENSE %{buildroot}%{_defaultlicensedir}/%{name}/LICENSE

%files
%license LICENSE
%{_bindir}/realitlscanner

%changelog
