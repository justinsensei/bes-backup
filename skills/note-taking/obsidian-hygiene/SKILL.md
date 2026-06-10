---
name: obsidian-hygiene
description: Use when performing daily or ad-hoc vault maintenance, running lints, resolving duplicate ID conflicts, or converting legacy inline tags to categories.
version: 1.2.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, operations, hygiene, maintenance, lint, duplicate-id]
    related_skills: [obsidian, obsidian-utilities]
---

# Obsidian Operation: Vault Hygiene & Maintenance

- **Linked References:**
  - **[Resolving ID Conflicts](references/resolving-id-conflicts.md):** Step-by-step recipe to resolve clashing note identifiers.

## Overview
This operational skill governs manual and automated procedures to maintain a clean, perfectly-linked, conflict-free vault. It handles executing hygiene scripts and resolving complex metadata anomalies (like duplicate IDs).

---

## The Hygiene Process

### Step 1 — Automated Script Execution
Run the consolidated hygiene script at `~/.hermes/scripts/vault_hygiene.py` (which runs automatically daily at 9PM, or can be run manually) to check the health of the vault:
```bash
python3 ~/.hermes/scripts/vault_hygiene.py
```
This script performs:
1. **Misplaced Daily Notes:** Detects daily notes located outside `/Daily Notes/` and relocates them.
2. **Tag-to-Category Conversion:** Converts inline tags like `#people` or `#meeting` into formal category YAML frontmatter and removes the inline tag from the body.
3. **Identifier Diagnostics:** Performs high-speed scans for missing or duplicate `id` keys, or malformed `daily_note` links.
4. **Auto-Linking of Unlinked Mentions:** Automatically converts plain-text mentions of known contacts and projects (by title and aliases like "Tor", "Anya", "Dave") into proper wikilinks inside newly reconciled Granola meetings and Daily Notes modified within the last 7 days. This builds a robust, tight knowledge graph automatically without manual overhead.

---

### Step 2 — Resolve ID Conflicts
If the script reports duplicate ID conflicts, follow the classification and resolution steps detailed in the linked reference:
1. **Accidental Duplicate / Template Copies:** Keep the earlier note; delete the newer duplicate.
2. **Identical Sources (`-1` suffix):** Delete the `-1` file and globally heal internal wikilinks pointing to it.
3. **Distinct Content sharing an ID:** Generate a fresh 14-digit timestamp ID for the newer/source note and update its frontmatter.

---

### Step 3 — Manual Link Health Audit
Regularly verify that link targets are correct and not broken.
- Verify that newly moved notes didn't break external scripts.
- Review and clean up empty tags or stray formatting rules.

---

### Step 4 — Deactivation of Timelines & Transition to Native Backlinks
In June 2026, Justin transitioned away from bot-enriched timeline sections in favor of Obsidian's native **Backlinks** panel, which dynamically displays all mentions of a file with real-time context.
- **Read-Only Mentions:** Active timeline enrichment (appending `## Timeline` bullets to notes) has been completely deactivated.
- **Unresolved Link & Plain-Text Discovery:** The signals script (`check_vault_signals.py`) has been refactored to be read-only. It scans for both bracketed unresolved links AND plain-text candidates of new contacts (not yet in the vault) and feeds them to the Morning Briefing as candidates for contact card creation.
- **Manual Timeline Spacing (Legacy):** If any manual timelines are edited or maintained, keep exactly one empty line between the heading and the first item, with no blank lines between individual bullet points.

---

### Step 5 — Frontmatter Parsing and Overwrite Pitfalls

When designing or patching automated hygiene scripts that read, clean, and write back markdown files:
- **Infinite Overwrite Loops:** Avoid extracting `body_content` in a way that includes leading newlines (e.g. `text[fm_end+4:]`) and then checking if it needs an update using `.lstrip()` (e.g. `body_content != original_body`). Since writing the file adds a newline after the frontmatter closing delimiter `---`, the next read will extract the leading newline again, causing an endless loop of "fixing" and rewriting unchanged files. Always `.lstrip()` immediately upon extraction.
- **Massive Re-indexing Overhead:** Constantly rewriting files modifies their `mtime` and hash, which triggers heavy background semantic embedding and indexing runs. Always check if real changes occurred before writing the file back to disk.
