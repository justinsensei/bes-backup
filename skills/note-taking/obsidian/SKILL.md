---
name: obsidian
description: Core settings, paths, frontmatter schemas, baseline conventions, and note triage/sorting mapping rules for Justin's Obsidian vault.
version: 1.4.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, core, conventions, paths, frontmatter, triage, sorting]
    related_skills: [obsidian-contacts, obsidian-notes, obsidian-inputs, obsidian-utilities, llm-wiki, obsidian-hygiene]
---

# Obsidian: Core Vault Conventions & Triage Routing

## Overview
This is the foundational skill for interacting with Justin's Obsidian vault. It defines paths, general note-creation rules, frontmatter fields, standard formatting conventions, and global note-triage routing rules.

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
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Shortest-path link to creation day
category: "[[CategoryName]]"         # Single category link (quoted shortest-path wikilink)
---
```
- Use single quotes `'` or double quotes `"` around IDs and wikilinks to ensure YAML parsing is safe.
- **`aliases`** (optional): YAML list of alternative names for easy lookup.
- **`project`** (optional): Quoted shortest-path wikilink pointing to a parent project (placed last in frontmatter).

### Link Conventions
- **Shortest-Path Wikilinks:** Always use cleanest, shortest-path wikilinks (e.g., `[[Note Name]]` or `[[Note Name|Display Text]]`) instead of full folder path links (e.g., `[[Folder/Note Name]]`). 
- **Name Collisions:** Full paths are only permitted if a direct name collision actually exists in the vault (meaning two separate files share the exact same base filename in different directories). Known collision: `Cracking the Pm Career` (Readings merge — resolve during migration).
- **Formatting:** Keep display names concise and avoid full path leaks in normal note body reading.

### Formatting Rules
- **Horizontal Rules:** Always use exactly three hyphens `---` on a line by itself to represent a horizontal divider. Never use two hyphens or other symbols.
- **Heading & Bullet Spacing:** Ensure exactly one blank line exists between any heading (such as `## Timeline` or `## State`) and its subsequent content or bullet lists. Do not allow multiple consecutive blank lines to accumulate. Bulleted lists should be kept compact with zero blank lines between siblings.
- **Filename Conventions:**
  - **Daily Notes:** Must be `YYYY-MM-DD Weekday.md` (e.g. `2026-06-09 Tuesday.md`).
  - **Notes, Decisions, Thoughts, Memories, Concepts:** Must be `ID Title.md` (e.g. `20260609120000 Spaced Title.md`).
  - **References, Beliefs, Sources (compiled):** Must be `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).
  - **Readings (raw inputs):** `Title.md` or Readwise-exported names under `Inputs/Readings/` (no forced rename).
  - **Projects:** Must be `Title.md` under `Notes/Projects/` (e.g. `Spaced Title.md`).
  - **Contacts (People/Organizations):** Must be `Title.md` (e.g. `Aly Lalji.md`, `SignLab.md`).
  - **Meetings:** Must be `YYYY-MM-DD - Spaced Meeting Title.md` (e.g. `2026-06-09 - SignLab Product Alignment.md`).
  - Do not use kebab-case, lowercase hyphenated, or otherwise incorrect filenames. All names must be capitalized, spaced titles following these rules.
  - **Rationale:** As notes become less ephemeral and more authoritative (moving up the hierarchy), the date and/or ID is de-emphasized or omitted in the filename. Ephemeral, lower-tier notes are highly temporal (their place in time and sequence matters more), whereas canonical/authoritative notes (projects, people, beliefs, references) should stand out visually and contextually by title alone.

### Git & Synchronization
- Do NOT run `git` commands (add, commit, push) inside the vault. The background watcher `bes-vault-sync` handles commit and synchronization to GitHub automatically within seconds of filesystem writes.
- For detailed architecture, configuration, scripts, and pitfalls of the synchronization daemons (`bes-vault-sync` and `bes-autocommit`), see the **[Git & Synchronization Architecture Reference](references/git-and-synchronization-architecture.md)**.

---

## Global Note-Triage Routing Table

Notes are categorized with a single `category` YAML property containing a quoted wikilink to its category note. Based on this category, they must be sorted into the corresponding folder (matching the `Type:` folder mapping in the category's definition file):

| Target Folder | Target Category Link | Description / Type | Sub-skill Guidance |
|---|---|---|---|
| `Contacts/` | `category: "[[People]]"` | Individual contacts, friends, family, collaborators | `obsidian-people` |
| `Contacts/` | `category: "[[Organizations]]"` | Companies, schools, institutions, legal entities | `obsidian-organizations` |
| `Notes/` | `category: "[[Notes]]"` | Default category for conceptual, structured, or raw notes | `obsidian-notes` |
| `Notes/` | `category: "[[Sources]]"` | Compiled bibliographical records per work; links down to raw Readings | `llm-wiki` |
| `Notes/` | `category: "[[References]]"` | Useful facts, cheat sheets, guidelines, checklists | `obsidian-references-sources` |
| `Notes/` | `category: "[[Concepts]]"` | Other people's models/theories extracted from Sources | `obsidian-references-sources` |
| `Notes/` | `category: "[[Thoughts]]"` | Personal ideas, current opinions, research questions | `obsidian-thoughts-beliefs` |
| `Notes/` | `category: "[[Beliefs]]"` | Evolved concepts/thoughts - trusted models, core guiding principles | `obsidian-thoughts-beliefs` |
| `Notes/` | `category: "[[Decisions]]"` | Team or individual decisions and reasoning logs | `obsidian-decisions` |
| `Notes/` | `category: "[[Memories]]"` | Journal-like personal notes of things I want to remember | |
| `Notes/Projects/` | `category: "[[Projects]]"` | Hubs for notes about ongoing work, milestones, travel | `obsidian-projects` |
| `Daily Notes/` | `category: "[[Daily Notes]]"` | Daily notes containing schedules and work logs | `obsidian-daily-notes` |
| `Inputs/Meetings/` | `category: "[[Meetings]]"` | Meeting agendas, summaries, outcomes (Granola reconcile) | `obsidian-meetings` |
| `Inputs/Readings/` | `category: "[[Readings]]"` | Raw reading imports — Readwise, clippings (immutable) | `llm-wiki` |
| `Inputs/Emails/` | `category: "[[Emails]]"` | Email thread summaries | `bes-email-dispatch` |
| `Inputs/Slack/` | `category: "[[Slack]]"` | Slack conversation summaries | `slack` |
| `Utilities/` | `category: "[[Categories]]"` | Category definition notes (`Utilities/Categories/`) | `obsidian-utilities` |

---

## Action Steps for Triage
1. **Determine Category:** Read note content and title. Map it to exactly one category above. Convert legacy inline tags (e.g. `#meeting`) to the property and remove from body.
2. **Update YAML:** Set `category: "[[<CategoryName>]]"` using targeted `patch`.
3. **Move File:** Relocate the file from `inbox/` to its corresponding target folder. Create folders with `mkdir -p` if missing.

---

## Linked Utility Scripts
- **`scripts/heal_wikilinks.py`:** Statically re-runnable python script to scan the entire vault, identify base-filename collisions, and automatically heal/simplify any full-path wikilinks down to clean shortest-path wikilinks. Runs completely dynamically and safely.
