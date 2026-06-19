---
name: obsidian
description: Use when Justin asks you to search the vault, find/read notes, or ingest raw items. This is a thin pointer skill that instructs Bes to dynamically read and apply the canonical Cursor rules and skills maintained in the vault.
version: 2.0.0
author: Bes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [obsidian, core, conventions, rules, pointers, thin-assistant]
    related_skills: [did-i-already-do-this, bes-slack-ingest, bes-telegram-ingest, bes-email-dispatch]
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

## Verification Checklist
- [ ] Active rules (including `main.mdc`, `note-creation.mdc`, `obsidian-contacts.mdc`, `file-operations.mdc`, and `obsidian-syntax.mdc`) retrieved from `/home/justin.guest/Developer/obsidian-vault/.cursor/rules/` before executing the operation
- [ ] Note frontmatter, title, and location checked against the retrieved Cursor rules
- [ ] Newly created notes land in `/home/justin.guest/Developer/obsidian-vault/Inbox/` first (except raw feed folders bypass)
- [ ] Central wiki log (`Utilities/log.md`) updated with the new creation under the correct date header
