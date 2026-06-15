---
name: obsidian-hygiene
description: Use when running vault hygiene checks, interpreting vault_hygiene.py output, or triaging structural vault issues (IDs, folders, ghost links, source linkage). Structural lint only — semantic contradictions belong to llm-wiki.
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, hygiene, vault, lint, triage]
    related_skills: [obsidian, llm-wiki, wind-down, morning-briefing]
---

# Obsidian Vault Hygiene

## Overview

Operator docs for `vault_hygiene.py` and its cron wrapper. Enforces the three-layer taxonomy (Inputs → Sources → maturity tiers) with auto-fixes for safe structural issues and reports for human triage.

For the background real-time git synchronization process, see [references/vault-synchronization.md](references/vault-synchronization.md).
For mass suffix-ID note renaming and link-repair migrations, see [references/rename-notes-id-suffix-migration.md](references/rename-notes-id-suffix-migration.md) and the utility script [scripts/rename_notes_append_id.py](scripts/rename_notes_append_id.py).

## When to Use

- Morning briefing Job B (tier-1 auto-fixes)
- Wind-down EIIRP Step 4 (`python3 ~/.hermes/scripts/vault_hygiene.py`)
- Interpreting Telegram alerts from cron job `0b12d967fdf6`
- After taxonomy migration — verify wrong-folder and legacy-path reports

**Don't use for:** semantic contradiction scans, Reading→Source promotion, or maturity-tier promotion (use `llm-wiki` and `obsidian-suggest-promotions`).

## Vault Path

`OBSIDIAN_VAULT_PATH` from `~/.hermes/.env` (typically `/home/justin.guest/vault` on bes-vm).

## Step 1 — Run hygiene

```bash
python3 ~/.hermes/scripts/vault_hygiene.py
```

**Auto-fix tier (silent unless printed):**
- **Filename Capitalization & Spacing Healing:** Auto-corrects lowercase initialisms/acronyms (`AI`, `ADHD`, `B2C`, `B2B`, `AB`, `GTM`, `ASL`, `DAU`, `WSP`, `SP`, `PR`, `OKR`, `OKRs`, `K12`, `EdTech`, `SPED`), proper nouns (`Amazon`, `Costco`, `PostHog`, `SignLab`, `SmartPass`, `Duolingo`, `PowerSchool`, `Lingvano`, `Raptor`, `Breezeway`), grammar spacing (like `doesn t` -> `doesn't`), and dynamically harvested contact names (filtered through common-word blacklists). Renames on disk and heals all matching wikilink targets across the vault.
- Reconcile Granola `Meetings/` → `Inputs/Meetings/` with `category: "[[Meetings]]"`
- **Dynamic ID-Suffix Fallback Resolution:** Automatically resolves any wikilink containing a 14-digit ID suffix to its active disk path (even if the title text was renamed or kebab-cased) to suppress false-positive Ghost Link warnings.
- Auto-link entities in meeting bodies and recent daily notes (last 7 days)
- Legacy `[[Sources]]` on `Inputs/Readings/` → `[[Readings]]`
- Misplaced daily notes → `Daily Notes/`
- Tag-to-category conversion per design doc

**Report tier (stdout):**

| Section | Severity | Meaning |
|---------|----------|---------|
| `## 🔴 ID conflicts` | Red | Duplicate `id` values |
| `## 🔴 Non-unique aliases` | Red | Same alias on multiple contacts |
| `## 🔴 Missing ID` | Red | Note lacks `id` |
| `## 🔴 Missing daily_note` | Red | Note lacks `daily_note` |
| `## 🔴 Wrong folder` | Red | Category/folder mismatch |
| `## ⚠️ Ghost Links` | Warning | Wikilink target missing |
| `## ⚠️ Orphan Notes` | Warning | Zero in/out links |
| `## ⚠️ Source linkage` | Warning | Compiled Source missing `## Raw inputs` |
| `## ⚠️ Citation & Reading URL Issues` | Warning | (Disabled) Broken URLs in Readings - no longer audited |
| `## ⚠️ Legacy path links` | Warning | Wikilinks still use `Logs/` paths |

Cron (`vault_hygiene_cron.py`) surfaces all 🔴 and taxonomy-relevant ⚠️ sections to Telegram.

## Three-layer immutability

