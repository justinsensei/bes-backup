---
name: bes-slack-ingest
description: Capture and ingest Slack conversations as brief pointer records with a short topic description and participant list.
version: 2.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [slack, obsidian, ingest, logs]
    related_skills: [obsidian, obsidian-logs, obsidian-graph-enrichment, obsidian-vault-jam]
---

# Bes Slack Ingest

Captures noteworthy Slack threads and brain-dumps as lightweight pointer records inside `Inputs/Slack/`. 

These notes are intentionally **minimalist**. They must never contain point-by-point summaries, individual quotes, or try to capture decisions or thoughts. They function purely as a index/pointer back to Slack with a brief human-readable description.

## Synced Path
- `/home/justin.guest/vault/Inputs/Slack/YYYY-MM-DD-slug.md`

---

## Slack Log Note Structure

Every Slack log note must start with this frontmatter format:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Numerical string based on first message's timestamp
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Symmetrical daily note link
category: "[[Slack]]"                 # Quoted category link
channel: "channel-name"              # The source Slack channel
original_url: "https://slack.com/..." # Link to original discussion
participants:
  - "User A"
  - "User B"
---
```

Below the frontmatter, the body is kept super short:

```markdown
# 💬 Slack Thread: [Cleaned Title]

- **Channel:** #channel-name
- **Date:** YYYY-MM-DD
- **Original Thread:** [Slack Link](https://slack.com/...)

---

## 🎯 Topic Description
[A brief, 2-3 sentence human-readable description of the topic discussed. Acts as a simple pointer to the conversation without listing thoughts, decisions, or individual quotes.]
```

---

## The Creation vs. Enrichment Lifecycle

### 1. Initial Creation (First Ingest)
When a Slack brain reaction or capture is first triggered, create a **super short stub note** containing only the basic frontmatter (with initial participants found) and a temporary 1-sentence topic description placeholder.

### 2. Vault Enrichment Step
During subsequent vault enrichment runs (e.g., during Wind-Down, Morning Briefings, or an on-demand Vault Jam):
1. Review all Slack logs created since the previous vault enrichment run.
2. Read the source Slack thread replies if needed to refine and write a polished **2-3 sentence Topic Description**.
3. Verify and compile the complete list of **main participants** and ensure they are added to the frontmatter `participants` list.
4. **Enforce the Constraints:** Actively prune and remove any point-by-point summaries, individual thoughts, quotes, or decision trees that may have leaked into the logs. Keep them strictly as simple pointers.

---

## Unified Feeds Ingest Pattern

The Slack and Linear ingest pipelines are executed together by the unified cron job **"Unified Brain Feeds Ingest"** (`284c08eb12b7`) running every 120 minutes.
- **Unified Script:** `/home/justin.guest/.hermes/scripts/fetch_unified_ingest.py` runs both `fetch_slack_brains.py` and `fetch_linear_brains.py` in parallel and consolidates candidates into a single JSON object.
- **Workflow:** The agent processes incoming candidates, saves files to `/inbox/`, appends to today's daily note under `## 🗒 Notepad`, runs the marking-processed commands (`--mark-processed`), appends to `Utilities/log.md`, and runs `integrate_entities.py` to keep project hub states aligned.
