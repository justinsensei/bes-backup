---
name: obsidian-logs
description: Use when managing chronological directory structures for Daily Notes/ and Logs/Meetings/ and coordinating their sub-skills.
version: 1.2.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, logs, folder-conventions]
    related_skills: [obsidian, obsidian-daily-notes, obsidian-meetings]
---

# Obsidian Type: Chronological Directory Conventions

## Overview
This skill governs the structure and navigation of chronological log notes, pointing to focused sub-skills for daily journaling and meeting records.

---

- **Linked References:**
  - **[Readwise Highlights Sync](references/readwise-sync.md):** Rules, directory conventions, and schema standardizations for Readwise raw logs.

---

## Directories & Sub-skills
- **Daily Notes Directory:** `/home/justin.guest/vault/Daily Notes/`
  - Sub-skill: **`obsidian-daily-notes`** (`category: "[[Daily Notes]]"`)
- **Meetings Directory:** `/home/justin.guest/vault/Logs/Meetings/`
  - Sub-skill: **`obsidian-meetings`** (`category: "[[Meetings]]"`)
- **Emails Directory:** `/home/justin.guest/vault/Logs/Emails/`
  - Synced automatically from forwarded emails or email digests (`category: "[[Emails]]"`)
- **Slack Directory:** `/home/justin.guest/vault/Logs/Slack/`
  - Synced automatically from captured Slack discussions or brain-dumps (`category: "[[Slack]]"`)
- **Sources Directory:** `/home/justin.guest/vault/Logs/Sources/`
  - Synced automatically via `sync_readwise.py` (`category: "[[Sources]]"`)

---

## Folder-Level Rules

- **Strict Date Formats:** Ensure all chronological filenames strictly adhere to their respective date patterns:
  - Daily Notes: `YYYY-MM-DD Weekday.md` (capitalized weekday name).
  - Meetings, Emails, and Slack Logs: `YYYY-MM-DD - Spaced Title.md` (e.g. `2026-06-09 - SignLab Product Alignment.md`, `2026-06-09 - Product Feedback on Free to Play.md`).
- **Linking to Daily Notes:** Every chronological log file must link back to its creation day in its YAML `daily_note:` property.
- **Archive Raw Logs:** Never leave raw files in the root `/meetings/` folder. Ensure the automated hygiene script pre-processes and moves them to `/Logs/Meetings/`.
