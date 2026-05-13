%global package_version 0.8.7.9547
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
# The CPU-dispatcher binaries in Binaries/ carry relative RPATHs [.:Binaries]
# that are intentional (so the bundled libtbb.so.12 is found at runtime).
# Allow 0x0002 (invalid) + 0x0004 (insecure/relative) to suppress the errors.
%global __brp_check_rpaths QA_RPATHS=0x0006 /usr/lib/rpm/check-rpaths
%global __provides_exclude_from ^/usr/lib/%{name}/.*
%global __requires_exclude_from ^/usr/lib/%{name}/.*

Name:           y-cruncher
Version:        %{package_version}
Release:        1%{?dist}
Summary:        The first scalable multi-threaded Pi-benchmark for multi-core systems

# Custom freeware license; see bundled "Read Me.txt"
License:        LicenseRef-y-cruncher
URL:            https://github.com/Mysticial/%{name}
# The upstream tarball filename contains a literal space, encoded as %%20 here
# so that RPM does not treat it as a macro.
Source0:        https://github.com/Mysticial/%{name}/releases/download/v%{version}/%{name}.v%{version}-dynamic.tar.xz

ExclusiveArch:  x86_64

Requires:       glibc%{?_isa}
Requires:       libgcc%{?_isa}
Requires:       numactl-libs%{?_isa}
# libtbb.so.12 is bundled inside Binaries/ by upstream; no system tbb needed

%description
y-cruncher is a program that can compute Pi and other mathematical constants
to trillions of digits. It is the first multi-threaded Pi-benchmark for
multi-core systems and is widely used to stress-test hardware and benchmark
multi-core processors.

%prep
# The upstream tarball extracts to a directory whose name contains a space;
# setup accepts it fine when the -n argument is quoted.
%setup -q -n "%{name} v%{version}-dynamic"

# Rewrite the Username.txt path reference so it points to the XDG config
# location; store the result inside the source tree (as Username.xdg) so
# %install can reference it by a simple relative path after cd-ing here.
sed '/Username: / s|Username.txt|/etc/xdg/%{name}-username.conf|' \
    Username.txt > Username.xdg
rm Username.txt

# Rename files whose names contain Unicode fractions to ASCII-safe equivalents
mv "Binaries/Digits/Gamma(⅓).txt" "Binaries/Digits/Gamma(1-3).txt"
mv "Binaries/Digits/Gamma(¼).txt" "Binaries/Digits/Gamma(1-4).txt"
mv "Binaries/Digits/Gamma(⅕).txt" "Binaries/Digits/Gamma(1-5).txt"

%build
# Pre-built binary; nothing to build.

%install
# %{buildsubdir} is set by %setup and equals "y-cruncher v<ver>-dynamic";
# quote the cd to handle the embedded space.
cd "%{_builddir}/%{buildsubdir}"

# Install application files to /usr/lib/y-cruncher/
install -dm 0755 %{buildroot}/usr/lib/%{name}/
cp -rv --no-preserve=ownership %{name} Binaries "Custom Formulas" \
    -t %{buildroot}/usr/lib/%{name}/

# Expose the main executable on PATH via a symlink
install -dm 0755 %{buildroot}%{_bindir}/
ln -sv /usr/lib/%{name}/%{name} %{buildroot}%{_bindir}/%{name}

# Install the username config file to an XDG-compliant location, then
# symlink it back into the application directory where y-cruncher expects it
install -Dm 0644 Username.xdg \
    %{buildroot}%{_sysconfdir}/xdg/%{name}-username.conf
ln -sv %{_sysconfdir}/xdg/%{name}-username.conf \
    %{buildroot}/usr/lib/%{name}/Username.txt

# The upstream tarball ships .txt/.cfg data files with the executable bit set.
# Strip it proactively so brp-mangle-shebangs has nothing to complain about.
find %{buildroot}/usr/lib/%{name}/Binaries \
     %{buildroot}/usr/lib/%{name}/"Custom Formulas" \
     -type f \( -name '*.txt' -o -name '*.cfg' \) \
     -exec chmod 0644 {} +

# Documentation and license
install -Dm 0644 'Command Lines.txt' %{buildroot}%{_docdir}/%{name}/USAGE
install -Dm 0644 'Read Me.txt'       %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

%files
%license %{_datadir}/licenses/%{name}/LICENSE
%doc %{_docdir}/%{name}/USAGE
%{_bindir}/%{name}
/usr/lib/%{name}/
%config(noreplace) %{_sysconfdir}/xdg/%{name}-username.conf

%changelog
%autochangelog
