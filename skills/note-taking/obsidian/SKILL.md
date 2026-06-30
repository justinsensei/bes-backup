---
name: obsidian
description: Use when Justin asks you to search, read, write, or manage notes in the vault, OR when performing structural/physical vault maintenance (hygiene, task archiving, capitalization healing, link repair, and nightly cron plumbing).
version: 2.1.0
author: Bes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [obsidian, core, conventions, rules, pointers, thin-assistant, hygiene, maintenance, tasknotes, cron, links, automation]
    related_skills: [did-i-already-do-this, bes-slack-ingest, bes-telegram-ingest, bes-email-dispatch, obsidian-semantic-lint, bes-brain-ingest]
---

# Obsidian: Vault Operations & Schema Pointer

## Overview
Bes is a **thin assistant** designed for lightweight mobile query, search, and automated background plumbing (ingestion and daily note/hygiene runs).

To prevent drift and eliminate duplication of maintenance overhead, **the Obsidian vault itself is the sole canonical source of truth for all schemas, formats, layout structures, and workflows.** These conventions are actively maintained under:
1. **Cursor Rules:** `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/`
2. **Cursor Skills:** `/home/justin.guest/Developer/obsidian-vault/.cursor/skills/`

Bes does not store hard-coded copies of note formats, category tables, or sorting rules. Instead, this skill acts as a dynamic runtime instruction directing Bes to read the live rules directly from the filesystem prior to performing any note operations.

## When to Use
* **Use when** creating, editing, renaming, moving, searching, or reading any note in the vault.
* **Use when** running or reviewing automated ingestion pipelines (Slack, Telegram, Emails, Linear).
* **Use when** running daily scheduled hygiene checks.
* **Do not use for** modifying the underlying vault structures or schemas yourself (which is owned by Cursor).

## Rules of Engagement: Dynamic Rule Reading

Whenever you are asked to interact with files in the vault, you **must** obey the following rigid steps:

1. **Load Canonical Rules:** Read the live rules from the vault directory to retrieve current schemas, file naming conventions, and folders:
   * **General Rules (Categories, Folders, Links):** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/main.mdc`
   * **Note Formats & Frontmatter:** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/note-creation.mdc`
   * **Contacts Layouts (People/Orgs):** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/obsidian-contacts.mdc`
   * **File Operations (Moves, Renames, Links):** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/file-operations.mdc`
   * **Markdown & Syntax (Callouts, Math, YAML):** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/obsidian-syntax.mdc`
   * **Task Management (TaskNotes plugin & Archive):** Read `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/tasknotes.mdc` and `/home/justin.guest/Developer/obsidian-vault/TaskNotes/Setup.md`
2. **Apply Rules Dynamically:** Treat the retrieved markdown contents as absolute constraints. For example:
   * Verify the exact frontmatter syntax required (e.g., `id: "YYYYMMDDHHmmss"` and `daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"`).
   * Verify the correct category routing paths.
   * Verify filename formatting (e.g. `Title ID.md` vs `Title.md` vs `Title YYYY-MM-DD.md`).
3. **Execute Plumbing Safely:** When running automated daily cron jobs (like `vault_hygiene.py` or ingest feeds), cross-reference your script behavior against the retrieved rules to ensure the plumbing does not violate active vault conventions.

