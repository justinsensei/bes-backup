#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import hashlib
import time
import random
import struct
import argparse
import requests

# Set database path
DB_PATH = os.path.expanduser("~/.hermes/state/semantic_memory.db")
VAULT_PATH = os.path.expanduser("~/vault")

# Load sqlite-vec extension
import sqlite_vec

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    return conn

def init_db(conn):
    cursor = conn.cursor()
    # document metadata cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_cache (
            path TEXT PRIMARY KEY,
            mtime REAL,
            hash TEXT,
            title TEXT,
            category TEXT,
            last_indexed TEXT
        )
    """)
    # paragraphs / chunks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paragraphs (
            id TEXT PRIMARY KEY,
            document_path TEXT,
            chunk_index INTEGER,
            content TEXT,
            char_count INTEGER,
            FOREIGN KEY(document_path) REFERENCES document_cache(path) ON DELETE CASCADE
        )
    """)
    # vector tables
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents USING vec0(
            document_path TEXT PRIMARY KEY,
            embedding float[3072]
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_paragraphs USING vec0(
            paragraph_id TEXT PRIMARY KEY,
            embedding float[3072]
        )
    """)
    conn.commit()

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    
    api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_GENERATIVE_AI_API_KEY environment variable is not set")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:batchEmbedContents?key={api_key}"
    
    results = []
    chunk_size = 100
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i+chunk_size]
        
        requests_payload = []
        for txt in chunk:
            cleaned_txt = txt.strip()
            if not cleaned_txt:
                cleaned_txt = "empty"
            requests_payload.append({
                "model": "models/gemini-embedding-2",
                "content": {"parts": [{"text": cleaned_txt}]}
            })
            
        payload = {"requests": requests_payload}
        
        for attempt in range(5):
            try:
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    embeddings_data = res.json().get("embeddings", [])
                    for emb in embeddings_data:
                        results.append(emb["values"])
                    break
                elif res.status_code == 429:
                    # Rate limit, backoff
                    time.sleep(2 ** attempt + random.random())
                else:
                    raise RuntimeError(f"API Error {res.status_code}: {res.text}")
            except Exception as e:
                if attempt == 4:
                    raise e
                time.sleep(2 ** attempt + random.random())
                
    return results

def get_embedding(text: str) -> list[float]:
    res = get_embeddings_batch([text])
    return res[0] if res else []

def parse_markdown_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.split("\n"):
                if ":" in line:
                    parts_kv = line.split(":", 1)
                    if len(parts_kv) == 2:
                        key, val = parts_kv
                        frontmatter[key.strip()] = val.strip().strip('"\'')
                    
    raw_paras = body.split("\n\n")
    paragraphs = []
    for idx, p in enumerate(raw_paras):
        p_clean = p.strip()
        if not p_clean:
            continue
        # Filter out headers, dividers, very short lines, and inline tags/links on single lines
        if p_clean.startswith("#") or p_clean.startswith("---") or len(p_clean) < 40:
            continue
        if p_clean.startswith("[[") and p_clean.endswith("]]") and "\n" not in p_clean:
            continue
        paragraphs.append((idx, p_clean))
        
    return frontmatter, body, paragraphs

def get_category_from_path(rel_path, frontmatter):
    fm_cat = frontmatter.get("category")
    if fm_cat:
        return fm_cat.replace("[[", "").replace("]]", "").strip()
        
    parts = rel_path.split(os.path.sep)
    if len(parts) > 1:
        if parts[0] == "Logs":
            if len(parts) > 2:
                return parts[1]
            return "Logs"
        if parts[0] == "Daily Notes":
            return "Daily Notes"
        if parts[0] == "Notes" and len(parts) > 2 and parts[1] == "Projects":
            return "Projects"
            
    return "Notes"

def delete_document_index(cursor, rel_path):
    cursor.execute("DELETE FROM document_cache WHERE path = ?", (rel_path,))
    cursor.execute("DELETE FROM paragraphs WHERE document_path = ?", (rel_path,))
    cursor.execute("DELETE FROM vec_documents WHERE document_path = ?", (rel_path,))
    # Delete paragraphs by ID matching prefix
    cursor.execute("DELETE FROM vec_paragraphs WHERE paragraph_id LIKE ?", (f"{rel_path}#%",))

def index_vault(verbose=False, batch_size=30):
    conn = get_db_connection()
    init_db(conn)
    cursor = conn.cursor()
    
    # Get currently cached files to find deletions
    cursor.execute("SELECT path, mtime, hash FROM document_cache")
    db_files = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    
    # Scan filesystem
    fs_files = {}
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities"}
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith(".md"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, VAULT_PATH)
                try:
                    mtime = os.path.getmtime(full_path)
                    fs_files[rel_path] = (full_path, mtime)
                except Exception:
                    pass
                    
    # Find files to delete
    deleted_paths = [p for p in db_files if p not in fs_files]
    if deleted_paths:
        print(f"Removing {len(deleted_paths)} deleted files from index...")
        for p in deleted_paths:
            delete_document_index(cursor, p)
        conn.commit()
        
    # Find files to update or insert
    pending_files = []
    for rel_path, (full_path, mtime) in fs_files.items():
        if rel_path in db_files:
            db_mtime, db_hash = db_files[rel_path]
            if mtime != db_mtime:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                if file_hash != db_hash:
                    pending_files.append((rel_path, full_path, mtime, file_hash))
        else:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            pending_files.append((rel_path, full_path, mtime, file_hash))
            
    if not pending_files:
        print("Index is up to date. No files modified.")
        return
        
    print(f"Found {len(pending_files)} new/modified files to index.")
    
    # Sort to prioritize Inputs/ (or legacy Logs/) first, then Daily Notes/
    pending_files.sort(key=lambda x: (
        0 if ("Inputs/" in x[0] or "Logs/" in x[0]) else (1 if "Daily Notes/" in x[0] else 2),
        x[0]
    ))
    
    # We process pending files in batches of `batch_size` (e.g. 30 files at a time)
    for idx_start in range(0, len(pending_files), batch_size):
        chunk_files = pending_files[idx_start:idx_start+batch_size]
        print(f"Indexing batch [{idx_start+1}-{min(idx_start+batch_size, len(pending_files))}/{len(pending_files)}]...")
        
        parsed_docs = []
        texts_to_embed = []
        
        # 1. Parse and extract all texts for this batch
        for rel_path, full_path, mtime, file_hash in chunk_files:
            try:
                frontmatter, body, paragraphs = parse_markdown_file(full_path)
                title = os.path.basename(full_path)[:-3]
                category = get_category_from_path(rel_path, frontmatter)
                
                doc_text = body[:8000]
                
                # Keep track of indices for matching embeddings later
                doc_index = len(texts_to_embed)
                texts_to_embed.append(doc_text)
                
                para_indices = []
                for chunk_idx, p_text in paragraphs:
                    para_indices.append((chunk_idx, p_text, len(texts_to_embed)))
                    texts_to_embed.append(p_text)
                    
                parsed_docs.append({
                    "rel_path": rel_path,
                    "mtime": mtime,
                    "file_hash": file_hash,
                    "title": title,
                    "category": category,
                    "doc_index": doc_index,
                    "paragraphs": para_indices
                })
            except Exception as e:
                print(f"Error parsing {rel_path}: {e}")
                
        # 2. Bulk embed all texts
        if not texts_to_embed:
            continue
            
        try:
            embeddings = get_embeddings_batch(texts_to_embed)
        except Exception as e:
            print(f"Error generating embeddings for batch: {e}")
            continue
            
        if not embeddings or len(embeddings) != len(texts_to_embed):
            print(f"Warning: Got {len(embeddings)} embeddings for {len(texts_to_embed)} texts. Skipping batch.")
            continue
            
        # 3. Write all docs to database in a single transaction
        for doc in parsed_docs:
            try:
                rel_path = doc["rel_path"]
                doc_emb = embeddings[doc["doc_index"]]
                
                # Delete old entries
                delete_document_index(cursor, rel_path)
                
                # Insert document cache
                cursor.execute("""
                    INSERT INTO document_cache (path, mtime, hash, title, category, last_indexed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (rel_path, doc["mtime"], doc["file_hash"], doc["title"], doc["category"], time.strftime("%Y-%m-%dT%H:%M:%SZ")))
                
                # Insert vec_documents
                doc_emb_bytes = struct.pack(f"{len(doc_emb)}f", *doc_emb)
                cursor.execute("""
                    INSERT INTO vec_documents (document_path, embedding)
                    VALUES (?, ?)
                """, (rel_path, doc_emb_bytes))
                
                # Insert paragraphs & vec_paragraphs
                for chunk_idx, p_text, global_idx in doc["paragraphs"]:
                    para_id = f"{rel_path}#{chunk_idx}"
                    p_emb = embeddings[global_idx]
                    
                    cursor.execute("""
                        INSERT INTO paragraphs (id, document_path, chunk_index, content, char_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (para_id, rel_path, chunk_idx, p_text, len(p_text)))
                    
                    p_emb_bytes = struct.pack(f"{len(p_emb)}f", *p_emb)
                    cursor.execute("""
                        INSERT INTO vec_paragraphs (paragraph_id, embedding)
                        VALUES (?, ?)
                    """, (para_id, p_emb_bytes))
                    
            except Exception as e:
                print(f"Error writing index for {doc['rel_path']}: {e}")
                
        # Commit after each batch
        conn.commit()
        
    print("Indexing complete!")

def search_semantic(query, limit=5, search_type="doc"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Generating embedding for query: '{query}'...")
    query_emb = get_embedding(query)
    if not query_emb:
        print("Could not generate query embedding.")
        return []
        
    query_bytes = struct.pack(f"{len(query_emb)}f", *query_emb)
    
    results = []
    if search_type == "doc":
        cursor.execute("""
            select 
                v.document_path,
                d.title,
                d.category,
                vec_distance_cosine(v.embedding, ?) as distance
            from vec_documents v
            join document_cache d on v.document_path = d.path
            order by distance
            limit ?
        """, (query_bytes, limit))
        for row in cursor.fetchall():
            score = 1.0 - row[3]
            results.append({
                "path": row[0],
                "title": row[1],
                "category": row[2],
                "score": score
            })
    else:
        cursor.execute("""
            select 
                v.paragraph_id,
                p.content,
                p.document_path,
                d.title,
                d.category,
                vec_distance_cosine(v.embedding, ?) as distance
            from vec_paragraphs v
            join paragraphs p on v.paragraph_id = p.id
            join document_cache d on p.document_path = d.path
            order by distance
            limit ?
        """, (query_bytes, limit))
        for row in cursor.fetchall():
            score = 1.0 - row[5]
            results.append({
                "para_id": row[0],
                "content": row[1],
                "path": row[2],
                "title": row[3],
                "category": row[4],
                "score": score
            })
            
    return results

def run_historical_bridge(target_file, limit=5, commit=False):
    # Normalize paths
    abs_target = os.path.abspath(os.path.expanduser(target_file))
    if not os.path.exists(abs_target):
        print(f"Error: Target file does not exist: {target_file}")
        sys.exit(1)
        
    rel_target = os.path.relpath(abs_target, VAULT_PATH)
    
    # Check if target is in our document cache, if not index it on-demand
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT hash, title, category FROM document_cache WHERE path = ?", (rel_target,))
    row = cursor.fetchone()
    if not row:
        print(f"Target note '{rel_target}' not indexed. Indexing now...")
        # Index on-demand
        try:
            mtime = os.path.getmtime(abs_target)
            with open(abs_target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            frontmatter, body, paragraphs = parse_markdown_file(abs_target)
            title = os.path.basename(abs_target)[:-3]
            category = get_category_from_path(rel_target, frontmatter)
            
            doc_text = body[:8000]
            para_texts = [p[1] for p in paragraphs]
            all_texts = [doc_text] + para_texts
            embeddings = get_embeddings_batch(all_texts)
            
            if embeddings:
                doc_emb = embeddings[0]
                para_embs = embeddings[1:]
                
                delete_document_index(cursor, rel_target)
                
                cursor.execute("""
                    INSERT INTO document_cache (path, mtime, hash, title, category, last_indexed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (rel_target, mtime, file_hash, title, category, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
                
                doc_emb_bytes = struct.pack(f"{len(doc_emb)}f", *doc_emb)
                cursor.execute("""
                    INSERT INTO vec_documents (document_path, embedding)
                    VALUES (?, ?)
                """, (rel_target, doc_emb_bytes))
                
                for (chunk_idx, p_text), p_emb in zip(paragraphs, para_embs):
                    para_id = f"{rel_target}#{chunk_idx}"
                    cursor.execute("""
                        INSERT INTO paragraphs (id, document_path, chunk_index, content, char_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (para_id, rel_target, chunk_idx, p_text, len(p_text)))
                    p_emb_bytes = struct.pack(f"{len(p_emb)}f", *p_emb)
                    cursor.execute("""
                        INSERT INTO vec_paragraphs (paragraph_id, embedding)
                        VALUES (?, ?)
                    """, (para_id, p_emb_bytes))
                conn.commit()
            else:
                print("Could not generate embeddings for target note.")
                sys.exit(1)
        except Exception as e:
            print(f"Error indexing target note on-demand: {e}")
            sys.exit(1)
            
    # Retrieve target embedding
    cursor.execute("SELECT embedding FROM vec_documents WHERE document_path = ?", (rel_target,))
    target_emb_bytes = cursor.fetchone()[0]
    
    # We want to search for similarity ONLY across Tier 1 logs:
    # Tier-1 inputs: Meetings, Readings, Slack, Emails, Daily Notes (Inputs/ or legacy Logs/)
    # We find the top semantically dense historical matches.
    cursor.execute("""
        select 
            v.document_path,
            d.title,
            d.category,
            vec_distance_cosine(v.embedding, ?) as distance
        from vec_documents v
        join document_cache d on v.document_path = d.path
        where d.category in ('Meetings', 'Readings', 'Slack', 'Daily Notes')
          and d.path != ?
        order by distance
        limit ?
    """, (target_emb_bytes, rel_target, limit))
    
    matches = []
    for row in cursor.fetchall():
        score = 1.0 - row[3]
        matches.append({
            "path": row[0],
            "title": row[1],
            "category": row[2],
            "score": score
        })
        
    print(f"\nSemantic Matches in Tier 1 Logs for: '{rel_target}'")
    print("="*60)
    for i, m in enumerate(matches, 1):
        print(f"{i}. {m['title']} ({m['category']}) | Similarity: {m['score']:.4f}")
        print(f"   Path: [[{m['path'][:-3].replace(os.path.sep, '/')}]]")
        
    if not matches:
        print("No matches found.")
        return
        
    if commit:
        # We append these backlinks to the target file.
        # Let's read the target file.
        with open(abs_target, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        content = "".join(lines)
        
        # Check if ## Related Logs or ## Related section already exists
        # We replace or append. Let's look for a standard spot.
        # Let's see if we can append at the very end or right after any existing headers.
        # We will create a clean "## Related Logs" section.
        # Remove empty trailing lines
        while lines and lines[-1].strip() == "":
            lines.pop()
            
        # Re-check if "## Related Logs" is already in the file.
        # If it is, we replace it.
        # Let's find the line index
        related_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("## Related Logs"):
                related_idx = i
                break
                
        # Generate the new backlinks text
        backlink_bullets = []
        backlink_bullets.append("## Related Logs")
        for m in matches:
            slug = m['path'][:-3].replace(os.path.sep, '/')
            backlink_bullets.append(f"* [[{slug}|{m['title']}]] | *({m['category']}, Similarity: {m['score']:.2%})*")
        backlink_bullets.append("") # trailing newline
        
        if related_idx != -1:
            # We replace everything from "## Related Logs" until the next heading or end of file
            next_heading_idx = len(lines)
            for j in range(related_idx + 1, len(lines)):
                if lines[j].strip().startswith("##"):
                    next_heading_idx = j
                    break
            lines[related_idx:next_heading_idx] = [b + "\n" for b in backlink_bullets]
            print(f"\nReplacing existing ## Related Logs section in '{rel_target}'...")
        else:
            # Append at the end
            lines.append("\n\n---\n") # add a divider
            lines.extend([b + "\n" for b in backlink_bullets])
            print(f"\nAppending ## Related Logs section to '{rel_target}'...")
            
        with open(abs_target, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("Successfully committed backlinks!")

def run_context_pruning(query, limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search paragraphs
    results = search_semantic(query, limit=limit, search_type="para")
    
    if not results:
        print("No matches found.")
        return
        
    print(f"\n--- SEMANTIC CONTEXT PRUNING FOR QUERY: '{query}' ---")
    print(f"Surfacing top {len(results)} semantically dense paragraphs from across history:\n")
    
    for i, r in enumerate(results, 1):
        print(f"[{i}] From [[{r['path'][:-3].replace(os.path.sep, '/')}|{r['title']}]] ({r['category']}) | Similarity: {r['score']:.4f}")
        print("-"*80)
        print(r['content'])
        print("-"*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Bes Semantic Pointer & Historical Bridging Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # 1. Index command
    subparsers.add_parser("index", help="Incrementally index the vault's Markdown files")
    
    # 2. Search command
    search_parser = subparsers.add_parser("search", help="Search the semantic index")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--type", choices=["doc", "para"], default="doc", help="Search for entire documents or individual paragraphs")
    search_parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    
    # 3. Bridge command
    bridge_parser = subparsers.add_parser("bridge", help="Find Tier 1 logs related to a Thought/Belief and append backlinks")
    bridge_parser.add_argument("target_file", type=str, help="Path to the Thought or Belief note")
    bridge_parser.add_argument("--limit", type=int, default=5, help="Number of related logs to surface")
    bridge_parser.add_argument("--commit", action="store_true", help="Write/append the backlinks to the target note")
    
    # 4. Prune command
    prune_parser = subparsers.add_parser("prune", help="Semantic context pruning: retrieve semantically dense paragraphs")
    prune_parser.add_argument("query", type=str, help="Topic or question")
    prune_parser.add_argument("--limit", type=int, default=10, help="Number of paragraphs to retrieve")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    if args.command == "index":
        index_vault(verbose=True)
    elif args.command == "search":
        res = search_semantic(args.query, limit=args.limit, search_type=args.type)
        if args.type == "doc":
            for i, r in enumerate(res, 1):
                print(f"{i}. [{r['category']}] {r['title']} (Similarity: {r['score']:.4f})")
                print(f"   Path: [[{r['path'][:-3].replace(os.path.sep, '/')}]]")
        else:
            for i, r in enumerate(res, 1):
                print(f"{i}. [{r['category']}] {r['title']} - Paragraph (Similarity: {r['score']:.4f})")
                print(f"   Path: [[{r['path'][:-3].replace(os.path.sep, '/')}]]")
                print(f"   Content: {r['content'][:150]}...")
    elif args.command == "bridge":
        run_historical_bridge(args.target_file, limit=args.limit, commit=args.commit)
    elif args.command == "prune":
        run_context_pruning(args.query, limit=args.limit)

if __name__ == "__main__":
    main()
