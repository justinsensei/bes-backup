---
name: llm-wiki
description: Use when ingesting inputs into the vault, compiling Readings into Source notes, integrating knowledge across pages, running wiki health checks, or filing durable query answers. Orchestrates Karpathy-style compounding wiki maintenance across Inputs / Sources / note-maturity tiers.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [wiki, knowledge, integration, sources, readings, compile]
    related_skills: [obsidian, obsidian-hygiene, work-log, bes-email-dispatch, wind-down, morning-briefing, did-i-already-do-this]
---

# llm-wiki — Compounding Vault Knowledge

## Overview

Orchestrates Karpathy-style wiki maintenance across Justin's three-layer taxonomy: immutable **Inputs**, compiled bibliographical **Sources**, and the unchanged **maturity ladder** (Notes→Thoughts→Concepts→Beliefs→References). Hybrid integration: light log append after ingest, full compile on demand, query synthesis for durable answers.

Deep reference: [architecture](references/architecture.md) | [integrate-light](references/integrate-light.md) | [integrate-entities](references/integrate-entities.md) | [integrate-full](references/integrate-full.md) | [integrate-query](references/integrate-query.md) | [lint](references/lint.md) | [index-and-log](references/index-and-log.md) | [taxonomy-migration](references/taxonomy-migration.md)

## When to Use

- After explicit ingest (email dispatch, Slack brain, Readwise, Granola reconcile)
- "integrate this", "wiki integrate today", "compile today's ingests"
- Wind-down EIIRP Step 5 (integrate-full)
- Research Q&A that should persist in the vault (integrate-query): "what do my notes say about…", "compare X and Y", "synthesize everything on Z"
- "run wiki lint" (semantic; structural → obsidian-hygiene)

**Don't use for:** daily work logs (work-log), structural hygiene (obsidian-hygiene), maturity promotion (obsidian-suggest-promotions — **unchanged**).

## Vault Path

`OBSIDIAN_VAULT_PATH` from `~/.hermes/.env`. Input paths use `Inputs/` (legacy `Logs/` accepted during migration).

## Three Layers

| Layer | Folder | Category | Immutable? | Bes edits body? |
|-------|--------|----------|------------|-----------------|
| 1 Inputs | `Inputs/Readings/` etc. | `[[Readings]]`, `[[Meetings]]`, `[[Emails]]`, `[[Slack]]` | Yes | Metadata only |
| 2 Compiled | `Notes/` | `[[Sources]]` | No | Yes (summary) |
| 3 Maturity | `Notes/` (+ subfolders) | Notes, Thoughts, Concepts, Beliefs, References, Decisions, Memories, Projects | No | Yes |

**Layer 3 ladder is unchanged.** Promotion Notes→Thoughts→Beliefs stays in `obsidian-suggest-promotions`. llm-wiki does not auto-promote maturity tiers.

**Link direction:** Concept → Source → Reading. Never Concept → Reading when Source exists.

## Integration Passes

| Pass | When | Actions |
|------|------|---------|
| **integrate-light** | Every explicit ingest; cron post-steps | Append `Utilities/log.md` with daily note wikilink. **Never modify Input bodies.** No index or notepad updates. |
| **integrate-entities** | After integrate-light; meeting reconcile | Update existing projects' State sections on decisions/status-changes only. Timelines are disabled. Update-only — no stub creation. |
| **integrate-full** | Wind-down Step 5; manual triggers | Reading→Source promotion, project/contact cross-refs, contradiction flags |
| **integrate-query** | Interactive durable Q&A | Search → synthesize → write to `inbox/` when durability met (3+ notes, comparison/decision analysis, cross-project connection, explicit "file this", same topic twice) → print complete note in channel, log append. See [integrate-query.md](references/integrate-query.md). Template: [query-synthesis.md](templates/query-synthesis.md). |

Cron runs **integrate-light + integrate-entities**. No auto-vault from raw streams.

## integrate-light (default after ingest)

See [integrate-light.md](references/integrate-light.md).

