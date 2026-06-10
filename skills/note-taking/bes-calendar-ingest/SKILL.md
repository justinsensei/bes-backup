---
name: bes-calendar-ingest
description: Use when working with bes calendar ingest. Sync, query, and ingest calendar
  events from Google Calendar (work and personal) to drive daily schedule planning
  and automated work logs.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - calendar
    - google-workspace
    - ingest
    - logs
    related_skills:
    - google-workspace
    - work-log
    - morning-briefing
    - wind-down
platforms:
- linux
---

# Bes Calendar Ingest

Handles Google Calendar syncs across all of your accounts (work, personal-main, personal-junk) to drive schedule-planning, morning briefings, and automated work log accomplishments.

## Credentials & Tokens
- Tokens are located at: `~/.hermes/google_tokens/{work,personal-main,personal-junk}.json`
- Wrapped in the cross-account script: `~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py`

---

## Querying Schedule (Read-Only)

To retrieve schedule events for a specific timeframe (e.g. today or tomorrow):
```bash
python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all calendar list --start <YYYY-MM-DD>T00:00:00<OFFSET> --end <YYYY-MM-DD>T23:59:59<OFFSET> --max 50
```

This schedule feeds directly into:
1. **Today's Daily Note:** Populates `## 📅 Schedule & Events`.
2. **Morning Briefing:** Drives the active schedule briefing.
3. **Daily Work Log:** Compiles and reconciles meeting attendances.

---

## Scheduling Events (Write Access)

Bes has write access to Google Calendar. You can directly schedule events on Justin's behalf (e.g., during briefings or from forwarded email instructions) rather than creating tasks in Todoist:
```bash
python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account work|personal-main calendar create --summary "Event Title" --start "2026-06-09T14:00:00" --end "2026-06-09T15:00:00" --description "Context..."
```
*Note: Specify the single correct target account; do not use `--account all` for write operations.*
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
