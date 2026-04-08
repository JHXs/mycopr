%global debug_package %{nil}
%global package_version 0.2.19

Name:           um-cli
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Unlock Music Project - CLI Edition

License:        MIT
URL:            https://git.um-react.app/um/cli
Source0:        %{url}/archive/v%{version}.tar.gz

BuildRequires:  golang >= 1.23

%description
Unlock Music Project - CLI Edition

um-cli is a command-line tool for unlocking music files.

%prep
%autosetup -n cli

%build
export CGO_ENABLED=0
go build -ldflags="-s -w" -o um ./cmd/um

%install
install -Dm755 um %{buildroot}/usr/bin/um

%files
/usr/bin/um

%changelog
