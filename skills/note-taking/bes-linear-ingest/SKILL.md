---
name: bes-linear-ingest
description: Capture and ingest Linear comments, updates, and documents as structured inbox files.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [linear, obsidian, ingest, logs]
    related_skills: [obsidian, obsidian-logs, obsidian-graph-enrichment, obsidian-vault-jam, llm-wiki, bes-slack-ingest]
---

# Bes Linear Ingest

Captures noteworthy Linear comments, project updates, and initiative updates carrying the `:obsidian_jg:` (or `🧠`/`brain`) reaction added by Justin.

All ingested files must land inside `/home/justin.guest/vault/inbox/` as a starting point.

## Synced Path
- `/home/justin.guest/vault/inbox/YYYY-MM-DD - Linear - [Title].md`

---

## Linear Log Note Structure

Every Linear log note must start with this frontmatter format:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Numerical string based on item's createdAt timestamp
daily_note: "[[Daily Notes/YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # e.g., [[Daily Notes/2026-06-11 Thursday|2026-06-11 Thursday]]
category: "[[Linear]]"               # Quoted category link
original_url: "https://linear.app/..." # Permalink to comment or update
author: "Author Name"                # Author of the comment/update
associated_with: "[[Target Page]]"   # Wikilink to associated project/initiative/issue
---
```

Below the frontmatter, the body has a clear synthesis of the discussion:

```markdown
# 📥 Linear Capture: [Spaced Capitalized Title]

- **Author:** Author Name
- **Date:** YYYY-MM-DD
- **Original Link:** [Linear Link](https://linear.app/...)
- **Associated With:** [[Target Page]]

## Topic Description
[A high-quality 2-3 sentence Topic Description synthesizing the comment/update, the parent issue/document/project/initiative context, and its corresponding thread.]
```

---

## Unified Feeds Ingest Pattern

The Linear and Slack ingest pipelines are executed together by the unified cron job **"Unified Brain Feeds Ingest"** (`284c08eb12b7`) running every 120 minutes.
- **Unified Script:** `/home/justin.guest/.hermes/scripts/fetch_unified_ingest.py` runs both `fetch_slack_brains.py` and `fetch_linear_brains.py` in parallel and consolidates candidates into a single JSON object.
- **Workflow:** The agent processes incoming candidates, saves files to `/inbox/`, appends to today's daily note under `## 🗒 Notepad`, runs the marking-processed commands (`--mark-processed`), appends to `Utilities/log.md`, and runs `integrate_entities.py` to keep project hub states aligned.
