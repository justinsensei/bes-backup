---
name: obsidian-people
description: Use when creating or updating contact notes representing individual people (family, friends, colleagues) under Notes/Contacts/ or Inbox/ with category "[[People]]".
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
- **New Contacts Landing Directory:** `/home/justin.guest/vault/Inbox/`
- **Permanent Directory:** `/home/justin.guest/vault/Contacts/`
- **Category link:** `category: "[[People]]"`

---

## Creation and Update Workflow

### Step 1 — Check for Duplicates
Always search both `/Contacts/` and `/Inbox/` by name, first name, or common alias before writing a new note.
- **Relocation Boundary**: Only brand-new contacts created by Bes should land in `/home/justin.guest/vault/Inbox/`. Never relocate or move existing contact notes already in `/home/justin.guest/vault/Contacts/` (created by Justin or prior processes) to the inbox. Always update them in-place.
- If the note already exists in either folder, update the existing note in-place in its current folder.
- If the note does not exist anywhere, create a brand-new note in `/home/justin.guest/vault/Inbox/`.

### Step 2 — Filename
Use the normal capitalized, spaced full name as the filename:
- `Anya Volosskaya.md` (Not lowercase, not hyphenated).

### Step 3 — Frontmatter Structure
Always wrap any bracketed wikilink inside the frontmatter in double quotes to prevent YAML syntax breakage (e.g. `category: "[[People]]"`).

```yaml
---
id: 'YYYYMMDDHHmmss'
category: "[[People]]"
aliases:
---
```

### Step 4 — Body Layout
Use the simplified personal profile layout. The body should only contain a brief, clean description of who they are and their role. Do NOT include any "State" sections, Roles, Relationships, or Family lists.

**Important Constraints:**
- **No Family Relationship Deduction:** Do not attempt to automatically deduce or populate family relationships. Justin will always maintain these manually.
- **No Third-Person Phrasing:** Avoid third-person phrasing such as "Justin's ___". Keep descriptions objective and concise.

```markdown
Short description of who they are and their role.
```

### Step 5 — Rely on Backlinks
Rely entirely on Obsidian's backlinks for chronological navigation. Do NOT add an "Open Threads" or "Timeline" section.
