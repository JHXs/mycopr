#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

PKGBUILD_VERSION_RE = re.compile(r"^pkgver=(.+)$")
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_USER_AGENT = "copr-ci-check-upstream/1.0"
PACKAGE_VERSION_FIELDS = {"package_version": "package_version"}
STRATEGY_STATE_FIELDS = {
    "commit": {"commit": "commit"},
    "git_snapshot": {
        "git_commit": "git_commit",
        "git_short": "git_short",
        "commit_date": "commit_date",
    },
}
SUPPORTED_SOURCE_TYPES = {"github_release", "aur_pkgbuild", "gitea_release", "git_commit"}
SUPPORTED_UPDATE_STRATEGIES = {"package_version", *STRATEGY_STATE_FIELDS}


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
    validate_packages(packages)
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


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=DEFAULT_HTTP_TIMEOUT) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=DEFAULT_HTTP_TIMEOUT) as response:
        return response.read().decode("utf-8")


def read_macro(spec_lines: list[str], macro_name: str) -> str:
    pattern = re.compile(rf"^%global\s+{re.escape(macro_name)}\s+(\S+)\s*$")
    for line in spec_lines:
        match = pattern.match(line)
        if match:
            return match.group(1)
    raise RuntimeError(f"could not find %global {macro_name}")


def package_version_fields(package: dict) -> dict[str, str]:
    fields = package.get("spec_fields", PACKAGE_VERSION_FIELDS)
    if not isinstance(fields, dict) or not fields:
        raise RuntimeError(f"package {package['name']} has invalid spec_fields")

    normalized = {}
    for macro_name, state_key in fields.items():
        if not isinstance(macro_name, str) or not macro_name:
            raise RuntimeError(f"package {package['name']} has invalid spec_fields macro name")
        if not isinstance(state_key, str) or not state_key:
            raise RuntimeError(f"package {package['name']} has invalid spec_fields state key")
        normalized[macro_name] = state_key
    return normalized


def package_version_rule(package: dict) -> dict | None:
    rule = package.get("version_replace")
    if rule is None:
        return None
    if not isinstance(rule, dict):
        raise RuntimeError(f"package {package['name']} has invalid version_replace")
    if set(rule) != {"from", "to"}:
        raise RuntimeError(f"package {package['name']} has invalid version_replace keys")
    if not isinstance(rule["from"], str) or not isinstance(rule["to"], str):
        raise RuntimeError(f"package {package['name']} has invalid version_replace values")
    return rule


def strategy_state_fields(package: dict) -> dict[str, str]:
    strategy = package["update_strategy"]
    if strategy == "package_version":
        return package_version_fields(package)
    try:
        return STRATEGY_STATE_FIELDS[strategy]
    except KeyError as exc:
        raise RuntimeError(f"unsupported update_strategy: {strategy}") from exc


