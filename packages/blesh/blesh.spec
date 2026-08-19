%global nightly_date 20260818
%global git_short 63c23e9
%global snapshot %{nightly_date}git%{git_short}

Name:           blesh
Version:        0.4.0~%{snapshot}
Release:        1%{?dist}
Summary:        Bash Line Editor

License:        BSD-3-Clause
URL:            https://github.com/akinomyoga/ble.sh
Source0:        %{url}/releases/download/nightly/ble-nightly-%{nightly_date}+%{git_short}.tar.xz
Source1:        %{url}/raw/%{git_short}/LICENSE.md
Source2:        %{url}/raw/%{git_short}/README.md
Source3:        %{url}/raw/%{git_short}/README-ja_JP.md
Source4:        %{url}/raw/%{git_short}/docs/CONTRIBUTING.md
Source5:        %{url}/raw/%{git_short}/docs/Release.md

BuildArch:      noarch
Requires:       bash

%description
ble.sh is a command line editor written in pure Bash which replaces the default
GNU Readline. It provides syntax highlighting, enhanced completion, vim editing
mode, and other interactive shell editing features.

%prep
%autosetup -n ble-nightly-%{nightly_date}+%{git_short}

%build
# Upstream nightly tarballs are pre-built shell scripts.

%install
mkdir -p %{buildroot}%{_datadir}/blesh
cp -a . %{buildroot}%{_datadir}/blesh/

install -dm0755 %{buildroot}%{_docdir}/%{name}
install -pm0644 %{SOURCE1} %{buildroot}%{_docdir}/%{name}/LICENSE.md
install -pm0644 %{SOURCE2} %{buildroot}%{_docdir}/%{name}/README.md
install -pm0644 %{SOURCE3} %{buildroot}%{_docdir}/%{name}/README-ja_JP.md
install -pm0644 %{SOURCE4} %{buildroot}%{_docdir}/%{name}/CONTRIBUTING.md
install -pm0644 %{SOURCE5} %{buildroot}%{_docdir}/%{name}/Release.md

%files
%license %{_docdir}/%{name}/LICENSE.md
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/README-ja_JP.md
%doc %{_docdir}/%{name}/CONTRIBUTING.md
%doc %{_docdir}/%{name}/Release.md
%{_datadir}/blesh/

%changelog
* Tue Jun 09 2026 ikunji <ikunji@ikunji@duck.com> - 0.4.0~20260528gitf38850c-1
- Initial package from nightly 20260528+f38850c
