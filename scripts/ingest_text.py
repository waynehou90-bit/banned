#!/usr/bin/env python3
"""Ingest TXT / Markdown files into the BHA SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import chunk_text, json_dumps, normalize_text, read_text_lossy, sha256_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest TXT/Markdown files into SQLite.")
    parser.add_argument("--input", required=True, help="Input file or directory.")
    parser.add_argument("--db", default="db/bha.sqlite", help="SQLite database path.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in characters.")
    parser.add_argument("--overlap", type=int, default=120, help="Chunk overlap in characters.")
    return parser.parse_args()


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() in {".txt", ".md"}:
            yield path
        return
    for suffix in ("*.txt", "*.md"):
        yield from path.rglob(suffix)


def infer_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        clean = line.strip().lstrip("#").strip()
        if 3 <= len(clean) <= 120:
            return clean
    return path.stem


def insert_file(
    conn: sqlite3.Connection,
    file_path: Path,
    root: Path,
    chunk_size: int,
    overlap: int,
) -> tuple[bool, int]:
    raw = read_text_lossy(file_path)
    text = normalize_text(raw)
    if not text:
        return False, 0

    title = infer_title(text, file_path)
    rel_path = str(file_path.relative_to(root)) if file_path.is_relative_to(root) else str(file_path)
    doc_hash = sha256_text("\n".join([title, rel_path, text]))

    metadata = {
        "inferred_title": title,
        "file_path": rel_path,
        "file_suffix": file_path.suffix.lower(),
    }

    conn.execute(
        """
        INSERT OR IGNORE INTO documents
        (doc_hash, title, author, date, source, tags, url, file_path, file_type, raw_metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (doc_hash, title, "", "", "", "", "", rel_path, file_path.suffix.lower().lstrip("."), json_dumps(metadata)),
    )
    doc_id = conn.execute("SELECT id FROM documents WHERE doc_hash = ?", (doc_hash,)).fetchone()[0]

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
        print(f"No TXT/MD files found under {input_path}")
        return

    inserted_docs = 0
    inserted_chunks = 0
    errors = 0

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for file_path in files:
            try:
                inserted, n_chunks = insert_file(conn, file_path, root, args.chunk_size, args.overlap)
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
