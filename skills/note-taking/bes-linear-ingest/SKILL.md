---
name: bes-linear-ingest
description: Capture and ingest Linear comments, updates, and documents as structured inbox files.
version: 1.0.0
author: Bes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [linear, obsidian, ingest, logs]
    related_skills: [obsidian, obsidian-logs, obsidian-graph-enrichment, obsidian-vault-jam, llm-wiki, bes-slack-ingest]
---

# Bes Linear Ingest

Captures noteworthy Linear comments, project updates, and initiative updates carrying the `:obsidian_jg:` (or `🧠`/`brain`) reaction added by Justin.

All ingested files bypass the inbox and must land inside `/home/justin.guest/Developer/obsidian-vault/Inputs/Linear/` directory.

## Synced Path
- `/home/justin.guest/Developer/obsidian-vault/Inputs/Linear/YYYY-MM-DD - Linear - [Title].md`

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
associated_with: "https://linear.app/..."   # External link to associated project/initiative/issue
---
```

Below the frontmatter, the body has a clear synthesis of the discussion:

```markdown
# 📥 Linear Capture: [Spaced Capitalized Title]

- **Author:** Author Name
- **Date:** YYYY-MM-DD
- **Original Link:** [Linear Link](https://linear.app/...)
- **Associated With:** [Cleaned Title](https://linear.app/...)

## Topic Description
[A high-quality 2-3 sentence Topic Description synthesizing the comment/update, the parent issue/document/project/initiative context, and its corresponding thread.]
```

---

## Unified Feeds Ingest Pattern

The Linear, Slack, Telegram, and Gmail (Email Dispatch) ingest pipelines are executed together by the unified cron job **"Unified Brain Feeds Ingest"** (`284c08eb12b7`) running every 30 minutes.
- **Unified Script:** `/home/justin.guest/.hermes/scripts/fetch_unified_ingest.py` runs `fetch_linear_brains.py`, `fetch_slack_brains.py`, `poll_bes_inbox.py --json`, and `fetch_telegram_brains.py` in parallel and consolidates candidates into a single JSON object with `linear`, `slack`, `emails`, and `telegram` keys.
- **Workflow:** The agent processes incoming candidates, saves files directly to their respective `Inputs/` folder (such as `Inputs/Linear/`, `Inputs/Slack/`, `Inputs/Telegram/`, `Inputs/Emails/`), runs the marking-processed commands (`--mark-processed`), appends to `Utilities/log.md`, and runs `integrate_entities.py` to keep project hub states aligned. No daily note appending is performed (as the Notepad section is retired).
