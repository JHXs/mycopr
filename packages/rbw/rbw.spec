%global debug_package %{nil}
%global _debugsource_packages 0
%global forgeurl        https://github.com/doy/rbw
%global package_version 1.15.0

Name:           rbw
Version:        %{package_version}
Release:        1%{?dist}
Summary:        unofficial bitwarden cli

License:        MIT
URL:            %{forgeurl}
Source0:        %{forgeurl}/releases/download/%{version}/rbw_%{version}_linux_amd64.tar.gz

Requires:       pinentry

ExclusiveArch:  x86_64

%description
unofficial bitwarden cli

%prep
# setup: 此处文件在tar包根目录的，添加 -c 参数（会创建目录），也就是 -c -n
%autosetup -c

%build
# no build steps needed

%install
install -Dm0755 %{name} %{buildroot}%{_bindir}/%{name}
install -Dm0755 %{name}-agent %{buildroot}%{_bindir}/%{name}-agent
install -Dm644 completion/bash %{buildroot}%{_datadir}/bash-completion/completions/rbw
install -Dm644 completion/fish %{buildroot}%{_datadir}/fish/vendor_completions.d/rbw.fish
install -Dm644 completion/zsh  %{buildroot}%{_datadir}/zsh/site-functions/_rbw

%files
%{_bindir}/%{name}
%{_bindir}/%{name}-agent
%{_datadir}/bash-completion/completions/rbw
%{_datadir}/fish/vendor_completions.d/rbw.fish
%{_datadir}/zsh/site-functions/_rbw

%changelog
* Sat Apr 18 2026 Ikunji <ikunji@duck.com> - 1.15.0-1
- Package upstream Linux release binaries for Copr
