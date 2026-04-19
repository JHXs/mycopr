import re
import argparse
import json
from pathlib import Path
from datetime import datetime
from common import apply_transform

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def update_spec(config, data):
    spec_path = Path(config["spec"])
    content = spec_path.read_text()
    new_content = content

    if config["type"] == "github_commit_complex":
        new_content = re.sub(r'(%global git_commit\s+)\S+', rf'\g<1>{data["sha"]}', new_content)
        new_content = re.sub(r'(%global git_short\s+)\S+', rf'\g<1>{data["short"]}', new_content)
        new_content = re.sub(r'(%global commit_date\s+)\S+', rf'\g<1>{data["date"]}', new_content)
        if "%changelog" in new_content and data["short"] not in content:
            date_str = datetime.now().strftime("%a %b %d %Y")
            entry = f"* {date_str} GitHub Actions <actions@github.com> - {data['date']}git{data['short']}\n- Auto-update to commit {data['short']}: {data['msg']}\n\n"
            new_content = new_content.replace("%changelog\n", f"%changelog\n{entry}")
    else:
        default_transforms = {"package_version": "strip_v"}
        if config["type"] == "github_commit":
            default_transforms = {"commit": "raw"}
        
        transforms = config.get("transforms", default_transforms)
        for var_name, rule in transforms.items():
            val = data.get("version") or data.get("sha")
            val = apply_transform(val, rule)
            new_content = re.sub(rf'(%global {var_name}\s+)\S+', rf'\g<1>{val}', new_content)
        
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
    with open("packages.toml", "rb") as f:
        config = tomllib.load(f)[args.pkg]

    updated = update_spec(config, data)

    print(f"updated={'true' if updated else 'false'}")
    print(f"version={data.get('version') or data.get('short') or 'updated'}")
    print(f"copr_repos={','.join(config['copr_repos'])}")
    print(f"spec_file={config['spec']}")

if __name__ == "__main__":
    main()
