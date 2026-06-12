---
name: obsidian-meetings
description: Use when creating or cleaning up chronological meeting notes and managing Granola reconciliation under Logs/Meetings/ with category "[[Meetings]]".
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, logs, meetings, granola, reconciliation]
    related_skills: [obsidian, obsidian-logs]
---

# Obsidian: Meetings & Granola Management

## Overview
This skill governs chronological meeting notes, including formatting templates and the automated cleanup workflow for raw meetings synced from Granola.

---

## Folder & Category
- **Directory:** `/home/justin.guest/vault/Logs/Meetings/`
- **Category link:** `category: "[[Meetings]]"`

---

## Filename Conventions
- Filename format: `YYYY-MM-DD - Spaced Meeting Title.md`.
- Example: `2026-06-09 - SignLab Product Alignment.md`.

---

## Meeting Note Structure
```markdown
---
id: 'YYYYMMDDHHmmss'
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

---

## Ingestion & Sync Pipeline
- **Granola Sync:** Raw transcripts and notes dropped into `/Meetings/` are automatically swept and processed into your formatted Meetings directory. This ingestion logic is handled by the **`bes-granola-ingest`** skill.
