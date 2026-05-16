#!/usr/bin/env python3
"""Sync upstream banned-historical-archives data into a local raw-data directory."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

UPSTREAM_REPO = "https://github.com/banned-historical-archives/banned-historical-archives.github.io.git"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone or update upstream source branch.")
    parser.add_argument("--branch", default="json", choices=["json", "txt", "master", "main"], help="Upstream branch to sync.")
    parser.add_argument("--target", default="data/raw", help="Local target directory.")
    parser.add_argument("--repo", default=UPSTREAM_REPO, help="Upstream git repository URL.")
    parser.add_argument("--force", action="store_true", help="Delete target branch directory before cloning.")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    args = parse_args()
    target_root = Path(args.target)
    target_dir = target_root / args.branch

    target_root.mkdir(parents=True, exist_ok=True)

    if args.force and target_dir.exists():
        shutil.rmtree(target_dir)

    if (target_dir / ".git").exists():
        run(["git", "fetch", "--depth", "1", "origin", args.branch], cwd=target_dir)
        run(["git", "checkout", args.branch], cwd=target_dir)
        run(["git", "reset", "--hard", f"origin/{args.branch}"], cwd=target_dir)
    else:
        if target_dir.exists() and any(target_dir.iterdir()):
            raise RuntimeError(f"Target exists and is not an empty git repo: {target_dir}")
        run([
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            args.branch,
            args.repo,
            str(target_dir),
        ])

    print(f"Synced {args.branch} branch to {target_dir}")


if __name__ == "__main__":
    main()
