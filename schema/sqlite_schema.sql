PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_hash TEXT NOT NULL UNIQUE,
    title TEXT,
    author TEXT,
    date TEXT,
    source TEXT,
    tags TEXT,
    url TEXT,
    file_path TEXT NOT NULL,
    file_type TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_metadata TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    title,
    author,
    date,
    source,
    tags,
    text,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, title, author, date, source, tags, text)
    SELECT
        new.id,
        COALESCE(d.title, ''),
        COALESCE(d.author, ''),
        COALESCE(d.date, ''),
        COALESCE(d.source, ''),
        COALESCE(d.tags, ''),
        new.text
    FROM documents d
    WHERE d.id = new.document_id;
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, title, author, date, source, tags, text)
    SELECT
        'delete',
        old.id,
        COALESCE(d.title, ''),
        COALESCE(d.author, ''),
        COALESCE(d.date, ''),
        COALESCE(d.source, ''),
        COALESCE(d.tags, ''),
        old.text
    FROM documents d
    WHERE d.id = old.document_id;
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, title, author, date, source, tags, text)
    SELECT
        'delete',
        old.id,
        COALESCE(d.title, ''),
        COALESCE(d.author, ''),
        COALESCE(d.date, ''),
        COALESCE(d.source, ''),
        COALESCE(d.tags, ''),
        old.text
    FROM documents d
    WHERE d.id = old.document_id;

    INSERT INTO chunks_fts(rowid, title, author, date, source, tags, text)
    SELECT
        new.id,
        COALESCE(d.title, ''),
        COALESCE(d.author, ''),
        COALESCE(d.date, ''),
        COALESCE(d.source, ''),
        COALESCE(d.tags, ''),
        new.text
    FROM documents d
    WHERE d.id = new.document_id;
END;

CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
