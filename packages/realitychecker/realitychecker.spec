%global debug_package %{nil}
%global __strip /bin/true
%global _build_id_links none
%global package_version 2.2.3

Name:           realitychecker
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Reality protocol target website checker

License:        MIT
URL:            https://github.com/V2RaySSR/RealityChecker
Source0:        %{url}/releases/download/v%{version}/reality-checker-linux-amd64.zip
Source1:        %{url}/releases/download/v%{version}/reality-checker-linux-arm64.zip

ExclusiveArch:  x86_64 aarch64

%description
RealityChecker is a one-click tool to check whether a website is suitable
as a Reality protocol destination, with TLS inspection, geo-location analysis,
and CDN detection.

%prep
%ifarch x86_64
unzip -o %{SOURCE0}
%endif
%ifarch aarch64
unzip -o %{SOURCE1}
%endif

%build
# Upstream ships prebuilt binaries.

%install
install -Dpm 0755 reality-checker %{buildroot}%{_bindir}/reality-checker

%files
%{_bindir}/reality-checker

%changelog
