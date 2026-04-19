import re
import httpx
from pathlib import Path

def apply_transform(v, transform_str):
    if not transform_str: return v
    for op in transform_str.split(','):
        op = op.strip()
        if op == "dot": v = v.replace('-', '.')
        elif op == "strip_v": v = v.lstrip('v')
        elif op.startswith("strip:"): v = v.replace(op[6:], "")
    return v

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

def get_aur_version(pkgname):
    url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkgname}"
    resp = httpx.get(url)
    resp.raise_for_status()
    match = re.search(r'^pkgver=(.*)$', resp.text, re.M)
    return {"version": match.group(1).strip()} if match else None

def get_gitea_release(api_base, repo):
    url = f"{api_base}/api/v1/repos/{repo}/releases"
    resp = httpx.get(url)
    resp.raise_for_status()
    releases = [r for r in resp.json() if not r.get("prerelease", False)]
    return {"version": releases[0]["tag_name"]} if releases else None

def fetch_upstream_data(config):
    pkg_type = config["type"]
    if pkg_type in ["github_release", "ge_proton"]:
        return get_github_release(config["repo"])
    elif pkg_type == "github_commit":
        return get_github_commit(config["repo"])
    elif pkg_type == "aur":
        return get_aur_version(config["repo"])
    elif pkg_type == "gitea_release":
        return get_gitea_release(config.get("api_base"), config["repo"])
    return None

def is_update_needed(config, data):
    spec_path = Path(config["spec"])
    if not spec_path.exists(): return True
    content = spec_path.read_text()

    # Default transforms logic
    default_transforms = {"package_version": "strip_v"}
    if config["type"] == "github_commit":
        default_transforms = {"commit": "raw"}
    
    transforms = config.get("transforms", default_transforms)
    for var_name, rule in transforms.items():
        # Get value from data: try var_name directly, then fallback to version/sha/short/date
        val = data.get(var_name)
        if val is None:
            if "short" in var_name: val = data.get("short")
            elif "date" in var_name: val = data.get("date")
            elif "commit" in var_name or "sha" in var_name: val = data.get("sha")
            else: val = data.get("version") or data.get("sha")
        
        val = apply_transform(val, rule)
        if re.search(rf'%global\s+{var_name}\s+{re.escape(val)}', content) is None:
            return True
    return False
