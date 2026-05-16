#!/usr/bin/env python3
"""Ingest JSON / JSONL files into the BHA SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import chunk_text, find_first, json_dumps, normalize_text, sha256_text  # noqa: E402

TEXT_KEYS = ["body", "content", "text", "article", "正文", "内容"]
TITLE_KEYS = ["title", "name", "标题", "篇名"]
AUTHOR_KEYS = ["author", "authors", "作者"]
DATE_KEYS = ["date", "time", "publish_date", "publication_date", "日期", "时间"]
SOURCE_KEYS = ["source", "出处", "来源", "刊物", "报纸"]
TAG_KEYS = ["tags", "keywords", "category", "categories", "标签", "关键词", "分类"]
URL_KEYS = ["url", "link", "source_url", "原文链接", "链接"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest JSON/JSONL files into SQLite.")
    parser.add_argument("--input", required=True, help="Input file or directory.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in characters.")
    parser.add_argument("--overlap", type=int, default=120, help="Chunk overlap in characters.")
    return parser.parse_args()


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() in {".json", ".jsonl"}:
            yield path
        return
    for suffix in ("*.json", "*.jsonl"):
        yield from path.rglob(suffix)


def load_records(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value
        return

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        value = json.load(f)

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item
    elif isinstance(value, dict):
        # Some exports may use {items: [...]} or {data: [...]}.
        for key in ("items", "data", "records", "articles", "documents"):
            if isinstance(value.get(key), list):
                for item in value[key]:
                    if isinstance(item, dict):
                        yield item
                return
        yield value


def extract_text(record: dict[str, Any]) -> str:
    text = find_first(record, TEXT_KEYS)
    if text:
        return normalize_text(text)

    # Fallback: concatenate plausible long string fields.
    parts: list[str] = []
    for key, value in record.items():
        if isinstance(value, str) and len(value) >= 80:
            parts.append(value)
    return normalize_text("\n\n".join(parts))


def insert_record(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    file_path: Path,
    root: Path,
    chunk_size: int,
    overlap: int,
) -> tuple[bool, int]:
    text = extract_text(record)
    if not text:
        return False, 0

    title = find_first(record, TITLE_KEYS)
    author = find_first(record, AUTHOR_KEYS)
    date = find_first(record, DATE_KEYS)
    source = find_first(record, SOURCE_KEYS)
    tags = find_first(record, TAG_KEYS)
    url = find_first(record, URL_KEYS)
    rel_path = str(file_path.relative_to(root)) if file_path.is_relative_to(root) else str(file_path)
    doc_hash = sha256_text("\n".join([title, author, date, source, text]))

    conn.execute(
        """
        INSERT OR IGNORE INTO documents
        (doc_hash, title, author, date, source, tags, url, file_path, file_type, raw_metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (doc_hash, title, author, date, source, tags, url, rel_path, "json", json_dumps(record)),
    )
    doc_id = conn.execute("SELECT id FROM documents WHERE doc_hash = ?", (doc_hash,)).fetchone()[0]

    # If this is a duplicate already chunked, skip.
    existing = conn.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?", (doc_id,)).fetchone()[0]
    if existing:
        return False, 0

    chunks = chunk_text(text, size=chunk_size, overlap=overlap)
    conn.executemany(
        """
        INSERT INTO chunks(document_id, chunk_index, text, char_start, char_end)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(doc_id, idx, chunk, start, end) for idx, (start, end, chunk) in enumerate(chunks)],
    )
    return True, len(chunks)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    db_path = Path(args.db)
    root = input_path if input_path.is_dir() else input_path.parent

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found. Run init_db.py first: {db_path}")

    files = list(iter_files(input_path))
    if not files:
        print(f"No JSON/JSONL files found under {input_path}")
        return

    inserted_docs = 0
    inserted_chunks = 0
    errors = 0

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for file_path in files:
            try:
                for record in load_records(file_path):
                    inserted, n_chunks = insert_record(conn, record, file_path, root, args.chunk_size, args.overlap)
                    if inserted:
                        inserted_docs += 1
                        inserted_chunks += n_chunks
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(f"ERROR {file_path}: {exc}", file=sys.stderr)
        conn.commit()

    print(f"Processed files: {len(files)}")
    print(f"Inserted documents: {inserted_docs}")
    print(f"Inserted chunks: {inserted_chunks}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
