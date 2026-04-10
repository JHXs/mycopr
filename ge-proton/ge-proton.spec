%global         debug_package %{nil}
%global package_version 10.33
%global         proton_name   GE-Proton
%global proton_ver 10-33
%global         proton_nv     %{proton_name}%{proton_ver}
%global         proton_dir    %{_datadir}/steam/compatibilitytools.d/%{name}

%global         __requires_exclude_from ^%{proton_dir}/.*
%global         __provides_exclude_from ^%{proton_dir}/.*

Name:           ge-proton
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Compatibility tool for Steam Play based on Wine and additional components.
License:        BSD-3-Clause AND LGPL-2.1-or-later AND LGPL-2.0-or-later AND MIT AND Zlib AND MPL-2.0 AND OFL-1.1 AND GPL-2.0-or-later AND BSD-2-Clause AND MS-PL

URL:            https://github.com/GloriousEggroll/proton-ge-custom
Source0:        %{url}/releases/download/%{proton_nv}/%{proton_nv}.tar.gz

Requires:       vulkan-loader%{?_isa}
Requires:       mesa-vulkan-drivers%{?_isa}

%description
GE-Proton is GloriousEggroll's custom build of Proton, tracking bleeding-edge
Proton Experimental Wine. It includes improvements not found in Valve's Proton.

%prep
%autosetup -n %{proton_nv}

%build
sed -i 's/"GE-Proton[^"]*"/"ge-proton"/' compatibilitytool.vdf

find files/bin -type f -name 'wine*' -executable \
    -exec strip --preserve-dates --strip-unneeded {} \;

%install
install -dm 0755 %{buildroot}%{proton_dir}
install -dm 0755 %{buildroot}%{_docdir}/%{name}

install -pm 0644 LICENSE      %{buildroot}%{_docdir}/%{name}/
install -pm 0644 LICENSE.OFL  %{buildroot}%{_docdir}/%{name}/
install -pm 0644 PATENTS.AV1  %{buildroot}%{_docdir}/%{name}/

cp -a \
    compatibilitytool.vdf \
    filelock.py \
    files \
    proton \
    proton_3.7_tracked_files \
    protonfixes \
    toolmanifest.vdf \
    user_settings.sample.py \
    version \
    %{buildroot}%{proton_dir}/

ln -sf unzip %{buildroot}%{proton_dir}/protonfixes/files/bin/zipinfo

# Fix permissions on non-executable text assets
find %{buildroot}%{proton_dir}/protonfixes \
    -type f \( -name '*.py' -o -name '*.verb' \) ! -path '*/bin/*' \
    -exec chmod 0644 {} +

find %{buildroot}%{proton_dir}/files/share/wine/mono \
    -type f \( -name '*.config' -o -name '*.rsp' -o -name '*.targets' \) \
    -exec chmod 0644 {} +

chmod 0644 %{buildroot}%{proton_dir}/user_settings.sample.py

%files
%license LICENSE LICENSE.OFL PATENTS.AV1
%doc %{_docdir}/%{name}/
%{proton_dir}/

%changelog
%autochangelog
