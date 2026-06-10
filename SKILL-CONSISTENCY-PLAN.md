# Bes Skill Consistency Plan

**Executor:** Cursor agent in `bes-backup` (Justin). **Not Bes.** Bes is the consumer of the finished authoring skill + validator going forward.

**Deliverable:** Work happens in the local git repo; VM deploy (`~/.hermes/skills/`, `~/.hermes/scripts/`) is documented for Justin to run after merge.

Each phase ends with `python3 scripts/validate_skills.py` passing at the configured strictness for that phase (run locally in `bes-backup`).

See `.cursor/plans/bes_skill_consistency_b10c6485.plan.md` for the full plan with todos. This file is the repo-local copy for reference.

## Post-merge VM deploy (Justin / Bes)

1. Deploy `scripts/validate_skills.py` → `~/.hermes/scripts/`
2. Sync `bes-backup/skills/` → `~/.hermes/skills/` (git pull or rsync)
3. Sync `bes-backup/scripts/` → `~/.hermes/scripts/`
4. Fresh Bes session: `skill_view` on `bes-skill-authoring`, `work-log`, `morning-briefing`
5. Optional: morning briefing cache recovery smoke test (read-only)

## Completed (Cursor agent)

- Rewrote `bes-skill-authoring` (v2) with two-tree model and validator workflow
- Added `scripts/validate_skills.py` and `scripts/normalize_skills.py`
- Normalized 57 skills; `validate_skills.py --strict` passes locally (0 errors, 0 warnings)
- Removed duplicate scripts: `fetch_slack_brains.py` (skill copy), `check_vault_signals.py` (skill copy), `semantic_pointer.py` (skill copy)
- Generated `skills/SKILLS-INDEX.md` via `--index`
- Phase 2 infra: `work-log` autonomous branch, `morning-briefing` hygiene/template alignment, `manage-projects` deprecated, `related_skills` rename map applied repo-wide
- Phase 4: `cron/jobs.json` morning-briefing + slack-brain prompts aligned (`obsidian-hygiene`, `vault_hygiene_cron.py`, `[[Thoughts]]` taxonomy, env-var paths); `vault-hygiene-design.md` references `obsidian-hygiene`

### Validation snapshot

```
python3 scripts/validate_skills.py --strict
→ 0 errors, 0 warnings, 67 info (bundled-manifest peers without local SKILL.md)
```

Intentional `external_related_skills` remain on: `google-workspace` (himalaya), `native-mcp` (mcporter), `writing-plans` / `subagent-driven-development` (test-driven-development, requesting-code-review), and similar bundled-only peers.

Deprecated: `manage-projects` (`metadata.hermes.deprecated: true`).

## Maintenance workflow (ongoing)

Edit skill in `bes-backup` → `python3 scripts/validate_skills.py --strict` → deploy to VM → verify in fresh session.
