import re
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGES_TOML = REPO_ROOT / "packages" / "packages.toml"
README = REPO_ROOT / "README.md"
START_MARKER = "<!-- AUTO-GENERATED:STATUS_TABLE:START -->"
END_MARKER = "<!-- AUTO-GENERATED:STATUS_TABLE:END -->"


def load_packages():
    with PACKAGES_TOML.open("rb") as f:
        return tomllib.load(f)


def read_spec_name(spec_path_str, fallback_name):
    spec_path = REPO_ROOT / spec_path_str
    content = spec_path.read_text(errors="ignore")
    match = re.search(r"^Name:\s*(\S+)", content, re.M)
    return match.group(1) if match else fallback_name


def pick_status_repo(config):
    repos = config.get("copr_repos", [])
    return repos[-1] if repos else None


def build_status_table():
    packages = load_packages()
    lines = [
        "| Package | Status |",
        "| --- | --- |",
    ]

    for package_key, config in packages.items():
        package_name = read_spec_name(config["spec"], package_key)
        repo = pick_status_repo(config)
        if repo is None:
            status = "N/A"
        else:
            image = (
                f"https://copr.fedorainfracloud.org/coprs/{repo}/package/"
                f"{package_name}/status_image/last_build.png"
            )
            link = (
                f"https://copr.fedorainfracloud.org/coprs/{repo}/package/"
                f"{package_name}/"
            )
            status = f"[![Copr build status]({image})]({link})"

        lines.append(f"| `{package_name}` | {status} |")

    return "\n".join(lines)


def update_readme():
    content = README.read_text()
    table = build_status_table()
    replacement = f"{START_MARKER}\n{table}\n{END_MARKER}"
    pattern = rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}"
    new_content = re.sub(pattern, replacement, content, flags=re.S)

    if new_content == content:
        return False

    README.write_text(new_content)
    return True


def main():
    updated = update_readme()
    print("updated=true" if updated else "updated=false")


if __name__ == "__main__":
    main()
