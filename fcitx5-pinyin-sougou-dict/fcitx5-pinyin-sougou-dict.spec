%global package_version 20260410

Name:           fcitx5-pinyin-sougou-dict
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Sogou Pinyin dictionary for Fcitx5

License:        MIT
URL:            https://github.com/JHXs/mycopr
Source0:        https://github.com/JHXs/mycopr/raw/refs/heads/main/fcitx5-pinyin-sougou-dict/fcitx5-pinyin-sougou-dict.dict

BuildArch:      noarch
# BuildRequires:  unzip
Requires:       libime
Requires:       fcitx5-chinese-addons

%description
This package provides the Sogou Pinyin dictionary for Fcitx5, which is a popular input method framework for Linux. The Sogou Pinyin dictionary is widely used for Chinese input and offers a comprehensive set of words and phrases to enhance the typing experience. By installing this package, users can enjoy improved accuracy and efficiency when using Fcitx5 for Chinese input.

%prep
# nothing

%build
# No build steps required for this package as it only contains dict files.

%install
ls -R .
mkdir -p %{buildroot}/usr/share/fcitx5/pinyin/dictionaries/
cp %{SOURCE0} %{buildroot}/usr/share/fcitx5/pinyin/dictionaries/

%files
/usr/share/fcitx5/pinyin/dictionaries/

%changelog
* Fri Apr 10 2026 ikunji <ikunji@duck.com> - 20260410-1
- Initial package for fcitx5-pinyin-sougou-dict 20260410.
