---
name: obsidian-logs
description: Use when managing chronological directory structures for Notes/Daily Notes/ and Inputs/ directories and coordinating their sub-skills.
version: 1.3.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, inputs, logs, folder-conventions]
    related_skills: [obsidian, obsidian-daily-notes, obsidian-meetings]
---

# Obsidian Type: Chronological Directory & Input Conventions

## Overview
This skill governs the structure and navigation of chronological input notes and raw incoming streams under `Inputs/`, pointing to focused sub-skills for daily journaling, meeting records, and synced readings.

---

- **Linked References:**
  - **[Readwise Highlights Sync](references/readwise-sync.md):** Rules, directory conventions, and schema standardizations for Readwise raw inputs.

---

## Directories & Sub-skills
- **Daily Notes Directory:** `/home/justin.guest/vault/Notes/Daily Notes/`
  - Sub-skill: **`obsidian-daily-notes`** (`category: "[[Daily Notes]]"`)
- **Meetings Directory:** `/home/justin.guest/vault/Inputs/Meetings/`
  - Sub-skill: **`obsidian-meetings`** (`category: "[[Meetings]]"`)
- **Emails Directory:** `/home/justin.guest/vault/Inputs/Emails/`
  - Synced automatically from forwarded emails or email digests (`category: "[[Emails]]"`)
- **Slack Directory:** `/home/justin.guest/vault/Inputs/Slack/`
  - Synced automatically from captured Slack discussions or brain-dumps (`category: "[[Slack]]"`)
- **Readings Directory:** `/home/justin.guest/vault/Inputs/Readings/`
  - Synced automatically via `sync_readwise.py` (`category: "[[Readings]]"`)

---

## Folder-Level Rules

- **Strict Date Formats:** Ensure all chronological filenames strictly adhere to their respective date patterns:
  - Daily Notes: `YYYY-MM-DD Weekday.md` (capitalized weekday name).
  - **Meetings, Emails, and Slack Inputs:** `YYYY-MM-DD - Spaced Title.md` (e.g. `2026-06-09 - SignLab Product Alignment.md`, `2026-06-09 - Product Feedback on Free to Play.md`).
- **Linking to Daily Notes:** Every chronological input file must link back to its creation day in its YAML `daily_note:` property.
- **Archive Raw Inputs:** Never leave raw files in the root `/Meetings/` folder. Ensure the automated hygiene script pre-processes and moves them to `/Inputs/Meetings/`.