def validate_package(package: dict) -> None:
    required_fields = ["name", "subdir", "spec", "build_repos", "source_type", "update_strategy"]
    missing = [field for field in required_fields if field not in package]
    if missing:
        raise RuntimeError(
            f"package {package.get('name', '<unknown>')} is missing required fields: {', '.join(missing)}"
        )

    if package["source_type"] not in SUPPORTED_SOURCE_TYPES:
        raise RuntimeError(
            f"package {package['name']} has unsupported source_type: {package['source_type']}"
        )
    if package["update_strategy"] not in SUPPORTED_UPDATE_STRATEGIES:
        raise RuntimeError(
            f"package {package['name']} has unsupported update_strategy: {package['update_strategy']}"
        )
    if not isinstance(package["build_repos"], list) or not package["build_repos"]:
        raise RuntimeError(f"package {package['name']} has invalid build_repos")
    if not all(isinstance(repo, str) and repo for repo in package["build_repos"]):
        raise RuntimeError(f"package {package['name']} has invalid build_repos entries")

    source_requirements = {
        "github_release": ["github_repo"],
        "aur_pkgbuild": ["aur_package"],
        "gitea_release": ["gitea_base_url", "gitea_repo"],
        "git_commit": ["github_repo"],
    }
    for field in source_requirements[package["source_type"]]:
        value = package.get(field)
        if not isinstance(value, str) or not value:
            raise RuntimeError(f"package {package['name']} is missing {field}")

    if package["source_type"] == "git_commit" and package["update_strategy"] not in {"commit", "git_snapshot"}:
        raise RuntimeError(
            f"package {package['name']} uses git_commit with unsupported update_strategy"
        )
    if package["source_type"] != "git_commit" and package["update_strategy"] in {"commit", "git_snapshot"}:
        raise RuntimeError(
            f"package {package['name']} requires source_type git_commit for update_strategy {package['update_strategy']}"
        )

    state_fields = strategy_state_fields(package)
    if package["update_strategy"] != "package_version" and (
        "spec_fields" in package or "version_replace" in package
    ):
        raise RuntimeError(
            f"package {package['name']} can only use spec_fields/version_replace with package_version"
        )

    package_version_rule(package)
    if package["update_strategy"] == "package_version":
        raw_version_used = "raw_version" in state_fields.values()
        if raw_version_used and package["source_type"] != "github_release":
            raise RuntimeError(
                f"package {package['name']} uses raw_version but source_type is not github_release"
            )


def validate_packages(packages: list[dict]) -> None:
    seen_names = set()
    for package in packages:
        name = package.get("name")
        if name in seen_names:
            raise RuntimeError(f"duplicate managed package name: {name}")
        seen_names.add(name)
        validate_package(package)


def read_state_from_macros(spec_lines: list[str], macro_state_map: dict[str, str]) -> dict[str, str]:
    return {
        state_key: read_macro(spec_lines, macro_name)
        for macro_name, state_key in macro_state_map.items()
    }


def read_current_state(spec_path: pathlib.Path, package: dict) -> dict[str, str]:
    spec_lines = spec_path.read_text(encoding="utf-8").splitlines()
    return read_state_from_macros(spec_lines, strategy_state_fields(package))


def fetch_latest_github_release(github_repo: str, tag_prefix: str) -> str:
    url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    payload = fetch_json(url)

    try:
        tag_name = payload["tag_name"]
    except KeyError as exc:
        raise RuntimeError(f"missing tag_name in GitHub release response for {github_repo}") from exc

    if tag_prefix and tag_name.startswith(tag_prefix):
        return tag_name[len(tag_prefix) :]
    return tag_name


def format_commit_date(timestamp: str) -> str:
    return timestamp.split("T", 1)[0].replace("-", "")


def fetch_latest_github_commit(github_repo: str, github_branch: str | None) -> dict[str, str]:
    params = {"per_page": 1}
    if github_branch:
        params["sha"] = github_branch
    query = urllib.parse.urlencode(params)
    url = f"https://api.github.com/repos/{github_repo}/commits?{query}"
    payload = fetch_json(url)

    if not isinstance(payload, list) or not payload:
        raise RuntimeError(f"unexpected commit response for {github_repo}")

    try:
        commit = payload[0]
        sha = commit["sha"]
        commit_data = commit["commit"]
        author = commit_data["author"]
        message = commit_data["message"].splitlines()[0].strip()
    except KeyError as exc:
        raise RuntimeError(f"missing commit metadata in GitHub commit response for {github_repo}") from exc

    return {
        "commit": sha,
        "git_commit": sha,
        "git_short": sha[:7],
        "commit_date": format_commit_date(author["date"]),
        "commit_msg": message,
    }


def fetch_aur_pkgbuild_version(aur_package: str) -> str:
    quoted_package = urllib.parse.quote(aur_package, safe="")
    url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={quoted_package}"
    payload = fetch_text(url)

    for line in payload.splitlines():
        match = PKGBUILD_VERSION_RE.match(line.strip())
        if match:
            return match.group(1).strip().strip("'\"")
    raise RuntimeError(f"missing pkgver in AUR PKGBUILD for {aur_package}")


