---
name: obsidian
description: Core settings, paths, frontmatter schemas, baseline conventions, and note triage/sorting mapping rules for Justin's Obsidian vault.
version: 1.4.0
author: Bes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [obsidian, core, conventions, paths, frontmatter, triage, sorting]
    related_skills: [obsidian-contacts, obsidian-notes, obsidian-inputs, obsidian-utilities, llm-wiki, obsidian-hygiene]
---

# Obsidian: Core Vault Conventions & Triage Routing

## Overview
This is the foundational skill for interacting with Justin's Obsidian vault. It defines paths, general note-creation rules, frontmatter fields, standard formatting conventions, and global note-triage routing rules. Interactive synthesis filing (durable Q&A answers) → `llm-wiki` integrate-query (saved to `inbox/` on creation).

---

## Automation & Governance Principles

To maintain high quality, trust, and alignment, the PKMS operates under a strict division of labor between automation and human oversight:

1. **Simple Administration (Hands-off & Automated):**
   - Administrative tasks like ingesting raw inputs (emails, Slack, Linear), linting, fixing broken links, and file moving are fully automated and run hands-off.
   - **Fail-Loudly Rule:** All automated admin scripts and cron jobs must fail loudly. If a script, API connection, token, or platform fetcher fails or crashes, the wrapper must propagate the exit code and print error logs so that the cron system raises an immediate, conspicuous alert. No exceptions can be silently caught or swallowed (e.g., returning empty lists on platform fetch failures is prohibited).

2. **Knowledge Creation & Modification (Strictly Human-in-the-Loop):**
   - Any process that creates or modifies knowledge in the vault (writing concepts, thoughts, beliefs, or editing daily notes/work logs) must keep Justin in the loop.
   - These processes must **never run automatically in the background** via cron or daemon. They can only be triggered manually in chat, or chained to interactive, reviewed routines (like the morning briefing or evening wind-down).
   - All newly generated knowledge notes must be saved under the `inbox/` directory for active manual review and triage.

3. **Gray Area (Case-by-Case):**
   - Tasks like **Work Logs** must be reviewed and aligned in chat before being written to the daily note. This review is a key step of the interactive daily wind-down and morning briefing rituals.
   - For any brand-new administrative automation, begin with a human-in-the-loop manual process to ensure stability and accuracy before fully automating it.

---

## Note Hierarchy (The Three-Tier System)
The vault utilizes a unidirectional, three-tier conceptual hierarchy to manage the evolution of knowledge:

