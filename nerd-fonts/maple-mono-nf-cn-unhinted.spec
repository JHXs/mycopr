%global package_version 7.9
%{!?_fontbasedir:%global _fontbasedir %{_datadir}/fonts}

Name:           maple-mono-nf-cn-unhinted
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Open source monospace font with round corner, ligatures and Nerd-Font icons for IDE and terminal

License:        OFL-1.1
URL:            https://github.com/subframe7536/maple-font
Source0:        https://github.com/subframe7536/maple-font/releases/download/v%{version}/MapleMono-NF-CN-unhinted.zip

BuildArch:      noarch
BuildRequires:  unzip
BuildRequires:  fonts-srpm-macros
Requires:       fontconfig

%description
Open source monospace font with round corner, ligatures and Nerd-Font icons
for IDE and terminal, featuring fine-grained customization options.
This package provides the CN (Chinese) variant, unhinted, with Nerd Font patches.

%prep
%setup -q -c -T
unzip -q "%{SOURCE0}" -d %{name}-%{version}
cd %{name}-%{version}

%build
# Pre-built TTF fonts, no compilation needed

%install
mkdir -p %{buildroot}%{_fontbasedir}/%{name}
find %{_builddir}/%{name}-%{version} -type f -name '*.ttf' -exec cp -p {} %{buildroot}%{_fontbasedir}/%{name}/ \;

%files
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%post
fc-cache -sf %{_fontbasedir}/%{name} &> /dev/null || :

%postun
if [ "$1" -eq 0 ]; then
    fc-cache -sf %{_fontbasedir} &> /dev/null || :
fi

%changelog
* Sun Apr 19 2026 GitHub Actions <actions@github.com> - 7.9-1
- Update to 7.9

* Thu Apr 09 2026 hansel <user@example.com> - 7.8-1
- Initial package for maple-mono-nf-cn-unhinted font v7.8
