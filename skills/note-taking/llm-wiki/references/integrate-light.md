# integrate-light

Runs after every **explicit** ingest. Never modifies Input bodies.

## Outputs

1. **`Utilities/log.md`** — append ingest line with timestamp, type, title, path
2. **`Utilities/index.md`** — update relevant section (Inputs, Sources, Projects, Entities)
3. **Daily note notepad** — one bullet under `## 🗒 Notepad`

## Per input type

### Reading (Readwise, clipper → `Inputs/Readings/`)

```markdown
* <HH:MM> | Reading ingested: [[Reading Title]] — <one-line gist>
```

Index: add under `## Inputs / Readings` if not present.

### Meeting (Granola → `Inputs/Meetings/`)

```markdown
* <HH:MM> | Meeting logged: [[YYYY-MM-DD - Title]] — <one-line gist>
```

Index: `## Inputs / Meetings`

### Email (`Inputs/Emails/`)

```markdown
* <HH:MM> | Email logged: [[YYYY-MM-DD - Subject]] — <one-line gist>
```

Index: `## Inputs / Emails`

### Slack (`Inputs/Slack/` or inbox → triaged)

```markdown
* <HH:MM> | Slack logged: [[YYYY-MM-DD - Title]] — <one-line gist>
```

Index: `## Inputs / Slack`

## Immutability

- Do not edit Reading/Email/Slack body text
- Do not create Source notes (that's integrate-full)
- Do not promote maturity tiers

## Cron post-step

After `bes-email-dispatch` or `slack-brain` cron completes filing:

1. Load this reference
2. Run integrate-light for each new file
3. Confirm `Utilities/log.md` and index updated