1. **Tier 1 (Raw & Ephemeral Inputs):**
   - *Categories:* `[[Scraps]]` (default for quick-capture), `[[Concepts]]` (others' thinking), `[[Decisions]]`, `[[Memories]]`.
   - *Filename Format:* `Title ID.md` (e.g., `Spaced Title 20260610120000.md`).
   - *Role:* Scratchpads, raw brain dumps, source clippings, or raw logs. Almost everything defaults to `[[Scraps]]`.

2. **Tier 2 (Emergent, Synthesized & Factual Supporting Notes):**
   - *Categories:* `[[Notes]]` (compiled factual support), `[[Thoughts]]` (opinions/theories).
   - *Filename Format:* `Title ID.md` (retains creation ID/timestamp at the end).
   - *Role:* Personal ideas, active theories, open research questions, or compiled factual information supporting higher tiers.

3. **Tier 3 (Permanent & Conviction Beliefs):**
   - *Categories:* `[[Beliefs]]` (guiding models), `[[References]]` (checklists/cheat sheets).
   - *Filename Format:* For `[[References]]`, `Title.md` (no ID string in the filename). For `[[Beliefs]]`, `Title ID.md` (ID at the end, if retaining creation ID).
   - *Role:* Trusted, highly stable playbooks. Beliefs require a specific structure (core thesis, exactly 3 **Core Tenets**, and 2 **Application** scenarios).

**Core Hierarchy Rules:**
- **The Unidirectional Link Rule:** Higher-tier notes must not link downward to lower-tier notes (e.g., a `[[Belief]]` or `[[Reference]]` cannot link to an ephemeral `[[Scrap]]`, `[[Note]]`, or `[[Thought]]`).
- **Default to Scraps:** All quick-captures, fleeting brain dumps, and unrefined jottings default to Tier 1 `[[Scraps]]`.
- **Reversion Naming:** If a note is demoted back to Tier 1 or Tier 2, its filename is reverted to restore the 14-digit ID prefix.

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
- **Executive Summaries**: When present, should be a blockquote at the top of the note *without* the `Executive summary:` prefix. Just the text.
  - **Daily Notes:** Must be `YYYY-MM-DD Weekday.md` (e.g. `2026-06-09 Tuesday.md`).
  - **Notes, Decisions, Thoughts, Memories, Concepts, Scraps, Beliefs, Sources (compiled):** Must be named `Title ID.md` with the ID at the end (e.g. `Spaced Title 20260609120000.md`).
  - **References:** Must be named `Title.md` with no ID string in the filename (e.g. `Spaced Title.md`).
  - **Readings (raw inputs):** `Title.md` or Readwise-exported names under `Inputs/Readings/` (no forced rename).
  - **Projects:** Must be `Title.md` under `Notes/Projects/` (e.g. `Spaced Title.md`).
  - **Contacts (People/Organizations):** Must be `Title.md` (e.g. `Aly Lalji.md`, `SignLab.md`).
  - **Meetings:** Must be `YYYY-MM-DD - Spaced Meeting Title.md` (e.g. `2026-06-09 - SignLab Product Alignment.md`).
  - Do not use kebab-case, lowercase hyphenated, or otherwise incorrect filenames. All names must be capitalized, spaced titles following these rules. Filenames are automatically normalized and healed for correct acronym casing (e.g., `AI`, `ADHD`, `B2C`) and proper nouns by the `vault_hygiene` pipeline.
  - **Rationale:** As notes become less ephemeral and more authoritative (moving up the hierarchy), the date and/or ID is de-emphasized or omitted in the filename. Ephemeral, lower-tier notes are highly temporal (their place in time and sequence matters more), whereas canonical/authoritative notes (projects, people, beliefs, references) should stand out visually and contextually by title alone.

### Git & Synchronization
- Do NOT run `git` commands (add, commit, push) inside the vault. The background watcher `bes-vault-sync` handles commit and synchronization to GitHub automatically within seconds of filesystem writes.
- For detailed architecture, configuration, scripts, and pitfalls of the synchronization daemons (`bes-vault-sync` and `bes-autocommit`), see the **[Git & Synchronization Architecture Reference](references/git-and-synchronization-architecture.md)**.

---

## Global Note-Triage Routing Table

Notes are categorized with a single `category` YAML property containing a quoted wikilink to its category note. Based on this category, they must be sorted into the corresponding folder (matching the `Type:` folder mapping in the category's definition file):

| Target Folder | Target Category Link | Description / Type | Sub-skill Guidance |
|---|---|---|---|
| `Notes/Contacts/` | `category: "[[People]]"` | Individual contacts, friends, family, collaborators | `obsidian-people` |
| `Notes/Contacts/` | `category: "[[Organizations]]"` | Companies, schools, institutions, legal entities | `obsidian-organizations` |
| `Notes/` | `category: "[[Notes]]"` | Compiled, factual supporting notes | `obsidian-notes` |
| `Notes/` | `category: "[[Sources]]"` | Compiled bibliographical records per work; links down to raw Readings | `llm-wiki` |
| `Notes/` | `category: "[[References]]"` | Useful facts, cheat sheets, guidelines, checklists | `obsidian-references-sources` |
| `Notes/` | `category: "[[Concepts]]"` | Other people's models/theories extracted from Sources | `obsidian-references-sources` |
| `Notes/` | `category: "[[Thoughts]]"` | Personal ideas, current opinions, research questions | `obsidian-thoughts-beliefs` |
| `Notes/` | `category: "[[Beliefs]]"` | Evolved concepts/thoughts - trusted models, core guiding principles | `obsidian-thoughts-beliefs` |
| `Notes/` | `category: "[[Decisions]]"` | Team or individual decisions and reasoning logs | `obsidian-decisions` |
| `Notes/` | `category: "[[Memories]]"` | Journal-like personal notes of things I want to remember | |
| `Notes/Projects/` | `category: "[[Projects]]"` | Hubs for notes about ongoing work, milestones, travel | `obsidian-projects` |
| `Notes/Daily Notes/` | `category: "[[Daily Notes]]"` | Daily notes containing schedules and work logs | `obsidian-daily-notes` |
| `Inputs/Meetings/` | `category: "[[Meetings]]"` | Meeting agendas, summaries, outcomes (Granola reconcile) | `obsidian-meetings` |
| `Inputs/Readings/` | `category: "[[Readings]]"` | Raw reading imports — Readwise, clippings (immutable) | `llm-wiki` |
| `Inputs/Emails/` | `category: "[[Emails]]"` | Email thread summaries | `bes-email-dispatch` |
| `Inputs/Slack/` | `category: "[[Slack]]"` | Slack conversation summaries | `slack` |
| `Inputs/Telegram/` | `category: "[[Telegram]]"` | Telegram session summaries | `bes-telegram-ingest` |
| inbox/ | category: "[[Scraps]]" | Fleeting brain dumps, raw quick-captures, scraps | `obsidian-notes` |
| `Utilities/` | `category: "[[Categories]]"` | Category definition notes (`Utilities/Categories/`) | `obsidian-utilities` |

---

## Action Steps for Triage
1. **Determine Category:** Read note content and title. Map it to exactly one category above. Convert legacy inline tags (e.g. `#meeting`) to the property and remove from body.
2. **Update YAML:** Set `category: "[[<CategoryName>]]"` using targeted `patch`.
3. **Move File:** Relocate the file from `inbox/` to its corresponding target folder. Create folders with `mkdir -p` if missing.

---

## Linked Utility Scripts
- **`scripts/migrate_note_names_2026.py`:** Statically re-runnable python script to scan the entire vault, detect files with old naming conventions (ID prefix or ID-carrying References), rename them safely (IDs at the end for notes, no IDs for References), check for collisions, and heal all corresponding wikilinks across the vault.
- **`scripts/heal_wikilinks.py`:** Statically re-runnable python script to scan the entire vault, identify base-filename collisions, and automatically heal/simplify any full-path wikilinks down to clean shortest-path wikilinks. Runs completely dynamically and safely.
