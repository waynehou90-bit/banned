#!/usr/bin/env python3
"""Batch export default ChatGPT Project archive packs.

Reads packs/default_packs.json and calls the same export logic used by
scripts/export_project_pack.py. This creates Project-readable Markdown packs
under project_sources/ so a ChatGPT Project can index them from GitHub.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export default BHA Project packs from local SQLite database.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument("--config", default="packs/default_packs.json", help="Pack config JSON path.")
    parser.add_argument("--out", default="project_sources", help="Output root directory.")
    parser.add_argument("--only", nargs="*", default=[], help="Optional pack names to export. If omitted, export all.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def load_config(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    packs = data.get("packs", [])
    if not isinstance(packs, list):
        raise ValueError("Config field 'packs' must be a list")
    return packs


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    db_path = Path(args.db)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Build it first with init_db.py and ingest_json.py.")

    packs = load_config(config_path)
    selected = set(args.only)
    if selected:
        packs = [pack for pack in packs if pack.get("pack_name") in selected]

    if not packs:
        print("No packs selected.")
        return

    script = Path(__file__).resolve().parent / "export_project_pack.py"

    for pack in packs:
        pack_name = str(pack["pack_name"])
        query = str(pack["query"])
        limit = str(pack.get("limit", 200))
        source = str(pack.get("source", ""))
        date = str(pack.get("date", ""))

        cmd = [
            sys.executable,
            str(script),
            "--db",
            str(db_path),
            "--query",
            query,
            "--pack-name",
            pack_name,
            "--limit",
            limit,
            "--out",
            args.out,
        ]
        if source:
            cmd.extend(["--source", source])
        if date:
            cmd.extend(["--date", date])

        print("\n>>> " + " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, check=True)

    print("\nDone. Review project_sources/, then commit and push the generated packs.")


if __name__ == "__main__":
    main()