## Common Pitfalls
1. **Improvising Conventions:** Relying on cached memory or general knowledge to write note properties, file names, or folder paths. Always read the live `.cursor/rules/` files from disk first.
2. **Hard-coding YAML properties in scripts:** If a Cursor rule shifts (e.g., taxonomy change), scripts should be reviewed for alignment to prevent automated pipeline drift.
3. **Failing to check for existing files:** Before creating any note or stub, search both `/Notes/` and `/Inbox/` by name to prevent duplicate stubs.
4. **Failing to update the central wiki log:** Any newly created note (including manual quick-captures or scraps in `Inbox/`) must be logged in `Utilities/log.md` under the correct daily header (creating the header in `## YYYY-MM-DD Weekday` format if it doesn't already exist for the current date).

## Vault Hygiene & Structural Plumbing

Unlike semantic linting (which audits note content for meaning), physical and structural hygiene ensures files are in correct folders, filenames follow capitalizations, stale or completed tasks are archived, and cross-references (wikilinks) remain functional.

### Daily Vault Hygiene Pipeline
The pipeline runs autonomously every night at 9:00 PM via the cron job **"vault-hygiene"** (`0b12d967fdf6`), running `vault_hygiene_cron.py`.
The script runs silently under a **watchdog pattern**:
- Normal successful runs or quiet auto-fixes produce **no stdout**, meaning no Telegram alert is sent.
- Warnings or errors (flagged by `# 🔴` or `# ⚠️` markers) are surfaced to Telegram.

### Core Hygiene Operations

#### 1. TaskNotes Sweep & Archive (Daily)
TaskNotes represent actionable work items. Completed or abandoned items are swept out of active view to keep folders tidy:
- **`TaskNotes/Tasks/` (Subfolders):** Notes with `status: done` (case-insensitive) are moved to `TaskNotes/Archive/`.
- **`TaskNotes/` Root Directory (no subfolders):** Notes with `status: done` or `status: dropped` (case-insensitive) are moved to `TaskNotes/Archive/`.
- **Link Healing:** When a note is moved to `Archive/`, the pipeline scans all Markdown files in the vault and updates their internal wikilinks (e.g., `[[TaskNotes/Some Task]]` -> `[[TaskNotes/Archive/Some Task]]`) to prevent broken links.
- **Filename Collisions:** If an archived task has a filename collision in `Archive/`, the script appends a numeric suffix (e.g., `Some Task_1.md`).

#### 2. EIIRP Task Promotion (Checkbox-to-Note Conversion)
- **Operation:** Scans the last 96 hours of Daily Notes for raw markdown checkboxes formatted as `- [ ] <Task Name> #task`.
- **Promotion:** Automatically promotes these checkboxes into separate physical TaskNote files in `TaskNotes/Tasks/` using the standard TaskNote schema, keeping the vault highly organized.

#### 3. Filename Capitalization & Link Healing
- **Standard Proper Nouns & Acronyms:** Matches files against pre-defined rules (e.g. `ai` -> `AI`, `signlab` -> `SignLab`, `typescript` -> `TypeScript`) and renames mismatched files.
- **Link Repair:** Updates references across all files in the vault to use the corrected, newly renamed capitalized filepath.

#### 4. Folder Boundary Constraints
- **Scope Rule:** Folder-wide health audits (Missing ID, Missing Daily Note, Ghost Links, and Orphan Notes) are strictly restricted to the `Notes/` directory and its subdirectories.
- **Why:** This avoids false positives and warning noise from temporary or inbox files in `Inbox/` or `TaskNotes/`.

#### 5. Automated ID Conflict Resolution
- **Operation:** When multiple notes in the vault share the same 14-digit `id` field in their frontmatter, the pipeline automatically resolves the conflict.
- **Resolution:**
  - Keeps the alphabetical/first file's ID unchanged.
  - Increments the ID for subsequent conflicting files until a globally unique ID in the vault is found.
  - Rewrites the frontmatter `id:` field in the resolved files.
  - If the conflicting ID is present in the filename, renames the file to match the new ID.
  - Heals any incoming wikilinks to the renamed files across the entire vault.

---

### Technical & Environment Architecture: The Bidirectional Sync Gotcha
On the VM environment, changes to tracked scripts (like `vault_hygiene.py`) and configurations have a strict directory mapping.
- **The Pitfall:** The VM's active runtime directory is **`~/.hermes/`**, but there is also a backup repository at **`~/bes-backup/`**.
- **The Mirror Mechanism:** The system runs a background daemon `bes-autocommit.service` which watches `~/.hermes/` and mirrors its contents into `~/bes-backup/` (using `rsync --delete`).
- **How to Avoid Reversion:** You must **never** edit python scripts directly in `~/bes-backup/scripts/` or files under `~/bes-backup/`. If you do, your changes will be silently deleted and overwritten on the next sync event!
- **Rule:** Always apply patches and write files to the active runtime paths under **`~/.hermes/`** (e.g., `~/.hermes/scripts/vault_hygiene.py`). The background daemon will safely mirror and commit those changes to git.

---

## Expanded Verification Checklist
- [ ] Active rules (including `main.mdc`, `note-creation.mdc`, `obsidian-contacts.mdc`, `file-operations.mdc`, and `obsidian-syntax.mdc`) retrieved from `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/` before executing the operation
- [ ] Note frontmatter, title, and location checked against the retrieved Cursor rules
- [ ] Newly created notes land in `/home/justin.guest/Developer/obsidian-vault/Inbox/` first (except raw feed folders bypass)
- [ ] Central wiki log (`Utilities/log.md`) updated with the new creation under the correct date header
- [ ] Run the hygiene script manually when auditing: `python3 ~/.hermes/scripts/vault_hygiene_cron.py`
- [ ] Verify stdout of hygiene script only contains legitimate unresolved errors or is empty for a clean state
- [ ] Confirm moved tasks exist in `TaskNotes/Archive/` and are deleted from their source paths
- [ ] Check `git -C ~/bes-backup status` and ensure the autocommit service safely mirrored and pushed updates
