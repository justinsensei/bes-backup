# Semantic Pointer: Implementation & Technical Reference

This reference details the lightweight, on-demand local semantic memory architecture built for Justin's Obsidian vault.

---

## Architectural Principles
1. **Zero Package Bloat:** Avoids heavy local vector databases, PyTorch, or CUDA dependencies (saving >1.5 GB in dependencies).
2. **Local Vector Engine:** Uses the `sqlite-vec` (version `0.1.9`) extension within standard Python SQLite.
3. **High-Performance Batching:** Utilizes Gemini's REST endpoint `batchEmbedContents` with a custom parallel chunking mechanism to index up to 180 files/minute.
4. **Non-Destructive & Incremental:** Relies on content hashing (MD5) and file `mtime` modification checks to prevent redundant indexing.

---

## Database Schema (`semantic_memory.db`)

The database is structured to support both document-level similarity (for note bridging) and granular paragraph-level similarity (for context pruning):

```sql
-- 1. Document Metadata Cache
CREATE TABLE IF NOT EXISTS document_cache (
    path TEXT PRIMARY KEY,
    mtime REAL,
    hash TEXT,
    title TEXT,
    category TEXT,
    last_indexed TEXT
);

-- 2. Granular Paragraph Chunks
CREATE TABLE IF NOT EXISTS paragraphs (
    id TEXT PRIMARY KEY, -- e.g., "Notes/example.md#chunk_idx"
    document_path TEXT,
    chunk_index INTEGER,
    content TEXT,
    char_count INTEGER,
    FOREIGN KEY(document_path) REFERENCES document_cache(path) ON DELETE CASCADE
);

-- 3. sqlite-vec Document Embeddings (3072-dimensional)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents USING vec0(
    document_path TEXT PRIMARY KEY,
    embedding float[3072]
);

-- 4. sqlite-vec Paragraph Embeddings (3072-dimensional)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_paragraphs USING vec0(
    paragraph_id TEXT PRIMARY KEY,
    embedding float[3072]
);
```

---

## Technical Details & API Quirks

### 1. Vector Serialisation in SQLite
In Python's `sqlite3`, vectors are inserted as binary blobs using native float serialization:
```python
import struct
# Serialize 3072 floats as 32-bit little-endian floats
binary_embedding = struct.pack(f"{len(embedding)}f", *embedding)
```

### 2. Google Gemini Embedding API
Uses model `models/gemini-embedding-2` yielding `3072` dimensions.
- **Single Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key=...`
- **Batch Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:batchEmbedContents?key=...` (allows up to 100 requests per payload).

### 3. Verification & Cosine Similarity Queries
Standard cosine distance query in `sqlite-vec`:
```sql
SELECT 
    v.document_path,
    1.0 - vec_distance_cosine(v.embedding, ?) as similarity
FROM vec_documents v
ORDER BY similarity DESC
LIMIT 5;
```
