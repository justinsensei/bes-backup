# Vault Audit — 2026-05-22

Full structural and frontmatter audit of `/home/justin.guest/Developer/obsidian-vault`.

## Vault size

| Folder | Files |
|--------|-------|
| Notebook/ | 324 |
| Daily Notes/ | 228 (archived) |
| Granola/ | 52 (summaries + transcripts) |
| Readwise/ | 112 |
| References/ | 38 |
| Templates/ | 7 |
| Root | 2 (today's daily note + Bes Setup.md) |
| **Total** | **~796** |

## Notebook breakdown

| Type | Count |
|------|-------|
| category: [[Meetings]] | 148 |
| category: [[People]] | 149 |
| category: [[Organizations]] | 1 |
| No category field | 25 |

- 153 notes are date-prefixed (`YYYY-MM-DD Title`) — these are meeting notes, correctly in Notebook.
- 171 notes have no date prefix — mix of People, Orgs, and uncategorized notes.

## Issues and resolution status

### ✅ FIXED — Misplaced daily notes in Notebook/ (5 files)
Files named `YYYY-MM-DD Weekday.md` (no topic after the weekday) accidentally in `Notebook/` instead of `Daily Notes/`. **Moved 2026-05-22** by vault_hygiene.py.

Files moved:
- `2026-05-20 Wednesday.md`
- `2026-05-19 Tuesday.md`
- `2026-05-18 Monday.md`
- `2026-03-17 Tuesday.md`
- `2025-10-01 Wednesday.md`

Detection going forward: filename `YYYY-MM-DD (Monday|Tuesday|…).md` with no extra words after the weekday.

### ⚠️ OPEN — Notebook notes missing category (20 files, post-fix)

Justin's decision (2026-05-22): **not every note needs a category**. Only object/entity notes do. These should not be force-categorized.

The `#project` and `#meeting` tags were NOT converted for notes without a date-prefix filename — too ambiguous. Example: `Dianne AI Workshop` had `#project` but was workshop pre-work, not a GTD project object.

Remaining uncategorized (not object notes, leave alone):
```
Sports fandom sucks 20260423102157.md
Dianne AI Workshop 20260420141613.md
ASL Facts.md
Tor's thoughts about Artemis-style code bots 20260514080631.md
Spring Performance 20260501134243.md
Single-agent for Clio for now 20260519111334.md
Response to Tor's thoughts on Artemis 20260514081149.md
Fighting with Jamie 20260519075445.md
AI Agents 2026 H1.md
Mobile Game Doctors.md
Cursor on Agent-Powered Dev 20260513084557.md
The Beginning of Infinity 20260506092057.md
Benchmarks - notification opt-in rate.md
Bot thoughts - Clio vs Artemis 20260513091336.md
PostHog → CustomerIO 20260423101926.md
Benchmarks - Subscription page CTR.md
Madeira 2026.md
Belize 2026.md
Benchmarks - user retention.md
Brain dump on Bes 20260519162610.md
```

### ⚠️ OPEN — Bes Setup.md in vault root
Sole project note with `category: "[[Projects]]"`. Lives in vault root by manage-projects convention — INTENTIONAL. Project notes go in root, not Notebook.

### ⚠️ OPEN — Readwise bulk import bug (112 files)
All 112 Readwise notes have identical malformed frontmatter from a one-time import run:
- `id: "2026052211:53 AM"` (should be `YYYYMMDDHHmmss`)
- `daily_note: "2026-05-22 Friday"` (plain string, not wikilink)

Do NOT patch manually — plugin overwrites on next sync. Fix belongs in Readwise import template/settings.

### ⚠️ OPEN — References/2026-06 Sienna PA Registration.md
No frontmatter at all (just a PDF embed). Needs `id` and `daily_note` added manually. Will show up in daily hygiene report until fixed.

### LOW PRIORITY — Daily Notes missing daily_note field
Many archived daily notes (in `Daily Notes/`) have `id` but no `daily_note` in frontmatter — they predate the convention. Low priority; filename is the date reference. Hygiene script skips `Daily Notes/` entirely.

## What hygiene script skips

- `Granola/` — own schema, third-party managed
- `Readwise/` — own schema, plugin-managed
- `Daily Notes/` — backfilling `daily_note` is low-value
- `Templates/` — contains Templater syntax, never auto-edit
- `Categories/` — legitimately live there, not Notebook
- `.trash/`, `.cursor/`, `.claude/` — system/IDE metadata
