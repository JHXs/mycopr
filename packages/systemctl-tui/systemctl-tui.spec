%global debug_package %{nil}
%global package_version 0.5.2

Name:           systemctl-tui
Version:        %{package_version}
Release:        1%{?dist}
Summary:        A fast, simple TUI for interacting with systemd services and their logs

License:        MIT
URL:            https://github.com/rgwood/systemctl-tui
Source0:        %{URL}/releases/download/v%{version}/systemctl-tui-%{_arch}-unknown-linux-musl.tar.gz
Source1:        %{URL}/raw/refs/tags/v%{version}/LICENSE
Source2:        %{URL}/raw/refs/tags/v%{version}/README.md

ExclusiveArch:  x86_64 aarch64

%description
systemctl-tui is an unofficial terminal user interface for systemctl, providing
an interactive way to inspect and manage systemd units.

%prep
# autosetup: 此处文件在tar包根目录的，添加 -c 参数（会创建目录）
%autosetup -c
cp -p %{SOURCE1} LICENSE
cp -p %{SOURCE2} README.md

%build
# no build steps needed

%install
install -Dm 0755 %{name} %{buildroot}%{_bindir}/%{name}

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}

%changelog
* Wed Apr 22 2026 hansel <58466533+JHXs@users.noreply.github.com> - 0.5.2-1
- Initial package
