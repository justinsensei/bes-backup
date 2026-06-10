# integrate-light

Runs after every **explicit** ingest. Never modifies Input bodies.

## Output

Append one line to **`Utilities/log.md`** only. No `Utilities/index.md` updates. No daily notepad bullets.

## Bootstrap (first run)

If `Utilities/log.md` does not exist, create it from `skills/note-taking/llm-wiki/templates/log.md` (copy to vault after `bes-pull`). Start with the header only — no fake history.

## Log line format

Group by date heading. Fields: `time | type | wikilink-to-note | vault-relative-path | wikilink-to-daily-note`

```markdown
## YYYY-MM-DD

- HH:MM | slack | [[YYYY-MM-DD - Title]] | inbox/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | email | [[YYYY-MM-DD - Subject]] | Inputs/Emails/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | reading | [[Reading Title]] | Inputs/Readings/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | meeting | [[YYYY-MM-DD - Title]] | Inputs/Meetings/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | query | [[Synthesis Title]] | Notes/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | source-compile | [[Source Title]] | Notes/Title.md | [[2026-06-10 Tuesday]]
```

Daily note wikilink: use the ingested note's `daily_note` frontmatter value, or compute from ingest date.

## Per input type

| Type | `type` token | Typical path |
|------|--------------|--------------|
| Readwise / clipper | `reading` | `Inputs/Readings/` |
| Granola meeting | `meeting` | `Inputs/Meetings/` |
| Email log | `email` | `Inputs/Emails/` |
| Slack (inbox or triaged) | `slack` | `inbox/` or `Inputs/Slack/` |

## Immutability

- Do not edit Reading/Email/Slack body text
- Do not create Source notes (that's integrate-full)
- Do not promote maturity tiers
- Do not modify daily notes (Slack cron step 7 may add its own notepad bullet separately — that is not integrate-light)

## Cron post-step

After `bes-email-dispatch` or `slack-brain` cron completes filing:

1. Load this reference
2. Run integrate-light for each new file
3. Run `python3 ~/.hermes/scripts/integrate_entities.py <ingest_rel_path> [--gist "..."]` for each new file
4. Confirm one new line appended to `Utilities/log.md` with correct daily note wikilink
5. Report hub updates: `→ updated [[Project]], [[Contact]]` when JSON report lists matches
