# um-cli (Copr)

Copr packaging for um-cli.

## Unlock Music Project - CLI Edition

Original: Web Edition https://git.um-react.app/um/web

### Features

- All Algorithm Supported By unlock-music/web
- Complete Metadata & Cover Image

## Install

```bash
sudo dnf copr enable ikunji/um-cli
sudo dnf install um-cli
```

## How to build

1. Clone the repository:

```shell
git clone https://github.com/JHXs/um-cli-copr && cd um-cli-copr
```

2. Install the required dependencies:

```shell
sudo dnf install -y rpmdevtools rpm-build
```

3. Set up the RPM build environment:

```shell
rpmdev-setuptree
```

4. Build the RPM package:

```shell
rpmbuild -bb um-cli.spec
```

5. Install the RPM package:

```shell
sudo dnf install ~/rpmbuild/RPMS/x86_64/um-*.rpm
```

