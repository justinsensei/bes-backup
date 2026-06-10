---
name: did-i-already-do-this
description: Use when working with did i already do this. Look up whether Justin has
  already done something he may have forgotten.
triggers:
- did I already do X
- have I done X
- did I send / write / finish / complete X
- did I ever X
version: 1.0.0
author: Bes
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - did
---

# Did I Already Do This?

Justin captures completed work in **Todoist** or **Obsidian**. Check in this order:

## 1. Todoist completed tasks
Use `mcp_todoist_find_completed_tasks` with a relevant keyword search. Cast a wide date range if unsure when it might have happened.

## 2. Obsidian notes / work logs
Use the `obsidian` skill to search notes. Work logs, meeting notes, and project notes are the most likely places. Search by keyword; also check dated work log entries if a rough timeframe is known.

## 3. Session search (last resort)
Use `session_search` to scan past conversation transcripts. Useful if the thing was discussed or decided here but may not have been formally captured anywhere.

## Notes
- If nothing turns up in any of the three, say so plainly — don't speculate that it was done.
- If you find it, report where you found it and any relevant details (date, project, note title).
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