| Path | Body edits allowed? |
|------|---------------------|
| `Inputs/Readings/`, `Emails/`, `Slack/` | Frontmatter only — never auto-link or compile |
| `Inputs/Meetings/` | Entity auto-link + `### Related` project sections |
| `Notes/` with `[[Sources]]` | Full body (integrate-full keeps summary current) |
| Maturity notes in `Notes/` | Full body |

## Category placement quick reference

| Category | Folder |
|----------|--------|
| `[[Readings]]` | `Inputs/Readings/` |
| `[[Meetings]]` | `Inputs/Meetings/` |
| `[[Emails]]` | `Inputs/Emails/` |
| `[[Slack]]` | `Inputs/Slack/` |
| `[[Sources]]` (compiled) | `Notes/` |
| `[[Thoughts]]`, `[[Concepts]]`, etc. | `Notes/` per obsidian triage table |

## Hygiene tiers

| Tier | Owner | Schedule |
|------|-------|----------|
| Tier 1 auto-fix | `vault_hygiene.py` | Daily (morning briefing Job B, wind-down, 9pm cron) |
| Tier 2 structural report | `vault_hygiene_cron.py` → Telegram | Daily 9pm when issues |
| Tier 3 semantic report | `wiki_semantic_lint.py` | Monthly 1st + on-demand |

- **obsidian-hygiene:** tiers 1–2 (this skill)
- **llm-wiki `references/lint.md`:** tier 3 — orphans (inbound), stale summaries, contradictions
- **obsidian-suggest-promotions:** maturity ladder — unchanged

---

## Environment Diagnostics (Smoke Tests)
To prevent silent background cron or tooling failures (such as expired API keys or path changes), run the environmental diagnostics utility at system startup or on-demand:
```bash
python3 ~/.hermes/scripts/smoke_test_env.py
```
This utility verifies:
- Write access and existence of the active vault path (`/home/justin.guest/vault`).
- Python dependency environment integrity (such as `requests`, `yaml`, `dotenv` packages).
- Network reachability and authentication of critical integrations (**Todoist**, **Slack**, **Linear**, **Readwise**, and **OpenRouter**) with graceful timeouts (5s).
- Outputs a formatted live console checklist and saves a structured, machine-readable JSON log at `~/.hermes/health_report.json`.

## Common Pitfalls

1. Running hygiene before migration — expect `Logs/` paths in reports; feature-detection handles both.
2. Expecting auto-link in Readings — immutability guard prevents it.
3. Confusing Layer 2 `[[Sources]]` (compiled, `Notes/`) with raw Readings (`Inputs/Readings/`).
4. Auto-moving wrong-folder notes — hygiene reports only; wind-down EIIRP triages moves.
5. **Multi-Match Unpacking Gotchas**: In the underlying matching pipeline of `vault_entities.py` (which `vault_hygiene.py` relies on for Granola reconciliations), if multiple project hubs score equally, trying to unpack the candidate list as a tuple (`for _, ent in top_hits`) rather than iterating plain dictionaries (`for ent in top_hits`) triggers a `ValueError: too many values to unpack (expected 2)`.
6. **Mismatched Test Directories**: Contact paths in the vault migrated from root `/Contacts/` to `/Notes/Contacts/`. If entity unit tests (e.g., `test_integrate_entities.py`) fail to align mock directories with `/Notes/Contacts/`, contact matches will fail silently. Always keep test environments aligned with active production schemas.
7. **Intermediate Unmasking in Auto-Linkers**: When performing multi-pass regex replacements (such as wrapping contacts in wikilinks based on an alias list), never unmask intermediate replacements during the key-matching loop. Newly generated links must remain masked (e.g. as `__NEW_LINK_MASK_i__`) until *all* pattern passes are completed; otherwise, nested elements (e.g., matching a shorter alias inside a newly wrapped longer link) will trigger infinite bracket nesting (e.g., `[[[[[[[[SignLab]]]]]]]]`).
8. **External URL Auditing Disabled**: Auditing external URLs/citations in Readings is disabled per user request. Only internal wikilinks are audited during hygiene runs.
9. **Wikilinks in YAML Frontmatter**: Bracketed wikilinks in YAML frontmatter must always be enclosed in double quotes (e.g. `category: "[[People]]"`). Plain brackets without quotes (e.g. `category: [[People]]`) will be treated as flow sequences by YAML parsers, causing syntax exceptions. `vault_hygiene.py` includes a Tier-1 auto-wrapping regex rule to automatically catch and heal unwrapped links.
10. **Inappropriate Capitalization Overruns**: In filename capitalization auto-healing, harvesting words from contacts dynamically (e.g. `Haiku Learning` -> `learning`) can cause common English words (like `learning`, `design`, `pittsburgh`) to become inappropriately capitalized in filenames. Always maintain a robust `BLACKLIST_WORDS` set inside `vault_hygiene.py` to prevent standard words from being mis-identified as proper nouns.
11. **Cron/Scheduler Timeout and Subprocess Mismatch**: Background cron wrappers (such as `vault_hygiene_cron.py`) running in `no_agent: true` mode are subject to a strict 120s script execution limit enforced by the scheduler. If the script triggers long-running tasks like `semantic_pointer.py index` as a subprocess (which has a 500s timeout to generate embeddings via external APIs), the scheduler will forcefully kill the parent process mid-execution. Always decouple intensive operations like semantic indexing from daily sync/hygiene runs (e.g., schedule them as separate low-priority crons), and ensure all subprocesses run with explicit timeouts (`timeout=100`) to fail-fast. Additionally, be aware that `approvals.cron_mode: deny` automatically blocks arbitrary local code execution (`execute_code`) and shell commands with execution flags (`-e` or `-c`) from running unattended in background tasks.

