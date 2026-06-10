# Utilities Wiki Log

Paths relative to `$OBSIDIAN_VAULT_PATH` (vault root).

## Utilities/log.md

Chronological ingest log. Append-only lines grouped by date:

```markdown
# Wiki Log

Append-only record of ingests, compiles, and filed queries. Do not edit prior lines.

## YYYY-MM-DD

- HH:MM | slack | [[YYYY-MM-DD - Title]] | inbox/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | email | [[YYYY-MM-DD - Subject]] | Inputs/Emails/foo.md | [[2026-06-10 Tuesday]]
- HH:MM | source-compile | [[Source Title]] | Notes/Title.md | [[2026-06-10 Tuesday]]
```

Fields: `time | type | wikilink-to-note | vault-relative-path | wikilink-to-daily-note`

## integrate-light updates

- **log.md:** one line per ingest with daily note wikilink as last field
- No index.md maintenance
- No daily notepad bullets from integrate-light

## integrate-full updates

- Append `source-compile` lines to log.md when creating or refreshing Source notes
- No index.md maintenance

## Bootstrap

Copy `skills/note-taking/llm-wiki/templates/log.md` to `$OBSIDIAN_VAULT_PATH/Utilities/log.md` once before the first ingest. integrate-light creates the file from template if missing.

## Deferred: Utilities/index.md

A human browse catalog (`index.md`) is **not** maintained. Agents use `semantic_pointer.py`, folder taxonomy, and frontmatter instead. Revisit at semantic lint (item 5) only if a curated catalog becomes necessary — until then, `log.md` + semantic search suffice.
