%global debug_package %{nil}
%global _debugsource_packages 0
%global __strip /bin/true
%global _build_id_links none
%global package_version 0.4.10

Name:           computer-use-linux
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Linux desktop control over MCP — AT-SPI, GNOME Shell, Wayland portals, ydotool

License:        MIT
URL:            https://github.com/agent-sh/computer-use-linux
Source0:        https://github.com/agent-sh/computer-use-linux/releases/download/v%{version}/computer-use-linux-x86_64-unknown-linux-gnu
Source1:        https://github.com/agent-sh/computer-use-linux/releases/download/v%{version}/computer-use-linux-cosmic-x86_64-unknown-linux-gnu
Source2:        https://github.com/agent-sh/computer-use-linux/releases/download/v%{version}/computer-use-linux-aarch64-unknown-linux-gnu
Source3:        https://github.com/agent-sh/computer-use-linux/releases/download/v%{version}/computer-use-linux-cosmic-aarch64-unknown-linux-gnu
Source4:        https://raw.githubusercontent.com/agent-sh/computer-use-linux/v%{version}/LICENSE

ExclusiveArch:  x86_64 aarch64

%description
computer-use-linux is a Rust MCP server and CLI for Linux desktop control.
It reads accessibility trees, takes screenshots, and drives clicks, scrolls,
and keystrokes across GNOME, KDE/KWin, Hyprland, i3, and COSMIC — Wayland-first,
X11 best-effort.

This package installs the upstream prebuilt binaries under /opt/computer-use-linux
and provides symlinks in /usr/bin for both the main binary and the COSMIC helper.

%prep
cp -p %{SOURCE4} LICENSE

%build
# Upstream ships prebuilt binaries.

%install
%ifarch x86_64
install -Dm0755 %{SOURCE0} %{buildroot}/opt/%{name}/bin/computer-use-linux
install -Dm0755 %{SOURCE1} %{buildroot}/opt/%{name}/bin/computer-use-linux-cosmic
%endif
%ifarch aarch64
install -Dm0755 %{SOURCE2} %{buildroot}/opt/%{name}/bin/computer-use-linux
install -Dm0755 %{SOURCE3} %{buildroot}/opt/%{name}/bin/computer-use-linux-cosmic
%endif

install -dm0755 %{buildroot}%{_bindir}
ln -sf /opt/%{name}/bin/computer-use-linux %{buildroot}%{_bindir}/computer-use-linux
ln -sf /opt/%{name}/bin/computer-use-linux-cosmic %{buildroot}%{_bindir}/computer-use-linux-cosmic

install -Dm0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/computer-use-linux
%{_bindir}/computer-use-linux-cosmic
/opt/%{name}/

%changelog
* Sat Jun 07 2026 Hansel <hansel@example.com> - 0.2.6-1
- Initial package for computer-use-linux v0.2.6
