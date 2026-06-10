# Taxonomy Migration — Logs → Inputs

Run on VM vault via `scripts/migrate_logs_to_inputs.py`. **Pause `bes-vault-sync` during bulk rename.**

## Folder map

| Old | New |
|-----|-----|
| `Logs/` | `Inputs/` |
| `Logs/Sources/` | `Inputs/Readings/` (merge) |
| `Logs/Readings/` | `Inputs/Readings/` (merge) |
| `Logs/Meetings/` | `Inputs/Meetings/` |
| `Logs/Emails/` | `Inputs/Emails/` |
| `Logs/Slack/` | `Inputs/Slack/` |
| `Logs/Granola/` | `Inputs/Meetings/` or archive |

## Category map

| Old | New |
|-----|-----|
| `[[Sources]]` on input paths | `[[Readings]]` |
| `Utilities/Categories/Sources.md` | Rewrite as compiled biblio (`Type: Notes/`) |
| (new) `Utilities/Categories/Readings.md` | `Type: Inputs/Readings/` |

## Script usage

```bash
# Dry-run (default)
python3 ~/.hermes/scripts/migrate_logs_to_inputs.py

# Execute
python3 ~/.hermes/scripts/migrate_logs_to_inputs.py --apply
```

Reports: files moved, categories changed, filename collisions, unresolved `Logs/` wikilinks.

Does **not** auto-create compiled Source notes — that's post-migration `integrate-full` work.

## Known collision

`Cracking the Pm Career` in both `Logs/Readings/` and `Logs/Sources/` — script reports conflict; manual dedupe required.

## VM follow-ups

1. Update `~/sync_readwise.py`: `vault/Logs/Sources/` → `vault/Inputs/Readings/`
2. `python3 ~/.hermes/scripts/semantic_pointer.py index`
3. Restart `bes-vault-sync`
4. `python3 ~/.hermes/scripts/vault_hygiene.py` — verify report sections

## Rollback

If migration fails mid-run with `--apply`, restore from vault git history (`bes-vault-sync` commits). Re-run dry-run before second attempt.

## Category note templates

### Readings.md (`Utilities/Categories/Readings.md`)

```markdown
---
category: "[[Categories]]"
---

# Readings

Type: Inputs/Readings/

Raw imported reading notes — Readwise exports, clippings, transcripts. Immutable input layer. Bes may edit frontmatter only; compilation to [[Sources]] happens via integrate-full.
```

### Sources.md (`Utilities/Categories/Sources.md`) — rewrite

```markdown
---
category: "[[Categories]]"
---

# Sources

Type: Notes/

Compiled bibliographical records — one per work (book, article, paper). Metadata + Bes-maintained summary. Links down to raw [[Readings]] via `## Raw inputs`. Feeds [[Concepts]] and [[Thoughts]]; distinct from maturity ladder.
```
