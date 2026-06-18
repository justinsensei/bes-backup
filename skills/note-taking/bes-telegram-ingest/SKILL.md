---
name: bes-telegram-ingest
description: Capture and ingest flagged Telegram conversation sessions as pointer and summary records in Obsidian.
version: 1.0.0
author: Bes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [telegram, obsidian, ingest, logs, state-db]
    related_skills: [obsidian, obsidian-logs, llm-wiki, work-log]
---

# Bes Telegram Ingest

Captures flagged Telegram conversation sessions as structured, searchable summary inputs inside `Inputs/Telegram/`. 

These records summarize the session's context, capture key takeaways or next steps, and store the metadata required to look up the complete, raw transcripts in the local session database (`state.db`).

## Synced Path
- Initial Creation / Folder: `/home/justin.guest/Developer/obsidian-vault/Inputs/Telegram/YYYY-MM-DD - Telegram - [Title].md` (e.g., `2026-06-11 - Telegram - Background Ingestion of Flagged Telegram Sessions.md`)
- Category: `[[Telegram]]`

---

## Triggering Ingestion
Sessions are flagged for ingestion in two ways during Telegram chats:
1. **Reaction:** Justin reacts to any bot response using the `🧠` emoji.
2. **Text Message:** Justin includes the `🧠` emoji in any of his messages during the session.

---

## State & Schema Integration
Ingestion runs in the background to avoid polluting active session context.
- **Database Path:** `/home/justin.guest/.hermes/state.db`
- **Schema Columns (Added in `sessions` table):**
  * `brain_flagged INTEGER DEFAULT 0` — set to `1` when flagged.
  * `ingested INTEGER DEFAULT 0` — set to `1` once processed by the background cron job.

### Platform Hooks (Reaction Capture)
A `MessageReactionHandler` is configured in `gateway/platforms/telegram.py` to listen for incoming reaction updates. When a `🧠` reaction is detected:
1. It looks up the message ID in the `messages` table under `platform_message_id`.
2. It resolves the associated `session_id`.
3. It updates `sessions` to set `brain_flagged = 1` directly in `state.db`.

---

## Background Plumbing (Cron & Poller)
A background poller script `fetch_telegram_brains.py` runs on a schedule (every 30 minutes) as part of a scheduled cron job:
- **Scan Phase:** Queries `state.db` for sessions that are either marked `brain_flagged = 1` or contain a user message with the `"🧠"` string, where `ingested = 0`.
- **Extraction Phase:** Formats the session metadata and raw message history, printing it as JSON to be digested by the background agent.
- **Mark Phase:** Runs with `--mark-processed <SESSION_ID>` to set `ingested = 1` in `state.db`.

---

## Ingest Note Structure

Every Telegram session log note must use this frontmatter format:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Numerical string based on session start time
daily_note: "[[Daily Notes/YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Symmetrical daily note link
category: "[[Telegram]]"              # Quoted category link
session_id: "YYYYMMDD_HHMMSS_xxxxxxxx" # The unique session identifier in state.db
source_db: "/home/justin.guest/.hermes/state.db" # Database where session resides
---
```

Below the frontmatter, the body is structured as follows:

```markdown
# 📥 Telegram Session Capture: [Title]

- **Session ID:** `session_id`
- **Date:** YYYY-MM-DD
- **Database:** `/home/justin.guest/.hermes/state.db`

## Summary
- **Topic A:** [Provide a concise, high-quality summary of the session: what was discussed, decisions made, and any open questions.]
- **Topic B:** [Concise statement, attributing decisions/takeaways accurately]
```
