#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.request

PACKAGE_VERSION_RE = re.compile(r"^%global\s+package_version\s+(\S+)\s*$")
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_USER_AGENT = "copr-ci-check-upstream/1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check managed packages for upstream updates.")
    parser.add_argument("--packages-json", type=pathlib.Path, required=True)
    parser.add_argument(
        "--packages",
        help="Comma-separated package names to limit the run. Defaults to all enabled packages.",
    )
    parser.add_argument(
        "--force-build",
        action="store_true",
        help="Mark selected packages for build even when no upstream change is detected.",
    )
    parser.add_argument("--report-json", type=pathlib.Path)
    parser.add_argument("--github-output", type=pathlib.Path)
    return parser.parse_args()


def load_packages(packages_json: pathlib.Path) -> list[dict]:
    raw = json.loads(packages_json.read_text(encoding="utf-8"))
    packages = []
    for package in raw.get("packages", []):
        if not package.get("enabled", True):
            continue
        packages.append(package)
    if not packages:
        raise RuntimeError(f"no enabled packages found in {packages_json}")
    return packages


def filter_packages(packages: list[dict], package_filter: str | None) -> list[dict]:
    if not package_filter:
        return packages

    requested = [name.strip() for name in package_filter.split(",") if name.strip()]
    if not requested:
        raise RuntimeError("the --packages filter was provided but no package name was found")

    index = {package["name"]: package for package in packages}
    missing = [name for name in requested if name not in index]
    if missing:
        raise RuntimeError(f"unknown managed package(s): {', '.join(missing)}")
    return [index[name] for name in requested]


def read_current_version(spec_path: pathlib.Path, strategy: str) -> str:
    if strategy != "package_version":
        raise RuntimeError(f"unsupported update_strategy for phase one: {strategy}")

    for line in spec_path.read_text(encoding="utf-8").splitlines():
        match = PACKAGE_VERSION_RE.match(line)
        if match:
            return match.group(1)
    raise RuntimeError(f"could not find %global package_version in {spec_path}")


def fetch_latest_github_release(github_repo: str, tag_prefix: str) -> str:
    url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=DEFAULT_HTTP_TIMEOUT) as response:
        payload = json.load(response)

    try:
        tag_name = payload["tag_name"]
    except KeyError as exc:
        raise RuntimeError(f"missing tag_name in GitHub release response for {github_repo}") from exc

    if tag_prefix and tag_name.startswith(tag_prefix):
        return tag_name[len(tag_prefix) :]
    return tag_name


def fetch_latest_version(package: dict) -> str:
    source_type = package.get("source_type")
    if source_type != "github_release":
        raise RuntimeError(f"unsupported source_type for phase one: {source_type}")

    github_repo = package.get("github_repo")
    if not github_repo:
        raise RuntimeError(f"package {package['name']} is missing github_repo")
    return fetch_latest_github_release(github_repo, package.get("tag_prefix", ""))


def build_matrix(packages: list[dict]) -> list[dict]:
    matrix = []
    for package in packages:
        for build_repo in package.get("build_repos", []):
            matrix.append(
                {
                    "name": package["name"],
                    "subdir": package["subdir"],
                    "spec": package["spec"],
                    "build_repo": build_repo,
                }
            )
    return matrix


def write_github_output(output_path: pathlib.Path, values: dict[str, str]) -> None:
    with output_path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def main() -> int:
    args = parse_args()
    packages_json = args.packages_json.resolve()
    base_dir = packages_json.parent

    packages = filter_packages(load_packages(packages_json), args.packages)

    report_packages = []
    changed_packages = []
    for package in packages:
        spec_path = base_dir / package["subdir"] / package["spec"]
        current_version = read_current_version(spec_path, package["update_strategy"])
        latest_version = fetch_latest_version(package)
        changed = current_version != latest_version

        package_report = {
            **package,
            "spec_path": str(spec_path.relative_to(base_dir)),
            "current_version": current_version,
            "latest_version": latest_version,
            "changed": changed,
        }
        report_packages.append(package_report)
        if changed:
            changed_packages.append(package_report)

    build_packages = packages if args.force_build else changed_packages
    report = {
        "packages_json": str(packages_json.relative_to(base_dir)),
        "force_build": args.force_build,
        "selected_packages": [package["name"] for package in packages],
        "changed_packages": [package["name"] for package in changed_packages],
        "packages": report_packages,
    }

    if args.report_json:
        args.report_json.write_text(
            json.dumps(report, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    values = {
        "selected_any": str(bool(packages)).lower(),
        "selected_names": ",".join(package["name"] for package in packages),
        "changed_any": str(bool(changed_packages)).lower(),
        "changed_names": ",".join(package["name"] for package in changed_packages),
        "build_required": str(bool(build_packages)).lower(),
        "build_matrix_json": compact_json(build_matrix(build_packages)),
    }
    if args.github_output:
        write_github_output(args.github_output, values)

    for package in report_packages:
        status = "changed" if package["changed"] else "unchanged"
        print(
            f"{package['name']}: current={package['current_version']} "
            f"latest={package['latest_version']} status={status}"
        )
    print(f"selected={values['selected_names']}")
    print(f"changed={values['changed_names']}")
    print(f"build_required={values['build_required']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
