---
name: obsidian-organizations
description: Use when creating or updating contact notes representing company, school, or institutional entities under Contacts/ or Inbox/ with category "[[Organizations]]".
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, contacts, organizations, business]
    related_skills: [obsidian, obsidian-contacts]
---

# Obsidian: Organizations Management

## Overview
This skill governs the structure and standard templates for institutional entities (companies, schools, partner organizations, clubs).

---

## Folder & Category
- **New Contacts Landing Directory:** `/home/justin.guest/vault/Inbox/`
- **Permanent Directory:** `/home/justin.guest/vault/Contacts/`
- **Category link:** `category: "[[Organizations]]"`

---

## Creation and Update Workflow

### Step 1 — Check for Duplicates
Always search both `/Contacts/` and `/Inbox/` by name, acronym, or common alias before writing a new organization note.
- **Relocation Boundary**: Only brand-new contacts created by Bes should land in `/home/justin.guest/vault/Inbox/`. Never relocate or move existing contact notes already in `/home/justin.guest/vault/Contacts/` (created by Justin or prior processes) to the inbox. Always update them in-place.
- If the note already exists in either folder, update the existing note in-place in its current folder.
- If the note does not exist anywhere, create a brand-new note in `/home/justin.guest/vault/Inbox/`.

### Step 2 — Filename
Use the capitalized, spaced official name as the filename:
- `Waldorf School of Pittsburgh.md` (Not lowercase, not hyphenated).
### Step 3 — Frontmatter Structure
Always wrap any bracketed wikilink inside the frontmatter in double quotes to prevent YAML syntax breakage (e.g. `category: "[[Organizations]]"`).

```yaml
---
id: 'YYYYMMDDHHmmss'
category: "[[Organizations]]"
aliases:
  - Acronym (e.g. WSP)
  - Short Name
---
```

### Step 4 — Body Layout
Use the standard organizational profile layout:

```markdown
> Executive summary: brief description of who this organization is and our connection.

## State
- **Type:** School/Partner/Vendor/Employer
- **Key Contacts:** [[Person Name]], [[Another Person]]

## Open Threads
- 

---

## Timeline
- YYYY-MM-DD | Ingest — Context of creation / updates.
```

### Step 5 — Updating Timeline
- Read the existing file first to preserve the layout.
- Insert the new event chronologically at the top of the `## Timeline` section.
- Maintain accurate mapping of members or contacts linked to this organization.
