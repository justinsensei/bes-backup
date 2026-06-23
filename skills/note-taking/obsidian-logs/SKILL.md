---
name: obsidian-logs
description: "Master conventions for chronological logs: governs Daily Notes, Meetings, and incoming Inputs (Emails, Slack, Readings)."
version: 1.4.0
author: Bes
index: yes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [obsidian, logs, daily-notes, meetings, inputs, folder-conventions]
    related_skills: [obsidian, obsidian-notes, work-log, bes-granola-ingest]
---

# Obsidian Type: Chronological Directory & Input Conventions

This master skill governs the structure, naming, templates, and navigation of chronological log files and incoming raw input streams under `/Notes/Daily Notes/` and `/Inputs/` directories.

---

## 1. Directory Navigation & Coordinates

- **Daily Notes Directory:** `/home/justin.guest/Developer/obsidian-vault/Notes/Daily Notes/`
  - *Category:* `category: "[[Daily Notes]]"`
- **Meetings Directory:** `/home/justin.guest/Developer/obsidian-vault/Inputs/Meetings/`
  - *Category:* `category: "[[Meetings]]"`
- **Emails Directory:** `/home/justin.guest/Developer/obsidian-vault/Inputs/Emails/` (`category: "[[Emails]]"`)
- **Slack Directory:** `/home/justin.guest/Developer/obsidian-vault/Inputs/Slack/` (`category: "[[Slack]]"`)
- **Readings Directory:** `/home/justin.guest/Developer/obsidian-vault/Inputs/Readings/` (`category: "[[Readings]]"`)
  - *Linked Reference:* [Readwise Highlights Sync](references/readwise-sync.md) covers directory conventions for Readwise raw inputs.

---

## 2. Daily Notes Management

Daily Notes are the central journal and timeline for Justin's day.

### Naming Convention
- **Format:** `YYYY-MM-DD Weekday.md` (e.g., `2026-06-09 Tuesday.md`, `2026-06-14 Sunday.md`). Weekdays must be fully capitalized, separated from the date by a space.

### Note Layout & Structure
A Daily Note begins with an executive summary callout block followed by chronological schedule, scratchpad, work log, and notepad sections (note: the Accomplishments section was retired as redundant):
```markdown
---
id: "YYYYMMDDHHmmss"
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Daily Notes]]"
---

|> [!summary] Summary Callout
|> High-level executive bullet summary of the day.

## 🌄 Morning Briefing
- Work Log Review (Yesterday)
- Heads-Up (Urgent Tasks, Inbox/Calendar Candidates)

## 🗓 Schedule & Events
- List of meetings, calendar events, or appointments for the day.

## 🗒 Scratchpad
- Inline tasks and daily check-offs.

## ✅ Work Log
### 🚀 Highlights & Decisions
- Key milestones, critical choices, and active decisions made during the day.

## 🗒 Notepad
- Freeform scratchpad, thoughts, or rapid logs captured during the day (e.g. Slack/Email summaries).
```

### Interaction with `work-log`
When compiling a work log, fetch events from Google Calendar, Linear, Todoist, and Slack, compile today's summary, and append/update the schedule and Highlights & Decisions sections directly inside today's Daily Note (omitting accomplishments/completed task lists entirely).

---

## 3. Meetings & Granola Management

Governs meeting note formatting and the ingestion of raw transcripts.

### Naming Convention
- **Format:** `YYYY-MM-DD - Spaced Meeting Title.md` (e.g., `2026-06-09 - SignLab Product Alignment.md`).

### Meeting Note Layout
```markdown
---
id: "YYYYMMDDHHmmss"
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Meetings]]"
---

# Meeting Title

**Date:** YYYY-MM-DD
**Attendees:** [[Justin Goff]], [[Person Name]]

---

## Agenda
- 

## Notes
- 

## Action Items
- [ ] 
```

### Ingestion & Sync Pipeline
- **Granola Sync:** Raw transcripts and notes dropped into `/Meetings/` are automatically swept, formatted, and moved into the `/Inputs/Meetings/` directory. This is automated by the `bes-granola-ingest` skill.
- **No Raw Logs in Root:** Raw unformatted files must never be left in `/Meetings/`. Ensure automated routines move and archive them inside `/Inputs/Meetings/`. Every meeting note must link back to its creation day in its YAML `daily_note:` property.
