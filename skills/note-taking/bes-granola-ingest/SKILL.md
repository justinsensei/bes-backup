---
name: bes-granola-ingest
description: Use when working with bes granola ingest. Sweep, sanitize, and ingest
  machine-generated meeting transcripts and notes from Granola into vault/Logs/Meetings/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - granola
    - meetings
    - ingest
    - logs
    related_skills:
    - obsidian
    - obsidian-logs
    - obsidian-meetings
platforms:
- linux
---

# Bes Granola Ingest

Manages the ingestion pipeline for machine-generated meeting logs and transcripts synced from your Granola app. The sync directory acts as a landing zone, while this skill sweeps, formats, and files them.

## Sync Directories
- **Raw Landing Zone:** `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/meetings/`
- **Processed Destination:** `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Logs/Meetings/YYYY-MM-DD - Spaced Title.md`

---

## Reconciliation Workflow

Meetings synced from Granola are swept automatically by the vault hygiene script (`vault_hygiene.py` or the custom `reconcile_granola.py` wrapper):

1. **Scan Source:** Scans `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/meetings/` for raw notes.
2. **Inject Standard Frontmatter:** Extracts the date from the file metadata or title, then inserts a standard numeric `id` and a symmetrical `daily_note` link:
   ```yaml
   ---
   id: 'YYYYMMDDHHmmss'
   daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
   category: "[[Meetings]]"
   ---
   ```
3. **Format Cleanup:** Strips double hyphens, double rules, and extraneous sync headers.
4. **Relocation:** Saves the sanitized file to `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Logs/Meetings/` and deletes the raw file from the landing zone `/meetings/`.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
