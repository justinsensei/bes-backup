---
name: obsidian-people
description: Use when creating or updating contact notes representing individual people (family, friends, colleagues) under Contacts/ or inbox/ with category "[[People]]".
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, contacts, people, biography]
    related_skills: [obsidian, obsidian-contacts]
---

# Obsidian: People Contacts Management

## Overview
This skill governs the structure and standard templates for individual person notes representing real-world people (family, friends, colleagues, partners).

---

## Folder & Category
- **New Contacts Landing Directory:** `/home/justin.guest/vault/inbox/`
- **Permanent Directory:** `/home/justin.guest/vault/Contacts/`
- **Category link:** `category: "[[People]]"`

---

## Creation and Update Workflow

### Step 1 — Check for Duplicates
Always search both `/Contacts/` and `/inbox/` by name, first name, or common alias before writing a new note.
- **Relocation Boundary**: Only brand-new contacts created by Bes should land in `/home/justin.guest/vault/inbox/`. Never relocate or move existing contact notes already in `/home/justin.guest/vault/Contacts/` (created by Justin or prior processes) to the inbox. Always update them in-place.
- If the note already exists in either folder, update the existing note in-place in its current folder.
- If the note does not exist anywhere, create a brand-new note in `/home/justin.guest/vault/inbox/`.

### Step 2 — Filename
Use the normal capitalized, spaced full name as the filename:
- `Anya Volosskaya.md` (Not lowercase, not hyphenated).

### Step 3 — Frontmatter Structure
```yaml
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[People]]"
aliases:
  - Nickname
  - Maiden Name
---
```

### Step 4 — Body Layout
Use the standard personal profile layout to compile a single, scannable source of truth:

```markdown
> Executive summary: brief scannable description of who they are / role.

## State
- **Role:** Title or relationship (e.g., Lead Developer, [[Sam]]'s teacher)
- **Company:** [[Company Name]] (if applicable)
- **Relationship:** Colleague/Friend/Teammate/Family

## Open Threads
- 

---

## Timeline
- YYYY-MM-DD | Ingest — Context of creation / updates.
```

### Step 5 — Updating Timeline
- Read the existing file first to preserve layout.
- Insert the new event chronologically at the top of the `## Timeline` section.
- Keep the `Executive summary` and `State` fields up to date with any newly learned facts.
