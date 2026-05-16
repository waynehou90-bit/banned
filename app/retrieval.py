from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def connect_db(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def quote_fts_query(query: str) -> str:
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
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


def search_fts(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
    source: str = "",
    date: str = "",
) -> list[dict[str, Any]]:
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
    rows = conn.execute(sql, (query, source, source, date, date, limit)).fetchall()
    return [_row_to_dict(row) for row in rows]


def search_like(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
    source: str = "",
    date: str = "",
) -> list[dict[str, Any]]:
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
        c.char_start,
        c.char_end,
        c.text,
        substr(c.text, 1, 260) AS snippet,
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
    rows = conn.execute(sql, (query, query, query, query, source, source, date, date, limit)).fetchall()
    return [_row_to_dict(row) for row in rows]


def retrieve(
    db_path: str | Path,
    query: str,
    limit: int = 10,
    source: str = "",
    date: str = "",
) -> list[dict[str, Any]]:
    with connect_db(db_path) as conn:
        try:
            results = search_fts(conn, query, limit, source, date)
            if not results:
                results = search_fts(conn, quote_fts_query(query), limit, source, date)
        except sqlite3.OperationalError:
            results = []

        if not results:
            results = search_like(conn, query, limit, source, date)

    return results


def get_stats(db_path: str | Path) -> dict[str, Any]:
    with connect_db(db_path) as conn:
        docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        sources = conn.execute("SELECT COUNT(DISTINCT source) FROM documents WHERE source != ''").fetchone()[0]
    return {"documents": docs, "chunks": chunks, "sources": sources, "db_path": str(db_path)}
