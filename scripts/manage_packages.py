import os
import re
import httpx
import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def get_latest_github_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()["tag_name"]

def get_latest_github_commit(repo):
    url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()[0]
    return {
        "sha": data["sha"],
        "short": data["sha"][:7],
        "date": data["commit"]["author"]["date"].split('T')[0].replace('-', ''),
        "msg": data["commit"]["message"].split('\n')[0][:60]
    }

def get_aur_version(pkgname):
    url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkgname}"
    resp = httpx.get(url)
    resp.raise_for_status()
    match = re.search(r'^pkgver=(.*)$', resp.text, re.M)
    return match.group(1).strip() if match else None

def get_gitea_release(api_base, repo):
    url = f"{api_base}/api/v1/repos/{repo}/releases"
    resp = httpx.get(url)
    resp.raise_for_status()
    releases = [r for r in resp.json() if not r.get("prerelease", False)]
    return releases[0]["tag_name"] if releases else None

def apply_transform(v, transform_str):
    """通用转换逻辑: strip:xxx, dot, strip_v"""
    if not transform_str: return v
    for op in transform_str.split(','):
        op = op.strip()
        if op == "dot":
            v = v.replace('-', '.')
        elif op == "strip_v":
            v = v.lstrip('v')
        elif op.startswith("strip:"):
            v = v.replace(op[6:], "")
    return v

def update_spec(spec_path, raw_version, pkg_config):
    content = Path(spec_path).read_text()
    new_content = content
    updated = False

    # 1. 处理复杂的 Commit 类型 (带 Changelog 更新)
    if pkg_config["type"] == "github_commit_complex":
        version_obj = raw_version # raw_version is a dict here
        new_content = re.sub(r'(%global git_commit\s+)\S+', rf'\g<1>{version_obj["sha"]}', new_content)
        new_content = re.sub(r'(%global git_short\s+)\S+', rf'\g<1>{version_obj["short"]}', new_content)
        new_content = re.sub(r'(%global commit_date\s+)\S+', rf'\g<1>{version_obj["date"]}', new_content)
        if "%changelog" in new_content and version_obj["short"] not in content:
            date_str = datetime.now().strftime("%a %b %d %Y")
            entry = f"* {date_str} GitHub Actions <actions@github.com> - {version_obj['date']}git{version_obj['short']}\n- Auto-update to commit {version_obj['short']}: {version_obj['msg']}\n\n"
            new_content = new_content.replace("%changelog\n", f"%changelog\n{entry}")
    
    # 2. 通用的变量转换逻辑
    else:
        # 默认转换配置
        default_transforms = {"package_version": "strip_v"}
        if pkg_config["type"] == "github_commit":
            default_transforms = {"commit": "raw"}
        
        transforms = pkg_config.get("transforms", default_transforms)
        
        for var_name, rule in transforms.items():
            # 如果是 commit 类型，raw_version 是字典
            val = raw_version["sha"] if isinstance(raw_version, dict) else raw_version
            val = apply_transform(val, rule)
            new_content = re.sub(rf'(%global {var_name}\s+)\S+', rf'\g<1>{val}', new_content)
        
        # 统一重置 Release 号 (可选)
        if pkg_config.get("reset_release", True) and "github_commit" not in pkg_config["type"]:
            new_content = re.sub(r'(Release:\s+)\S+', r'\g<1>1%{?dist}', new_content)

    if new_content != content:
        Path(spec_path).write_text(new_content)
        updated = True
    return updated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", required=True)
    args = parser.parse_args()

    with open("packages.toml", "rb") as f:
        full_config = tomllib.load(f)
        config = full_config[args.pkg]

    pkg_type = config["type"]
    raw_version = None

    if pkg_type in ["github_release", "ge_proton"]: # ge_proton 也是从 release 获取
        raw_version = get_latest_github_release(config["repo"])
    elif pkg_type in ["github_commit", "github_commit_complex"]:
        raw_version = get_latest_github_commit(config["repo"])
    elif pkg_type == "aur":
        raw_version = get_aur_version(config["repo"])
    elif pkg_type == "gitea_release":
        raw_version = get_gitea_release(config["api_base"], config["repo"])

    if not raw_version:
        print(f"Error: Could not fetch version for {args.pkg}")
        sys.exit(1)

    updated = update_spec(config["spec"], raw_version, config)
    
    v_str = raw_version if isinstance(raw_version, str) else raw_version["short"]
    print(f"updated={str(updated).lower()}")
    print(f"version={v_str}")
    print(f"copr_repos={','.join(config['copr_repos'])}")
    print(f"spec_file={config['spec']}")

if __name__ == "__main__":
    main()
