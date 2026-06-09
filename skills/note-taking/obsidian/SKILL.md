---
name: obsidian
description: Core settings, paths, frontmatter schemas, and baseline conventions for Justin's Obsidian vault.
version: 1.2.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, core, conventions, paths, frontmatter]
    related_skills: [obsidian-categorize-and-sort, obsidian-logs, obsidian-contacts, obsidian-hygiene]
---

# Obsidian: Core Vault Conventions

## Overview
This is the foundational skill for interacting with Justin's Obsidian vault. It defines paths, general note-creation rules, frontmatter fields, and standard formatting conventions.

---

## Vault Path
- Vault root directory: `/home/justin.guest/vault`
- Environmental variable: `OBSIDIAN_VAULT_PATH` set in `~/.hermes/.env` (resolves to `/home/justin.guest/vault` inside VM).

---

## Baseline Conventions

### Frontmatter Schema
Every manual note must have a YAML frontmatter block containing at least these fields:
```yaml
---
id: 'YYYYMMDDHHmmss'                 # Numerical string based on creation time
daily_note: "[[Logs/Daily/YYYY-MM-DD-weekday|YYYY-MM-DD Weekday]]" # Link to creation day
category: "[[CategoryName]]"         # Single category link (optional but standard)
---
```
- Use single quotes `'` or double quotes `"` around IDs and wikilinks to ensure YAML parsing is safe.
- **`aliases`** (optional): YAML list of alternative names for easy lookup.
- **`project`** (optional): Quoted wikilink pointing to a parent project (placed last in frontmatter).

### Formatting Rules
- **Horizontal Rules:** Always use exactly three hyphens `---` on a line by itself to represent a horizontal divider. Never use two hyphens or other symbols.
- **Filename Case:** All regular notes (except Daily Notes and Meetings which use date prefixes) must be capitalized normal-spaced names, e.g. `Jamie's room.md`, `Aly Lalji.md`. Do not use kebab-case or lowercase hyphenated filenames.

### Git & Synchronization
- Do NOT run `git` commands (add, commit, push) inside the vault. The background watcher `bes-vault-sync` handles commit and synchronization to GitHub automatically within seconds of filesystem writes.
