#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a managed package in Copr.")
    parser.add_argument("--packages-json", type=pathlib.Path, required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--build-repo", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--clone-url", required=True)
    parser.add_argument("--copr-config", type=pathlib.Path, required=True)
    return parser.parse_args()


def load_package(packages_json: pathlib.Path, package_name: str) -> dict:
    raw = json.loads(packages_json.read_text(encoding="utf-8"))
    for package in raw.get("packages", []):
        if package.get("enabled", True) and package["name"] == package_name:
            return package
    raise RuntimeError(f"unknown managed package: {package_name}")


def main() -> int:
    args = parse_args()
    package = load_package(args.packages_json.resolve(), args.package)
    if args.build_repo not in package.get("build_repos", []):
        raise RuntimeError(
            f"build repo {args.build_repo} is not configured for package {args.package}"
        )

    command = [
        "copr-cli",
        "--config",
        str(args.copr_config),
        "buildscm",
        "--clone-url",
        args.clone_url,
        "--commit",
        args.commit,
        "--subdir",
        package["subdir"],
        "--spec",
        package["spec"],
        "--type",
        "git",
        "--method",
        "rpkg",
        args.build_repo,
    ]
    print("Running:", " ".join(command))
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
