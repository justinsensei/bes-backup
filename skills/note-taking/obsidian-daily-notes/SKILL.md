---
name: obsidian-daily-notes
description: Use when creating or formatting chronological daily notes under Daily Notes/ with category "[[Daily Notes]]".
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, logs, daily-notes, schedule]
    related_skills: [obsidian, obsidian-logs, work-log]
---

# Obsidian: Daily Notes Management

## Overview
This skill governs the filename format, structure, templates, and standard sections of Justin's Daily Notes.

---

## Folder & Category
- **Directory:** `/home/justin.guest/vault/Daily Notes/`
- **Category link:** `category: "[[Daily Notes]]"`

---

## Filename Conventions
- Filename format: `YYYY-MM-DD Weekday.md` (capitalized weekday, space instead of hyphen after date).
- Examples: `2026-06-09 Tuesday.md`, `2026-06-14 Sunday.md`.

---

## Note Layout & Structure

A Daily Note is structured with an executive summary/callout followed by specific chronological work and schedule sections:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Daily Notes]]"
---

> [!summary] Summary Callout
> High-level executive bullet summary of the day.

## 📅 Schedule & Events
- List of meetings, calendar events, or appointments for the day.

## 🚀 Highlights & Decisions
- Key milestones or critical choices made during the day.

## 🏆 Accomplishments
- Bulleted list of completed work items and achievements.

## 🗒 Notepad
- Freeform scratchpad, thoughts, or rapid logs captured during the day.
```

---

## Interaction with `work-log`
When executing the `work-log` skill:
1. Fetch events from Google Calendar, Linear, Todoist, and Slack.
2. Compile and summarize the work log.
3. Append or update the accomplishments and schedule sections directly inside today's daily note.
