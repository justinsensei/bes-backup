---
name: bes-readwise-ingest
description: Sync and ingest highlights from books, articles, or papers tagged 'vault' in Readwise into vault/Logs/Sources/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [readwise, ingest, readings, obsidian]
    related_skills: [obsidian, obsidian-logs, obsidian-references-sources]
---

# Bes Readwise Ingest

Pulls book highlights, web clips, and article annotations from your Readwise account and formats them into clean markdown reading records inside `/home/justin.guest/vault/Logs/Sources/`.

## Trigger & Filter
*   **Trigger:** Triggered automatically or via running the sync script.
*   **Filter:** Only highlights tagged `'vault'` (case-insensitive) in Readwise are exported to your vault.

---

## Sync Mechanism
The sync is driven by the sync script located at your home directory:
`python3 ~/sync_readwise.py`

---

## Sources Log Note Structure

Every Readwise synced reading note must strictly adhere to the following template:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Single-quoted string matching latest highlight's timestamp
daily_note: "[[Daily Notes/YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Standardized symmetrical daily note link
category: "[[Sources]]"             # Quoted category wikilink
---
```

Below the frontmatter, the body follows this layout:

### Title
Large H1 heading matching the book or article title (e.g., `# Atomic Habits`).

### Citation Line
Directly below the title, provide a formal single-line citation:
`Author. *Title*. [Link](URL)`

### Highlights
A bulleted log of extracted highlights grouped cleanly.
- Highlight item A
- Highlight item B
