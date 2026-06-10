# integrate-light

Runs after every **explicit** ingest. Never modifies Input bodies.

## Output

Append one line to **`Utilities/log.md`** only. No `Utilities/index.md` updates. No daily notepad bullets.

## Log line format

```markdown
- HH:MM | slack | [[YYYY-MM-DD - Title]] | inbox/foo.md | [[2026-06-10 Tuesday]]
```

Fields: `time | type | wikilink-to-note | vault-relative-path | wikilink-to-daily-note`

The daily note wikilink comes from the ingested note's `daily_note` frontmatter, or is computed from the ingest date (`[[YYYY-MM-DD Weekday]]`).

## Type tokens

| Input | type token |
|-------|------------|
| Readwise / clipper → `Inputs/Readings/` | `reading` |
| Granola → `Inputs/Meetings/` | `meeting` |
| Email dispatch → `Inputs/Emails/` | `email` |
| Slack brain → `inbox/` or `Inputs/Slack/` | `slack` |
| integrate-query filed synthesis | `query` |
| integrate-full Source promotion | `source-compile` |

## Bootstrap

If `Utilities/log.md` does not exist, create it from `skills/note-taking/llm-wiki/templates/log.md` before appending. No historical backfill.

## Immutability

- Do not edit Reading/Email/Slack body text
- Do not create Source notes (that's integrate-full)
- Do not promote maturity tiers

## Cron post-step

After `bes-email-dispatch` or `slack-brain` cron completes filing:

1. Load this reference
2. Run integrate-light for each new file
3. Confirm `Utilities/log.md` has one new line per ingest with daily note wikilink
