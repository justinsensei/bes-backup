---
name: obsidian-contacts
description: Use when managing the Contacts/ directory, preventing duplicate notes, and coordinating People and Organizations categories.
version: 1.4.0
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
- **Relocation Boundary**: Only brand-new contacts created by Bes should land in `/home/justin.guest/vault/inbox/`. Never relocate or move existing contact notes already in `/home/justin.guest/vault/Contacts/` (created by Justin or prior processes) to the inbox. Always update them in-place.
- If the contact does not exist anywhere, create the new note in the `/inbox/` directory.

### Step 2 — Filename Capitalization
All files (whether in `/inbox/` or `/Contacts/`) must use standard Capitalized, spaced names (prefer full names over first-name-only filenames):
- Correct: `Andy Goff.md`, `Andrew Novak.md`, `Kristina Kennedy.md`
- Incorrect: `andy.md`, `andrew.md`, `christina.md`
- Avoid first-name-only filenames unless the person is universally referred to by that name and has no last name in context. Using first-name-only names leads to severe timeline pollution and generic name collisions from books, articles, or other public figures (e.g., `Andy Grove`, `Andrew Chen`, `David Deutsch`).

### Step 3 — Handling Aliases to Prevent Collisions
To enable short-name links while keeping filenames unique:
1. Save the file under the full name (e.g., `Kristina Kennedy.md`).
2. Add the first name or nickname in the frontmatter `aliases:` field:
   ```yaml
   aliases:
     - Kristina
     - Kristina Kennedy
     - Christina
   ```
3. The background scripts will automatically match the first name as an alias without generating duplicate candidate notes or polluting timelines.

### Step 3 — Mapping Connections
- Individual people notes must link to their respective organizations (e.g. `- **Company:** [[SignLab]]`).
- Organizations must link to their key representatives.
- Maintain family connections accurately using spaced wikilinks (e.g. `[[Sam]]'s teacher`, `[[Nana]]'s friend`).

---

## Pitfalls & Safeguards

### Alias Hygiene & Link-Hijacking Prevention
- **Avoid Generic First-Name Aliases**: Never add a highly generic or common first name (e.g., `Linda`, `Georgia`, `Drew`) as a generic alias in the frontmatter of a full-name contact note (e.g., `Linda Massie.md` or `Georgia Sullivan.md`) if there are other entities, companies, or plain-text terms (such as `Georgia Tech`, `Lindy Effect`, or the state of `Georgia`) that share that name.
- **Why**: Broad aliases cause automated background scripts (like `check_vault_signals.py`) and AI parsers to perform "link-hijacking"—incorrectly mapping technical research, company meetings, or regional references onto family members' timeline notes, creating huge amounts of cross-pollution and duplicates.
- **Safe Alias Rule**: Only use single-name aliases when they are absolutely unique in the vault context (e.g., `Larry` for `Andrew Lawrence` is safe, but `Andy`, `Andrew`, `David`, or `Jim` are unsafe and must map to specific individuals like `Andy Goff` or `Andy Masley` instead of general notes).

### Step 4 — Generic Name Collisions & Deduplication
To prevent auto-generated notes from colliding on generic first names (e.g., `Andy` or `Andrew` colliding with `Andy Goff`, `Andrew Novak`, etc.):
- **Never create a generic first-name contact file** (e.g. `andy.md` or `andrew.md`) unless the person is uniquely known by only that single name. If a generic first-name file exists and is polluted with multiple people's timelines, perform an LLM-driven deduplication to split them into their respective capitalized full-name files (e.g. `Andy Goff.md` and `Andy Masley.md`), and delete the generic file.
- **Alias Resolution**: Ensure that any unique nickname/alias (like `Larry` for `Andrew Lawrence`) is registered in the main file's frontmatter `aliases` list. This prevents the unresolved links scanner from proposing a duplicate card for the nickname.
- **Contextual Verification**: When analyzing legacy timeline entries to untangle them, verify the context (e.g. family mentions like Pat/Kath/Meghan for family, or professional terms like architect/design/surveyor for contractors, or topics like pretending to learn for references) to ensure accurate attribution.

### Step 5 — Speech-to-Text & Mishearing Normalization
Granola or other automated transcription tools occasionally mishear names or introduce spelling variations (e.g. transcribing **"Dhruv"** as **"Drew"**, or spelling **"Kristina"** as **"Christina"**). When such homophone or mishearing clusters are identified:
1. **Consolidate to Actual Name**: Merge the timelines, rename the note to the person's capitalized, correct full name, and delete the misheard/alternate contact note.
2. **Add Alias**: Register the misheard spelling (e.g. `Drew`, `Christina`) in the frontmatter `aliases:` list of the consolidated contact note, so future automated speech-to-text references map correctly.
3. **Vault-Wide Update**: Do a global search-and-replace for wikilinks pointing to the old/misheard spelling (e.g. replacing `[[Drew]]` or `[[drew]]` with `[[Dhruv]]`), keeping your note links perfectly clean.
