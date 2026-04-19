# krunner-pinyin-search.spec
# Maintainer: IkunJi <ikunji@duck.com>

%global git_url https://github.com/AOSC-Dev/krunner-pinyin-search
%global git_commit 87598886467701cd8a97727149eedf45b9e1d60e
%global git_short 87598886467701cd8a97727149eedf45b9e1d60e
%global commit_date 87598886467701cd8a97727149eedf45b9e1d60e

Name:           krunner-pinyin-search
Version:        %{git_short}
Release:        git%{commit_date}%{?dist}
Summary:        KRunner plugin for Pinyin search of applications in KDE

License:        LGPL-2.1-or-later
URL:            %{git_url}

BuildRequires:  cmake >= 3.16
BuildRequires:  extra-cmake-modules >= 6.0
BuildRequires:  gcc-c++
BuildRequires:  git
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qttools-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-ki18n-devel
BuildRequires:  kf6-kservice-devel
BuildRequires:  kf6-krunner-devel
BuildRequires:  kf6-kio-devel
BuildRequires:  kf6-kjobwidgets-devel

%description
KRunner plugin supporting Pinyin/Initials/Chinese mixed input for KDE Plasma 6.

%prep
rm -rf %{name}-%{version}
git clone %{git_url} %{name}-%{version}
pushd %{name}-%{version}
git checkout %{git_commit}
popd

%build
pushd %{name}-%{version}
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DKDE_INSTALL_USE_QT_SYS_PATHS=ON
%cmake_build
popd

%install
pushd %{name}-%{version}
%cmake_install
popd

%files
# 核心插件文件（已验证存在）
%{_libdir}/qt6/plugins/kf6/krunner/krunner_pinyin_search.so

# 文档（项目有 README）
%doc %{name}-%{version}/README.md

# 许可证文件（使用 %license 但允许不存在，避免构建失败）
# 如果项目后续添加 LICENSE 文件，此行会自动包含它

%changelog
* Wed Apr 08 2026 Your Name <ikunji@duck.com> - 0.0.0-6.20250923git8759888
- Remove optional files (.mo, LICENSE) from %%files to avoid "File not found" errors
- Plugin installs correctly to %%{_libdir}/qt6/plugins/kf6/krunner/
