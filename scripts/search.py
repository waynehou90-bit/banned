#!/usr/bin/env python3
"""Search the BHA SQLite FTS database from the command line."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search SQLite FTS database.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results.")
    parser.add_argument("--source", default="", help="Optional source filter.")
    parser.add_argument("--date", default="", help="Optional date substring filter.")
    return parser.parse_args()


def quote_fts_query(query: str) -> str:
    # SQLite FTS MATCH syntax is strict. Quoting the full user query gives a safer phrase search.
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def search_fts(conn: sqlite3.Connection, query: str, limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    sql = """
    SELECT
        d.title,
        d.author,
        d.date,
        d.source,
        d.tags,
        d.url,
        d.file_path,
        c.chunk_index,
        snippet(chunks_fts, 5, '[', ']', '...', 24) AS snippet,
        bm25(chunks_fts) AS rank
    FROM chunks_fts
    JOIN chunks c ON c.id = chunks_fts.rowid
    JOIN documents d ON d.id = c.document_id
    WHERE chunks_fts MATCH ?
      AND (? = '' OR d.source LIKE '%' || ? || '%')
      AND (? = '' OR d.date LIKE '%' || ? || '%')
    ORDER BY rank
    LIMIT ?
    """
    return list(conn.execute(sql, (query, source, source, date, date, limit)))


def search_like(conn: sqlite3.Connection, query: str, limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    sql = """
    SELECT
        d.title,
        d.author,
        d.date,
        d.source,
        d.tags,
        d.url,
        d.file_path,
        c.chunk_index,
        substr(c.text, 1, 220) AS snippet,
        0.0 AS rank
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE (c.text LIKE '%' || ? || '%'
        OR d.title LIKE '%' || ? || '%'
        OR d.author LIKE '%' || ? || '%'
        OR d.source LIKE '%' || ? || '%')
      AND (? = '' OR d.source LIKE '%' || ? || '%')
      AND (? = '' OR d.date LIKE '%' || ? || '%')
    LIMIT ?
    """
    return list(conn.execute(sql, (query, query, query, query, source, source, date, date, limit)))


def print_results(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("No results.")
        return

    for i, row in enumerate(rows, start=1):
        print("=" * 88)
        print(f"[{i}] {row['title'] or '(untitled)'}")
        if row["author"]:
            print(f"作者: {row['author']}")
        if row["date"]:
            print(f"日期: {row['date']}")
        if row["source"]:
            print(f"来源: {row['source']}")
        if row["tags"]:
            print(f"标签: {row['tags']}")
        if row["url"]:
            print(f"链接: {row['url']}")
        print(f"文件: {row['file_path']} | chunk: {row['chunk_index']}")
        print("-" * 88)
        print((row["snippet"] or "").replace("\n", " "))
    print("=" * 88)


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = search_fts(conn, args.query, args.limit, args.source, args.date)
            if not rows:
                rows = search_fts(conn, quote_fts_query(args.query), args.limit, args.source, args.date)
        except sqlite3.OperationalError:
            rows = search_like(conn, args.query, args.limit, args.source, args.date)

        if not rows:
            rows = search_like(conn, args.query, args.limit, args.source, args.date)

    print_results(rows)


if __name__ == "__main__":
    main()
