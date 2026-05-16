#!/usr/bin/env python3
"""Shared utilities for BHA database ingestion."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def chunk_text(text: str, size: int = 1000, overlap: int = 120) -> list[tuple[int, int, str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")

    text = normalize_text(text)
    if not text:
        return []

    chunks: list[tuple[int, int, str]] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + size, text_len)
        # Prefer ending at a paragraph or sentence boundary when possible.
        if end < text_len:
            window = text[start:end]
            boundary_candidates = [window.rfind("\n\n"), window.rfind("。"), window.rfind("；"), window.rfind("？"), window.rfind("！")]
            boundary = max(boundary_candidates)
            if boundary > int(size * 0.55):
                end = start + boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((start, end, chunk))
        if end >= text_len:
            break
        start = max(0, end - overlap)

    return chunks


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return "; ".join(as_text(item) for item in value if as_text(item))
    return str(value).strip()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def find_first(record: dict[str, Any], keys: list[str]) -> str:
    lowered = {str(k).lower(): v for k, v in record.items()}
    for key in keys:
        if key in record and as_text(record[key]):
            return as_text(record[key])
        if key.lower() in lowered and as_text(lowered[key.lower()]):
            return as_text(lowered[key.lower()])
    return ""


def read_text_lossy(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "big5", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")
