# Utilities Index & Log

Paths relative to `$OBSIDIAN_VAULT_PATH` (vault root).

## Utilities/log.md

Chronological ingest log. Append-only lines:

```markdown
## YYYY-MM-DD

- HH:MM | reading | [[Title]] | Inputs/Readings/Title.md
- HH:MM | meeting | [[YYYY-MM-DD - Title]] | Inputs/Meetings/...
- HH:MM | email | [[YYYY-MM-DD - Subject]] | Inputs/Emails/...
- HH:MM | slack | [[YYYY-MM-DD - Title]] | Inputs/Slack/...
- HH:MM | query | [[Synthesis Title]] | Notes/...
- HH:MM | source-compile | [[Source Title]] | Notes/Title.md
```

## Utilities/index.md

Curated map of vault knowledge. Suggested sections:

```markdown
# Vault Index

## Inputs
### Readings
- [[Title]] — one-line

### Meetings
### Emails
### Slack

## Sources
- [[Compiled Source Title]] — links to Readings

## Concepts
## Projects
## Entities
### People
### Organizations
```

## integrate-light updates

- **log.md:** one line per ingest
- **index.md:** add entry under correct section; do not remove existing entries
- **Daily note:** notepad bullet with wikilink + gist

## integrate-full updates

- Refresh Source entries under `## Sources`
- Add cross-refs under Concepts/Projects when compile creates new links
- Log `source-compile` lines in log.md
