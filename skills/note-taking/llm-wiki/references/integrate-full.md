# integrate-full

Multi-page compile pass. **On-demand or wind-down EIIRP Step 5 only** — never from cron alone.

## Manual triggers

- "integrate this"
- "wiki integrate today"
- "compile today's ingests"
- "integrate [[Project Name]]"
- "run wiki lint" (starts with structural check via obsidian-hygiene, then semantic)

Confirm with Justin before bulk edits to mature notes.

## Reading → Source promotion

For each new/modified Reading in scope:

1. Check if compiled Source exists in `Notes/<Title>.md` with `category: "[[Sources]]"`
2. If missing, create from template (see SKILL.md Source note template)
3. If exists, refresh `## Summary` from Reading highlights
4. Ensure `## Raw inputs` links to all related Reading note(s)

**Filename:** `Title.md` under `Notes/` — no timestamp prefix.

## Project / contact compile

- Link today's ingests to active `[[Projects]]` hubs where contextually clear
- Add back-links on project notes under `## Related inputs` (append only)
- Do not relocate contacts — inbox rule unchanged

## Contradiction scan (lightweight)

Flag when:
- Two Sources describe the same work with conflicting metadata
- A Concept contradicts its linked Source summary
- A Belief conflicts with a linked Concept

Report only — do not auto-resolve. Full semantic lint: `references/lint.md`.

## What integrate-full does NOT do

- Auto-promote Notes→Thoughts→Concepts→Beliefs (`obsidian-suggest-promotions`)
- Modify immutable Input bodies (Readings/Emails/Slack)
- Run without explicit trigger or wind-down Step 5 approval

## Wind-down integration

Phase 4 EIIRP Step 5: after Justin approves triage report, run integrate-full for today's Reading ingest scope. Offer Source note creation for items surfaced in Phase 3 Reading Review.

When creating or refreshing a Source note, append a `source-compile` line to `Utilities/log.md` (see [index-and-log.md](index-and-log.md)). No `Utilities/index.md` maintenance.
