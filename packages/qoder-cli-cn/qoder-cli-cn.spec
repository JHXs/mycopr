%global debug_package %{nil}
%global _debugsource_packages 0
%global __strip /bin/true
%global _build_id_links none
%global package_version 1.0.43

Name:           qoder-cli-cn
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Qoder CLI (CN version) - An agentic AI coding tool built for command-line developers

License:        LicenseRef-Qoder-Product-Service
URL:            https://qoder.com.cn
Source0:        https://static.qoder.com.cn/qoder-cli-cn/releases/%{version}/qoderclicn-linux-x64.tar.gz
Source1:        https://static.qoder.com.cn/qoder-cli-cn/releases/%{version}/qoderclicn-linux-arm64.tar.gz
Source2:        LICENSE
Source3:        qoderclicn.bash
Source4:        qoderclicn.zsh
Source5:        qoderclicn.fish

ExclusiveArch:  x86_64 aarch64

Requires:       glibc
Requires:       bash

%description
Qoder CLI (CN version) is an agentic AI coding tool built for command-line
developers, providing MCP server management, plugin support, agent skills,
and remote session capabilities.

This package installs the prebuilt upstream Linux release binary along with
shell completions for Bash, Zsh, and Fish.

%prep
%setup -q -c -n %{name}-%{version}

cp -p %{SOURCE2} LICENSE
cp -p %{SOURCE3} qoderclicn.bash
cp -p %{SOURCE4} qoderclicn.zsh
cp -p %{SOURCE5} qoderclicn.fish

%build
# Pre-built binary, no compilation needed.

%install
%ifarch x86_64
tar -xzf %{SOURCE0} -C %{_builddir}/%{name}-%{version}
%endif
%ifarch aarch64
tar -xzf %{SOURCE1} -C %{_builddir}/%{name}-%{version}
%endif

install -Dm0755 %{_builddir}/%{name}-%{version}/qoderclicn %{buildroot}%{_bindir}/qoderclicn

install -Dm0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

install -Dm0644 qoderclicn.bash %{buildroot}%{_datadir}/bash-completion/completions/qoderclicn
install -Dm0644 qoderclicn.zsh %{buildroot}%{_datadir}/zsh/site-functions/_qoderclicn
install -Dm0644 qoderclicn.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/qoderclicn.fish

%files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/qoderclicn
%{_datadir}/bash-completion/completions/qoderclicn
%{_datadir}/zsh/site-functions/_qoderclicn
%{_datadir}/fish/vendor_completions.d/qoderclicn.fish

%changelog
* Sat Jun 06 2026 Ikunji ikunji@duck.com - 1.0.11-1
- Initial package for Qoder CLI CN
