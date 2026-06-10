---
name: bes-readwise-ingest
description: Use when working with bes readwise ingest. Sync and ingest highlights
  from books, articles, or papers tagged 'vault' in Readwise into vault/Logs/Sources/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - readwise
    - ingest
    - readings
    - obsidian
    related_skills:
    - obsidian
    - obsidian-logs
    - obsidian-references-sources
platforms:
- linux
---

# Bes Readwise Ingest

Pulls book highlights, web clips, and article annotations from your Readwise account and formats them into clean markdown reading records inside `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Logs/Sources/`.

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
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Standardized symmetrical daily note link
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
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