def fetch_latest_gitea_release(gitea_base_url: str, gitea_repo: str, tag_prefix: str) -> str:
    base_url = gitea_base_url.rstrip("/")
    repo = gitea_repo.strip("/")
    url = f"{base_url}/api/v1/repos/{repo}/releases"
    payload = fetch_json(url)

    if not isinstance(payload, list):
        raise RuntimeError(f"unexpected Gitea release response for {gitea_repo}")

    stable_release = next((release for release in payload if not release.get("prerelease", False)), None)
    if stable_release is None:
        raise RuntimeError(f"no stable release found for {gitea_repo}")

    try:
        tag_name = stable_release["tag_name"]
    except KeyError as exc:
        raise RuntimeError(f"missing tag_name in Gitea release response for {gitea_repo}") from exc

    if tag_prefix and tag_name.startswith(tag_prefix):
        return tag_name[len(tag_prefix) :]
    return tag_name


def normalize_package_version(package: dict, raw_version: str) -> str:
    rule = package_version_rule(package)
    if not rule:
        return raw_version
    return raw_version.replace(rule["from"], rule["to"])


def fetch_upstream_state(package: dict) -> dict[str, str]:
    source_type = package.get("source_type")
    if source_type == "github_release":
        github_repo = package.get("github_repo")
        if not github_repo:
            raise RuntimeError(f"package {package['name']} is missing github_repo")
        raw_version = fetch_latest_github_release(github_repo, package.get("tag_prefix", ""))
        return {
            "raw_version": raw_version,
            "package_version": normalize_package_version(package, raw_version),
        }

    if source_type == "aur_pkgbuild":
        aur_package = package.get("aur_package")
        if not aur_package:
            raise RuntimeError(f"package {package['name']} is missing aur_package")
        return {"package_version": fetch_aur_pkgbuild_version(aur_package)}

    if source_type == "gitea_release":
        gitea_base_url = package.get("gitea_base_url")
        gitea_repo = package.get("gitea_repo")
        if not gitea_base_url or not gitea_repo:
            raise RuntimeError(
                f"package {package['name']} is missing gitea_base_url or gitea_repo"
            )
        return {
            "package_version": fetch_latest_gitea_release(
                gitea_base_url,
                gitea_repo,
                package.get("tag_prefix", ""),
            )
        }

    if source_type == "git_commit":
        github_repo = package.get("github_repo")
        if not github_repo:
            raise RuntimeError(f"package {package['name']} is missing github_repo")
        commit_state = fetch_latest_github_commit(github_repo, package.get("github_branch"))
        if package.get("update_strategy") == "commit":
            return {"commit": commit_state["commit"]}
        if package.get("update_strategy") == "git_snapshot":
            return {
                "git_commit": commit_state["git_commit"],
                "git_short": commit_state["git_short"],
                "commit_date": commit_state["commit_date"],
                "commit_msg": commit_state["commit_msg"],
            }
        raise RuntimeError(
            f"source_type git_commit does not support update_strategy {package.get('update_strategy')}"
        )

    raise RuntimeError(f"unsupported source_type: {source_type}")


def state_summary(state: dict[str, str]) -> str:
    if len(state) == 1:
        return next(iter(state.values()))
    return ",".join(f"{key}={value}" for key, value in state.items())


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
        current_state = read_current_state(spec_path, package)
        upstream_state = fetch_upstream_state(package)
        changed = current_state != {
            key: upstream_state[key]
            for key in current_state
        }

        package_report = {
            **package,
            "spec_path": str(spec_path.relative_to(base_dir)),
            "current_state": current_state,
            "upstream_state": upstream_state,
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
            f"{package['name']}: current={state_summary(package['current_state'])} "
            f"latest={state_summary(package['upstream_state'])} status={status}"
        )
    print(f"selected={values['selected_names']}")
    print(f"changed={values['changed_names']}")
    print(f"build_required={values['build_required']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
