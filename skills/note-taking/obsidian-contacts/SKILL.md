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
This skill governs the physical structure and coordinate mapping of the `/Notes/Contacts/` directory in Justin's vault.

---

## Directory & Sub-skills
- **New Contacts Landing Directory:** `/home/justin.guest/vault/inbox/`
- **Permanent Contacts Directory:** `/home/justin.guest/vault/Notes/Contacts/`
- **Sub-skills (Categories):**
  - **`obsidian-people`**: For individual contacts, family members, friends, or colleagues (`category: "[[People]]"`).
  - **`obsidian-organizations`**: For companies, schools, legal entities, or institutions (`category: "[[Organizations]]"`).

---

## Folder-Level Rules

### Step 1 — Check for Duplicates
Before writing any contact file, always search both `/Notes/Contacts/` and `/inbox/` by name, first name, last name, abbreviation, or known aliases.
- Use `search_files(target='files', path='/home/justin.guest/vault/Notes/Contacts')` and `search_files(target='files', path='/home/justin.guest/vault/inbox')`.
- **Relocation Boundary**: Only brand-new contacts created by Bes should land in `/home/justin.guest/vault/inbox/`. Never relocate or move existing contact notes already in `/home/justin.guest/vault/Notes/Contacts/` (created by Justin or prior processes) to the inbox. Always update them in-place.
- If the contact does not exist anywhere, create the new note in the `/inbox/` directory.

### Step 2 — Filename Capitalization
All files (whether in `/inbox/` or `/Notes/Contacts/`) must use standard Capitalized, spaced names (prefer full names over first-name-only filenames):
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
   ```

### Step 4 — Frontmatter Identifiers and No Daily Note Link
- **Unique Timestamp-Based ID:** Every contact file must have a unique 14-digit ID (`id: "YYYYMMDDHHMMSS"`) in its frontmatter, based on its file creation/birth timestamp (e.g., `stat -c %W`). If there is an ID conflict with any other file in the vault, resolve it by tweaking the last digit or two (e.g., incrementing it).
- **No Daily Note Property:** Contacts do not require a `daily_note:` link. Do NOT add `daily_note:` to frontmatter for any contact, and exclude contacts (both People and Organizations) from daily-note audits in vault hygiene.

### Step 5 — Simple People Template Guidelines
For people notes (`category: "[[People]]"`), keep the template simple:
1. **No Open Threads or Timeline:** Do not include "Open Threads" or "Timeline" sections. Rely entirely on native backlinks for navigation.
2. **Short Description:** Start right after the frontmatter with a plain, short description (no blockquotes, no "Justin's" third-person references).
3. **State Section:** Include a `## State` section with `Role:` and `Relationship:`.
4. **Family Line:** If relevant, include a `Family:` key with a single-line list of family members (e.g. `- **Family:** [[Spouse]] (spouse) [[Child]] (child)`). Do not use bullet points or nested lists for family members.

### Step 6 — Naming & Alias Guidelines (Collision Prevention)
To prevent automatic link-hijacking and timeline pollution from background analysis scripts (like `check_vault_signals.py`), follow these rules:
1. **Avoid Overly Aggressive First-Name Aliases**: Never register overly generic, common first names (like `Mac`, `Georgia`, `Linda`, `Andrew`, `Andy`) as standalone aliases in a contact's frontmatter.
   * *Why*: Standalone aliases like `Mac` will match unrelated system terms like `MacMini`, `macOS`, or `MacBook`. Standalone aliases like `Georgia` will match `Georgia Tech` or the US state of Georgia.
2. **Qualify High-Collision Names**: For family members or close friends with highly common names, use their full name (e.g., `Georgia Sullivan`, `Linda Massie`, `Mac Lawrence`) as the primary file name, and only register specific non-colliding aliases in frontmatter (or omit generic first-name aliases entirely if they risk matching system or business terms).
3. **Deduplication Triage Protocol**: If a generic contact (like `andy.md` or `david.md`) becomes polluted:
   * Perform a vault-wide regex/content search to classify mentions into distinct, actual individuals based on family/work context.
   * Filter out non-person matches (authors, books, hardware, random names).
   * Create separate files for newly discovered people in the `/inbox/` directory.
   * Update existing profiles in-place under `/Notes/Contacts/` with clean timelines.
   * Delete the polluted generic file and clean up any false timeline entries in related contacts' notes (e.g., in `oleksii.md` or `Kristina Kennedy.md`).

