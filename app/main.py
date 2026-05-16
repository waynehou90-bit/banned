from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.retrieval import get_stats, retrieve

DB_PATH = os.getenv("BHA_DB_PATH", "db/bha.sqlite")

app = FastAPI(
    title="Banned Historical Archives Retrieval API",
    description="SQLite FTS5 retrieval API for a local Banned Historical Archives database.",
    version="0.1.0",
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query.")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of chunks to return.")
    source: str = Field("", description="Optional source substring filter.")
    date: str = Field("", description="Optional date substring filter, e.g. 1967 or 1967-01.")


class SearchResponse(BaseModel):
    query: str
    limit: int
    count: int
    results: list[dict[str, Any]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict[str, Any]:
    try:
        return get_stats(DB_PATH)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/search", response_model=SearchResponse)
def search_get(
    q: str = Query(..., min_length=1, description="Search query."),
    limit: int = Query(10, ge=1, le=50),
    source: str = Query(""),
    date: str = Query(""),
) -> SearchResponse:
    try:
        results = retrieve(DB_PATH, q, limit=limit, source=source, date=date)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SearchResponse(query=q, limit=limit, count=len(results), results=results)


@app.post("/search", response_model=SearchResponse)
def search_post(payload: SearchRequest) -> SearchResponse:
    try:
        results = retrieve(
            DB_PATH,
            payload.query,
            limit=payload.limit,
            source=payload.source,
            date=payload.date,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SearchResponse(query=payload.query, limit=payload.limit, count=len(results), results=results)