12. **Commented-out Wikilinks**: The script now ignores wikilinks inside HTML comments (`<!-- [[link]] -->`). This is useful for temporarily disabling a link without deleting it. The regex `re.findall(r'<!--.*?-->|\[\[([^\]]+)\]\]', text)` is used to find all wikilinks, and then the commented-out ones are skipped.

13. **Nested Double-Brackets Link Corruption**: Highly nested brackets (e.g., `[[[[Contact [[Contact SuffixID...`) can occur during complex multi-pass link-wrapping operations or copy-pasting. These corruptions block standard parsed target lookup and must be manually or programmatically unnested before standard resolution can work.

## How to Resolve Ghost Links

When the hygiene script reports "Ghost Links", it means there are wikilinks pointing to notes that don't exist. Here's the process to resolve them:

1.  **Identify Daily Notes**: If the ghost link is a daily note (e.g., `[[2026-03-01 Sunday]]` or `[[2025-06-26 Thursday]]`), create the missing placeholder daily note using the standard template in `Daily Notes/` (id should be `'YYYYMMDD000000'`).
2.  **ID-Based Healing & Resolution**: For obsolete kebab-case links that contain a 14-digit timestamp ID (e.g., `[[the-habit-loop-20250612134304]]` which contains `20250612134304`), `vault_hygiene.py` now natively implements an in-memory resolution fallback to suppress false ghost link alerts. However, the links inside the markdown files should still be permanently healed.
    - **Automated Script**: Run `python3 ~/.hermes/skills/note-taking/obsidian-hygiene/scripts/heal_kebab_links.py` to automatically heal all ID-matched ghost links in-place across the vault.
3.  **Fuzzy/Casing Healing**: Many ghost links are obsolete kebab-case links from previous schema eras, or have minor casing/punctuation discrepancies (e.g., Torres vs (Torres)).
    - **Normalization Rule:** Convert both the ghost link target and all existing note basenames in the vault to a normalized, lowercase alphanumeric-only string (strip all spaces, hyphens, parentheses, etc. e.g., `continuous-interviewing-torres-20250723173842` and `Continuous interviewing (Torres) 20250723173842` both normalize to `continuousinterviewingtorres20250723173842`).
    - If a unique normalized match exists, heal the link.
3.  **Heal Links Safely**: Perform case-insensitive search and replace of the link targets inside the referencing files.
    - **Safeguard Section Anchors & Display Text:** Use a regex pattern like `\[\[\s*<old_target>\s*(?P<extra>[|#][^\]]*)?\]\]` to capture any trailing section anchors or display aliases (e.g. `[[old#section|display]]`), replacing with `[[<new_target>\g<extra>]]`.
4.  **Comment Out Remaining**: For other ghost links with no fuzzy counterpart, either comment them out (`<!-- [[link]] -->`) or verify if they represent a note that needs to be created.

## Verification Checklist


- [ ] Script completes without traceback
- [ ] Granola meetings land in `Inputs/Meetings/` with `[[Meetings]]`
- [ ] No `[[Sources]]` left on input Reading paths
- [ ] Cron Telegram includes wrong-folder / source-linkage when present
- [ ] Semantic re-index triggered at end of run
