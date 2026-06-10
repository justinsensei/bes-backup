---
name: bes-skill-authoring
description: "Use when creating, editing, or reviewing any Bes SKILL.md — conventions, frontmatter, script placement, validation, and deploy workflow."
version: 2.0.0
author: Bes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [skills, authoring, bes, conventions, skill-md, validator]
    related_skills: [writing-plans]
---

# Authoring Bes Skills

## Overview

Bes skills are durable procedural knowledge stored in the `bes-backup` git repo and deployed to the Hermes runtime on the VM. This skill is the single source of truth for how to create and maintain them consistently.

## Two-tree model

| Tree | Path | Role |
|---|---|---|
| **Source (git)** | `${BES_BACKUP:-$HOME/bes-backup}/skills/<category>/<name>/SKILL.md` | Edit here. Commit to git. |
| **Source scripts** | `${BES_BACKUP:-$HOME/bes-backup}/scripts/` | Operational scripts (cron, hygiene, pollers). |
| **Runtime skills** | `${HERMES_HOME:-$HOME/.hermes}/skills/` | Deployed copy Bes loads at session start. |
| **Runtime scripts** | `${HERMES_HOME:-$HOME/.hermes}/scripts/` | Deployed operational scripts. |

**Rules:**
- Always edit the **repo** first, never `skill_manage(action='create')` for in-repo skills (that writes to `~/.hermes/skills/` only and bypasses git).
- After repo edits: run validator, then deploy to VM (git pull / rsync — whatever Justin uses).
- `skill_manage(action='patch')` and `skill_manage(action='edit')` work on deployed skills for small runtime hotfixes, but mirror changes back into `bes-backup` or they will be lost on next deploy.

## When to Use

- Creating a new skill
- Editing or patching any existing skill
- SOUL.md says "update the skill" after discovering a stale path or pitfall
- Before committing skill changes (run validator)

**Don't use for:** one-off task instructions that won't be reused — those belong in a conversation, not a skill.

## Canonical variables

Use these in skill prose and command examples instead of hardcoded VM paths:

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}}"
HERMES="${HERMES_HOME:-$HOME/.hermes}"
REPO="${BES_BACKUP:-$HOME/bes-backup}"
DAILY_TEMPLATE="${VAULT}/Utilities/Templates/daily_note.md"
```

Canonical daily-note template path: `$OBSIDIAN_VAULT_PATH/Utilities/Templates/daily_note.md` (capital U in Utilities).

## Required frontmatter

Hard requirements (enforced by `scripts/validate_skills.py`):

- Starts with `---` as first bytes (no leading blank line or BOM)
- Closes with `\n---\n` before body
- Parses as YAML
- `name` and `description` present
- `description` ≤ 1024 chars; full file ≤ 100,000 chars
- `name` ≤ 64 chars, lowercase + hyphens

**Canonical shape:**

```yaml
---
name: skill-name
description: "Use when <trigger>. <one-line behavior>."
version: 1.0.0
author: Bes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [short, tags]
    related_skills: [in-repo-skill-names]
    external_related_skills: [bundled-only-peers]   # optional
    deprecated: false                                  # optional
---
```

- `related_skills` lives **only** under `metadata.hermes`, never at YAML root.
- Every `related_skills` entry must match a `name:` in this repo, unless listed in `external_related_skills` (for bundled Hermes peers not committed here, e.g. `himalaya`).
- `description` should start with `Use when` for Bes-native skills.
- No emoji in H1 titles for new or edited skills.

## Script placement

| Type | Location | Examples |
|---|---|---|
| Operational / cron / cross-skill | `bes-backup/scripts/` only | `vault_hygiene.py`, `fetch_slack_brains.py`, `validate_skills.py` |
| Skill-tied CLI wrapper | `skills/<cat>/<name>/scripts/` | `slack.py`, `linear_api.py`, `gws_multi.py` |

**No duplicate basenames** across `scripts/` and `skills/*/scripts/`. Runtime references operational scripts as `${HERMES}/scripts/<name>.py`.

## Directory placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories in this repo: `apple`, `autonomous-ai-agents`, `creative`, `daily-rituals`, `devops`, `gaming`, `mcp`, `media`, `mlops`, `note-taking`, `productivity`, `research`, `social-media`, `software-development`.

Supporting files: `references/`, `scripts/`, `templates/`, `assets/` under the skill directory.

## Peer structure

Minimum sections for Bes-native skills:

```
# Title (no emoji)

## Overview
## When to Use
## <topic sections>
## Common Pitfalls
## Verification Checklist
```

Split content past ~20k chars into `references/*.md`.

## Workflow

1. Survey peers in the target category (`find skills/<category> -name SKILL.md`).
2. Draft or edit in `bes-backup/skills/...`.
3. Validate: `python3 ${REPO}/scripts/validate_skills.py --skill <name>` then `--strict` for full tree.
4. Deploy repo changes to VM (`~/.hermes/skills/`, `~/.hermes/scripts/`).
5. Fresh Bes session: `skill_view(name='<name>')` to confirm loader sees changes.

## Deprecation

Set `metadata.hermes.deprecated: true` and point to the replacement skill in the body. Do not delete skills unless Justin asks.

## Tirith / security scanner

Do not embed pipe-to-interpreter command shapes in skill examples or subagent context blocks (e.g. piping stdout into python3 one-liners, bash, node -e, or curl-to-sh install patterns). Use `jq` for JSON. Use tempfile scripts for Python.

Use `jq` for JSON parsing. For non-trivial Python post-processing, write a script to a tempfile and run `python3 /tmp/foo.py`.

## Validator CLI

```bash
python3 scripts/validate_skills.py                  # all skills
python3 scripts/validate_skills.py --skill work-log
python3 scripts/validate_skills.py --strict         # warnings fail
python3 scripts/validate_skills.py --index          # emit skills/SKILLS-INDEX.md
```

## Common Pitfalls

1. **Using `skill_manage(create)` for repo skills.** Creates a runtime-only copy; git repo won't have it.
2. **`related_skills` at YAML root.** Must be under `metadata.hermes`.
3. **Dangling `related_skills`.** Use `external_related_skills` for peers not in this repo.
4. **Duplicate script files.** One canonical path per operational script.
5. **Hardcoded `/home/justin.guest/`.** Use `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}` patterns.
6. **Expecting current session to see new skills.** Loader is cached at session start; verify in a fresh session.
7. **Four different daily-note template paths.** Only `Utilities/Templates/daily_note.md`.

## Verification Checklist

- [ ] File at `skills/<category>/<name>/SKILL.md` in `bes-backup`
- [ ] `python3 scripts/validate_skills.py --skill <name>` passes
- [ ] `related_skills` resolve in-repo or are in `external_related_skills`
- [ ] No duplicate operational scripts
- [ ] Deployed to `~/.hermes/skills/` on VM
- [ ] Confirmed in fresh `skill_view` session
