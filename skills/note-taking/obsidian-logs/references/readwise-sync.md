# Readwise Highlights Sync & Log Conventions

## Overview
Readwise data consists of raw highlight dumps and reading logs. These are chronological records of consumption, not conceptual synthesis. Therefore, they are treated as **Logs** rather than **Sources** (which are reserved for hand-extracted summaries and insights).

---

## Directory & Category
- **Path:** `/home/justin.guest/vault/Logs/Readwise/`
- **Category:** `category: "[[Readwise]]"`
- **Category Metadata File:** `vault/Utilities/Categories/Readwise.md` (`Type: Logs`)

---

## Sync Mechanism (`~/sync_readwise.py`)
The sync is driven by `~/sync_readwise.py` using the Readwise API. 
- **Filter:** It only pulls books and articles tagged `vault` (case-insensitive) in Readwise.
- **State:** Sync progress is stored in `/home/justin.guest/.readwise_sync_state.json`.

---

## Frontmatter & Formatting Rules
All synced Readwise log notes must strictly adhere to the following template:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Single-quoted string matching latest highlight's timestamp
daily_note: "[[Daily Notes/YYYY-MM-DD-weekday|YYYY-MM-DD Weekday]]" # Standardized daily note link
category: "[[Readwise]]"             # Quoted category wikilink
---
```

### Content Structure
1. **Citation Line:** `Author. *Title*. [Link](URL)`
2. **Document Note/Summary:** (Optional) If present, written below the citation.
3. **Highlights Section:** Starts with `# Highlights`, followed by a bulleted list of active highlights (deleted ones filtered out).
4. **NO Legacy Tags:** Never write `#source` or `#meeting` in these log files.

---

## Maintenance & Migration
If raw highlights are found in `vault/sources/` (a common historical legacy), they must be migrated to `vault/Logs/Readwise/` and sanitized to match this schema, removing any `#source` tags in the process.
