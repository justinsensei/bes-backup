---
name: obsidian-semantic-pointer
description: Use when working with obsidian semantic pointer. Manage and operate the
  Obsidian Semantic Pointer CLI for on-demand historical bridging, semantic search,
  and context pruning.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - obsidian
    - semantic-pointer
    - embeddings
    - vector-search
    - sqlite-vec
    - note-taking
    related_skills:
    - obsidian-graph-enrichment
    - obsidian-notes
    - obsidian-logs
platforms:
- linux
---

# Obsidian: Semantic Pointer & AI Memory Integration

This skill outlines the usage, syntax, maintenance, and automated workflows of the **Semantic Pointer** utility, which solves the synonym problem and historical blindspots in Justin's vault.

---

## Technical Foundations
- **Path:** `~/.hermes/scripts/semantic_pointer.py`
- **Database:** `~/.hermes/state/semantic_memory.db`
- **Engine:** `sqlite-vec` (version `0.1.9`) + Google Gemini `gemini-embedding-2` API (3072 dimensions).
- **Watermarks:** Incremental updates use file `mtime` and content MD5 hashes.

---

## CLI Usage Guide

The utility is run from the terminal under the main python virtual environment.

### 1. Incremental Indexing
Indexes new or modified files. Automatically prioritizes `Logs/` and `Daily Notes/` first, making incremental checks blazingly fast.
```bash
python3 ~/.hermes/scripts/semantic_pointer.py index
```

### 2. On-Demand Historical Bridging (Thought/Belief Backlinking)
Finds the most semantically relevant archived Tier 1 logs (Meetings, Sources, Slack, Daily Notes) from the past, and appends/updates them under a clean `## Related Logs` header at the end of a newly drafted Thought or Belief note.
```bash
# Preview matches only
python3 ~/.hermes/scripts/semantic_pointer.py bridge "vault/Notes/Target Note.md" --limit 5

# Write backlinks directly to the note
python3 ~/.hermes/scripts/semantic_pointer.py bridge "vault/Notes/Target Note.md" --limit 5 --commit
```

### 3. Semantic Context Pruning (LLM Context Optimization)
Instead of feeding raw, lengthy log files into your active context window, retrieve the top $N$ most semantically dense paragraph chunks from across the entire vault history matching your topic:
```bash
python3 ~/.hermes/scripts/semantic_pointer.py prune "your synthesis topic" --limit 10
```

### 4. Vector Similarity Search
Search across full documents (`--type doc`) or individual paragraph chunks (`--type para`):
```bash
# Document-level search
python3 ~/.hermes/scripts/semantic_pointer.py search "search query" --type doc --limit 5

# Paragraph-level search
python3 ~/.hermes/scripts/semantic_pointer.py search "search query" --type para --limit 5
```

---

## Automation & Integration

The Semantic Pointer is fully integrated into the daily **9PM Vault Hygiene Cron Job** (`vault_hygiene.py`). Any newly added daily notes, meeting logs, reading summaries, or Slack ingestion files are indexed automatically each night, keeping the vector space in perfect alignment without manual intervention.

To manually trigger a full hygiene and indexing run:
```bash
python3 ~/.hermes/scripts/vault_hygiene.py
```

---

## Troubleshooting & Maintenance

### Re-Indexing from Scratch
If schema changes occur or the database gets corrupted, delete the SQLite file and trigger a fresh index. 
```bash
# Delete DB
rm -f ~/.hermes/state/semantic_memory.db

# Full rebuild
python3 ~/.hermes/scripts/semantic_pointer.py index
```

### Missing API Keys
Ensure `GOOGLE_GENERATIVE_AI_API_KEY` is present in your environment:
```bash
export GOOGLE_GENERATIVE_AI_API_KEY="AIzaSy..."
```
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
