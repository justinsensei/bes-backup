---
name: obsidian-hygiene
description: Use when performing structural and physical vault maintenance, configuring the nightly cron plumbing, archiving completed TaskNotes, resolving filename capitalization, or fixing broken link path associations.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, hygiene, maintenance, tasknotes, cron, links, automation]
    related_skills: [obsidian, obsidian-semantic-lint, bes-brain-ingest]
---

# Obsidian Vault Hygiene & Structural Plumbing

## Overview
This skill governs the physical layout, file movement, capitalization healing, link repair, and automated daily maintenance routines of Justin's Obsidian vault. It is powered by `vault_hygiene.py` and its cron wrapper `vault_hygiene_cron.py`.

Unlike semantic linting (which audits note content for meaning), physical hygiene ensures files are in correct folders, filenames follow capitalizations, stale or completed tasks are archived, and cross-references (wikilinks) remain functional.

---

## Daily Vault Hygiene Pipeline
The pipeline runs autonomously every night at 9:00 PM via the cron job **"vault-hygiene"** (`0b12d967fdf6`), running `vault_hygiene_cron.py`.

The script runs silently under a **watchdog pattern**:
- Normal successful runs or quiet auto-fixes produce **no stdout**, meaning no Telegram alert is sent.
- Warnings or errors (flagged by `# 🔴` or `# ⚠️` markers) are surfaced to Telegram.

---

## Core Hygiene Operations

### 1. TaskNotes Sweep & Archive (Daily)
TaskNotes represent actionable work items. Completed or abandoned items are swept out of active view to keep folders tidy:
- **`TaskNotes/Tasks/` (Subfolders):** Notes with `status: done` (case-insensitive) are moved to `TaskNotes/Archive/`.
- **`TaskNotes/` Root Directory (no subfolders):** Notes with `status: done` or `status: dropped` (case-insensitive) are moved to `TaskNotes/Archive/`.
- **Link Healing:** When a note is moved to `Archive/`, the pipeline scans all Markdown files in the vault and updates their internal wikilinks (e.g., `[[TaskNotes/Some Task]]` -> `[[TaskNotes/Archive/Some Task]]`) to prevent broken links.
- **Filename Collisions:** If an archived task has a filename collision in `Archive/`, the script appends a numeric suffix (e.g., `Some Task_1.md`).

### 2. EIIRP Task Promotion (Checkbox-to-Note Conversion)
- **Operation:** Scans the last 96 hours of Daily Notes for raw markdown checkboxes formatted as `- [ ] <Task Name> #task`.
- **Promotion:** Automatically promotes these checkboxes into separate physical TaskNote files in `TaskNotes/Tasks/` using the standard TaskNote schema, keeping the vault highly organized.

### 3. Filename Capitalization & Link Healing
- **Standard Proper Nouns & Acronyms:** Matches files against pre-defined rules (e.g. `ai` -> `AI`, `signlab` -> `SignLab`, `typescript` -> `TypeScript`) and renames mismatched files.
- **Link Repair:** Updates references across all files in the vault to use the corrected, newly renamed capitalized filepath.

### 4. Folder Boundary Constraints
- **Scope Rule:** Folder-wide health audits (Missing ID, Ghost Links, and Orphan Notes) are strictly restricted to the `Notes/` directory and its subdirectories.
- **Why:** This avoids false positives and warning noise from temporary or inbox files in `Inbox/` or `TaskNotes/`.

---

## Technical & Environment Architecture

### ⚠️ CRITICAL: The Bidirectional Sync Gotcha
On the VM environment, changes to tracked scripts (like `vault_hygiene.py`) and configurations have a strict directory mapping.
- **The Pitfall:** The VM's active runtime directory is **`~/.hermes/`**, but there is also a backup repository at **`~/bes-backup/`**.
- **The Mirror Mechanism:** The system runs a background daemon `bes-autocommit.service` which watches `~/.hermes/` and mirrors its contents into `~/bes-backup/` (using `rsync --delete`).
- **How to Avoid Reversion:** You must **never** edit python scripts directly in `~/bes-backup/scripts/` or files under `~/bes-backup/`. If you do, your changes will be silently deleted and overwritten on the next sync event!
- **Rule:** Always apply patches and write files to the active runtime paths under **`~/.hermes/`** (e.g., `~/.hermes/scripts/vault_hygiene.py`). The background daemon will safely mirror and commit those changes to git.

---

## Verification Checklist
- [ ] Run the hygiene script manually: `python3 ~/.hermes/scripts/vault_hygiene_cron.py`
- [ ] Verify stdout only contains legitimate unresolved errors or is empty for a clean state.
- [ ] Confirm moved tasks exist in `TaskNotes/Archive/` and are deleted from their source paths.
- [ ] Check `git -C ~/bes-backup status` and ensure the autocommit service safely mirrored and pushed updates.
