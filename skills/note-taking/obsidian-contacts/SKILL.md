---
name: obsidian-contacts
description: Use when managing the Contacts/ directory, preventing duplicate notes, and coordinating People and Organizations categories.
version: 1.3.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, contacts, folder-conventions]
    related_skills: [obsidian, obsidian-people, obsidian-organizations]
---

# Obsidian Type: Contacts Directory Conventions

## Overview
This skill governs the physical structure and coordinate mapping of the `/Contacts/` top-level directory in Justin's vault.

---

## Directory & Sub-skills
- **New Contacts Landing Directory:** `/home/justin.guest/vault/inbox/`
- **Permanent Contacts Directory:** `/home/justin.guest/vault/Contacts/`
- **Sub-skills (Categories):**
  - **`obsidian-people`**: For individual contacts, family members, friends, or colleagues (`category: "[[People]]"`).
  - **`obsidian-organizations`**: For companies, schools, legal entities, or institutions (`category: "[[Organizations]]"`).

---

## Folder-Level Rules

### Step 1 — Check for Duplicates
Before writing any contact file, always search both `/Contacts/` and `/inbox/` by name, first name, last name, abbreviation, or known aliases.
- Use `search_files(target='files', path='/home/justin.guest/vault/Contacts')` and `search_files(target='files', path='/home/justin.guest/vault/inbox')`.
- It is critical to update existing biography files in their current location (whether in `/Contacts/` or `/inbox/`) rather than creating overlapping notes.
- If the contact does not exist anywhere, create the new note in the `/inbox/` directory.

### Step 2 — Filename Capitalization
All files (whether in `/inbox/` or `/Contacts/`) must use standard Capitalized, spaced names:
- `Aly Lalji.md`
- `SignLab.md`
- Do not use lowercase or hyphenated slug names.

### Step 3 — Mapping Connections
- Individual people notes must link to their respective organizations (e.g. `- **Company:** [[SignLab]]`).
- Organizations must link to their key representatives.
- Maintain family connections accurately using spaced wikilinks (e.g. `[[Sam]]'s teacher`, `[[Nana]]'s friend`).
