#!/usr/bin/env python3
"""Export SQLite search results into ChatGPT Project-readable Markdown packs.

This solves the practical limitation that ChatGPT Projects can index repository
text files but cannot execute a local SQLite database. The script queries the
local BHA SQLite database and emits Markdown/JSON files under project_sources/.
Commit the generated pack to GitHub, index the repository in ChatGPT Project,
and the Project can retrieve the selected archive chunks as source files.

Important retrieval note:
SQLite FTS5 with the default unicode61 tokenizer is not reliable for Chinese
word segmentation. For Chinese archive work, this exporter therefore supports
multi-query recall and LIKE fallback. Use repeated --query flags or separate
terms with OR / | / comma / Chinese comma / semicolon.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "bha-pack"


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def quote_fts_query(query: str) -> str:
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def split_query_terms(queries: Iterable[str]) -> list[str]:
    terms: list[str] = []
    for query in queries:
        for item in re.split(r"\s+(?:OR|or)\s+|[|,，;；\n]+", query):
            item = item.strip()
            if item:
                terms.append(item)
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            result.append(term)
    return result


def search_fts(conn: sqlite3.Connection, query: str, limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    sql = """
    SELECT
        d.id AS document_id,
        d.title,
        d.author,
        d.date,
        d.source,
        d.tags,
        d.url,
        d.file_path,
        c.chunk_index,
        c.char_start,
        c.char_end,
        c.text,
        snippet(chunks_fts, 5, '[', ']', '...', 32) AS snippet,
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
    try:
        rows = conn.execute(sql, (query, source, source, date, date, limit)).fetchall()
        if rows:
            return rows
        return conn.execute(sql, (quote_fts_query(query), source, source, date, date, limit)).fetchall()
    except sqlite3.OperationalError:
        return []


