%global debug_package %{nil}
%global package_version 5.3.3

Name:           cc-switch-cli
Version:        %{package_version}
Release:        1%{?dist}
Summary:        本项目是原版 CC-Switch 的 CLI 分支。🔄 WebDAV 同步功能与上游项目完全兼容。致谢： 原始架构和核心功能来自 https://github.com/farion1231/cc-switch

License:        MIT
URL:            https://github.com/SaladDay/cc-switch-cli
Source0:        %{url}/releases/download/v%{version}/cc-switch-cli-v%{version}-linux-x64.tar.gz

BuildArch:      x86_64

# 运行依赖
Requires:       ca-certificates

%description

统一管理 Claude Code、Codex、Gemini、OpenCode 与 OpenClaw 的供应商配置，并按应用提供 MCP 服务器、Skills 扩展、提示词、本地代理路由和环境检查等能力。
本项目是原版 CC-Switch 的 CLI 分支。WebDAV 同步功能与上游项目完全兼容。致谢： 原始架构和核心功能来自 https://github.com/farion1231/cc-switch

%prep
%setup -q -c -n %{name}-%{version}

%build
# Pre-built bin, no compilation needed

%install
mkdir -p %{buildroot}%{_bindir}
install -m 0755 %{_builddir}/%{name}-%{version}/cc-switch %{buildroot}%{_bindir}/

%files
%dir %{_bindir}
%{_bindir}/cc-switch

%changelog
* Sun Apr 19 2026 hansel <user@example.com> - 5.3.2
- Initial package for cc-switch-cli v5.3.2
