# Vault Hygiene Script — Design Notes

Scripts: `~/.hermes/scripts/vault_hygiene.py` (main), `~/.hermes/scripts/vault_hygiene_cron.py` (cron wrapper).

Cron job id: `0b12d967fdf6`, schedule: daily 9pm, deliver: telegram (red + taxonomy warnings).

## Architecture

Two-tier design:
- **Auto-fix tier**: runs silently, applies safe structural corrections
- **Report tier**: emits findings to stdout; cron wrapper passes 🔴 and taxonomy-relevant ⚠️ sections to Telegram

The cron wrapper imports stdout from the main script and passes through lines under alert headers (ID conflicts, wrong folder, ghost links, source linkage, legacy paths, citation issues). Clean runs and auto-fix-only runs produce no Telegram message (watchdog pattern).

## Three-layer taxonomy (Inputs / Sources / maturity)

| Layer | Folder | Category | Hygiene may edit body? |
|-------|--------|----------|------------------------|
| 1 — Inputs | `Inputs/Readings/`, `Meetings/`, `Emails/`, `Slack/` | `[[Readings]]`, `[[Meetings]]`, etc. | Metadata only on Readings/Emails/Slack; Meetings get entity auto-link |
| 2 — Compiled biblio | `Notes/` | `[[Sources]]` | Yes (summary kept current by llm-wiki integrate-full) |
| 3 — Maturity | `Notes/` (+ subfolders) | Notes, Thoughts, Concepts, Beliefs, References, Decisions, Memories, Projects | Yes |

**Transition:** Script feature-detects `Inputs/` vs legacy `Logs/` paths until migration completes.

## Auto-fix decisions

### Misplaced daily notes
**Detection:** filename matches `YYYY-MM-DD (Weekday).md` exactly — no extra words after the weekday name.
**Action:** move to `Daily Notes/`.

### Tag-to-category conversion
**Always convert:** `#people`, `#person`, `#organizations`, `#organization`.
**Date-prefix only:** `#meetings`/`#meeting`, `#projects`/`#project` — only if filename starts `YYYY-MM-DD`.
**Readings:** `#readings` / `#reading` → `category: "[[Readings]]"` (no date prefix required).
**Sources (context-aware):** `#sources` under `Inputs/` paths → `[[Readings]]`; under `Notes/` → `[[Sources]]`.
**Action:** write `category: "[[Wikilink]]"` to frontmatter, remove tag from body.

### Legacy category on input paths
**Detection:** `category: "[[Sources]]"` on file under `Inputs/Readings/` (or legacy `Logs/Readings/`, `Logs/Sources/`).
**Action:** auto-rewrite to `category: "[[Readings]]"`.

### Granola meeting reconcile
**Source:** `Meetings/` (raw Granola sync).
**Destination:** `Inputs/Meetings/` (fallback `Logs/Meetings/` during transition).
**Action:** write `id`, `daily_note`, `category: "[[Meetings]]"`; auto-link entities in meeting body; delete raw file after reconcile.

### Granola-to-Project linking
**Detection:** matches key terms of active project notes in meeting body.
**Action:** appends `### Related` at bottom with project wikilink. Meetings only — never on Readings/Emails/Slack.

### Input immutability
- **Auto-link bodies:** `Inputs/Meetings/` and recent `Daily Notes/` only
- **Do not auto-link:** `Inputs/Readings/`, `Inputs/Emails/`, `Inputs/Slack/` (preserve raw import text)
- **Do not append `### Related`:** Readings, Emails, Slack

### Healing broken timestamp-less links
**Detection:** A broken wikilink whose target title (e.g., `[[ADHD Product Strategy Framework]]`) matches an existing note on disk that has a 14-digit timestamp ID suffix (e.g., `ADHD Product Strategy Framework 20260616102600.md`).
**Action:** Automatically rewrite the wikilink to target the full timestamped filename while utilizing an alias to display the short title (or preserving the existing section/custom alias):
- `[[ADHD Product Strategy Framework]]` -> `[[ADHD Product Strategy Framework 20260616102600|ADHD Product Strategy Framework]]`
- `[[ADHD Product Strategy Framework#Introduction]]` -> `[[ADHD Product Strategy Framework 20260616102600#Introduction|ADHD Product Strategy Framework]]`
- `[[ADHD Product Strategy Framework|My Strategy]]` -> `[[ADHD Product Strategy Framework 20260616102600|My Strategy]]`
If multiple timestamped versions exist for the same clean title, the script resolves to the newest lexicographical timestamp. No manual approval is required.

