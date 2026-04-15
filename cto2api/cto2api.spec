%global debug_package %{nil}
%global goipath         github.com/wyeeeee/cto2api
%global forgeurl        https://github.com/wyeeeee/cto2api

# Adjust these based on the upstream release
%global tag             main
%global commit          8d90676f408a558563d61f61cd91d75f91c97563
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           cto2api
Version:        %{shortcommit}
Release:        1%{?dist}
Summary:        OpenAI compatible API interface for CTO.NEW AI services

License:        MIT
URL:            %{forgeurl}
Source0:        %{forgeurl}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
# Source1:        cto2api.service

# Go compiler and tools
BuildRequires:  golang
BuildRequires:  git
BuildRequires:  systemd-rpm-macros

%description
CTO2API is a Go-based service that converts CTO.NEW's AI services into an
OpenAI-compatible API interface. It provides:

  * OpenAI-compatible API endpoint (/v1/chat/completions)
  * Support for streaming and non-streaming responses
  * Web management interface
  * Cookie rotation and statistics
  * API key authentication
  * Data persistence via JSON file

%prep
%autosetup -S git -n %{name}-%{commit}

%build
# Set Go build flags for optimization and reproducibility
export CGO_ENABLED=0
export GOFLAGS="-mod=readonly -trimpath"
export LDFLAGS="-s -w -X main.Version=%{version} -X main.Commit=%{shortcommit}"

# Build the binary
go build -v -ldflags "${LDFLAGS}" -o %{name} .

%install
# Install the binary
install -D -m 0755 %{name} %{buildroot}%{_bindir}/%{name}

%files
%doc README.md
%{_bindir}/%{name}

%changelog