### Step 5 — Filename & Link Capitalization
- **Strict Capitalization:** Never write lowercase filenames for contacts or organizations (e.g. do not use `Anya volosskaya.md`, `duolingo.md`, `smartpass.md`).
- **Standard Formatting:** 
  - People: Capitalize both First and Last names (e.g., `Anya Volosskaya.md`, `Aly Lalji.md`, `Matt McIlvride.md`).
  - Organizations: Use correct corporate casing (e.g., `Duolingo.md`, `SmartPass.md`, `PowerSchool.md`, `SignOn.md`, `SV Academy.md`).
- **Renaming & Healing:** If contacts are found with incorrect lowercase filenames, use `git mv` to rename them, and run a vault-wide search-and-replace to update all internal links to use the correct casing, keeping your index perfectly coherent.

### Step 6 — Contact ID Generation & Uniqueness
Every contact file (including brand-new ones created by Bes) must have an `id` field in its frontmatter.
- **Format:** The ID must be a 14-digit double-quoted string `id: "YYYYMMDDHHMMSS"` based on the file's birth (creation) timestamp.
- **Acquiring Birth Time:** On Linux, query the birth timestamp via `stat -c %W <filepath>`. If unsupported or returning `0`, fall back to the modification time (`mtime`).
- **Enforcing Uniqueness:** Scan all `.md` files in the vault to collect existing IDs before assigning a new one. 
- **Conflict Resolution:** If the formatted timestamp matches any existing ID in the vault (common when files are imported or created in batches), tweak the last digit or two (e.g., incrementing them) until a completely unique ID is obtained.
- **Frontmatter Insertion:** Insert the ID as the first field right below the opening `---` of the frontmatter:
  ```yaml
  ---
  id: "20260611074153"
  category: "[[People]]"
  ---
  ```

### Step 7 — Pruning Obsolete Contacts
To maintain vault cleanliness and hygiene, prune obsolete contact notes periodically. A contact is considered safe to prune/remove if both of the following conditions are met:
1. **No Backlinks:** There are no wikilinks (`[[Contact Name]]`) or markdown links to the contact filename or any of its registered aliases from any other note in the vault.
2. **Empty Body:** The body of the note is completely empty (contains nothing except the frontmatter block and whitespace).
*Always perform a Dry Run and check with the user before deleting files.*

### Step 6 — Contact ID Convention (Strict ID Uniqueness)
- **Every contact must have a unique ID** field in its frontmatter:
  ```yaml
  id: "YYYYMMDDHHMMSS"
  ```
- **ID Generation**: The ID is based on the file creation/birth timestamp formatted as a 14-digit string `YYYYMMDDHHMMSS`. On Linux, this birth timestamp can be fetched via `stat -c %W` (falling back to modification time if birth time is unavailable).
- **ID Uniqueness**: Before assigning an ID to a contact (whether creating a new one or repairing an existing one), verify that the ID is completely unique across the entire vault (check other notes' IDs as well).
- **Conflict Resolution**: If the generated ID is already in use (common when notes are imported or created in batches), tweak the last digit or two (e.g. increment) until a completely unique ID is obtained.

---

## Pitfalls & Safeguards

### YAML Quote Hygiene in Frontmatter
- **Always Wrap Wikilinks in Quotes**: Any bracketed links inside the YAML frontmatter (such as `category: "[[People]]"`, `category: "[[Organizations]]"`, or `daily_note: "[[YYYY-MM-DD]]"`) **must** be wrapped in double quotes. Omitting quotes around brackets causes YAML parser exceptions and breaks vault hygiene scripts.

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