1. Append one line to `Utilities/log.md` (time, type, note wikilink, path, daily note wikilink)
2. Create `Utilities/log.md` from `templates/log.md` if missing (see [integrate-light.md](references/integrate-light.md))
3. Run `integrate_entities.py` on the ingest (see [integrate-entities.md](references/integrate-entities.md))
4. Confirm hub updates from JSON report; set ingest `project:` frontmatter when script matches exactly one project

**Immutability:** Do not edit bodies under `Inputs/Readings/`, `Inputs/Emails/`, `Inputs/Slack/`.

## integrate-full (on demand)

See [integrate-full.md](references/integrate-full.md).

**Manual triggers:** "integrate this", "wiki integrate today", "compile today's ingests", "integrate [[Project]]", "run wiki lint".

**Reading → Source promotion:** For each scoped Reading, create or update `Notes/<Title>.md`:

```yaml
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Sources]]"
---
```

```markdown
# Title

- **Author:**
- **URL:**
- **Type:** book | article | paper | video

## Summary
Bes-compiled synthesis (kept current by integrate-full).

## Raw inputs
- [[Reading note title]]

## Related
- [[Concept or Project links]]
```

Confirm with Justin before bulk mature-note edits.

## integrate-query

See [integrate-query.md](references/integrate-query.md). Search → synthesize → write to `inbox/` for manual review when durability threshold met → print complete note in channel and run integrate-light log append. Template: [query-synthesis.md](templates/query-synthesis.md). Interactive sessions only — not cron.

## Semantic lint (tier-3)

See [lint.md](references/lint.md).

**Monthly cron** (`wiki_semantic_lint_cron.py`, 1st of month): deterministic orphans, stale summaries, promotion gaps, link chains, contradiction candidates → `Utilities/reports/semantic-lint-*.md` + `~/.hermes/state/semantic_lint_last.json`.

**On-demand:** Run `vault_hygiene.py` first (structural), then `wiki_semantic_lint.py`. Agent reviews contradiction candidates — never auto-edit Beliefs.

## Boundaries

| Skill | Role |
|-------|------|
| work-log | Daily activity — not wiki compile |
| obsidian-hygiene | ID, folders, ghosts, URLs |
| obsidian-suggest-promotions | Maturity ladder — **do not modify** |
| bes-email-dispatch | Ingest emails → then integrate-light |

## Taxonomy migration

One-time `Logs/` → `Inputs/` via `scripts/migrate_logs_to_inputs.py`. See [taxonomy-migration.md](references/taxonomy-migration.md). Category templates for `Utilities/Categories/Readings.md` and rewritten `Sources.md` included there.

## Common Pitfalls

1. Compiling into Reading bodies — Inputs are immutable; compile to Source notes only.
2. Skipping integrate-light after cron ingest — log drifts; ingests become untraceable.
3. Auto-promoting maturity tiers — belongs to obsidian-suggest-promotions, not llm-wiki.
4. Linking Concepts directly to Readings — use Source as intermediary.
5. Running integrate-full from cron without approval — light pass only in autonomous runs.
6. Generating dense, bulky notes during query synthesis — keep integrations and syntheses highly atomic and focused, avoiding oversized multi-topic summaries.
7. Attempting to write timeline or related inputs lists to contact or project notes — automated timelines are disabled in favor of native backlinks; only update project `## State` on decisions/status.

## Verification Checklist

- [ ] integrate-light appended log line with daily note wikilink
- [ ] integrate-entities updated matched hub pages (or report shows unmatched only)
- [ ] No Input body edits on Readings/Emails/Slack
- [ ] Compiled Sources have `## Raw inputs` with Reading links
- [ ] Layer 3 notes untouched unless integrate-full explicitly scoped
- [ ] obsidian-hygiene run for structural baseline before semantic lint
- [ ] integrate-query: filed note exists in `inbox/` with Question, Synthesis, Sources consulted sections
- [ ] integrate-query: printed the complete created note in the chat channel for review
- [ ] integrate-query: log line appended with `query` token
- [ ] integrate-query: Sources consulted section populated with upstream wikilinks
