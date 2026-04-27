%global debug_package %{nil}
%global _debugsource_packages 0
%global __strip /bin/true
%global _build_id_links none
%global package_version 2.1.119

Name:           claude-code
Version:        %{package_version}
Release:        1%{?dist}
Summary:        An agentic coding tool that lives in your terminal

License:        LicenseRef-claude-code
URL:            https://github.com/anthropics/claude-code
Source0:        https://code.claude.com/docs/en/legal-and-compliance.md
Source1:        https://downloads.claude.ai/claude-code-releases/%{version}/linux-x64/claude
Source2:        https://downloads.claude.ai/claude-code-releases/%{version}/linux-arm64/claude

ExclusiveArch:  x86_64 aarch64

Requires:       bash
Recommends:     git
Recommends:     gh
Recommends:     glab
Recommends:     ripgrep
Recommends:     tmux
Recommends:     bubblewrap
Recommends:     socat

%description
Claude Code is an agentic coding tool that lives in your terminal.

This package installs the upstream self-contained Linux executable under
/opt/claude-code and provides a /usr/bin/claude wrapper that disables the
upstream autoupdater for system package manager installations.

%prep
cp -p %{SOURCE0} LICENSE

%build
# Upstream ships a prebuilt self-contained executable.

%install
%ifarch x86_64
install -Dm0755 %{SOURCE1} %{buildroot}/opt/%{name}/bin/claude
%endif
%ifarch aarch64
install -Dm0755 %{SOURCE2} %{buildroot}/opt/%{name}/bin/claude
%endif

install -dm0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/claude <<'EOF'
#!/bin/sh
export DISABLE_AUTOUPDATER=1
exec /opt/claude-code/bin/claude "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/claude

install -Dm0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/claude
/opt/%{name}/

%changelog
* Mon Apr 27 2026 Hansel <hansel@example.com> - 2.1.119-1
- Initial package for Claude Code
