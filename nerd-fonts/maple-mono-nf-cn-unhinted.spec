%global package_version 7.8

Name:           maple-mono-nf-cn-unhinted
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Open source monospace font with round corner, ligatures and Nerd-Font icons for IDE and terminal

License:        OFL-1.1
URL:            https://github.com/subframe7536/maple-font
Source0:        https://github.com/subframe7536/maple-font/releases/download/v%{version}/MapleMono-NF-CN-unhinted.zip
# SHA256: ab88522932cf4015dffeaef6dedc59a22a5fefecdcc6e583d9fcd997da5b7cac

BuildArch:      noarch
BuildRequires:  unzip
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
mkdir -p %{buildroot}%{_fontdir}/%{name}
cp -p *.ttf %{buildroot}%{_fontdir}/%{name}/

%files
%dir %{_fontdir}/%{name}
%{_fontdir}/%{name}/*.ttf

%post
fc-cache -sf %{_fontdir}/%{name} &> /dev/null || :

%postun
if [ "$1" -eq 0 ]; then
    fc-cache -sf %{_fontdir} &> /dev/null || :
fi

%changelog
* Thu Apr 09 2026 hansel <user@example.com> - 7.9-1
- Initial package for maple-mono-nf-cn-unhinted font v7.9
