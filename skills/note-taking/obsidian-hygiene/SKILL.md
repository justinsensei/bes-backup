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
- Reconcile Granola `meetings/` → `Inputs/Meetings/` with `category: "[[Meetings]]"`
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
| `## ⚠️ Citation & Reading URL Issues` | Warning | Broken URLs in Readings |
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

## Hygiene vs llm-wiki

- **obsidian-hygiene:** structural (this skill)
- **llm-wiki `references/lint.md`:** semantic (contradictions, stale summaries) — on demand
- **obsidian-suggest-promotions:** maturity ladder — unchanged

## Common Pitfalls

1. Running hygiene before migration — expect `Logs/` paths in reports; feature-detection handles both.
2. Expecting auto-link in Readings — immutability guard prevents it.
3. Confusing Layer 2 `[[Sources]]` (compiled, `Notes/`) with raw Readings (`Inputs/Readings/`).
4. Auto-moving wrong-folder notes — hygiene reports only; wind-down EIIRP triages moves.

## Verification Checklist

- [ ] Script completes without traceback
- [ ] Granola meetings land in `Inputs/Meetings/` with `[[Meetings]]`
- [ ] No `[[Sources]]` left on input Reading paths
- [ ] Cron Telegram includes wrong-folder / source-linkage when present
- [ ] Semantic re-index triggered at end of run
