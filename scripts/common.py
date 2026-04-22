import re
import httpx
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = REPO_ROOT / "packages"
PACKAGES_TOML = PACKAGES_DIR / "packages.toml"


def load_packages():
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with PACKAGES_TOML.open("rb") as f:
        return tomllib.load(f)


def resolve_repo_path(path_str):
    return REPO_ROOT / path_str

def apply_transform(v, transform_str):
    if not transform_str: return v
    for op in transform_str.split(','):
        op = op.strip()
        if op == "dot": v = v.replace('-', '.')
        elif op == "strip_v": v = v.lstrip('v')
        elif op.startswith("strip:"): v = v.replace(op[6:], "")
    return v

# github 相关函数
def get_github_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()
    return {"version": resp.json()["tag_name"]}

def get_github_commit(repo):
    url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()[0]
    sha = data["sha"]
    short = sha[:7]
    date = data["commit"]["author"]["date"].split('T')[0].replace('-', '')
    return {
        "sha": sha,
        "git_commit": sha,
        "short": short,
        "git_short": short,
        "date": date,
        "commit_date": date,
        "msg": data["commit"]["message"].split('\n')[0][:60]
    }

# aur 相关函数
def parse_pkgbuild_var(text, var_name):
    match = re.search(rf'^{re.escape(var_name)}=(.*)$', text, re.M)
    if not match:
        return None

    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value

def get_aur_version(pkgname):
    url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkgname}"
    resp = httpx.get(url)
    resp.raise_for_status()

    pkgver = parse_pkgbuild_var(resp.text, "pkgver")
    if not pkgver:
        return None

    data = {"version": pkgver}
    pkgdate = parse_pkgbuild_var(resp.text, "pkgdate")
    if pkgdate:
        data.update({
            "date": pkgdate,
            "pkgdate": pkgdate,
            "package_date": pkgdate,
        })
    return data

# gitea 相关函数
def get_gitea_release(api_base, repo):
    url = f"{api_base}/api/v1/repos/{repo}/releases"
    resp = httpx.get(url)
    resp.raise_for_status()
    releases = [r for r in resp.json() if not r.get("prerelease", False)]
    return {"version": releases[0]["tag_name"]} if releases else None

def fetch_upstream_data(config):
    pkg_type = config["type"]
    if pkg_type in ["github_release"]:
        return get_github_release(config["repo"])
    elif pkg_type == "github_commit":
        return get_github_commit(config["repo"])
    elif pkg_type == "aur":
        return get_aur_version(config["repo"])
    elif pkg_type == "gitea_release":
        return get_gitea_release(config.get("api_base"), config["repo"])
    return None

def get_default_transforms(config):
    # Most release packages update %global package_version; commit packages
    # usually track a raw commit hash instead.
    if config["type"] == "github_commit":
        return {"commit": "raw"}
    return {"package_version": "strip_v"}

def pick_upstream_value(data, var_name):
    # Prefer an exact key first, then fall back to the most likely upstream
    # field based on the macro name we are trying to update.
    value = data.get(var_name)
    if value is not None:
        return value

    if "short" in var_name:
        return data.get("short")
    if "date" in var_name:
        return data.get("date")
    if "commit" in var_name or "sha" in var_name:
        return data.get("sha")

    # Release packages typically expose version; commit-based packages can still
    # fall back to the full sha when no better match exists.
    return data.get("version") or data.get("sha")

def is_update_needed(config, data):
    spec_path = resolve_repo_path(config["spec"])
    if not spec_path.exists():
        return True

    content = spec_path.read_text()
    transforms = config.get("transforms", get_default_transforms(config))

    for var_name, rule in transforms.items():
        upstream_value = pick_upstream_value(data, var_name)
        expected_value = apply_transform(upstream_value, rule)
        # We consider the package up to date only when the spec already contains
        # the exact %global macro/value pair implied by upstream.
        pattern = rf'%global\s+{var_name}\s+{re.escape(expected_value)}'

        if re.search(pattern, content) is None:
            return True

    return False
