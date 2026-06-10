---
name: obsidian-utilities
description: Use when managing vault hygiene, automatic linting, tag conversions, ID conflicts, and the Utilities/ templates or categories folder.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, utilities, hygiene, maintenance, lint, categories]
    related_skills: [obsidian, obsidian-notes, obsidian-logs]
---

# Obsidian Type: Utilities & Vault Hygiene

- **Linked References:**
  - **[Resolving ID Conflicts](references/resolving-id-conflicts.md):** Step-by-step recipe to resolve clashing note identifiers.
  - **[Refactoring Categories](references/refactoring-categories.md):** Step-by-step recipe and automation template for bulk category renaming.

## Overview
This skill governs the system configurations, automation scripts, metadata linting, and automated tag sweeps designed to maintain perfect integrity across Justin's vault.

---

## Directory Conventions
- **Directory:** `/home/justin.guest/vault/Utilities/`
- **Sub-folders:**
  - `/Utilities/Categories/` (Category representation files).
  - `/Utilities/Templates/` (Reusable layouts and structural models).
  - `/Utilities/Attachments/` (Native images, PDFs, media storage).
- **Wiki log:** `/Utilities/log.md` — append-only ingest audit trail maintained by `llm-wiki` integrate-light (see `skills/note-taking/llm-wiki/references/index-and-log.md`).

---

## Vault Hygiene Automation

A consolidated hygiene script runs daily at 9PM (via a system cron job) at `~/.hermes/scripts/vault_hygiene.py`.

### Automated Cleanup Steps
1. **Misplaced Daily Notes:** Scans the entire vault for any `YYYY-MM-DD Weekday.md` files outside the `/Daily Notes/` directory and moves them there.
2. **Tag-to-Category Conversion:** Automatically converts inline tags in the body to their corresponding formal `category:` YAML property, removing the tag from the body text:
   - `#people`, `#person` $\rightarrow$ `category: "[[People]]"` (moves note to `/Contacts/`)
   - `#organization`, `#organizations` $\rightarrow$ `category: "[[Organizations]]"` (moves note to `/Contacts/`)
   - `#meeting`, `#meetings` $\rightarrow$ `category: "[[Meetings]]"` (moves note to `/Logs/Meetings/` — only if filename starts with `YYYY-MM-DD`)
   - `#project`, `#projects` $\rightarrow$ `category: "[[Projects]]"` (moves note to `/Notes/` — only if filename starts with `YYYY-MM-DD`)
3. **Identifier Diagnostics:** Runs diagnostic scans across all markdown files to detect:
   - Duplicate `id` frontmatter values.
   - Missing `id` properties.
   - Missing or malformed `daily_note` links.
4. **Exclusions:** Ignores the `.git/`, `.trash/`, `Utilities/` templates, and automated external sync folders (like `sources/` or `meetings/`) to prevent processing raw incoming files prematurely.
