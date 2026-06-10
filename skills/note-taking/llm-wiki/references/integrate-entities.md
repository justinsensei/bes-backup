# integrate-entities

Cron-safe, append-only pass that fans out each ingest to existing **contact** and **project** hub pages. Runs after integrate-light on every ingest pipeline (email, Slack, meeting reconcile).

**Update-only for both entity types** — never auto-create contact or project stubs in cron. Discovery stays in wind-down (Phase 2 contacts, Phase 2b projects).

## Script

```bash
python3 ~/.hermes/scripts/integrate_entities.py <ingest_rel_path> [--gist "one-line summary"]
```

Prints JSON report:

```json
{
  "updated": { "projects": ["K12 GTM"], "contacts": ["Endre"] },
  "skipped": ["K12 GTM:Timeline"],
  "unmatched": { "project_candidates": [], "contact_candidates": [] }
}
```

Unmatched project candidates accumulate at `~/.hermes/state/integrate_entities_unmatched.json` (keyed by date) for wind-down Phase 2b.

## Symmetric entity model

| Dimension | Contacts (`Contacts/` + typed `inbox/`) | Projects (`Notes/Projects/`) |
|-----------|----------------------------------------|------------------------------|
| Cron policy | Update existing only | Update existing only |
| Discovery | Morning briefing → wind-down Phase 2 | **Wind-down Phase 2b only** |
| Always append | `## Timeline` | `## Related inputs` + `## Timeline` |
| On decisions | `## Timeline` with resolution gist | Above + `## State` bullet |
| On meetings | `## Timeline` for attendees | Related inputs + Timeline; State if status language |
| Ingest frontmatter | — | Set `project: "[[Name]]"` on single high-confidence match |
| Aliases | Contact frontmatter | Project frontmatter |

## Canonical hub schemas

### Contact hub

```markdown
> Executive summary: Briefing for <Name>.

## State
- **Role:**
- **Company:**
- **Relationship:**

## Open Threads
-

---

## Timeline
- YYYY-MM-DD | [[source|title]] — <gist>
```

### Project hub

```markdown
> Executive summary: <One-line project purpose>.

Status: Active

## State
- <Current focus / latest status>

## Timeline
- YYYY-MM-DD | [[source|title]] — <gist>

## Related inputs
- YYYY-MM-DD | [[source|title]] — <gist>
```

If sections are missing, integrate-entities **creates them** (append-only). Never rewrites executive summary or Status line.

## Matching rules

| Signal | Contacts | Projects |
|--------|----------|----------|
| Slack | `participants` frontmatter; @mention names | `#channel` via channel map; title/body tokens; decision titles |
| Email | From/To/CC; names in summary | subject + body keywords; explicit instruction; `project:` frontmatter |
| Meeting | Auto-linked wikilinks; attendee names | Title tokens; body overlap; `### Related` on meeting note |

**Confidence:** append only when unambiguous (exact title/alias, channel-map hit, frontmatter `project:`, or ≥2 significant token overlap). Skip ambiguous keys.

## Channel → project map

`~/.hermes/state/channel-project-map.json`:

```json
{
  "product-leads": "SignLab Product",
  "classroom": "SignLab Classroom"
}
```

Checked before fuzzy fallback. Ship empty; Justin seeds entries over time.

## Section templates

**Related inputs / Timeline (projects and contacts):**

```markdown
- YYYY-MM-DD | [[shortest-path|Title]] — <gist>
```

**State (projects, decisions only):**

```markdown
- YYYY-MM-DD | Decision — <one-line resolution> ([[shortest-path|Title]])
```

## Idempotency

Skip if the same source wikilink already appears in the target section.

## Boundaries

- Never create new contact/project pages
- Never edit Input bodies (except ingest frontmatter `project:` metadata)
- Never truncate existing sections
- integrate-full **refreshes** State/summaries for a scope; integrate-entities is the per-ingest default

## Agent fallback

If report lists high-signal `unmatched.project_candidates` (decision notes, channel context, explicit names in title), agent may do one semantic project match and re-run append — but must not create pages.