def search_like(conn: sqlite3.Connection, query: str, limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    sql = """
    SELECT
        d.id AS document_id,
        d.title,
        d.author,
        d.date,
        d.source,
        d.tags,
        d.url,
        d.file_path,
        c.chunk_index,
        c.char_start,
        c.char_end,
        c.text,
        CASE
            WHEN d.title LIKE '%' || ? || '%' THEN '[title] ' || d.title
            WHEN d.author LIKE '%' || ? || '%' THEN '[author] ' || d.author
            WHEN d.source LIKE '%' || ? || '%' THEN '[source] ' || d.source
            ELSE substr(c.text, max(1, instr(c.text, ?) - 80), 260)
        END AS snippet,
        0.0 AS rank
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE (c.text LIKE '%' || ? || '%'
        OR d.title LIKE '%' || ? || '%'
        OR d.author LIKE '%' || ? || '%'
        OR d.source LIKE '%' || ? || '%'
        OR d.tags LIKE '%' || ? || '%')
      AND (? = '' OR d.source LIKE '%' || ? || '%')
      AND (? = '' OR d.date LIKE '%' || ? || '%')
    LIMIT ?
    """
    return conn.execute(
        sql,
        (query, query, query, query, query, query, query, query, query, source, source, date, date, limit),
    ).fetchall()


def search_one_term(conn: sqlite3.Connection, term: str, limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    rows = search_fts(conn, term, limit, source, date)
    if rows:
        return rows
    return search_like(conn, term, limit, source, date)


def search_many(conn: sqlite3.Connection, queries: list[str], limit: int, source: str = "", date: str = "") -> list[sqlite3.Row]:
    terms = split_query_terms(queries)
    if not terms:
        return []

    per_term_limit = max(limit, 50)
    merged: dict[tuple[int, int], sqlite3.Row] = {}

    for term in terms:
        for row in search_one_term(conn, term, per_term_limit, source, date):
            key = (row["document_id"], row["chunk_index"])
            if key not in merged:
                merged[key] = row
            if len(merged) >= limit:
                break
        if len(merged) >= limit:
            break

    return list(merged.values())[:limit]


def row_to_record(row: sqlite3.Row, pack_name: str) -> dict[str, Any]:
    citation_id = f"{pack_name}::doc{row['document_id']}::chunk{row['chunk_index']}"
    return {
        "citation_id": citation_id,
        "document_id": row["document_id"],
        "title": row["title"] or "",
        "author": row["author"] or "",
        "date": row["date"] or "",
        "source": row["source"] or "",
        "tags": row["tags"] or "",
        "url": row["url"] or "",
        "file_path": row["file_path"] or "",
        "chunk_index": row["chunk_index"],
        "char_start": row["char_start"],
        "char_end": row["char_end"],
        "snippet": (row["snippet"] or "").replace("\n", " "),
        "text": row["text"] or "",
        "rank": row["rank"],
    }


def write_pack(out_dir: Path, pack_name: str, queries: list[str], source: str, date: str, records: list[dict[str, Any]]) -> None:
    pack_dir = out_dir / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    query_display = " | ".join(queries)

    manifest = {
        "pack_name": pack_name,
        "queries": queries,
        "query": query_display,
        "source_filter": source,
        "date_filter": date,
        "generated_at": generated_at,
        "record_count": len(records),
        "purpose": "ChatGPT Project-readable archive pack generated from local BHA SQLite database.",
        "retrieval_note": "Chinese recall uses multi-query FTS plus LIKE fallback; citation evidence still comes from exported chunks.",
    }

    (pack_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    index_lines = [
        f"# BHA Project Pack｜{pack_name}",
        "",
        "## 生成信息",
        "",
        f"- 查询词：`{query_display}`",
        f"- 来源过滤：`{source or '无'}`",
        f"- 日期过滤：`{date or '无'}`",
        f"- 生成时间：`{generated_at}`",
        f"- chunk 数量：`{len(records)}`",
        "",
        "## 使用规则",
        "",
        "1. 本文件夹是从本地 SQLite/FTS5 检索结果导出的 Project 可索引档案包。",
        "2. ChatGPT Project 只能读取这些已提交到 GitHub 的文本，不等于可以查询完整 SQLite 数据库。",
        "3. 回答时必须引用 `citation_id`、`title`、`date`、`source`、`file_path`、`chunk_index`。",
        "4. 单一 chunk 只可作为材料线索，不可直接作为完整历史结论。",
        "5. 若材料不足，结论标注为“待核实”。",
        "",
        "## 命中材料索引",
        "",
        "| # | citation_id | title | date | source | file_path | chunk |",
        "|---|---|---|---|---|---|---|",
    ]

    for idx, rec in enumerate(records, start=1):
        title = (rec["title"] or "").replace("|", "｜")
        source_text = (rec["source"] or "").replace("|", "｜")
        file_path = (rec["file_path"] or "").replace("|", "｜")
        index_lines.append(
            f"| {idx} | `{rec['citation_id']}` | {title} | {rec['date']} | {source_text} | `{file_path}` | {rec['chunk_index']} |"
        )

    (pack_dir / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    chunk_lines = [
        f"# BHA Project Pack Chunks｜{pack_name}",
        "",
        "本文件供 ChatGPT Project 索引用。每个条目保留可回溯元数据。",
        "",
    ]

    for idx, rec in enumerate(records, start=1):
        chunk_lines.extend(
            [
                "---",
                "",
                f"## {idx}. {rec['title'] or '(untitled)'}",
                "",
                f"- citation_id: `{rec['citation_id']}`",
                f"- title: {rec['title']}",
                f"- author: {rec['author']}",
                f"- date: {rec['date']}",
                f"- source: {rec['source']}",
                f"- tags: {rec['tags']}",
                f"- url: {rec['url']}",
                f"- file_path: `{rec['file_path']}`",
                f"- document_id: `{rec['document_id']}`",
                f"- chunk_index: `{rec['chunk_index']}`",
                f"- char_range: `{rec['char_start']}-{rec['char_end']}`",
                "",
                "### 命中片段",
                "",
                rec["snippet"],
                "",
                "### 正文 chunk",
                "",
                rec["text"],
                "",
            ]
        )

    (pack_dir / "chunks.md").write_text("\n".join(chunk_lines) + "\n", encoding="utf-8")

    jsonl_path = pack_dir / "chunks.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ChatGPT Project-readable archive pack from SQLite search results.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument(
        "--query",
        required=True,
        action="append",
        help="Search query used to select archive chunks. Can be repeated. OR/|/comma separated terms are split for Chinese recall.",
    )
    parser.add_argument("--pack-name", default="", help="Pack folder name. Defaults to slugified first query.")
    parser.add_argument("--out", default="project_sources", help="Output root directory.")
    parser.add_argument("--limit", type=int, default=200, help="Maximum chunks to export.")
    parser.add_argument("--source", default="", help="Optional source filter.")
    parser.add_argument("--date", default="", help="Optional date filter.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    pack_name = slugify(args.pack_name or args.query[0])
    out_dir = Path(args.out)

    with connect(db_path) as conn:
        rows = search_many(conn, args.query, args.limit, args.source, args.date)

    records = [row_to_record(row, pack_name) for row in rows]
    write_pack(out_dir, pack_name, args.query, args.source, args.date, records)

    print(f"Exported {len(records)} chunks to {out_dir / pack_name}")
    print("Next step: git add project_sources/<pack>; git commit; then re-index this repo in ChatGPT Project.")


if __name__ == "__main__":
    main()
