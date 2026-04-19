#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

RELEASE_RE = re.compile(r"^(Release:\s+)(\S+)(\s*)$")
CHANGELOG_HEADER = "%changelog"
AUTOCHANGELOG_MARKER = "%autochangelog"
CHANGELOG_AUTHOR = "GitHub Actions <actions@github.com>"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update spec files from a check_upstream report.")
    parser.add_argument("--report-json", type=pathlib.Path, required=True)
    parser.add_argument("--github-output", type=pathlib.Path)
    return parser.parse_args()


def write_github_output(output_path: pathlib.Path, values: dict[str, str]) -> None:
    with output_path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def changelog_date(now: dt.datetime) -> str:
    return (
        f"{DAY_NAMES[now.weekday()]} "
        f"{MONTH_NAMES[now.month - 1]} "
        f"{now.day:02d} "
        f"{now.year}"
    )


def add_changelog_entry(lines: list[str], version: str, message: str) -> list[str]:
    if AUTOCHANGELOG_MARKER in lines:
        return lines

    entry = [
        f"* {changelog_date(dt.datetime.now(dt.UTC))} {CHANGELOG_AUTHOR} - {version}-1",
        f"- {message}",
        "",
    ]

    if CHANGELOG_HEADER in lines:
        index = lines.index(CHANGELOG_HEADER)
        return lines[: index + 1] + entry + lines[index + 1 :]

    trimmed = lines[:]
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    return trimmed + ["", CHANGELOG_HEADER] + entry


def short_commit(commit: str) -> str:
    return commit[:7]


def package_version_fields(package: dict) -> dict[str, str]:
    return package.get("spec_fields", {"package_version": "package_version"})


def update_macros(
    lines: list[str],
    *,
    replacements: dict[str, str],
    release_value: str | None,
    changelog_version: str,
    changelog_message: str,
) -> tuple[list[str], bool]:
    updated = []
    changed = False
    found_macros = set()
    patterns = {
        name: re.compile(rf"^(%global\s+{re.escape(name)}\s+)(\S+)(\s*)$")
        for name in replacements
    }

    for line in lines:
        macro_match = None
        for name, pattern in patterns.items():
            match = pattern.match(line)
            if match:
                macro_match = (name, match)
                break
        if macro_match is not None:
            name, match = macro_match
            found_macros.add(name)
            current_value = match.group(2)
            new_value = replacements[name]
            if current_value != new_value:
                updated.append(f"{match.group(1)}{new_value}{match.group(3)}")
                changed = True
            else:
                updated.append(line)
            continue

        match = RELEASE_RE.match(line)
        if match:
            if release_value is not None and match.group(2) != release_value:
                updated.append(f"{match.group(1)}{release_value}{match.group(3)}")
                changed = True
            else:
                updated.append(line)
            continue

        updated.append(line)

    missing = sorted(set(replacements) - found_macros)
    if missing:
        raise RuntimeError(f"missing %global: {', '.join(missing)}")

    if changed:
        updated = add_changelog_entry(updated, changelog_version, changelog_message)
    return updated, changed


def update_package_version(
    lines: list[str],
    package: dict,
    upstream_state: dict[str, str],
) -> tuple[list[str], bool]:
    version = upstream_state["package_version"]
    return update_macros(
        lines,
        replacements={
            macro_name: upstream_state[state_key]
            for macro_name, state_key in package_version_fields(package).items()
        },
        release_value="1%{?dist}",
        changelog_version=version,
        changelog_message=f"Update to {version}",
    )


def update_commit(lines: list[str], upstream_state: dict[str, str]) -> tuple[list[str], bool]:
    commit = upstream_state["commit"]
    return update_macros(
        lines,
        replacements={"commit": commit},
        release_value="1%{?dist}",
        changelog_version=short_commit(commit),
        changelog_message=f"Update to commit {commit}",
    )


def update_git_snapshot(lines: list[str], upstream_state: dict[str, str]) -> tuple[list[str], bool]:
    snapshot_version = f"{upstream_state['commit_date']}git{upstream_state['git_short']}"
    message = (
        f"Auto-update to upstream commit {upstream_state['git_short']}: "
        f"{upstream_state['commit_msg']}"
    )
    return update_macros(
        lines,
        replacements={
            "git_commit": upstream_state["git_commit"],
            "git_short": upstream_state["git_short"],
            "commit_date": upstream_state["commit_date"],
        },
        release_value=None,
        changelog_version=snapshot_version,
        changelog_message=message,
    )


def update_spec_file(spec_path: pathlib.Path, package: dict, upstream_state: dict[str, str]) -> bool:
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    strategy = package["update_strategy"]
    if strategy == "package_version":
        updated_lines, changed = update_package_version(lines, package, upstream_state)
    elif strategy == "commit":
        updated_lines, changed = update_commit(lines, upstream_state)
    elif strategy == "git_snapshot":
        updated_lines, changed = update_git_snapshot(lines, upstream_state)
    else:
        raise RuntimeError(f"unsupported update_strategy: {strategy}")

    if changed:
        spec_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    args = parse_args()
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    repo_root = pathlib.Path.cwd().resolve()

    updated_files = []
    updated_packages = []
    for package in report.get("packages", []):
        if not package.get("changed"):
            continue
        spec_path = repo_root / package["spec_path"]
        if update_spec_file(spec_path, package, package["upstream_state"]):
            updated_files.append(package["spec_path"])
            updated_packages.append(package["name"])

    values = {
        "updated_any": str(bool(updated_files)).lower(),
        "updated_names": ",".join(updated_packages),
        "updated_files": " ".join(updated_files),
    }
    if args.github_output:
        write_github_output(args.github_output, values)

    print(f"updated_packages={values['updated_names']}")
    print(f"updated_files={values['updated_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
