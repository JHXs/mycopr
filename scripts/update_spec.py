import re
import argparse
import json
from datetime import datetime
from common import apply_transform, load_packages, resolve_repo_path

def update_spec(config, data):
    spec_path = resolve_repo_path(config["spec"])
    content = spec_path.read_text()
    new_content = content

    # 1. 通用变量映射 (根据 transforms 配置)
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
        new_content = re.sub(rf'(%global\s+{var_name}\s+)\S+', rf'\g<1>{val}', new_content)

    # 2. 自动生成 Changelog (如果配置了 update_changelog)
    if config.get("update_changelog") and "%changelog" in new_content:
        # 仅当 spec 中还没有这个 commit short 时才更新
        short_sha = data.get("short")
        if short_sha and short_sha not in content:
            date_str = datetime.now().strftime("%a %b %d %Y")
            commit_date = data.get("date", "")
            commit_msg = data.get("msg", "Auto-update")
            entry = f"* {date_str} GitHub Actions <actions@github.com> - {commit_date}git{short_sha}\n- Auto-update to commit {short_sha}: {commit_msg}\n\n"
            new_content = new_content.replace("%changelog\n", f"%changelog\n{entry}")

    # 3. 统一重置 Release 号 (仅限非 commit 类型)
    if config.get("reset_release", True) and "commit" not in config["type"]:
        new_content = re.sub(r'(Release:\s+)\S+', r'\g<1>1%{?dist}', new_content)

    if new_content != content:
        spec_path.write_text(new_content)
        return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", required=True)
    parser.add_argument("--upstream-data", required=True)
    args = parser.parse_args()

    data = json.loads(args.upstream_data)
    config = load_packages()[args.pkg]

    import sys
    print(f"📝 Updating {args.pkg} spec file...", file=sys.stderr)
    updated = update_spec(config, data)
    
    if updated:
        print(f"  ✨ Successfully updated to {data.get('version') or data.get('short')}", file=sys.stderr)
    else:
        print(f"  ℹ️ No changes needed for spec file", file=sys.stderr)

    # 输出结果给 GHA
    print(f"updated={'true' if updated else 'false'}")
    print(f"version={data.get('version') or data.get('short') or 'updated'}")
    print(f"copr_repos={','.join(config['copr_repos'])}")
    print(f"spec_file={config['spec']}")

if __name__ == "__main__":
    main()
