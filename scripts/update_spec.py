#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

PACKAGE_VERSION_RE = re.compile(r"^(%global\s+package_version\s+)(\S+)(\s*)$")
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


def add_changelog_entry(lines: list[str], version: str) -> list[str]:
    if AUTOCHANGELOG_MARKER in lines:
        return lines

    entry = [
        f"* {changelog_date(dt.datetime.now(dt.UTC))} {CHANGELOG_AUTHOR} - {version}-1",
        f"- Update to {version}",
        "",
    ]

    if CHANGELOG_HEADER in lines:
        index = lines.index(CHANGELOG_HEADER)
        return lines[: index + 1] + entry + lines[index + 1 :]

    trimmed = lines[:]
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    return trimmed + ["", CHANGELOG_HEADER] + entry


def update_package_version(lines: list[str], new_version: str) -> tuple[list[str], bool]:
    updated = []
    changed = False
    version_updated = False

    for line in lines:
        match = PACKAGE_VERSION_RE.match(line)
        if match:
            version_updated = True
            current_version = match.group(2)
            if current_version != new_version:
                updated.append(f"{match.group(1)}{new_version}{match.group(3)}")
                changed = True
            else:
                updated.append(line)
            continue

        match = RELEASE_RE.match(line)
        if match:
            desired_release = "1%{?dist}"
            if match.group(2) != desired_release:
                updated.append(f"{match.group(1)}{desired_release}{match.group(3)}")
                changed = True
            else:
                updated.append(line)
            continue

        updated.append(line)

    if not version_updated:
        raise RuntimeError("missing %global package_version")

    if changed:
        updated = add_changelog_entry(updated, new_version)
    return updated, changed


def update_spec_file(spec_path: pathlib.Path, strategy: str, latest_version: str) -> bool:
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    if strategy != "package_version":
        raise RuntimeError(f"unsupported update_strategy for phase one: {strategy}")

    updated_lines, changed = update_package_version(lines, latest_version)
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
        if update_spec_file(spec_path, package["update_strategy"], package["latest_version"]):
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