### Completed TaskNotes Sweep
**Detection:** TaskNote files under `TaskNotes/Tasks/` where frontmatter contains `status: done`.
**Action:** Move the completed TaskNote to `TaskNotes/Archive/` (handling filename collisions robustly by appending incremental suffixes). To keep internal links intact, automatically scan the entire vault and rewrite any wikilinks pointing to the old task path (e.g., `[[TaskNotes/Tasks/old_stem]]` -> `[[TaskNotes/Archive/new_stem]]`).

## Report-only decisions

### Wrong folder (`## 🔴 Wrong folder`)
| Category | Expected location |
|----------|-------------------|
| `[[Readings]]` | `Inputs/Readings/` |
| `[[Meetings]]` | `Inputs/Meetings/` |
| `[[Emails]]` | `Inputs/Emails/` |
| `[[Slack]]` | `Inputs/Slack/` |
| `[[Sources]]` (compiled) | `Notes/` (not `Notes/Projects/`) |
| `[[Readings]]` on `Notes/` | Report — never auto-move |
| Maturity tiers | `Notes/` per triage table |

### Source linkage (`## ⚠️ Source linkage`)
Compiled `[[Sources]]` notes under `Notes/` must have `## Raw inputs` with at least one Reading wikilink.

### Legacy path links (`## ⚠️ Legacy path links`)
Wikilinks still containing `Logs/` after migration — feeds gap detection for `migrate_logs_to_inputs.py`.

### Citation & Reading URL Issues
URL validation on markdown links in `Inputs/Readings/` (legacy: `Logs/Sources/`, `Logs/Readings/`).

### ID conflicts / Missing ID / Missing daily_note
Report but never auto-fix.

*Note: The **Missing ID**, **Ghost Links**, and **Orphan Notes** checks are strictly restricted to the `Notes/` folder and its subfolders to prevent false-positive reports on temporary files (`Inbox/`, `TaskNotes/`, etc.).*

## Hygiene tiers

| Tier | Check | Owner | Schedule |
|------|-------|-------|----------|
| 1 | Auto-fix (Granola, tags, daily notes, entity auto-link) | `vault_hygiene.py` | Daily |
| 2 | Structural report (ID, ghosts, zero in+out orphans, folders, URLs) | `vault_hygiene_cron.py` | Daily 9pm |
| 3 | Semantic report (inbound orphans, stale Sources, promotion gaps, contradiction candidates) | `wiki_semantic_lint.py` | Monthly 1st + on-demand |

Cron job ids: tier 2 → `0b12d967fdf6`; tier 3 → `a3f8c2e91b04`.

| Workflow | Owner |
|----------|-------|
| Contradiction adjudication, Source refresh | `llm-wiki` integrate-full / agent on-demand |
| Reading→Source promotion | `llm-wiki` integrate-full only |
| Notes→Thoughts→Beliefs promotion | `obsidian-suggest-promotions` (unchanged) |

## What's intentionally skipped

| Folder | Reason |
|--------|--------|
| `Readwise/` | Plugin-managed, overwritten on sync |
| `Daily Notes/` | Backfilling daily_note is low-value |
| `Templates/` | Live Templater syntax — never auto-edit |
| `Utilities/Categories/` | Category definition notes legitimately live here |
| Root daily notes | Today's note in vault root is intentional |

## Known persistent issues (as of 2026-06-10)

- Today's daily note may have stale hardcoded `id` from template — check `Utilities/Templates/Daily Note.md`.
- `Cracking the Pm Career` collision in Readings/Sources — resolve during migration, do not auto-delete.
