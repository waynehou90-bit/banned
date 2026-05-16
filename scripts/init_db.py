#!/usr/bin/env python3
"""Initialize the SQLite database for Banned Historical Archives."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize SQLite database.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument(
        "--schema",
        default="schema/sqlite_schema.sql",
        help="Path to SQL schema file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    schema_path = Path(args.schema)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    print(f"Initialized database: {db_path}")


if __name__ == "__main__":
    main()
