%global debug_package %{nil}
%global _debugsource_packages 0
%global package_version 6.1.2

Name:           linux-enable-ir-emitter
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Enables infrared cameras that are not directly enabled out-of-the-box

License:        MIT
URL:            https://github.com/EmixamPP/linux-enable-ir-emitter
Source0:        %{URL}/archive/refs/tags/%{version}/%{name}-%{version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc-c++
BuildRequires:  meson
BuildRequires:  cmake
BuildRequires:  pkgconfig
BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(opencv4)
BuildRequires:  argparse-devel
BuildRequires:  yaml-cpp-devel

Requires:       kmod
%{?systemd_requires}

Conflicts:      chicony-ir-toggle
Conflicts:      linux-enable-ir-emitter-git

%description
linux-enable-ir-emitter provides support for infrared cameras that are not
directly enabled out of the box on Linux. It enables the infrared emitter when
an infrared camera is invoked, and can automatically configure many UVC infrared
cameras.

%prep
%autosetup -n %{name}-%{version}

# Fedora packages systemd unit files under %%{_unitdir}, not /etc/systemd/system.
sed -i "s|get_option('sysconfdir') / 'systemd/system'|'%{_unitdir}'|" meson.build

# Use absolute paths in the systemd unit.
sed -i \
    -e 's|ExecStartPre = modprobe uvcvideo|ExecStartPre = /usr/sbin/modprobe uvcvideo|' \
    -e 's|ExecStartPre= sleep 1|ExecStartPre = /usr/bin/sleep 1|' \
    -e 's|ExecStart = linux-enable-ir-emitter --verbose run|ExecStart = %{_bindir}/linux-enable-ir-emitter --verbose run|' \
    boot_service/systemd/%{name}.service

%build
%meson \
    -Dboot_service=systemd \
    -Dconfig_dir=%{_sysconfdir} \
    -Dcreate_config_dir=true \
    -Dcreate_log_dir=true \
    -Dtests=false
%meson_build

%install
%meson_install

# Meson installs README and LICENSE under %%{_datadir}/doc; let RPM's %%doc and
# %%license handling install and tag them instead.
rm -f %{buildroot}%{_datadir}/doc/%{name}/README.md
rm -f %{buildroot}%{_datadir}/doc/%{name}/LICENSE
rmdir --ignore-fail-on-non-empty %{buildroot}%{_datadir}/doc/%{name}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%{_datadir}/bash-completion/completions/%{name}
%{_datadir}/zsh/site-functions/_%{name}
%dir %{_sysconfdir}/%{name}
%dir %{_localstatedir}/log/%{name}

%changelog
* Sat Apr 18 2026 Ikunji <ikunji@duck.com> - 6.1.2-1
- Initial package
