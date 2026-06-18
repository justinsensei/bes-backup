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

Captures noteworthy Slack threads and brain-dumps as high-quality synthesized input notes inside `Inputs/Slack/`.

These notes capture a high-quality summary showing "who said what" clearly to retain crucial context and decisions, without storing verbatim message lists.

## Synced Path
- `/home/justin.guest/Developer/obsidian-vault/Inputs/Slack/YYYY-MM-DD - Spaced Title.md`

---

## Slack Input Note Structure

Every Slack input note must start with this frontmatter format:

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

Below the frontmatter, the body is structured cleanly as a synthesized summary:

```markdown
# [Cleaned Title] — YYYY-MM-DD

## Summary
[A high-quality, 2-3 sentence synthesis of the thread's core outcome, decisions, or findings.]

## Who Said What

### [Participant Name]
- [Key point, contribution, or decision made by this participant]
```

---

## The Creation vs. Enrichment Lifecycle

### 1. Initial Creation (First Ingest)
When a Slack brain reaction or capture is first triggered, create a high-quality initial draft note with the correct frontmatter and a clean summary of the initial thread.

### 2. Vault Enrichment Step
During subsequent vault enrichment runs (e.g., during Wind-Down, Morning Briefings, or an on-demand Vault Jam):
1. Review all Slack inputs created since the previous vault enrichment run.
2. If further replies occurred in the source Slack thread, refine and enrich the summary and "Who Said What" section to keep it accurate.
3. Verify and compile the complete list of participants and ensure they are added to the frontmatter `participants` list.
4. **Enforce the Synthesis Rule:** Ensure no raw transcripts or verbatim message lines remain in the input. All content must be synthesized into summary form.

---

## Unified Feeds Ingest Pattern

The Slack, Linear, and Gmail (Email Dispatch) ingest pipelines are executed together by the unified cron job **"Unified Brain Feeds Ingest"** (`284c08eb12b7`) running every 120 minutes.
- **Unified Script:** `/home/justin.guest/.hermes/scripts/fetch_unified_ingest.py` runs `fetch_slack_brains.py`, `fetch_linear_brains.py`, and `poll_bes_inbox.py --json` in parallel and consolidates candidates into a single JSON object with `slack`, `linear`, and `emails` keys.
- **Workflow:** The agent processes incoming candidates, saves files to `/Inbox/` (or `Inputs/Emails/` for emails), appends to today's daily note under `## 🗒 Notepad`, runs the marking-processed commands (`--mark-processed`), appends to `Utilities/log.md`, and runs `integrate_entities.py` to keep project hub states aligned.
